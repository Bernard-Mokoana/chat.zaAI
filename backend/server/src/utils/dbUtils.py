from uuid import UUID

from sqlalchemy.orm import Session

from src.services.conversation_services import ConversationService
from backend.database.models.conversations import Conversation
from backend.database.models.messages import Message

conversation_service = ConversationService()

def save_chat_message(db: Session, user_id: str, chat_token: str, role: str, content: str):
    return conversation_service.save_chat_message(
        db=db,
        user_id=user_id,
        chat_token=chat_token,
        role=role,
        content=content
    )

def get_conversation_history_from_db(
    db: Session,
    user_id: str,
    chat_token: str,
    limit: int = 20,
) -> list[dict[str, str]]:
    try:
        conversation_id = UUID(chat_token)
        user_uuid = UUID(user_id)
    except ValueError as exc:
        raise ValueError("Invalid conversation or user id") from exc

    conversation = (
        db.query(Conversation)
        .filter(Conversation.id == conversation_id)
        .first()
    )

    if not conversation:
        return []

    if conversation.user_id != user_uuid:
        raise PermissionError("Conversation does not belong to user")

    messages = (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.desc())
        .limit(limit)
        .all()
    )

    return [
        {"role": msg.role, "msg": msg.content}
        for msg in reversed(messages)
    ]
