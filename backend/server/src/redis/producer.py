from typing import Optional

import redis.exceptions
import logging

logger = logging.getLogger(__name__)
class Producer():
    def __init__(self, redis_client):
        self.redis_client = redis_client

    async def add_to_stream(self, data: dict, stream_channel: str) -> Optional[str]:
        try:
            msg_id = await self.redis_client.xadd(name=stream_channel, id="*", fields=data)
            logger.info(f"Message id {msg_id} added to {stream_channel} stream")
            return msg_id
        
        except (redis.exceptions.ConnectionError, redis.exceptions.TimeoutError) as e:
            logger.warning(f"Transient error sending message to stream: {e}")
            return None
        
        except Exception as e:
            logger.error(f"Error sending message to stream => {e}")
            raise
