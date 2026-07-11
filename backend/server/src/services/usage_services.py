from backend.database.models.usage_logs import UsageLog
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session


def create_usage_log(
    db: Session,
    user_id: str,
    event_type: str,
    model: str | None = None,
    total_tokens: int | None = None,
    message_count: int | None = None,
) -> UsageLog:

    log_entry = UsageLog(
        user_id=user_id,
        event_type=event_type,
        model=model,
        total_tokens=total_tokens if total_tokens is not None else 0,
        message_count=message_count if message_count is not None else 0,
    )
    db.add(log_entry)
    try:
        db.commit()
        db.refresh(log_entry)
        return log_entry
    except SQLAlchemyError:
        db.rollback()
        raise
