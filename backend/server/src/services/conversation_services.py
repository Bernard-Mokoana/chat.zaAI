import asyncio
import contextlib
import logging
import redis.exceptions
import uuid

from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from fastapi import WebSocket

from backend.database.models.conversations import Conversation
from backend.database.models.messages import Message

from src.schema.chat import Chat
from src.socket.utils import validate_token
from src.middlewares.rateLimiter import RateLimiterStore, WS_MESSAGE_RULE


logger = logging.getLogger(__name__)

MESSAGE_CHANNEL = "message_channel"
RESPONSE_CHANNEL = "response_channel"

ws_message_limiter = RateLimiterStore()

class ConversationService:
    def save_chat_message(self, db: Session, user_id: str, chat_token: str, role: str, content: str) -> Message:
        normalized_role = self._normalize_message_role(role)

        try:
            conversation_uuid = UUID(chat_token)
        except ValueError:
            raise ValueError(f"Invalid chat_token format: {chat_token}")
        
        try:
             conversation = (
                 db.query(Conversation)
                 .filter(Conversation.id == conversation_uuid)
                 .first()
                 )   
             
             if not conversation:
                 conversation = Conversation(
                     id=conversation_uuid,
                     user_id=UUID(user_id),
                     title=self._build_title(content, normalized_role),
                     )
                 db.add(conversation)
                 db.flush()
                 
             elif str(conversation.user_id) != str(user_id):
                 raise PermissionError("Conversation does not belong to user")
             
             message = Message(
                 conversation_id=conversation.id,
                 user_id=UUID(user_id),
                 role=normalized_role,
                 content=content,
                 )
             
             db.add(message)
             db.commit()
             db.refresh(message)

        except SQLAlchemyError as e:
             db.rollback()
             logger.error(f"Database error saving chat message: {e}")
             raise

        return message

    def _normalize_message_role(self, role: str) -> str:
        role_map = {
            "human": "user",
            "user": "user",
            "bot": "assistant",
            "assistant": "assistant",
            "system": "system",
        }
        normalized_role = role.lower().strip()
        if normalized_role not in role_map:
            raise ValueError(f"Invalid message role: {role}")
        return role_map[normalized_role]

    async def create_chat_session(self, redis_client, user_id: str, name: str) -> dict:
        token = str(uuid.uuid4())
        chat_session = Chat(token=token, user_id=str(user_id), messages=[], name=name)
        payload = chat_session.model_dump()

        try:
            await redis_client.json().set(token, "$", payload)
            await redis_client.expire(token, 3600)
        except redis.exceptions.RedisError as e:
            logger.error(f"Failed to create chat session in Redis: {e}")
            raise

        return payload
    
    async def get_chat_session(self, redis_client, token: str, user_id: str) -> dict:
        data = await redis_client.json().get(token, "$")
        session = self._unwrap_redis_json(data)

        if not session:
            raise ValueError("Session expired or does not exist")
        
        if str(session.get("user_id")) != str(user_id):
            raise PermissionError("Forbidden")
        
        return session
    
    async def validate_websocket_session(self, redis_client, access_token: str, chat_token: str) -> dict:
        token_payload = await validate_token(access_token)

        user_id = token_payload.get("id")
        if not user_id:
            raise PermissionError("Invalid token payload")
        
        session = await self.get_chat_session(
            redis_client=redis_client,
            token=chat_token,
            user_id=str(user_id)
        )

        return {
            "user_id": str(user_id),
            "chat_token": chat_token,
            "session": session,
        }
    
    def _unwrap_redis_json(self, data):
        if isinstance(data, list) and len(data) > 0:
            return data[0]
        return data
    
    def _build_title(self, content: str, role: str) -> str:
        if role == "user" and content:
            return content[:50]
        return "New Chat"
    
class ChatOrchestrator:
    def __init__(self, manager, producer, consumer):
        self.manager = manager
        self.producer = producer
        self.consumer = consumer

    async def run(self, websocket: WebSocket, chat_token: str) -> None:
        listener_task = asyncio.create_task(
            self._response_listener(websocket, chat_token)
        )

        try:
            await self.manager.connect(websocket)

            while True:
                data = await websocket.receive_text()

                result = ws_message_limiter.check(
                    key=chat_token,
                    rule=WS_MESSAGE_RULE,
                )

                if not result.allowed:
                    await self.manager.send_personal_message(
                        "Too many messages. Please wait a moment before sending another one",
                        websocket,
                    )
                    continue

                await self.producer.add_to_stream(
                    {chat_token: data},
                    MESSAGE_CHANNEL,
                )
        finally:
            try:
                self.manager.disconnect(websocket)
            except Exception as e:
                logger.debug(f"Disconnect failed (may already be disconnected): {e}")


            listener_task.cancel()

            with contextlib.suppress(asyncio.CancelledError):
                await listener_task

    async def _response_listener(self, websocket: WebSocket, chat_token: str) -> None:
        last_id = "$"

        while True:
            try:
                response = await self.consumer.consume_stream(
                    stream_channel=RESPONSE_CHANNEL,
                    block=10000,
                    count=1,
                    last_id=last_id,
                )

                if not response:
                    continue
                
                for _, messages in response:
                    for message in messages:
                        message_id, field = message
                        message_id = self._decode(message_id)

                        response_token, response_message = self._extract_response(field)
                        last_id = message_id

                        if chat_token != str(response_token):
                            continue

                        try:
                            await self.manager.send_personal_message(
                                response_message,
                                websocket,
                                )
                        except Exception as e:
                            logger.warning(f"Failed to send response message: {e}")

                        await self.consumer.delete_message(
                            stream_channel=RESPONSE_CHANNEL,
                            message_id=message_id,
                        )
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                logger.error("Error in response listener: %s", exc)

    def _extract_response(self, fields: dict) -> tuple[str | None, str | None]:
        token_key = next(iter(fields.keys()), None)
        message_value = next(iter(fields.values()), None)

        return self._decode(token_key), self._decode(message_value)
    
    def _decode(self, value):
        if isinstance(value, (bytes, bytearray)):
            return value.decode("utf-8")
        return value
    
