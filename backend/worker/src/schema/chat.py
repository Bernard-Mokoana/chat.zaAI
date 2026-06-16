from datetime import datetime, timezone
from pydantic import BaseModel, Field
from uuid import UUID, uuid4

from datetime import datetime, timezone
from pydantic import BaseModel, Field
from uuid import UUID, uuid4

class Message(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    msg: str
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())