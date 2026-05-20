from src.redis.config import Redis
import json
import asyncio
import logging
from src.model.gptj import GPT
from src.redis.cache import Cache
from src.schema.chat import Message
from src.redis.stream import StreamConsumer
from src.redis.producer import Producer

redis_client = Redis()
logger = logging.getLogger(__name__)

async def main():
    json_client = redis_client.create_json_connection()
    redis_conn = await redis_client.create_connection()
    consumer = StreamConsumer(redis_conn)
    cache = Cache(json_client)
    producer = Producer(redis_conn)
    gpt_client = GPT()

    print("Stream consumer started")
    print("Stream waiting for new messages")

    while True:
        try:
            response = await consumer.consume_stream(stream_channel="message_channel", count=1, block=5000)
            
            if response:
                for stream, messages in response:
                    for message in  messages:
                        message_id = message[0]

                        if not message[1] or not isinstance(message[1], dict):
                            print(f"Malformed messages {message_id}, skipping")
                            await consumer.delete_message(stream_channel="message_channel", message_id=message_id)
                            continue

                        token_bytes, msg_bytes = next(iter(message[1].items()))
                        token = token_bytes.decode("utf-8") if isinstance(token_bytes, (bytes, bytearray)) else str(token_bytes)
                        message_text = msg_bytes.decode("utf-8") if isinstance(msg_bytes, (bytes, bytearray)) else str(msg_bytes)
                        
                        msg = Message(msg=message_text)
                                                
                        await cache.add_message_to_cache(token=token, source="Human", message_data=msg.model_dump())
                        
                        data = cache.get_chat_history(token=token)
                        
                        # Handle missing or empty messages
                        message_data = data.get('messages', [])[-4:] if data else []
                        if not message_data:
                            logger.error(f"Cache failure: No chat history for token {token} immediately after adding message")
                            continue
                         
                        input_text = " ".join(i["msg"] for i in message_data)

                        res = gpt_client.query(input_text)
                        
                        msg = Message(msg=res)
                        
                        # Extract only the text string for stream, not the full JSON dump
                        stream_data = {str(token): msg.msg}
                        
                        await producer.add_to_stream(stream_data, "response_channel")
                        
                        await cache.add_message_to_cache(token=token, source="Bot", message_data=msg.model_dump())
                        
                        await consumer.delete_message(stream_channel="message_channel", message_id=message_id)
        
        except Exception as e:
            print(f"Error processing message: {e}")
            continue

if __name__ == "__main__":
    asyncio.run(main())
