import logging
from datetime import date
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.dialects.postgresql import insert

from backend.database.models.conversations import Conversation
from backend.database.models.messages import Message
from backend.database.models.usage_logs import UsageLog

logger = logging.getLogger(__name__)


def save_worker_message(session_factory: sessionmaker, user_id: str, token: str, role: str, content: str):
    session = session_factory()
    try:
        try:
            conversation_id = UUID(token)
            normalized_role = _normalize_message_role(role)
            user_uuid = UUID(user_id)
        except ValueError as exc:
            logger.error(f"Invalid UUID format - token: {token}, user_id: {user_id}: {exc}")
            raise ValueError(f"Invalid token or user_id format: {exc}")

        conversation = (
            session.query(Conversation)
            .filter(Conversation.id == conversation_id)
            .first()
        )

        if not conversation:
            conversation = Conversation(
                id=conversation_id,
                user_id=user_uuid,
                title=(content[:50] if len(content) <= 50 else content[:47] + "...") if normalized_role == "user" and content else "New Chat",
            )
            session.add(conversation)
            session.flush()
        elif conversation.user_id != user_uuid:
            raise PermissionError("Conversation does not belong to user")

        session.add(
            Message(
                conversation_id=conversation.id,
                user_id=user_uuid,
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


def _normalize_message_role(role: str) -> str:
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


def log_worker_usage(session_factory: sessionmaker, user_id: str, model: str | None, total_tokens: int | None, message_count: int | None):
    try:
        with session_factory() as db:
            base_stmt = insert(UsageLog).values(
                user_id=user_id,
                log_date=date.today(),
                model=model or "unknown",
                total_tokens=total_tokens or 0,
                message_count=message_count or 0,
            )
            stmt = base_stmt.on_conflict_do_update(
                constraint="uq_usage_logs_user_date_model",
                set_={
                    "total_tokens": UsageLog.total_tokens + base_stmt.excluded.total_tokens,
                    "message_count": UsageLog.message_count + base_stmt.excluded.message_count,
                    "updated_at": func.now(),
                }
            )
            db.execute(stmt)
            db.commit()
    except Exception as e:
        logger.error("Failed to write metrics to usage_logs database: %s", e)

def get_conversation_history_from_db(session: Session, user_id: str, token: str, limit: int = 20) -> list:
    try:
        try:
            conversation_id = UUID(token)
            user_uuid = UUID(user_id)
        except ValueError as exc:
            logger.error(f"Invalid UUID format - token: {token}, user_id: {user_id}: {exc}")
            return []

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
        if isinstance(exc, PermissionError):
            raise
        logger.error(f"Failed to fetch conversation history from DB for conversation_id: {token}: {exc}")
        return []
