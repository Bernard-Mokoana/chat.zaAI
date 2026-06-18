import logging

logger = logging.getLogger(__name__)
class Producer:
    def __init__(self, redis_client):
        self.redis_client = redis_client

    async def add_to_stream(self, data: dict, stream_channel) -> str:
        msg_id = await self.redis_client.xadd(name=stream_channel, fields=data)
        logger.info("Message id %s added to %s stream", msg_id, stream_channel)
        return msg_id