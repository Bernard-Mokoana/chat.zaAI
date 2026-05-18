from src.redis.config import Redis
import json
import asyncio
from src.model.gptj import GPT
from src.redis.cache import Cache
from src.schema.chat import Message
from src.redis.stream import StreamConsumer
from src.redis.producer import Producer

redis_client = Redis()

async def main():
    json_client = redis_client.create_json_connection()
    redis_conn = await redis_client.create_connection()
    consumer = StreamConsumer(redis_conn)
    cache = Cache(json_client)
    producer = Producer(redis_conn)

    print("Stream consumer started")
    print("Stream waiting for new messages")

    while True:
        response = await consumer.consume_stream(stream_channel="message_channel", count=1, block=0)

        if response:
            for stream, messages in response:
                for message in  messages:
                    message_id = message[0]
                    token_bytes, msg_bytes = next(iter(message[1].items()))
                    token = token_bytes.decode("utf-8") if isinstance(token_bytes, (bytes, bytearray)) else str(token_bytes)
                    message_text = msg_bytes.decode("utf-8") if isinstance(msg_bytes, (bytes, bytearray)) else str(msg_bytes)

                    msg = Message(msg=message_text)

                    await cache.add_message_to_cache(token=token, source="Human", message_data=msg.model_dump())

                    data = await cache.get_chat_history(token=token)

                    message_data = data['messages'][-4:]
                    
                    input = ["" + i["msg"] for i in message_data]
                    input = " ".join(input)
                    
                    res = GPT().query(input)

                    msg = Message(
                        msg=res
                    )

                    # Extract only the text string for stream, not the full JSON dump
                    stream_data = {}
                    stream_data[str(token)] = msg.msg

                    await producer.add_to_stream(stream_data, "response_channel")

                    await cache.add_message_to_cache(token=token, source="Bot", message_data=msg.model_dump())

                await consumer.delete_message(stream_channel="message_channel", message_id=message_id)

if __name__ == "__main__":
    asyncio.run(main())
