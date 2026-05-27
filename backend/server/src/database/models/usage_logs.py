from sqlalchemy import Column, DateTime, Integer, String, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from ..config.databaseConfig import Base

class UsageLog(Base):
    __tablename__ = "usage_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    events = Column(String(100), nullable=False)
    total_tokens = Column(Integer, nullable=True)
    message_count = Column(Integer, nullable=True)
    model_name = Column(String(120), nullable=True)    
    log_date = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user = relationship("User", back_populates="usage_logs")