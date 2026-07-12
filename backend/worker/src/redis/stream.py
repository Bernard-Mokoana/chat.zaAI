import redis.asyncio as redis_async

class StreamConsumer:
    def __init__(self, redis_client: redis_async.Redis):
        self.redis_client = redis_client

    async def consume_stream(self, stream_channel, count: int, block: int, last_id: str = '0-0'):
        response = await self.redis_client.xread(
            streams={stream_channel: last_id}, count=count, block=block
        )
        return response

    async def delete_message(self, stream_channel, message_id):
        return await self.redis_client.xdel(stream_channel, message_id)