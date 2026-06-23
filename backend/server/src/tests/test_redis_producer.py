import pytest
from unittest.mock import AsyncMock
import redis.exceptions

from backend.server.src.redis.producer import Producer

@pytest.mark.asyncio
class TestProducer:
    @pytest.fixture(autouse=True)
    def setup_method(self):
        self.mock_redis_client = AsyncMock()
        self.producer = Producer(self.mock_redis_client)
        self.channel = "message_channel"
        self.data = {"token": "chat-uuid"}

    async def test_add_to_stream_happy_path(self):
        self.mock_redis_client.xadd.return_value = b"12345-0"

        result = await self.producer.add_to_stream(self.data, self.channel)

        assert result == b"12345-0"
        self.mock_redis_client.xadd.assert_called_once_with(name=self.channel, id="*", fields=self.data)

    async def test_add_to_stream_transient_error(self):
        self.mock_redis_client.xadd.side_effect = redis.exceptions.TimeoutError("Network latency")

        result = await self.producer.add_to_stream(self.data, self.channel)

        assert result is None

    async def test_add_to_stream_critical_error(self):
        self.mock_redis_client.xadd.side_effect = Exception("System Out of Memory")

        with pytest.raises(Exception, match="System Out of Memory"):
            await self.producer.add_to_stream(self.data, self.channel)