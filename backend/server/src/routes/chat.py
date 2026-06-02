from sqlalchemy.orm import Session
from fastapi import APIRouter, Request, HTTPException, Depends, WebSocket, WebSocketDisconnect, status

from src.socket.connection import ConnectionManager
from src.redis.producer import Producer
from src.redis.config import Redis
from src.redis.stream import StreamConsumer
from src.services.conversation_services import ChatOrchestrator
from src.middlewares.jwt_validation import get_current_user
from src.utils.dbUtils import conversation_service, get_conversation_history_from_db

from backend.database.models.users import User

from backend.database.config.databaseConfig import get_read_db

chat = APIRouter(prefix="/api/v1/chat", tags=["chat"])

manager = ConnectionManager()
redis = Redis()


@chat.post("/token")
async def token_generator(name: str, request: Request, current_user: User = Depends(get_current_user)):
    redis_client = await redis.create_connection()

    return await conversation_service.create_chat_session(
        redis_client=redis_client,
        user_id=str(current_user.id),
        name=name,
    )

@chat.get("/refresh_token")
async def refresh_token(request: Request, token: str, current_user: User = Depends(get_current_user)):
    redis_client = await redis.create_connection()

    try:
        return await conversation_service.get_chat_session(
            redis_client=redis_client,
            token=token,
            user_id=str(current_user.id),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
    
@chat.websocket("/chat")
async def websocket_endpoint(websocket: WebSocket):
    query_params = dict(websocket.query_params)
    token = query_params.get("token")
    chat_token = query_params.get("chat_token")

    if not token or not chat_token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    
    redis_client = await redis.create_connection()

    try:
        await conversation_service.validate_websocket_session(
            redis_client=redis_client,
            access_token=token,
            chat_token=chat_token,
        )
    except ValueError:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    except PermissionError:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    except Exception:
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
        return
    
    producer = Producer(redis_client)
    consumer = StreamConsumer(redis_client)

    orchestrator = ChatOrchestrator(
        manager=manager,
        producer=producer,
        consumer=consumer,
    )

    try:
        await orchestrator.run(websocket, chat_token)
    except WebSocketDisconnect:
        pass  # orchestrator.run's finally block handles disconnect
    # Update connectionManager disconnect to be idempotence

@chat.get("/history/{chat_token}")
async def get_chat_history(
    chat_token: str,
    db: Session = Depends(get_read_db),
    current_user: User = Depends(get_current_user),
):
    try:
        history = get_conversation_history_from_db(
            db=db,
            user_id=str(current_user.id),
            chat_token=chat_token,
            limit=50,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc))

    return {"status": "success", "history": history}
