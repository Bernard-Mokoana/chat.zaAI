import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import logging
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.services.dead_letter import route_to_dead_letter_queue
from src.utils.decoding import decode_fields


@pytest.fixture(autouse=True)
def suppress_logging():
    logging.disable(logging.CRITICAL)


class TestRouteToDeadLetterQueue:
    @patch("src.services.dead_letter.decode_fields", return_value={"decoded": True})
    async def test_valid_message_publishes_payload(self, mock_decode):
        producer = MagicMock()
        producer.add_to_stream = AsyncMock()
        original = (b"msg-1", {b"token": b"tok-1"})
        await route_to_dead_letter_queue(producer, original, "reason here")
        producer.add_to_stream.assert_called_once()
        payload = producer.add_to_stream.call_args[0][0]
        assert payload["original_id"] == "msg-1"
        assert payload["error_reason"] == "reason here"
        mock_decode.assert_called_once()

    async def test_malformed_envelope_is_logged_not_published(self):
        producer = MagicMock()
        producer.add_to_stream = AsyncMock()
        await route_to_dead_letter_queue(producer, (), "bad envelope")
        producer.add_to_stream.assert_not_called()

    async def test_deeply_malformed_envelope_skips_route(self):
        producer = MagicMock()
        producer.add_to_stream = AsyncMock()
        await route_to_dead_letter_queue(producer, None, "bad")
        producer.add_to_stream.assert_not_called()

    async def test_bytes_message_id_is_decoded(self):
        producer = MagicMock()
        producer.add_to_stream = AsyncMock()
        original = (b"msg-bytes", {b"field": b"val"})
        await route_to_dead_letter_queue(producer, original, "test")
        payload = producer.add_to_stream.call_args[0][0]
        assert payload["original_id"] == "msg-bytes"

    @patch("src.services.dead_letter.decode_fields", side_effect=RuntimeError("decode boom"))
    async def test_decode_failure_falls_back_to_raw_str(self, mock_decode):
        producer = MagicMock()
        producer.add_to_stream = AsyncMock()
        original = ("msg-2", {"raw": "data"})
        await route_to_dead_letter_queue(producer, original, "reason")
        payload = producer.add_to_stream.call_args[0][0]
        assert payload["original_id"] == "msg-2"
        assert "raw" in payload["payload"]

    async def test_publish_failure_is_logged(self):
        producer = MagicMock()
        producer.add_to_stream = AsyncMock(side_effect=RuntimeError("stream down"))
        original = ("msg-3", {"field": "value"})
        with patch("src.services.dead_letter.logger") as mock_log:
            await route_to_dead_letter_queue(producer, original, "reason")
            mock_log.error.assert_called_once()
