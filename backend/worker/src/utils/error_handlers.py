import logging

from src.redis.cache import Cache
from src.redis.producer import Producer
from src.redis.stream import StreamConsumer
from src.schema.chat import Message
   
from src.config.settings import RESPONSE_CHANNEL, STREAM_CHANNEL, MODEL_ERROR_MESSAGE

logger = logging.getLogger(__name__)


async def send_error_response(message_id, token: str, error_text: str, producer: Producer, cache: Cache, consumer: StreamConsumer) -> None:
    error_msg = Message(msg=error_text)
    try:   
        await producer.add_to_stream({str(token): error_msg.msg}, RESPONSE_CHANNEL)
    except Exception as exc:
        logger.error("Failed to publish error response for token %s: %s", token, exc)

    try:
        await cache.add_message_to_cache(
            token=token, source="Bot", message_data=error_msg.model_dump(mode="json")
            )
    except Exception as exc:
        logger.error("Failed to cache error message for token %s: %s", token, exc)

    try:      
        await consumer.delete_message(stream_channel=STREAM_CHANNEL, message_id=message_id)
    except Exception as exc:
        logger.error("Failed to delete message %s: %s", message_id, exc)


def _extract_scalar_id(message) -> bytes | str | None:
    if not isinstance(message, (list, tuple)) or len(message) == 0:
        return None
    candidate = message[0]
    if isinstance(candidate, (bytes, str)):
        return candidate
    return None


async def handle_invalid_envelope(message, producer: Producer, consumer: StreamConsumer) -> None:
    from src.services.dead_letter import route_to_dead_letter_queue

    fallback_id = _extract_scalar_id(message)

    await route_to_dead_letter_queue(
        producer,
        (fallback_id or "UNKNOWN_ID", {"raw_data": str(message)}),
        "Message wrapper missing essential fields",
    )

    if fallback_id is not None:
        await consumer.delete_message(
            stream_channel=STREAM_CHANNEL, message_id=fallback_id
        )


async def handle_cache_failure(message_id, token: str, raw_message, producer: Producer, cache: Cache, consumer: StreamConsumer) -> None:
    from src.services.dead_letter import route_to_dead_letter_queue

    logger.error(f"Cache miss: no history for token {token} after write")
    await route_to_dead_letter_queue(
        producer, raw_message, f"Cache history missing for token: {token}"
    )
    await send_error_response(message_id, token, MODEL_ERROR_MESSAGE, producer, cache, consumer)


async def handle_model_timeout(message_id, token: str, raw_message, timeout: float, producer: Producer, cache: Cache, 
                               consumer: StreamConsumer, timeout_message: str) -> None:
    from src.services.dead_letter import route_to_dead_letter_queue

    logger.error("Model timed out after %.0f seconds for token %s", timeout, token)
    await route_to_dead_letter_queue(
        producer, raw_message, "LLM Processing Timeout Exceeded"
    )
    await send_error_response(message_id, token, timeout_message, producer, cache, consumer)


async def handle_model_error(message_id, token: str, raw_message, exc: Exception, producer: Producer, cache: Cache, 
                             consumer: StreamConsumer, error_message: str,) -> None:
    from src.services.dead_letter import route_to_dead_letter_queue

    logger.error("Model query failed for token %s: %s", token, exc)
    await route_to_dead_letter_queue(
        producer, raw_message, f"Inference Exception: {exc}"
    )
    await send_error_response(message_id, token, error_message, producer, cache, consumer)