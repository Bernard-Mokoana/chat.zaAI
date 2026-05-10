import asyncio
import contextlib
import logging
from fastapi import APIRouter, WebSocket, Request, HTTPException, Depends, WebSocketDisconnect
import uuid

from ..socket.connection import ConnectionManager
from ..socket.utils import get_token
from ..redis.producer import Producer
from ..redis.config import Redis
from ..schema.chat import Chat
from ..redis.stream import StreamConsumer
from ..redis.cache import Cache
from src.services.jwt_validation import get_current_user
from src.database.models.users import User
from src.utils.token import Token

chat = APIRouter(prefix="/api/v1/chat", tags=["chat"])
manager = ConnectionManager()
redis = Redis()
token_util = Token()
logger = logging.getLogger(__name__)

@chat.post("/token")
async def token_generator(name: str, request: Request, current_user: User = Depends(get_current_user)):
    token = str(uuid.uuid4())

    if name == "":
        raise HTTPException(status_code=400, detail={
            "loc": "name", "message": "Enter a valid name"
        })
    
    redis_client = await redis.create_connection()
    chat_session = Chat(token=token, user_id=str(current_user.id), messages=[], name=name)

    payload = chat_session.model_dump()
    payload["user_id"] = str(current_user.id)

    await redis_client.json().set(str(token), "$", chat_session.model_dump())
    await redis_client.expire(str(token), 3600)

    return payload

@chat.get("/refresh_token")
async def refresh_token(request: Request, token: str, current_user: User = Depends(get_current_user)):
    json_client = redis.create_json_connection()
    cache = Cache(json_client)
    data = await cache.get_chat_history(token)

    if (data) == None:
        raise HTTPException(
            status_code=400, detail="Session expired or does not exist"
        )
    
    if str(data.get("user_id")) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Forbidden")
    
    return data


@chat.websocket("/chat")
async def websocket_endpoint(websocket: WebSocket, chat_token: str, token_payload=Depends(get_token)):
    redis_client = await redis.create_connection()

    user_id = str(token_payload.get("id"))
    logger.info("[WS DEBUG] handshake start user_id=%s chat_token=%s", user_id, chat_token)
    if not user_id:
        logger.warning("[WS DEBUG] missing user_id in token payload=%s", token_payload)
        await websocket.close(code=1008)
        return
    user_id = str(user_id)

    session = await redis_client.json().get(chat_token, "$")
    session_data = session[0] if isinstance(session, list) and session else session
    logger.info("[WS DEBUG] redis session raw=%s", session)
    logger.info(
        "[WS DEBUG] session_data exists=%s session_user_id=%s",
        bool(session_data),
        str(session_data.get("user_id")) if session_data else None,
    )
    if not session_data or str(session_data.get("user_id")) != user_id:
        logger.warning(
            "[WS DEBUG] ownership check failed user_id=%s session_user_id=%s chat_token=%s",
            user_id,
            str(session_data.get("user_id")) if session_data else None,
            chat_token,
        )
        await websocket.close(code=1008)
        return

    await manager.connect(websocket)
    logger.info("[WS DEBUG] websocket accepted user_id=%s chat_token=%s", user_id, chat_token)
    producer = Producer(redis_client)
    consumer = StreamConsumer(redis_client)
    last_id = "$"

    async def response_listener():
        nonlocal last_id
        while True:
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
                        await manager.send_personal_message(response_message, websocket)
                        await consumer.delete_message(stream_channel="response_channel", message_id=message_id)

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
