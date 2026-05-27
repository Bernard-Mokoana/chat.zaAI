from datetime import datetime
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid

class Message(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    msg: str
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())