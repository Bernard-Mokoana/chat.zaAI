import logging
from typing import Optional

from .decoding import decode_bytes

logger = logging.getLogger(__name__)


def parse_stream_message(message) -> Optional[tuple[str, str, str]]:
    if not isinstance(message, (list, tuple)) or len(message) < 2:
        logger.error("Structurally invalid message envelope: %s", message)
        return None

    message_id = message[0]
    fields = message[1]

    if not fields or not isinstance(fields, dict):
        logger.error("Malformed message payload for id=%s", message_id)
        return None

    token_bytes, msg_bytes = next(iter(fields.items()))
    token = decode_bytes(token_bytes)
    text = decode_bytes(msg_bytes)

    return message_id, token, text