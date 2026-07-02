from fastapi import WebSocket, WebSocketDisconnect, status

from backend.server.src.socket.connection import ConnectionManager
from backend.server.src.redis.producer import Producer
from backend.server.src.redis.config import Redis
from backend.server.src.redis.stream import StreamConsumer
from backend.server.src.services.conversation_services import ChatOrchestrator, ConversationService


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


async def create_websocket_ticket_service(
    redis: Redis,
    conversation_service: ConversationService,
    user_id: str,
    chat_token: str,
) -> dict:
    redis_client = await redis.create_connection()
    try:
        await conversation_service.get_chat_session(
            redis_client=redis_client,
            token=chat_token,
            user_id=user_id,
        )
        ws_ticket = await conversation_service.create_websocket_ticket(
            redis_client=redis_client,
            user_id=user_id,
            chat_token=chat_token,
        )
        return {"ws_ticket": ws_ticket}
    finally:
        await redis_client.close()


async def handle_websocket_connection(websocket: WebSocket, redis: Redis, manager: ConnectionManager, conversation_service: ConversationService ) -> None:
    query_params = dict(websocket.query_params)
    chat_token = query_params.get("chat_token")
    ws_ticket = query_params.get("ws_ticket")

    if not ws_ticket or not chat_token:
        await websocket.accept()
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    redis_client_validation = await redis.create_connection()
    try:
        validated_session = await conversation_service.validate_websocket_ticket(
            redis_client=redis_client_validation,
            ws_ticket=ws_ticket,
            chat_token=chat_token,
        )
    except (ValueError, PermissionError):
        await websocket.accept()
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    except Exception:
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
        await orchestrator.run(websocket, chat_token, validated_session["user_id"])
    except WebSocketDisconnect:
        pass  
    finally:
        await redis_client.close()
