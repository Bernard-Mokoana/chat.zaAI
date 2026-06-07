import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.config.databaseConfig import Base

from .base import TimestampMixin

if TYPE_CHECKING:
    from .user import User


class EmailVerificationToken(TimestampMixin, Base):
    __tablename__ = "email_verification_token"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash: Mapped[str] = mapped_column(Text, nullable=False, unique=True, index=True)
    jwt_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    ip: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_revoked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    replaced_by: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="email_verification_tokens")

    def mark_verified(self) -> None:
        self.is_verified = True

    def revoke(self) -> None:
        self.is_revoked = True
        self.revoked_at = datetime.now(timezone.utc)

    @property
    def is_valid(self) -> bool:
        return (
            not self.is_revoked
            and not self.is_verified
            and datetime.now(timezone.utc) < self.expires_at.replace(tzinfo=None)
        )

    def __repr__(self) -> str:
        return f"<EmailVerificationToken user_id={self.user_id} verifies={self.is_verified} revoked={self.is_revoked}>"