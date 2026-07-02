import logging

from fastapi import WebSocket, WebSocketDisconnect, status

from backend.server.src.socket.connection import ConnectionManager
from backend.server.src.redis.producer import Producer
from backend.server.src.redis.config import Redis
from backend.server.src.redis.stream import StreamConsumer
from backend.server.src.services.conversation_services import ChatOrchestrator, ConversationService

logger = logging.getLogger(__name__)


def _extract_access_token(websocket: WebSocket) -> str | None:
    protocol_header = websocket.headers.get("sec-websocket-protocol")
    if not protocol_header:
        return None

    protocols = [value.strip() for value in protocol_header.split(",") if value.strip()]
    return protocols[0] if protocols else None


async def create_token_service(redis: Redis, conversation_service: ConversationService, user_id: str, name: str) -> dict:
    redis_client = await redis.create_connection()
    try:
        return await conversation_service.create_chat_session(
            redis_client=redis_client,
            user_id=user_id,
            name=name,
        )
    finally:
        await redis_client.close()


async def refresh_token_service(redis: Redis, conversation_service: ConversationService, token: str, user_id: str) -> dict:
    redis_client = await redis.create_connection()
    try:
        return await conversation_service.get_chat_session(
            redis_client=redis_client,
            token=token,
            user_id=user_id,
        )
    finally:
        await redis_client.close()


async def handle_websocket_connection(websocket: WebSocket, redis: Redis, manager: ConnectionManager, conversation_service: ConversationService ) -> None:
    query_params = dict(websocket.query_params)
    chat_token = query_params.get("chat_token")
    access_token = _extract_access_token(websocket)

    if not access_token or not chat_token:
        await websocket.accept()
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    redis_client_validation = await redis.create_connection()
    try:
        validated_session = await conversation_service.validate_websocket_session(
            redis_client=redis_client_validation,
            access_token=access_token,
            chat_token=chat_token,
        )
    except (ValueError, PermissionError):
        await websocket.accept()
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    except Exception:
        logger.exception("Unexpected error during websocket session validation")
        await websocket.accept()
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
        return
    finally:
        await redis_client_validation.close()

    redis_client = await redis.create_connection()
    producer = Producer(redis_client)
    consumer = StreamConsumer(redis_client)

    orchestrator = ChatOrchestrator(
        manager=manager,
        producer=producer,
        consumer=consumer,
    )

    try:
        await orchestrator.run(
            websocket,
            chat_token,
            validated_session["user_id"],
            subprotocol=access_token,
        )
    except WebSocketDisconnect:
        pass  
    finally:
        await redis_client.close()
