import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import logging
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.handlers.MessageHandler import MessageHandler
from src.config.settings import (
    STREAM_CHANNEL,
    RESPONSE_CHANNEL,
    DEAD_LETTER_CHANNEL,
    MODEL_ERROR_MESSAGE,
    MODEL_TIMEOUT_MESSAGE,
    MAX_RETRIES,
)

logging.disable(logging.CRITICAL)


@pytest.fixture
def handler_fixtures():
    cache = MagicMock()
    cache.get_chat_history = AsyncMock()
    cache.add_message_to_cache = AsyncMock()
    producer = MagicMock()
    producer.add_to_stream = AsyncMock()
    consumer = MagicMock()
    consumer.delete_message = AsyncMock()
    session_factory = MagicMock()
    gpt = MagicMock()
    gpt.model_id = "model-x"
    return cache, producer, consumer, session_factory, gpt


def _make_handler(handler_fixtures):
    cache, producer, consumer, session_factory, gpt = handler_fixtures
    return MessageHandler(
        cache=cache,
        producer=producer,
        consumer=consumer,
        gpt_client=gpt,
        model_timeout=0.05,
        session_factory=session_factory,
    )


class TestMessageHandlerHandle:
    @patch("src.handlers.MessageHandler.parse_stream_message", return_value=None)
    @patch("src.handlers.MessageHandler.handle_invalid_envelope", new_callable=AsyncMock)
    async def test_invalid_envelope_calls_handler_and_returns(self, mock_handle_invalid, mock_parse, handler_fixtures):
        handler = _make_handler(handler_fixtures)
        await handler.handle("bad-message")
        mock_handle_invalid.assert_called_once_with("bad-message", handler.producer, handler.consumer)

    @patch("src.handlers.MessageHandler.parse_stream_message", return_value=("id-1", "tok-1", "text", 0))
    @patch.object(MessageHandler, "_process", new_callable=AsyncMock)
    async def test_valid_envelope_calls_process(self, mock_process, mock_parse, handler_fixtures):
        handler = _make_handler(handler_fixtures)
        await handler.handle("good-message")
        mock_process.assert_called_once_with("id-1", "tok-1", "text", raw_message="good-message")

    @patch("src.handlers.MessageHandler.parse_stream_message", return_value=("id-1", "tok-1", "text", 0))
    @patch.object(MessageHandler, "_process", new_callable=AsyncMock)
    async def test_exception_in_process_triggers_retry(self, mock_process, mock_parse, handler_fixtures):
        mock_process.side_effect = RuntimeError("boom")
        with patch.object(MessageHandler, "_handle_retry", new_callable=AsyncMock) as mock_retry:
            handler = _make_handler(handler_fixtures)
            await handler.handle("good-message")
            mock_retry.assert_called_once_with("id-1", "tok-1", "text", 0, pytest.ANY)


class TestMessageHandlerHandleRetry:
    async def test_retries_below_max(self, handler_fixtures):
        handler = _make_handler(handler_fixtures)
        await handler._handle_retry("id-1", "tok-1", "text", retry_count=MAX_RETRIES - 1, exception=RuntimeError("boom"))
        handler.producer.add_to_stream.assert_called_once_with(
            {"token": "tok-1", "text": "text", "retry_count": str(MAX_RETRIES)},
            STREAM_CHANNEL,
        )
        handler.consumer.delete_message.assert_called_once_with(stream_channel=STREAM_CHANNEL, message_id="id-1")

    async def test_exceeds_max_routes_to_dead_letter(self, handler_fixtures):
        handler = _make_handler(handler_fixtures)
        with patch("src.handlers.MessageHandler.route_to_dead_letter_queue", new_callable=AsyncMock) as mock_route:
            await handler._handle_retry("id-1", "tok-1", "text", retry_count=MAX_RETRIES, exception=RuntimeError("boom"))
            mock_route.assert_called_once_with(
                handler.producer,
                ("id-1", {"token": "tok-1", "text": "text", "retry_count": str(MAX_RETRIES), "error": str(RuntimeError("boom"))}),
                "Message id-1 (Token: tok-1) exceeded maximum retries (3). Sending to dead-letter channel.",
            )
        handler.consumer.delete_message.assert_called_once_with(stream_channel=STREAM_CHANNEL, message_id="id-1")


