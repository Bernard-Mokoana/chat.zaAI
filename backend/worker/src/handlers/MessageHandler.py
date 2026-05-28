import asyncio
import logging

from sqlalchemy.orm import sessionmaker

from src.model.gptj import GPT
from src.redis.cache import Cache
from src.redis.producer import Producer
from src.redis.stream import StreamConsumer
from src.schema.chat import Message

from src.config.settings import (RESPONSE_CHANNEL, STREAM_CHANNEL, MODEL_ERROR_MESSAGE, MODEL_TIMEOUT_MESSAGE, CHAT_HISTORY_WINDOW)
from src.services.model import query_model
from src.utils.parsing import parse_stream_message
from src.utils.error_handlers import (handle_invalid_envelope, handle_cache_failure, handle_model_timeout, handle_model_error)

from src.utils.dbHelper import run_db_log, run_db_save

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

        message_id, token, text = parsed
        await self._process(message_id, token, text, raw_message=message)

    async def _process(self, message_id, token: str, text: str, raw_message) -> None:
        # Fetch session metadata from cache to acquire user_id
        chat_metadata = self.cache.get_chat_history(token=token)
        if not chat_metadata or "user_id" not in chat_metadata:
            await handle_cache_failure(
                message_id, token, raw_message, self.producer, self.cache, self.consumer
            )
            return
        
        user_id = chat_metadata["user_id"]
        # Extract model name
        model_name = getattr(self.gpt_client, "model_name", "GPT-J")

        # Store incoming user message
        user_msg = Message(msg=text)
        self.cache.add_message_to_cache(
            token=token, source="Human", message_data=user_msg.model_dump()
        )

        # Persist Human Message to database via worker Thread
        try:
            await asyncio.wait_for(
                 asyncio.to_thread(self.run_db_save, user_id, token, "Human", text),
                 timeout=10.0
            )
        except Exception as e:
            logger.error(f"Failed to persist user message to DB: {e}")

        # Build prompt from recent chat history
        prompt = self._build_prompt(token)
        if prompt is None:
            await handle_cache_failure(
                message_id, token, raw_message, self.producer, self.cache, self.consumer
            )
            return

        # Query the model
        try:
            response_text = await self._call_model_with_logging(message_id, token, raw_message, prompt, user_id, model_name)
            if response_text is None:
                return  
        except Exception as e:
            return

        # Publish response
        await self._publish_response(message_id, token, response_text)

        # Persist Bot response via worker thread
        try:
            await asyncio.wait_for(
                asyncio.to_thread(self.run_db_save, user_id, token, "Bot", response_text),
                timeout=10.0
            )
        except Exception as e:
            logger.error(f"Failed to persist bot message to DB: {e}")

        estimated_tokens = len(prompt + response_text) // 4

        # Track success event in background thread
        await asyncio.to_thread(
            self.run_db_log,
            user_id,
            "inference_success",
            model_name,
            estimated_tokens,
            1
        )
        
    def _build_prompt(self, token: str) -> str | None:
        data = self.cache.get_chat_history(token=token)
        messages = (data.get("messages", []) if data else [])[-CHAT_HISTORY_WINDOW:]
        return " ".join(m["msg"] for m in messages) if messages else None

    async def _call_model_with_logging(self, message_id, token: str, raw_message, prompt: str, user_id: str, model_name: str) -> str | None:
        try:
            return await query_model(self.gpt_client, prompt, self.model_timeout)

        except asyncio.TimeoutError:
            # Track failure metric: Timeout
            await asyncio.to_thread(self.run_db_log, user_id, "model_timeout", model_name, 0, 1)
            await handle_model_timeout(
                message_id, token, raw_message, self.model_timeout,
                self.producer, self.cache, self.consumer, MODEL_TIMEOUT_MESSAGE,
            )
            raise

        except Exception as exc:
            # Track failure metric: Runtime processing error 
            await asyncio.to_thread(self.run_db_log, user_id, "model_error", model_name, 0, 1)
            await handle_model_error(
                message_id, token, raw_message, exc,
                self.producer, self.cache, self.consumer, MODEL_ERROR_MESSAGE,
            )
            raise

    async def _publish_response(self, message_id, token: str, response_text: str) -> None:
        bot_msg = Message(msg=response_text)
        await self.producer.add_to_stream({str(token): bot_msg.msg}, RESPONSE_CHANNEL)
        self.cache.add_message_to_cache(
            token=token, source="Bot", message_data=bot_msg.model_dump()
        )
        await self.consumer.delete_message(
            stream_channel=STREAM_CHANNEL, message_id=message_id
        )