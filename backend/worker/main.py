import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import asyncio
import logging

from backend.database.config.databaseConfig import SessionPrimary

from redis.exceptions import ConnectionError as RedisConnectionError

from src.redis.config import Redis
from src.redis.cache import Cache
from src.redis.stream import StreamConsumer
from src.redis.producer import Producer
from src.model.gptj import GPT

from src.config.settings import get_model_query_timeout, STREAM_CHANNEL
from src.handlers.MessageHandler import MessageHandler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

redis_client = Redis()

RETRY_BACKOFF_SEC = 5


async def main() -> None:
    json_client = redis_client.create_json_connection()
    redis_conn = await redis_client.create_connection()

    consumer = StreamConsumer(redis_conn)
    producer = Producer(redis_conn)
    cache = Cache(json_client)
    gpt_client = GPT()
    model_timeout = get_model_query_timeout()

    handler = MessageHandler(
        cache=cache,
        producer=producer,
        consumer=consumer,
        gpt_client=gpt_client,
        model_timeout=model_timeout,
        session_factory=SessionPrimary
    )

    logger.info("Stream consumer started, waiting for messages on '%s'", STREAM_CHANNEL)

    while True:
        try:
            response = await consumer.consume_stream(
                stream_channel=STREAM_CHANNEL, count=1, block=5000
            )
            if not response:
                continue

            for _stream_name, messages in response:
                for message in messages:
                    await handler.handle(message)

        except RedisConnectionError:
            logger.error(
                "Redis connection failed. Retrying in %d seconds...", RETRY_BACKOFF_SEC
            )
            await asyncio.sleep(RETRY_BACKOFF_SEC)

        except Exception:
            logger.exception("Unexpected error in consumer loop; continuing")


if __name__ == "__main__":
    asyncio.run(main())