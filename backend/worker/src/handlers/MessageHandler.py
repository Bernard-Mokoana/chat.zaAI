import asyncio
import logging

from sqlalchemy.orm import sessionmaker

from src.model.gptj import GPT
from src.redis.cache import Cache
from src.redis.producer import Producer
from src.redis.stream import StreamConsumer
from src.schema.chat import Message

from src.config.settings import (RESPONSE_CHANNEL, STREAM_CHANNEL, MODEL_ERROR_MESSAGE, DEAD_LETTER_CHANNEL, MODEL_TIMEOUT_MESSAGE, CHAT_HISTORY_WINDOW, MAX_RETRIES)
from src.services.model import query_model
from src.utils.parsing import parse_stream_message
from src.utils.error_handlers import (handle_invalid_envelope, handle_cache_failure, handle_model_timeout, handle_model_error)
from src.utils.dbHelper import log_worker_usage, save_worker_message, get_conversation_history_from_db



logger = logging.getLogger(__name__)


class MessageHandler:
    def __init__(self, cache: Cache, producer: Producer, consumer: StreamConsumer, gpt_client: GPT, model_timeout: float, session_factory: sessionmaker) -> None:
        self.cache = cache
        self.producer = producer
        self.consumer = consumer
        self.gpt_client = gpt_client
        self.model_timeout = model_timeout
        self.session_factory = session_factory

    async def handle(self, message) -> None:
        parsed = parse_stream_message(message)

        if parsed is None:
            await handle_invalid_envelope(message, self.producer, self.consumer)
            return

        message_id, token, text, retry_count = parsed

        try:
            await self._process(message_id, token, text, raw_message=message)
        except Exception as exc:
            await self._handle_retry(message_id, token, text, retry_count, exc)

    async def _handle_retry(self, message_id: str, token: str, text: str, retry_count: int, exception: Exception) -> None:
        if retry_count < MAX_RETRIES:
            new_retry_count = retry_count + 1

            logger.warning(
                "Processing failed for message %s (Token: %s). "
                "Retrying attempt %d/%d. Error: %s",
                message_id,
                token,
                new_retry_count,
                MAX_RETRIES,
                exception,
            )

            retry_payload = {
                token: text,
                "retry_count": str(new_retry_count),
            }

            await self.producer.add_to_stream(retry_payload, STREAM_CHANNEL)
        else:
            logger.error(
                "Message %s (Token: %s) exceeded maximum retries (%d). "
                "Sending to dead-letter channel.",
                message_id,
                token,
                MAX_RETRIES,
            )

            dead_letter_payload = {
                "token": token,
                "text": text,
                "retry_count": str(retry_count),
                "error": str(exception),
            }
            await self.producer.add_to_stream(dead_letter_payload, DEAD_LETTER_CHANNEL)

        # Delete the original message after handling (retry or dead-letter)
        await self.consumer.delete_message(
            stream_channel=STREAM_CHANNEL, message_id=message_id
        )

    async def _process(self, message_id: str, token: str, text: str, raw_message) -> None:
        # Fetch session metadata to acquire user_id
        chat_metadata = self.cache.get_chat_history(token=token)
        if not chat_metadata or "user_id" not in chat_metadata:
            await handle_cache_failure(
                message_id, token, raw_message, self.producer, self.cache, self.consumer
            )
            return

        user_id: str = chat_metadata["user_id"]
        model_name: str = getattr(self.gpt_client, "model_id", "GPT-J")

        # Store incoming user message in cache and DB
        user_msg = Message(msg=text)
        self.cache.add_message_to_cache(
            token=token, source="Human", message_data=user_msg.model_dump()
        )
        # Persist the incoming Human message to postgres
        await self._save_message(user_id, token, "human", text)

        # Build prompt from recent chat history (includes the message just added)
        prompt = await self._build_prompt_from_db(user_id, token)
        if prompt is None:
            await handle_cache_failure(
                message_id, token, raw_message, self.producer, self.cache, self.consumer
            )
            raise RuntimeError("Database history retrieval failure")

        # Query the model; propagate exceptions so _handle_retry can act on them
        response_text = await self._call_model_with_logging(
            message_id, token, raw_message, prompt, user_id, model_name
        )

        if not response_text:
            raise RuntimeError("Model returned an empty response.")

        # Publish response, persist to DB, and log usage
        await self._publish_response(message_id, token, response_text)
        await self._save_message(user_id, token, "bot", response_text)

        estimated_tokens = len(prompt + response_text) // 4
        await self._log_usage(user_id, "inference_success", model_name, estimated_tokens, 1)

    async def _build_prompt_from_db(self, user_id: str, token: str) -> str | None:
        try:
            def fetch_action():
                with self.session_factory() as session:
                    return get_conversation_history_from_db(
                        session=session,
                        user_id=user_id,
                        token=token,
                        limit=CHAT_HISTORY_WINDOW,
                    )
            
            history_rounds = await asyncio.to_thread(fetch_action)
            if not history_rounds:
                return None
            
            return " ".join(m["msg"] for m in history_rounds)
        except Exception as exc:
            logger.error(f"Error compiling prompt window from database: {exc}")
            return None

    async def _save_message(self, user_id: str, token: str, role: str, content: str) -> None:
        try:
            await asyncio.wait_for(
                asyncio.to_thread(
                    save_worker_message,
                    self.session_factory,
                    user_id,
                    token,
                    role,
                    content,
                ),
                timeout=10.0,
            )
        except (asyncio.TimeoutError, Exception) as exc:
            logger.error("Failed to persist %s message to DB: %s", role, exc)
            raise exc

    async def _log_usage(self, user_id: str, event_type: str, model: str | None, total_tokens: int | None, message_count: int | None) -> None:
        try:
            await asyncio.wait_for(
                asyncio.to_thread(
                    log_worker_usage,
                    self.session_factory,
                    user_id,
                    model,
                    total_tokens,
                    message_count,
                ),
                timeout=10.0,
            )
        except asyncio.TimeoutError:
            logger.error(
                "Timed out logging usage event '%s' for user %s", event_type, user_id
            )
        except Exception as exc:
            logger.error("Failed to log usage event '%s': %s", event_type, exc)

    async def _call_model_with_logging(self, message_id: str, token: str, raw_message, prompt: str, user_id: str, model_name: str) -> str:
        try:
            return await query_model(self.gpt_client, prompt, self.model_timeout)

        except asyncio.TimeoutError:
            await self._log_usage(user_id, "model_timeout", model_name, 0, 1)
            await handle_model_timeout(
                message_id,
                token,
                raw_message,
                self.model_timeout,
                self.producer,
                self.cache,
                self.consumer,
                MODEL_TIMEOUT_MESSAGE,
            )
            raise

        except Exception as exc:
            await self._log_usage(user_id, "model_error", model_name, 0, 1)
            await handle_model_error(
                message_id,
                token,
                raw_message,
                exc,
                self.producer,
                self.cache,
                self.consumer,
                MODEL_ERROR_MESSAGE,
            )
            raise

    async def _publish_response(self, message_id: str, token: str, response_text: str) -> None:
        bot_msg = Message(msg=response_text)
        await self.producer.add_to_stream(
            {str(token): bot_msg.msg}, RESPONSE_CHANNEL
        )
        self.cache.add_message_to_cache(
            token=token, source="Bot", message_data=bot_msg.model_dump()
        )
        await self.consumer.delete_message(
            stream_channel=STREAM_CHANNEL, message_id=message_id
        )
