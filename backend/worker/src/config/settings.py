import logging 
import os

logger = logging.getLogger(__name__)

DEFAULT_MODEL_QUERY_TIMEOUT_SEC = 60.0

STREAM_CHANNEL = "message_channel"
RESPONSE_CHANNEL = "response_channel"
DEAD_LETTER_CHANNEL = "dead_letter_channel"

MODEL_ERROR_MESSAGE = "Sorry, there was an error processing your message."
MODEL_TIMEOUT_MESSAGE = "Sorry, the model took too long to respond. Please try again."

CHAT_HISTORY_WINDOW = 4

MAX_RETRIES = 3

def get_model_query_timeout() -> float:
    raw_timeout = os.environ.get("MODEL_QUERY_TIMEOUT_SEC")
    if not raw_timeout:
        return DEFAULT_MODEL_QUERY_TIMEOUT_SEC
    
    try:
        timeout = float(raw_timeout)
    except ValueError:
        logger.warning(
            "Invalid MODEL_QUERY_TIMEOUT_SEC=%r; using default %.0f seconds",
            raw_timeout,
            DEFAULT_MODEL_QUERY_TIMEOUT_SEC,
        )
        return DEFAULT_MODEL_QUERY_TIMEOUT_SEC
    
    if timeout <= 0:
        logger.warning(
            "MODEL_QUERY_TIMEOUT_SEC must be positive; using default %.0f seconds",
            DEFAULT_MODEL_QUERY_TIMEOUT_SEC,
        )
        return DEFAULT_MODEL_QUERY_TIMEOUT_SEC
    
    return timeout
    
