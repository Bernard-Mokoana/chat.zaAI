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

    # Semantic format used by retries: {"token": ..., "text": ..., "retry_count": ...}
    if "token" in fields and "text" in fields:
        token = decode_bytes(fields["token"])
        text = decode_bytes(fields["text"])
        retry_raw = decode_bytes(fields.get("retry_count", "0"))
    else:
        # Original format from server: token sits in the field name, text in the value
        token_bytes, msg_bytes = next(iter(fields.items()))
        token = decode_bytes(token_bytes)
        text = decode_bytes(msg_bytes)
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