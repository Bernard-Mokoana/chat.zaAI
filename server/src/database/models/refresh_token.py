from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Text, func  
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from ..config.databaseConfig import Base

class RefreshToken(Base):
    __tablename__ = "refresh_token"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token = Column(String(512), unique=True, nullable=False, index=True)
    jwt_id = Column(Text, nullable=False, index=True)
    user_agent = Column(Text, nullable=True)
    ip = Column(Text, nullable=True)
    is_revoked = Column(Boolean, default=False, nullable=False)
    replaced_by = Column(Text, nullable=True)
    revoked_at = Column(DateTime(timezone=True), nullable=True)    
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False) 
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False) 

    user = relationship("User", back_populates="refresh_tokens")