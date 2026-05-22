import asyncio
import contextlib
import logging
from fastapi import APIRouter, WebSocket, Request, HTTPException, Depends, WebSocketDisconnect, status
import uuid

from ..socket.utils import validate_token
from ..socket.connection import ConnectionManager
from ..redis.producer import Producer
from ..redis.config import Redis
from ..schema.chat import Chat
from ..redis.stream import StreamConsumer
from ..redis.cache import Cache
from src.middlewares.jwt_validation import get_current_user
from src.database.models.users import User
from src.utils.token import Token

logger = logging.getLogger(__name__)

chat = APIRouter(prefix="/api/v1/chat", tags=["chat"])
manager = ConnectionManager()
redis = Redis()
token_util = Token()

@chat.post("/token")
async def token_generator(name: str, request: Request, current_user: User = Depends(get_current_user)):
    token = str(uuid.uuid4())
    
    redis_client = await redis.create_connection()
    chat_session = Chat(token=token, user_id=str(current_user.id), messages=[], name=name)

    payload = chat_session.model_dump()

    await redis_client.json().set(str(token), "$", payload)
    await redis_client.expire(str(token), 3600)

    return payload

@chat.get("/refresh_token")
async def refresh_token(request: Request, token: str, current_user: User = Depends(get_current_user)):
    json_client = redis.create_json_connection()
    cache = Cache(json_client)
    data = cache.get_chat_history(token)

    if (data) == None:
        raise HTTPException(
            status_code=400, detail="Session expired or does not exist"
        )
    
    if str(data.get("user_id")) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Forbidden")
    
    return data


@chat.websocket("/chat")
async def websocket_endpoint(websocket: WebSocket):
    query_params = dict(websocket.query_params)
    token = query_params.get("token")
    chat_token = query_params.get("chat_token")

    if not token or not chat_token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    try:
        token_payload = await validate_token(token)
    except ValueError:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    except Exception:
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
        return

    redis_client = await redis.create_connection()

    user_id = token_payload.get("id")
    if not user_id:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    user_id = str(user_id)

    session = await redis_client.json().get(chat_token, "$")

    if isinstance(session, list) and len(session) > 0:
        session_data = session[0]
    else:
        session_data = session

    if not session_data or not isinstance(session_data, dict):
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    session_user_id = str(session_data.get("user_id"))

    if session_user_id != user_id:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await manager.connect(websocket)
    producer = Producer(redis_client)
    consumer = StreamConsumer(redis_client)
    last_id = "$"

    async def response_listener():
        nonlocal last_id
        while True:
            try:
                response = await consumer.consume_stream(
                    stream_channel="response_channel",
                    block=10000,
                    count=1,
                    last_id=last_id
                    )
                
                if not response:
                    continue
                
            
                for stream, messages in response:
                    for message in messages:
                        message_id = message[0].decode("utf-8") if isinstance(message[0], (bytes, bytearray)) else message[0]
                        token_key = next(iter(message[1].keys()), None)
                        message_value = next(iter(message[1].values()), None)
                        
                        response_token = token_key.decode("utf-8") if isinstance(token_key, (bytes, bytearray)) else token_key
                        last_id = message_id
                        
                        if chat_token == str(response_token):
                            response_message = message_value.decode("utf-8") if isinstance(message_value, (bytes, bytearray)) else message_value
                            try:
                                await manager.send_personal_message(response_message, websocket)
                                await consumer.delete_message(stream_channel="response_channel", message_id=message_id)
                            except asyncio.CancelledError:
                                raise
                            except Exception as e:
                                logger.error(f"Failed to send message: {e}")
            except asyncio.CancelledError:
                raise
            except Exception as e:
                logger.error(f"Error in response listener: {e}")

    listener_task = asyncio.create_task(response_listener())

    try:
        while True:
            data = await websocket.receive_text()
            stream_data = {chat_token: data}
            await producer.add_to_stream(stream_data, "message_channel")

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    finally:
        listener_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await listener_task
