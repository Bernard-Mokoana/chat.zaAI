from unittest.mock import AsyncMock

import pytest
from backend.server.src.redis.stream import StreamConsumer

from redis.exceptions import ConnectionError as RedisConnectionError
from redis.exceptions import TimeoutError as RedisTimeoutError


@pytest.mark.asyncio
class TestStreamConsumer:

    @pytest.fixture(autouse=True)
    def setup_method(self):
        self.mock_redis_client = AsyncMock()
        self.consumer = StreamConsumer(self.mock_redis_client)
        self.channel = "response_channel"

    async def test_consume_stream_happy_path(self):
        mock_response = [[b"response_channel", [(b"msg-id-1", {b"data": b"value"})]]]
        self.mock_redis_client.xread.return_value = mock_response

        result = await self.consumer.consume_stream(
            count=1, block=1000, stream_channel=self.channel
        )

        assert result == mock_response
        self.mock_redis_client.xread.assert_called_once_with(
            streams={self.channel: "$"}, count=1, block=1000
        )

    async def test_consume_stream_transient_error(self):
        self.mock_redis_client.xread.side_effect = RedisTimeoutError(
            "Stream blocking timeout"
        )

        result = await self.consumer.consume_stream(
            count=1, block=1000, stream_channel=self.channel
        )

        assert result == []

    async def test_delete_message_happy_path(self):
        self.mock_redis_client.xdel.return_value = 1

        result = await self.consumer.delete_message(self.channel, "msg-id-1")

        assert result is True
        self.mock_redis_client.xdel.assert_called_once_with(self.channel, "msg-id-1")

    async def test_delete_message_error(self):
        self.mock_redis_client.xdel.side_effect = RedisConnectionError("Redis offline")

        result = await self.consumer.delete_message(self.channel, "msg-id-1")

        assert result is False
