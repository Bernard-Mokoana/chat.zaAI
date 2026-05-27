import os
from urllib.parse import urlparse
from dotenv import load_dotenv
import redis
import redis.asyncio as redis_async

load_dotenv()

class Redis():
    def __init__(self):
        self.url = os.environ["REDIS_URL"]

    async def create_connection(self):
        return redis_async.from_url(self.url, db=0)
    
    def create_json_connection(self):
        return redis.Redis.from_url(self.url, decode_responses=True)