class TestMessageHandlerProcess:
    @patch.object(MessageHandler, "_save_message", new_callable=AsyncMock)
    @patch.object(MessageHandler, "_build_prompt_from_db", new_callable=AsyncMock)
    @patch.object(MessageHandler, "_call_model_with_logging", new_callable=AsyncMock)
    @patch.object(MessageHandler, "_publish_response", new_callable=AsyncMock)
    @patch.object(MessageHandler, "_log_usage", new_callable=AsyncMock)
    async def test_success_flow(self, mock_log_usage, mock_publish, mock_call, mock_build, mock_save, handler_fixtures):
        handler = _make_handler(handler_fixtures)
        handler.cache.get_chat_history.return_value = {"user_id": "u1"}
        mock_build.return_value = "Human: hi"
        mock_call.return_value = "Bot reply"

        await handler._process("msg-1", "tok-1", "hi", raw_message="raw")

        handler.cache.add_message_to_cache.assert_called()
        mock_save.assert_called_once_with("u1", "tok-1", "human", "hi")
        mock_build.assert_called_once_with("u1", "tok-1")
        mock_call.assert_called_once_with("msg-1", "tok-1", "raw", "Human: hi", "u1", "model-x")
        mock_publish.assert_called_once_with("msg-1", "tok-1", "Bot reply")
        mock_save.assert_any_call("u1", "tok-1", "bot", "Bot reply")
        mock_log_usage.assert_called_once_with("u1", "inference_success", "model-x", 4, 1)

    async def test_cache_missing_user_id_calls_cache_failure_and_returns(self, handler_fixtures):
        handler = _make_handler(handler_fixtures)
        handler.cache.get_chat_history.return_value = {}
        with patch("src.handlers.MessageHandler.handle_cache_failure", new_callable=AsyncMock) as mock_failure:
            with pytest.raises(RuntimeError, match="Database history retrieval failure"):
                await handler._process("msg-1", "tok-1", "hi", raw_message="raw")
            mock_failure.assert_called_once_with("msg-1", "tok-1", "raw", handler.producer, handler.cache, handler.consumer)

    async def test_empty_response_raises(self, handler_fixtures):
        handler = _make_handler(handler_fixtures)
        handler.cache.get_chat_history.return_value = {"user_id": "u1"}
        with patch.object(MessageHandler, "_build_prompt_from_db", new_callable=AsyncMock) as mock_build:
            with patch.object(MessageHandler, "_call_model_with_logging", new_callable=AsyncMock) as mock_call:
                mock_build.return_value = "Human: hi"
                mock_call.return_value = ""
                with pytest.raises(RuntimeError, match="Model returned an empty response."):
                    await handler._process("msg-1", "tok-1", "hi", raw_message="raw")


class TestMessageHandlerSaveMessage:
    async def test_success_saves_in_thread(self, handler_fixtures):
        handler = _make_handler(handler_fixtures)
        with patch("src.handlers.MessageHandler.save_worker_message", MagicMock()) as mock_save:
            with patch("asyncio.wait_for", AsyncMock(side_effect=lambda coro, timeout: coro)) as mock_wait:
                await handler._save_message("u1", "tok-1", "user", "hello")
            mock_save.assert_called_once_with(handler.session_factory, "u1", "tok-1", "user", "hello")

    async def test_timeout_is_logged_and_raised(self, handler_fixtures):
        handler = _make_handler(handler_fixtures)
        with patch("src.handlers.MessageHandler.save_worker_message", MagicMock()):
            with patch("asyncio.wait_for", new_callable=AsyncMock) as mock_wait:
                mock_wait.side_effect = asyncio.TimeoutError()
                with pytest.raises(asyncio.TimeoutError):
                    await handler._save_message("u1", "tok-1", "user", "hello")


class TestMessageHandlerLogUsage:
    async def test_timeout_is_logged(self, handler_fixtures):
        handler = _make_handler(handler_fixtures)
        with patch("src.handlers.MessageHandler.log_worker_usage", MagicMock()):
            with patch("asyncio.wait_for", new_callable=AsyncMock) as mock_wait:
                mock_wait.side_effect = asyncio.TimeoutError()
                await handler._log_usage("u1", "event", "model", 5, 1)

    async def test_other_exception_is_logged(self, handler_fixtures):
        handler = _make_handler(handler_fixtures)
        with patch("src.handlers.MessageHandler.log_worker_usage", MagicMock()):
            with patch("asyncio.wait_for", new_callable=AsyncMock) as mock_wait:
                mock_wait.side_effect = RuntimeError("boom")
                with pytest.raises(RuntimeError):
                    await handler._log_usage("u1", "event", "model", 5, 1)


