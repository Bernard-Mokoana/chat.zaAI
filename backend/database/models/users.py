import uuid 
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.config.databaseConfig import Base

from .base import SoftDeleteMixin, TimestampMixin

if TYPE_CHECKING:
    from .audit_log import AuditLog
    from .conversations import Conversation
    from .messages import Message
    from .tiers import Tier
    from .email_verification_token import EmailVerificationToken
    from .refresh_token import RefreshToken
    from .reset_password_token import ResetPasswordToken
    from .usage_logs import UsageLog

class User(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(250), nullable=False)
    email: Mapped[str] = mapped_column(String(250), nullable=False, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(250), nullable=True)
    tier_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tiers.id", ondelete="RESTRICT"), nullable=False, index=True)
    last_active_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    tier: Mapped["Tier"] = relationship("Tier", back_populates="users")
    conversations: Mapped[list["Conversation"]] = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")
    messages: Mapped[list["Message"]] = relationship("Message", back_populates="user", cascade="all, delete-orphan")
    usage_logs: Mapped[list["UsageLog"]] = relationship("UsageLog", back_populates="user", cascade="all, delete-orphan")
    refresh_tokens: Mapped[list["RefreshToken"]] = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")
    email_verification_tokens: Mapped[list["EmailVerificationToken"]] = relationship("EmailVerificationToken", back_populates="user", cascade="all, delete-orphan")
    reset_password_tokens: Mapped[list["ResetPasswordToken"]] = relationship("ResetPasswordToken", back_populates="user", cascade="all, delete-orphan")
    audit_logs: Mapped[list["AuditLog"]] = relationship("AuditLog", back_populates="user")

    def __repr__(self) -> str:
        return f"<User email={self.email!r} tier_id={self.tier_id}>"
