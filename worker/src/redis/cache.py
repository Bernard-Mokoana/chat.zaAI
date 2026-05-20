from .config import Redis
from redis.commands.json.path import Path
from datetime import datetime
from uuid import UUID

class Cache:
    def __init__(self, json_client):
        self.json_client = json_client
    
    def _json_safe(self, value):
        if isinstance(value, dict):
            return {k: self._json_safe(v) for k, v in value.items()}
        if isinstance(value, list):
            return [self._json_safe(v) for v in value]
        if isinstance(value, UUID):
            return str(value)
        if isinstance(value, datetime):
            return value.isoformat()
        return value

    def get_chat_history(self, token: str):
        data = self.json_client.json().get(
            str(token), Path.root_path())
        
        return data
    
    async def add_message_to_cache(self, token: str, source: str, message_data: dict):
        key = str(token)
        messages_path = Path(".messages")

        message_data = self._json_safe(message_data)
        
        source_normalized = (source or "").lower()
        if source_normalized == "human":
            message_data['msg'] = "Human: " + (message_data['msg'])
        elif source_normalized == "bot":
            message_data['msg'] = "Bot: " + (message_data['msg'])

        existing = self.json_client.json().get(key, Path.root_path())
        if existing is None:
            self.json_client.json().set(key, Path.root_path(), {"messages": [message_data]})
            return

        messages = self.json_client.json().get(key, messages_path)
        if messages is None:
            self.json_client.json().set(key, messages_path, [message_data])
            return

        self.json_client.json().arrappend(key, messages_path, message_data)
