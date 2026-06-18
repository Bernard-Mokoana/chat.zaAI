import logging
from .config import Redis
from redis.exceptions import ConnectionError as RedisConnectionError, TimeoutError as RedisTimeoutError

logger = logging.getLogger(__name__)

class StreamConsumer:
    def __init__(self, redis_client):
        self.redis_client = redis_client

    async def consume_stream(self, count: int, block: int, stream_channel, last_id: str = "$"):
        try:
            response = await self.redis_client.xread(
                streams={stream_channel: last_id}, count=count, block=block
            )
            return response
        except (RedisTimeoutError, RedisConnectionError) as exc:
            logger.warning("Transient Redis stream read error: %s", exc)
            return []
    
    async def delete_message(self, stream_channel, message_id):
        try:
            await self.redis_client.xdel(stream_channel, message_id)
            return True
        except(RedisTimeoutError, RedisConnectionError) as e: 
            logger.warning(f"Failed to delete message {message_id} from {stream_channel}: {e}")
            return False
        