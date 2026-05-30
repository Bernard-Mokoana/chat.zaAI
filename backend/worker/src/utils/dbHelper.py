import logging
from uuid import UUID

from sqlalchemy.orm import sessionmaker

from backend.database.models.conversations import Conversation
from backend.database.models.messages import Message
from backend.database.models.usage_logs import UsageLog

logger = logging.getLogger(__name__)


def save_worker_message(session_factory: sessionmaker, user_id: str, token: str, role: str, content: str):
    try:
        with session_factory() as db:
            conversation_id = UUID(token)
            normalized_role = role.lower()

            conversation = (
                db.query(Conversation)
                .filter(Conversation.id == conversation_id)
                .first()
            )

            if not conversation:
                conversation = Conversation(
                    id=conversation_id,
                    user_id=UUID(user_id),
                    title=content[:50] if normalized_role == "human" and content else "New Chat",
                )
                db.add(conversation)
                db.flush()

            db.add(
                Message(
                    conversation_id=conversation.id,
                    role=normalized_role,
                    content=content,
                )
            )
            db.commit()
    except Exception as e:
        logger.error(f"Failed to save worker messages: {e}")

def log_worker_usage(session_factory: sessionmaker, user_id: str, event_type: str, model_name: str | None, total_tokens: int | None, message_count: int | None):
    try:
        with session_factory() as db:
            db.add(
                UsageLog(
                    user_id=user_id,
                    events=event_type,
                    model_name=model_name,
                    total_tokens=total_tokens,
                    message_count=message_count,
                )
            )
            db.commit()
    except Exception as e:
        logger.error("Failed to write metrics to usage_logs database: %s", e)
