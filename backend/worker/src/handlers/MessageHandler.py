import asyncio
import logging

from src.model.gptj import GPT
from src.redis.cache import Cache
from src.redis.producer import Producer
from src.redis.stream import StreamConsumer
from src.schema.chat import Message

from src.config.settings import (RESPONSE_CHANNEL, STREAM_CHANNEL, MODEL_ERROR_MESSAGE, MODEL_TIMEOUT_MESSAGE, CHAT_HISTORY_WINDOW)
from src.services.model import query_model
from src.utils.parsing import parse_stream_message
from src.utils.error_handlers import (handle_invalid_envelope, handle_cache_failure, handle_model_timeout, handle_model_error)

logger = logging.getLogger(__name__)


class MessageHandler:
    def __init__(self, cache: Cache, producer: Producer, consumer: StreamConsumer, gpt_client: GPT, model_timeout: float) -> None:
        self.cache = cache
        self.producer = producer
        self.consumer = consumer
        self.gpt_client = gpt_client
        self.model_timeout = model_timeout

    async def handle(self, message) -> None:
        parsed = parse_stream_message(message)

        if parsed is None:
            await handle_invalid_envelope(message, self.producer, self.consumer)
            return

        message_id, token, text = parsed
        await self._process(message_id, token, text, raw_message=message)

    async def _process(self, message_id, token: str, text: str, raw_message) -> None:
        # Store incoming user message
        user_msg = Message(msg=text)
        self.cache.add_message_to_cache(
            token=token, source="Human", message_data=user_msg.model_dump()
        )

        # Build prompt from recent chat history
        prompt = self._build_prompt(token)
        if prompt is None:
            await handle_cache_failure(
                message_id, token, raw_message, self.producer, self.cache, self.consumer
            )
            return

        # Query the model
        response_text = await self._call_model(message_id, token, raw_message, prompt)
        if response_text is None:
            return  # error already handled inside _call_model

        # Publish response
        await self._publish_response(message_id, token, response_text)

    def _build_prompt(self, token: str) -> str | None:
        data = self.cache.get_chat_history(token=token)
        messages = (data.get("messages", []) if data else [])[-CHAT_HISTORY_WINDOW:]
        return " ".join(m["msg"] for m in messages) if messages else None

    async def _call_model(self, message_id, token: str, raw_message, prompt: str) -> str | None:
        try:
            return await query_model(self.gpt_client, prompt, self.model_timeout)

        except asyncio.TimeoutError:
            await handle_model_timeout(
                message_id, token, raw_message, self.model_timeout,
                self.producer, self.cache, self.consumer, MODEL_TIMEOUT_MESSAGE,
            )
            return None

        except Exception as exc:
            await handle_model_error(
                message_id, token, raw_message, exc,
                self.producer, self.cache, self.consumer, MODEL_ERROR_MESSAGE,
            )
            return None

    async def _publish_response(self, message_id, token: str, response_text: str) -> None:
        bot_msg = Message(msg=response_text)
        await self.producer.add_to_stream({str(token): bot_msg.msg}, RESPONSE_CHANNEL)
        self.cache.add_message_to_cache(
            token=token, source="Bot", message_data=bot_msg.model_dump()
        )
        await self.consumer.delete_message(
            stream_channel=STREAM_CHANNEL, message_id=message_id
        )