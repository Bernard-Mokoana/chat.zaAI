import logging
from typing import Optional

from .decoding import decode_bytes

logger = logging.getLogger(__name__)


def parse_stream_message(message) -> Optional[tuple[str, str, str, int]]:
    try:
        message_id, data = message

        token = data.get(b'token', b'').decode('utf-8') or data.get('token', '')
        text = data.get(b'text', b'').decode('utf-8') or data.get('text', '')

        retry_raw = data.get(b'retry_count', b'0').decode('utf-8') or data.get('retry_count', '0')
        retry_count = int(retry_raw)

        if not token or not text:
            return None
        
        return message_id, token, text, retry_count
    except Exception:
        return None