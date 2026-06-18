import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import asyncio
import logging
import signal
import threading

from backend.database.config.databaseConfig import sessionPrimary

from redis.exceptions import ConnectionError as RedisConnectionError

from src.redis.config import RedisManager
from src.redis.cache import Cache
from src.redis.stream import StreamConsumer
from src.redis.producer import Producer
from src.model.gptj import GPT

from src.config.settings import get_model_query_timeout, STREAM_CHANNEL
from src.handlers.MessageHandler import MessageHandler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

redis_manager = RedisManager()
shutdown_event = threading.Event()

RETRY_BACKOFF_SEC = 5
BLOCK_TIMEOUT_MS = 5000 

def handle_shutdown(signum, frame):
    logger.info("Received shutdown signal, stopping worker...")
    shutdown_event.set()

signal.signal(signal.SIGTERM, handle_shutdown)
signal.signal(signal.SIGINT, handle_shutdown)


async def main() -> None:
    async_client = await redis_manager.get_async_client()
    json_client = redis_manager.create_sync_json_client()

    consumer = redis_manager.consumer
    producer = Producer(async_client)
    cache = Cache(json_client)
    gpt_client = GPT()
    model_timeout = get_model_query_timeout()

    handler = MessageHandler(
        cache=cache,
        producer=producer,
        consumer=consumer,
        gpt_client=gpt_client,
        model_timeout=model_timeout,
        session_factory=sessionPrimary
    )

    logger.info("Stream consumer started, waiting for messages on '%s'", STREAM_CHANNEL)

    while not shutdown_event.is_set():
        try:
            response = await consumer.consume_stream(
                stream_channel=STREAM_CHANNEL, count=10, block=BLOCK_TIMEOUT_MS
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

            try:
                await async_client.aclose()
                json_client.close()
            except Exception:
                pass

            async_client = await redis_manager.get_async_client()
            json_client = redis_manager.get_async_client()
            consumer = redis_manager.consumer
            producer = Producer(async_client)
            cache = Cache(json_client)

            handler = MessageHandler(
                cache=cache,
                producer=producer,
                consumer=consumer,
                gpt_client=gpt_client,
                model_timeout=model_timeout,
                session_factory=sessionPrimary
            )

        except Exception:
            logger.exception("Unexpected error in consumer loop; continuing")
    
    logger.info("Worker shutdown complete")
    await async_client.aclose()
    json_client.close()


if __name__ == "__main__":
    asyncio.run(main())