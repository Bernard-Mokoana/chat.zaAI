import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import logging
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.utils.error_handlers import (
    _extract_scalar_id,
    send_error_response,
    handle_invalid_envelope,
    handle_cache_failure,
    handle_model_timeout,
    handle_model_error,
)
from src.config.settings import (
    RESPONSE_CHANNEL,
    STREAM_CHANNEL,
    MODEL_ERROR_MESSAGE,
    MODEL_TIMEOUT_MESSAGE,
)


@pytest.fixture(autouse=True)
def suppress_logging():
    logging.disable(logging.CRITICAL)


class TestExtractScalarId:
    def test_pure_string(self):
        assert _extract_scalar_id("id-123") == "id-123"

    def test_bytes(self):
        # _extract_scalar_id decodes bytes -> str (Redis stream IDs arrive as
        # bytes and downstream consumers, e.g. consumer.delete_message, need str)
        assert _extract_scalar_id(b"id-123") == "id-123"

    def test_empty_tuple_returns_none(self):
        assert _extract_scalar_id(()) is None

    def test_nested_list_returns_none(self):
        assert _extract_scalar_id([["nested"]]) is None

    def test_empty_string_returns_empty_string(self):
        assert _extract_scalar_id("") == ""


class TestSendErrorResponse:
    async def test_success_publishes_and_caches_and_deletes(self):
        producer = MagicMock()
        producer.add_to_stream = AsyncMock()
        cache = MagicMock()
        cache.add_message_to_cache = AsyncMock()
        consumer = MagicMock()
        consumer.delete_message = AsyncMock()
        await send_error_response("msg-1", "tok-1", "error text", producer, cache, consumer)
        producer.add_to_stream.assert_called_once_with({"tok-1": "error text"}, RESPONSE_CHANNEL)
        cache.add_message_to_cache.assert_called_once()
        consumer.delete_message.assert_called_once_with(stream_channel=STREAM_CHANNEL, message_id="msg-1")

    async def test_producer_failure_still_caches_and_deletes(self):
        producer = MagicMock()
        producer.add_to_stream = AsyncMock(side_effect=RuntimeError("stream down"))
        cache = MagicMock()
        cache.add_message_to_cache = AsyncMock()
        consumer = MagicMock()
        consumer.delete_message = AsyncMock()
        await send_error_response("msg-1", "tok-1", "error text", producer, cache, consumer)
        cache.add_message_to_cache.assert_called_once()
        consumer.delete_message.assert_called_once_with(stream_channel=STREAM_CHANNEL, message_id="msg-1")

    async def test_cache_failure_still_deletes(self):
        producer = MagicMock()
        producer.add_to_stream = AsyncMock()
        cache = MagicMock()
        cache.add_message_to_cache = AsyncMock(side_effect=RuntimeError("cache down"))
        consumer = MagicMock()
        consumer.delete_message = AsyncMock()
        await send_error_response("msg-1", "tok-1", "error text", producer, cache, consumer)
        consumer.delete_message.assert_called_once_with(stream_channel=STREAM_CHANNEL, message_id="msg-1")

    async def test_consumer_failure_is_logged(self):
        producer = MagicMock()
        producer.add_to_stream = AsyncMock()
        cache = MagicMock()
        cache.add_message_to_cache = AsyncMock()
        consumer = MagicMock()
        consumer.delete_message = AsyncMock(side_effect=RuntimeError("consumer down"))
        await send_error_response("msg-1", "tok-1", "error text", producer, cache, consumer)
        # Should not raise despite consumer failure


class TestHandleInvalidEnvelope:
    @patch("src.utils.error_handlers.route_to_dead_letter_queue", new_callable=AsyncMock)
    async def test_routes_to_dead_letter_and_deletes(self, mock_route):
        producer = MagicMock()
        producer.add_to_stream = AsyncMock()
        consumer = MagicMock()
        consumer.delete_message = AsyncMock()

        message = (b"msg-id", {b"raw": b"data"})
        await handle_invalid_envelope(message, producer, consumer)

        mock_route.assert_called_once()
        captured_payload = mock_route.call_args[0][1]
        assert captured_payload[0] == "msg-id"
        assert "raw_data" in captured_payload[1]
        consumer.delete_message.assert_called_once_with(stream_channel=STREAM_CHANNEL, message_id="msg-id")

    @patch("src.utils.error_handlers.route_to_dead_letter_queue", new_callable=AsyncMock)
    async def test_no_message_id_skips_delete(self, mock_route):
        producer = MagicMock()
        producer.add_to_stream = AsyncMock()
        consumer = MagicMock()
        consumer.delete_message = AsyncMock()
        # 123 is neither str nor bytes, so _extract_scalar_id returns None,
        # which is what actually exercises the "skip delete" branch.
        message = (123, {"data": "x"})
        await handle_invalid_envelope(message, producer, consumer)
        consumer.delete_message.assert_not_called()


class TestHandleCacheFailure:
    @patch("src.utils.error_handlers.send_error_response", new_callable=AsyncMock)
    @patch("src.utils.error_handlers.route_to_dead_letter_queue", new_callable=AsyncMock)
    async def test_logs_and_routes_and_sends_error(self, mock_route, mock_send):
        producer = MagicMock()
        cache = MagicMock()
        consumer = MagicMock()
        await handle_cache_failure("msg-1", "tok-1", "raw", producer, cache, consumer)
        mock_route.assert_called_once_with(producer, "raw", "Cache history missing for token: tok-1")
        mock_send.assert_called_once_with("msg-1", "tok-1", MODEL_ERROR_MESSAGE, producer, cache, consumer)


class TestHandleModelTimeout:
    @patch("src.utils.error_handlers.send_error_response", new_callable=AsyncMock)
    @patch("src.utils.error_handlers.route_to_dead_letter_queue", new_callable=AsyncMock)
    async def test_logs_and_routes_and_sends_timeout(self, mock_route, mock_send):
        producer = MagicMock()
        cache = MagicMock()
        consumer = MagicMock()
        await handle_model_timeout("msg-1", "tok-1", "raw", 5.0, producer, cache, consumer, MODEL_TIMEOUT_MESSAGE)
        mock_route.assert_called_once_with(producer, "raw", "LLM Processing Timeout Exceeded")
        mock_send.assert_called_once_with("msg-1", "tok-1", MODEL_TIMEOUT_MESSAGE, producer, cache, consumer)


class TestHandleModelError:
    @patch("src.utils.error_handlers.send_error_response", new_callable=AsyncMock)
    @patch("src.utils.error_handlers.route_to_dead_letter_queue", new_callable=AsyncMock)
    async def test_logs_and_routes_and_sends_error(self, mock_route, mock_send):
        producer = MagicMock()
        cache = MagicMock()
        consumer = MagicMock()
        exc = RuntimeError("model boom")
        await handle_model_error("msg-1", "tok-1", "raw", exc, producer, cache, consumer, MODEL_ERROR_MESSAGE)
        mock_route.assert_called_once_with(producer, "raw", "Inference Exception: model boom")
        mock_send.assert_called_once_with("msg-1", "tok-1", MODEL_ERROR_MESSAGE, producer, cache, consumer)