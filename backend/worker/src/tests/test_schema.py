import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pytest
from uuid import UUID
from datetime import datetime, timezone
from src.schema.chat import Message


class TestMessageSchema:
    def test_creates_with_required_fields(self):
        msg = Message(msg="Hello")
        assert msg.msg == "Hello"

    def test_generates_uuid(self):
        msg = Message(msg="Hello")
        assert isinstance(msg.id, UUID)

    def test_generates_iso_timestamp(self):
        msg = Message(msg="Hello")
        ts = msg.timestamp
        datetime.fromisoformat(ts)  # should not raise
        assert ts.endswith("+00:00") or ts.endswith("Z")

    def test_defaults_can_be_overridden(self):
        custom_id = UUID("12345678-1234-5678-1234-567812345678")
        custom_ts = "2024-01-01T00:00:00Z"
        msg = Message(id=custom_id, msg="Hi", timestamp=custom_ts)
        assert msg.id == custom_id
        assert msg.timestamp == custom_ts
