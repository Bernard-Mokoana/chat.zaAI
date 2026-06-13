import os
from dotenv import load_dotenv
import redis.asyncio as redis_async
import redis

load_dotenv()

class Redis():
    def __init__(self):
        self.url = os.environ.get('REDIS_URL')
        if not self.url:
            raise ValueError("REDIS_URL is required")

    async def create_connection(self):
        return redis_async.from_url(
            self.url,
            db=0,
            retry_on_timeout=True,
            socket_keepalive=True,
            socket_connect_timeout=10,
            socket_timeout=20,
        )
    
    def create_json_connection(self):
        return redis.Redis.from_url(self.url, decode_responses=True)
