import uuid 
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import TimestampMixin

from backend.database.config.databaseConfig import Base

if TYPE_CHECKING:
    from .users import User

class Tier(TimestampMixin, Base):
    __tablename__ = "tiers"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(50), nullable=True, unique=True)
    token_limit: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment="0 = unlimited")
    message_limit: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment="0 = unlimited")
    price_cents: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    users: Mapped[list["User"]] = relationship("User", back_populates="tier")

    def __repr__(self) -> str:
        return f"<Tier name={self.name!r} price_cents={self.price_cents}>"