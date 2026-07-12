from .parsing import parse_stream_message
from .decoding import decode_bytes, decode_fields
from .db_helper import log_worker_usage, save_worker_message

__all__ = [
    "parse_stream_message",
    "decode_bytes",
    "decode_fields",
    "send_error_response",
    "handle_invalid_envelope",
    "handle_cache_failure",
    "handle_model_timeout",
    "handle_model_error",
    "log_worker_usage",
    "save_worker_message",
]

# error_handlers is loaded lazily (PEP 562) rather than imported eagerly above.
# error_handlers imports from src.services.dead_letter, which itself imports
# from src.utils.decoding — an eager import here would force error_handlers
# to load as a side effect of importing ANY name from src.utils, creating a
# circular import back through this package. Deferring the import until one
# of these names is actually accessed breaks that cycle.
_ERROR_HANDLER_NAMES = {
    "send_error_response",
    "handle_invalid_envelope",
    "handle_cache_failure",
    "handle_model_timeout",
    "handle_model_error",
}


def __getattr__(name):
    if name in _ERROR_HANDLER_NAMES:
        from . import error_handlers
        return getattr(error_handlers, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")