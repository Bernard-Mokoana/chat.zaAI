import logging
from src.redis.producer import Producer
from src.utils.decoding import decode_fields

logger = logging.getLogger(__name__)

DEAD_LETTER_CHANNEL = "dead_letter_channel"


async def route_to_dead_letter_queue(producer: Producer, original_message: tuple, error_reason: str) -> None:
    try:
        message_id, raw_fields = original_message[0], original_message[1]

        payload = {
            "original_id": str(message_id),
            "error_reason": error_reason,
            "payload": str(decode_fields(raw_fields)),
        } 
        await producer.add_to_stream(payload, DEAD_LETTER_CHANNEL)
        logger.warning(
            "Message %s routed to %s. Reason: %s",
            message_id,
            DEAD_LETTER_CHANNEL,
            error_reason,
        )

    except Exception as exc:
        logger.error(f"Critical failure while attempting to route to Dead Letter Queue: {exc}")

