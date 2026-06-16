from sqlalchemy.orm import Session
from backend.database.models.usage_logs import UsageLog

def create_usage_log(db: Session, user_id: str, event_type: str, model_name: str | None = None, total_tokens: int | None = None, 
                     message_count: int | None = None) -> UsageLog:
    
    log_entry = UsageLog(
        user_id=user_id,
        events=event_type,
        model_name=model_name,
        total_tokens=total_tokens,
        message_count=message_count
    )
    db.add(log_entry)
    db.flush()
    db.refresh(log_entry)
    return log_entry