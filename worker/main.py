from src.redis.config import Redis
import asyncio
import logging
import os
from src.model.gptj import GPT
from src.redis.cache import Cache
from src.schema.chat import Message
from src.redis.stream import StreamConsumer
from src.redis.producer import Producer

redis_client = Redis()
logger = logging.getLogger(__name__)

DEFAULT_MODEL_QUERY_TIMEOUT_SEC = 60.0
MODEL_ERROR_MESSAGE = "Sorry, there was an error processing your message."
MODEL_TIMEOUT_MESSAGE = "Sorry, the model took too long to respond. Please try again."


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


async def query_model_with_timeout(gpt_client: GPT, prompt: str, timeout: float) -> str:
    return await asyncio.wait_for(
        asyncio.to_thread(gpt_client.query, prompt),
        timeout=timeout,
    )


async def route_to_dead_letter_queue(producer: Producer, original_message: tuple, error_reason: str):
    try:
        message_id = original_message[0]
        raw_fields = original_message[1]

        # Convert byte keys/values to readable string for diagnostics
        formatted_fields = {}
        if isinstance(raw_fields, dict):
            for k, v in raw_fields.items():
                k_str = k.decode('utf-8', errors='ignore') if isinstance(k, bytes) else str(k)
                v_str = v.decode('utf-8', errors='ignore') if isinstance(v, bytes) else str(v)
                formatted_fields[k_str] = v_str
        else:
            formatted_fields = {"raw_fallback_content": str(raw_fields)}

        dlq_payload = {
            "original_id": str(message_id),
            "error_reason": error_reason,
            "payload": str(formatted_fields)
        }

        await producer.add_to_stream(dlq_payload, "dead_letter_channel")
        logger.warning(f"Message {message_id} routed successfully to dead_letter_channel. Reason: {error_reason}")
    except Exception as dlq_ex:
        logger.error(f"Critical failure while attempting to route to Dead Letter Queue: {dlq_ex}")


async def main():
    json_client = redis_client.create_json_connection()
    redis_conn = await redis_client.create_connection()
    consumer = StreamConsumer(redis_conn)
    cache = Cache(json_client)
    producer = Producer(redis_conn)
    gpt_client = GPT()
    model_query_timeout = get_model_query_timeout()

    print("Stream consumer started")
    print("Stream waiting for new messages")

    while True:
        try:
            response = await consumer.consume_stream(stream_channel="message_channel", count=1, block=5000)
            
            if response:
                for stream, messages in response:
                    for message in  messages:

                        if not isinstance(message, (list, tuple)) or len(message) < 2:
                            logger.error(f"Structurally invalid message envelope encountered: {message}")
                            fallback_id = message[0] if (isinstance(message, (list, tuple)) and len(message) > 0) else "UNKNOWN_ID"

                            await route_to_dead_letter_queue(
                                producer,
                                (fallback_id, {"raw_data": str(message)}),
                                "Message wrapper missing essential fields (len < 2)"
                            )

                            if fallback_id != "UNKNOWN_ID":
                                await consumer.delete_message(stream_channel="message_channel", message_id=fallback_id)
                            continue

                        message_id = message[0]
                        message_payload = message[1]

                        if not isinstance(message_payload, dict) or not message_payload:
                            print(f"Malformed messages {message_id}, skipping")
                            await route_to_dead_letter_queue(producer, message, "Malformed message payload structure")
                            await consumer.delete_message(stream_channel="message_channel", message_id=message_id)
                            continue

                        token_bytes, msg_bytes = next(iter(message[1].items()))
                        token = token_bytes.decode("utf-8") if isinstance(token_bytes, (bytes, bytearray)) else str(token_bytes)
                        message_text = msg_bytes.decode("utf-8") if isinstance(msg_bytes, (bytes, bytearray)) else str(msg_bytes)
                        
                        msg = Message(msg=message_text)
                                                
                        cache.add_message_to_cache(token=token, source="Human", message_data=msg.model_dump())
                        
                        data = cache.get_chat_history(token=token)
                        
                        # Handle missing or empty messages
                        message_data = data.get('messages', [])[-4:] if data else []
                        if not message_data:
                            logger.error(f"Cache failure: No chat history for token {token} immediately after adding message")
                            await route_to_dead_letter_queue(producer, message, f"Cache history missing for token: {token}")

                            error_msg = Message(msg=MODEL_ERROR_MESSAGE)
                            await producer.add_to_stream({str(token): error_msg.msg}, "response_channel")
                            await cache.add_message_to_cache(token=token, source="Bot", message_data=error_msg.model_dump())
                            await consumer.delete_message(stream_channel="message_channel", message_id=message_id)
                            continue
                         
                        input_text = " ".join(i["msg"] for i in message_data)

                        try:
                            res = await query_model_with_timeout(
                                gpt_client,
                                input_text,
                                timeout=model_query_timeout,
                            )
                        except asyncio.TimeoutError:
                            logger.error(
                                "Model query timed out after %.0f seconds for token %s",
                                model_query_timeout,
                                token,
                            )
                            await route_to_dead_letter_queue(producer, message, "LLM Processing Timeout Exceeded")

                            timeout_msg = Message(msg=MODEL_TIMEOUT_MESSAGE)
                            await producer.add_to_stream({str(token): timeout_msg.msg}, "response_channel")
                            await cache.add_message_to_cache(token=token, source="Bot", message_data=timeout_msg.model_dump())
                            await consumer.delete_message(stream_channel="message_channel", message_id=message_id)
                            continue
                        except Exception as e:
                            logger.error("Model query failed for token %s: %s", token, e)
                            
                            await route_to_dead_letter_queue(producer, message, f"Inference Exception: {str(e)}")

                            error_msg = Message(msg=MODEL_ERROR_MESSAGE)
                            await producer.add_to_stream({str(token): error_msg.msg}, "response_channel")
                            await cache.add_message_to_cache(token=token, source="Bot", message_data=error_msg.model_dump())
                            await consumer.delete_message(stream_channel="message_channel", message_id=message_id)
                            continue
                        
                        msg = Message(msg=res)
                        
                        # Extract only the text string for stream, not the full JSON dump
                        stream_data = {str(token): msg.msg}
                        
                        await producer.add_to_stream(stream_data, "response_channel")
                        
                        cache.add_message_to_cache(token=token, source="Bot", message_data=msg.model_dump())
                        
                        await consumer.delete_message(stream_channel="message_channel", message_id=message_id)
        
        except Exception as e:
            print(f"Error processing message: {e}")
            logger.exception(f"Error processing message: {e}")
            continue

if __name__ == "__main__":
    asyncio.run(main())
