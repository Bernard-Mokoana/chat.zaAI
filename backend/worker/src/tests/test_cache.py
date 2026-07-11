import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pytest
from unittest.mock import MagicMock
from src.redis.cache import Cache


@pytest.fixture
def mock_json_client():
    client = MagicMock()
    client.json = MagicMock()
    return client


class TestCacheGetChatHistory:
    def test_get_chat_history_returns_data(self, mock_json_client):
        cache = Cache(mock_json_client)
        mock_json_client.json.get.return_value = {"messages": []}
        result = cache.get_chat_history("tok-1")
        assert result == {"messages": []}

    def test_get_chat_history_returns_none_when_missing(self, mock_json_client):
        cache = Cache(mock_json_client)
        mock_json_client.json.get.return_value = None
        assert cache.get_chat_history("tok-1") is None


class TestCacheAddMessage:
    def test_creates_new_key_with_human_prefix(self, mock_json_client):
        cache = Cache(mock_json_client)
        mock_json_client.json.get.return_value = None
        cache.add_message_to_cache("tok-1", "Human", {"msg": "Hello"})
        mock_json_client.json.set.assert_called_once_with(
            "tok-1", None, {"messages": [{"msg": "Human: Hello"}]}
        )

    def test_creates_new_key_with_bot_prefix(self, mock_json_client):
        cache = Cache(mock_json_client)
        mock_json_client.json.get.return_value = None
        cache.add_message_to_cache("tok-1", "Bot", {"msg": "Reply"})
        mock_json_client.json.set.assert_called_once_with(
            "tok-1", None, {"messages": [{"msg": "Bot: Reply"}]}
        )

    def test_appends_to_existing_key(self, mock_json_client):
        cache = Cache(mock_json_client)
        mock_json_client.json.get.side_effect = [
            {"messages": [{"msg": "Human: hi"}]},
            [{"msg": "Human: hi"}],
        ]
        cache.add_message_to_cache("tok-1", "Bot", {"msg": "reply"})
        mock_json_client.json.arrappend.assert_called_once_with(
            "tok-1", None, {"msg": "Bot: reply"}
        )
