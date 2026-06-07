import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from config.databaseConfig import Base

from .base import TimestampMixin

if TYPE_CHECKING:
    from .user import User

class ResetPasswordToken(TimestampMixin, Base):
    __tablename__ = "reset_password_token"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash: Mapped[str] = mapped_column(Text, nullable=False, unique=True, index=True)
    jwt_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    ip: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_revoked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_used: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="reset_password_tokens")

    def mark_used(self) -> None:
        self.is_used = True

    def revoke(self) -> None:
        self.is_revoked = True
        self.revoked_at = datetime.utcnow()

    @property
    def is_valid(self) -> bool:
        return (
            not self.is_revoked
            and not self.is_used
            and datetime.utcnow() < self.expires_at.replace(tzinfo=None)
        )

    def __repr__(self) -> str:
        return f"<ResetPasswordToken user_id={self.user_id} used={self.is_used} revoked={self.is_revoked}>"