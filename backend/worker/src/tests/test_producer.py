import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import logging
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.redis.producer import Producer

logging.disable(logging.CRITICAL)


class TestProducer:
    @pytest.mark.asyncio
    async def test_add_to_stream_returns_message_id(self):
        redis_client = MagicMock()
        redis_client.xadd = AsyncMock(return_value="123-0")
        producer = Producer(redis_client)
        result = await producer.add_to_stream({"key": "value"}, "channel-1")
        assert result == "123-0"
        redis_client.xadd.assert_called_once_with(name="channel-1", fields={"key": "value"})
