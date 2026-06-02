import logging
from uuid import UUID

from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError

from backend.database.models.conversations import Conversation
from backend.database.models.messages import Message
from backend.database.models.usage_logs import UsageLog

logger = logging.getLogger(__name__)


def save_worker_message(session_factory: sessionmaker, user_id: str, token: str, role: str, content: str):
    session = session_factory()
    try:
        conversation_id = UUID(token)
        normalized_role = role.lower()
        user_uuid = UUID(user_id)

        conversation = (
            session.query(Conversation)
            .filter(Conversation.id == conversation_id)
            .first()
        )

        if not conversation:
            conversation = Conversation(
                id=conversation_id,
                user_id=user_uuid,
                title=content[:50] if normalized_role == "human" and content else "New Chat",
            )
            session.add(conversation)
            session.flush()
        elif conversation.user_id != user_uuid:
            raise PermissionError("Conversation does not belong to user")

        session.add(
            Message(
                conversation_id=conversation.id,
                role=normalized_role,
                content=content,
            )
        )
        session.commit()
        logger.info("Successfully persisted %s message to DB for session token %s", role, token)

    except SQLAlchemyError as exc:
         session.rollback()
         logger.error(f"SQLAlchemy error during save_worker_message for token {token}: {exc}")
         raise
    
    except Exception as exc:
         session.rollback()
         logger.error(f"Unexpected error during save_worker_message for token: {token}: {exc}")
         raise
    
    finally:
         session.close()

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

def get_conversation_history_from_db(session: Session, user_id: str, token: str, limit: int = 20) -> list:
    try:
        conversation_id = UUID(token)
        user_uuid = UUID(user_id)

        conversation = (
            session.query(Conversation)
            .filter(Conversation.id == conversation_id)
            .first()
        )

        if not conversation:
            return []

        if conversation.user_id != user_uuid:
            raise PermissionError("Conversation does not belong to user")

        messages = (
            session.query(Message)
            .filter(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.desc())
            .limit(limit)
            .all()
        )

        return [
            {"role": msg.role, "msg": msg.content}
            for msg in reversed(messages)
            ]
    
    except Exception as exc:
        logger.error(f"Failed to fetch conversation history from DB for conversation_id: {token}: {exc}")
        return []
