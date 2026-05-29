import logging

from sqlalchemy.orm import sessionmaker

from backend.server.src.services.conversation_services import save_chat_message
from backend.server.src.services.usage_services import create_usage_log

logger = logging.getLogger(__name__)


def save_worker_message(session_factory: sessionmaker, user_id: str, token: str, role: str, content: str):
    try:
        with session_factory() as db:
            save_chat_message(
                db,
                user_id=user_id,
                chat_token=token,
                role=role,
                content=content,
                )
    except Exception as e:
        logger.error(f"Failed to save worker messages: {e}")

def log_worker_usage(session_factory: sessionmaker, user_id: str, event_type: str, model_name: str | None, total_tokens: int | None, message_count: int | None):
    try:
        with session_factory() as db:
            create_usage_log(
                db,
                user_id=user_id,
                event_type=event_type,
                model_name=model_name,
                total_tokens=total_tokens,
                message_count=message_count,
            )
    except Exception as e:
        logger.error("Failed to write metrics to usage_logs database: %s", e)
