import os
from urllib.parse import urlparse
from dotenv import load_dotenv
import redis
import redis.asyncio as redis_async

from src.redis.stream import StreamConsumer

load_dotenv()

class RedisManager:
    def __init__(self):
        self.url = os.environ.get("REDIS_URL")
        if not self.url:
            raise ValueError("REDIS_URL environment variable must be set.")
        
        self.shared_redis_client = redis_async.from_url(
            self.url,
            decode_responses=True,
            socket_timeout=60,            
            socket_connect_timeout=10,     
            health_check_interval=30
        )

        self.consumer = StreamConsumer(redis_client=self.shared_redis_client)

    async def get_async_client(self) -> redis_async.Redis:
        return self.shared_redis_client
    
    def create_sync_json_client(self) -> redis.Redis:
        return redis.Redis.from_url(self.url, decode_responses=True)

    async def create_connection(self):
        return redis_async.from_url(self.url, db=0)
    
    def create_json_connection(self):
        return redis.Redis.from_url(self.url, decode_responses=True)

