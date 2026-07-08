import uuid
from datetime import datetime, timezone
from typing import List

from pydantic import BaseModel, Field


class Message(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    msg: str
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class Chat(BaseModel):
    token: str
    user_id: str
    messages: List[Message]
    name: str
    session_start: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