class TestMessageHandlerCallModelWithLogging:
    async def test_success(self, handler_fixtures):
        handler = _make_handler(handler_fixtures)
        with patch.object(MessageHandler, "_log_usage", new_callable=AsyncMock):
            with patch("src.handlers.MessageHandler.query_model", AsyncMock(return_value="reply")) as mock_query:
                result = await handler._call_model_with_logging("m1", "tok", "raw", "prompt", "u1", "model-x")
                assert result == "reply"
                mock_query.assert_called_once_with(handler.gpt_client, "prompt", 0.05)

    async def test_timeout_logs_and_handles(self, handler_fixtures):
        handler = _make_handler(handler_fixtures)
        with patch.object(MessageHandler, "_log_usage", new_callable=AsyncMock) as mock_log:
            with patch.object(MessageHandler, "handle_model_timeout", new_callable=AsyncMock) as mock_timeout:
                with patch("src.handlers.MessageHandler.query_model", AsyncMock(side_effect=asyncio.TimeoutError())):
                    with pytest.raises(asyncio.TimeoutError):
                        await handler._call_model_with_logging("m1", "tok", "raw", "prompt", "u1", "model-x")
                    mock_log.assert_called_once_with("u1", "model_timeout", "model-x", 0, 1)
                    mock_timeout.assert_called_once()

    async def test_model_error_logs_and_handles(self, handler_fixtures):
        handler = _make_handler(handler_fixtures)
        with patch.object(MessageHandler, "_log_usage", new_callable=AsyncMock) as mock_log:
            with patch.object(MessageHandler, "handle_model_error", new_callable=AsyncMock) as mock_error:
                with patch("src.handlers.MessageHandler.query_model", AsyncMock(side_effect=RuntimeError("boom"))):
                    with pytest.raises(RuntimeError):
                        await handler._call_model_with_logging("m1", "tok", "raw", "prompt", "u1", "model-x")
                    mock_log.assert_called_once_with("u1", "model_error", "model-x", 0, 1)
                    mock_error.assert_called_once()


class TestMessageHandlerPublishResponse:
    async def test_publishes_response_and_caches(self, handler_fixtures):
        handler = _make_handler(handler_fixtures)
        await handler._publish_response("m1", "tok-1", "reply")
        handler.producer.add_to_stream.assert_called_once_with({"tok-1": "reply"}, RESPONSE_CHANNEL)
        handler.cache.add_message_to_cache.assert_called_once_with(token="tok-1", source="Bot", message_data={"msg": "reply", "id": pytest.ANY, "timestamp": pytest.ANY})
        handler.consumer.delete_message.assert_called_once_with(stream_channel=STREAM_CHANNEL, message_id="m1")


class TestMessageHandlerBuildPromptFromDb:
    async def test_builds_formatted_prompt(self, handler_fixtures):
        handler = _make_handler(handler_fixtures)
        with patch("src.handlers.MessageHandler.get_conversation_history_from_db", MagicMock(return_value=[
            {"role": "user", "msg": "hi"},
            {"role": "assistant", "msg": "reply"},
        ])):
            with patch("asyncio.to_thread", AsyncMock(return_value=[
                {"role": "user", "msg": "hi"},
                {"role": "assistant", "msg": "reply"},
            ])):
                prompt = await handler._build_prompt_from_db("u1", "tok-1")
                assert prompt == "Human: hi\nBot: reply"

    async def test_no_history_returns_empty_string(self, handler_fixtures):
        handler = _make_handler(handler_fixtures)
        with patch("asyncio.to_thread", AsyncMock(return_value=[])):
            prompt = await handler._build_prompt_from_db("u1", "tok-1")
            assert prompt == ""

    async def test_none_history_returns_none(self, handler_fixtures):
        handler = _make_handler(handler_fixtures)
        with patch("asyncio.to_thread", AsyncMock(return_value=None)):
            prompt = await handler._build_prompt_from_db("u1", "tok-1")
            assert prompt is None

    async def test_exception_logs_and_returns_none(self, handler_fixtures):
        handler = _make_handler(handler_fixtures)
        with patch("asyncio.to_thread", AsyncMock(side_effect=RuntimeError("db down"))):
            with patch("src.handlers.MessageHandler.logger") as mock_log:
                prompt = await handler._build_prompt_from_db("u1", "tok-1")
                assert prompt is None
                assert "Error compiling prompt" in mock_log.error.call_args[0][0]
