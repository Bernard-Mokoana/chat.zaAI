import logging
from typing import Optional

from .decoding import decode_bytes

logger = logging.getLogger(__name__)


def parse_stream_message(message) -> Optional[tuple[str, str, str, int]]:
    if not isinstance(message, (list, tuple)) or len(message) < 2:
        logger.error("Structurally invalid message envelope: %r", message)
        return None

    message_id = message[0]
    fields = message[1]

    if isinstance(message_id, bytes):
        message_id = message_id.decode("utf-8")

    if not fields or not isinstance(fields, dict):
        logger.error("Malformed message payload for id=%s: %r", message_id, fields)
        return None

    decoded_fields = {
        decode_bytes(key): decode_bytes(value)
        for key, value in fields.items()
    }
    if "token" in decoded_fields and "text" in decoded_fields:
        token = decoded_fields["token"]
        text = decoded_fields["text"]
        retry_raw = decoded_fields.get("retry_count", "0")
    else:
        token, text = next(iter(decoded_fields.items()))
        retry_raw = "0"

    if not token or not text:
        logger.warning(
            "Stream message %s missing required fields (token=%r, text=%r)",
            message_id, token, text,
        )
        return None

    try:
        retry_count = max(0, int(retry_raw))
    except ValueError:
        logger.warning(
            "Invalid retry_count %r for message %s — defaulting to 0",
            retry_raw, message_id,
        )
        retry_count = 0

    return message_id, token, text, retry_count