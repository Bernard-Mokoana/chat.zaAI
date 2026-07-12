import logging
from src.redis.producer import Producer
from src.utils.decoding import decode_fields   

logger = logging.getLogger(__name__)

DEAD_LETTER_CHANNEL = "dead_letter_channel"


async def route_to_dead_letter_queue(producer: Producer, original_message: tuple, error_reason: str) -> None:
    if not original_message or len(original_message) < 2:
        logger.error(
            "Cannot route to dead-letter queue: malformed message envelope %r",
            original_message,
        )
        return

    message_id, raw_fields = original_message[0], original_message[1]

    try:
        decoded = decode_fields(raw_fields)
    except Exception as exc:
        logger.error(
            "Failed to decode fields for message %s before dead-letter routing: %s",
            message_id,
            exc,
        )
        decoded = raw_fields

    if isinstance(message_id, bytes):
        message_id = message_id.decode("utf-8", errors="replace")

    payload = {
        "original_id": str(message_id),
        "error_reason": error_reason,
        "payload": str(decoded),
    }

    try:
        await producer.add_to_stream(payload, DEAD_LETTER_CHANNEL)
        logger.warning(
            "Message %s routed to %s. Reason: %s",
            message_id,
            DEAD_LETTER_CHANNEL,
            error_reason,
        )
    except Exception as exc:
        logger.error(
            "Critical failure routing message %s to dead-letter queue: %s",
            message_id,
            exc,
        )