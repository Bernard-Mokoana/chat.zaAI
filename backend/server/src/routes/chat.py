import logging

from sqlalchemy.orm import Session
from fastapi import APIRouter, Header, Request, HTTPException, Depends, WebSocket

from backend.server.src.socket.connection import ConnectionManager
from backend.server.src.redis.config import Redis
from backend.server.src.services.conversation_services import ConversationService
from backend.server.src.middlewares.jwt_validation import get_current_user
from backend.server.src.utils.dbUtils import get_conversation_history_from_db
from backend.server.src.services.chat_services import create_token_service, refresh_token_service, handle_websocket_connection

from backend.database.models.users import User
from backend.database.config.databaseConfig import get_read_db

chat = APIRouter(prefix="/api/v1/chat", tags=["chat"])

manager = ConnectionManager()
redis = Redis()
conversation_service = ConversationService()

logger = logging.getLogger(__name__)


@chat.post("/token")
async def token_generator(name: str, request: Request, current_user: User = Depends(get_current_user)):
    token_service = await create_token_service(
        redis=redis,
        conversation_service=conversation_service,
        user_id=str(current_user.id),
        name=name,
    )
    return token_service


@chat.get("/refresh_token")
async def refresh_token(request: Request, x_chat_token: str = Header(..., alias="X-Chat-Token"), current_user: User = Depends(get_current_user)):
    try:
        result = await refresh_token_service(
            redis=redis,
            conversation_service=conversation_service,
            token=x_chat_token,
            user_id=str(current_user.id),
        )
        return result
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc))


@chat.websocket("/chat")
async def websocket_endpoint(websocket: WebSocket):
    await handle_websocket_connection(
        websocket=websocket,
        redis=redis,
        manager=manager,
        conversation_service=conversation_service,
    )


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