from redis.commands.json.path import Path

import redis.exceptions
import logging

logger = logging.getLogger(__name__)

class Cache:
    def __init__(self, json_client):
        self.json_client = json_client

    def get_chat_history(self, token: str) -> dict | None:
        try:
            data = self.json_client.json().get(token, Path.root_path())
            return data
        except redis.exceptions.ResponseError as e:
            logger.debug(f"Chat history not found: {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to get chat history: {e}")
            raise


