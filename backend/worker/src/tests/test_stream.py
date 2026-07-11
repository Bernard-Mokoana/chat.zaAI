import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import logging
import pytest
from unittest.mock import AsyncMock, MagicMock

from src.redis.stream import StreamConsumer

logging.disable(logging.CRITICAL)


class TestStreamConsumer:
    async def test_consume_stream_calls_xread(self):
        redis_client = MagicMock()
        redis_client.xread = AsyncMock(return_value=[("stream-1", [("msg-1", {"f": "v"})])])
        consumer = StreamConsumer(redis_client)
        result = await consumer.consume_stream("stream-1", count=10, block=5000)
        redis_client.xread.assert_called_once_with(
            streams={"stream-1": "0-0"}, count=10, block=5000
        )
        assert result == [("stream-1", [("msg-1", {"f": "v"})])]

    async def test_delete_message_calls_xdel(self):
        redis_client = MagicMock()
        redis_client.xdel = AsyncMock(return_value=1)
        consumer = StreamConsumer(redis_client)
        result = await consumer.delete_message("stream-1", "msg-1")
        redis_client.xdel.assert_called_once_with("stream-1", "msg-1")
        assert result == 1
