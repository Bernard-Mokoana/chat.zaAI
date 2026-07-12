import sys
from pathlib import Path as SysPath

sys.path.insert(0, str(SysPath(__file__).resolve().parents[2]))

import pytest
from unittest.mock import MagicMock
from src.redis.cache import Cache


@pytest.fixture
def mock_json_client():
    client = MagicMock()
    return client


@pytest.fixture
def json_cmds(mock_json_client):
    return mock_json_client.json.return_value


def _path_str(path_arg):
    return getattr(path_arg, "strPath", str(path_arg))


class TestCacheGetChatHistory:
    @pytest.mark.asyncio
    async def test_get_chat_history_returns_data(self, mock_json_client, json_cmds):
        cache = Cache(mock_json_client)
        json_cmds.get.return_value = {"messages": []}

        result = await cache.get_chat_history("tok-1")

        assert result == {"messages": []}
        json_cmds.get.assert_called_once()
        args, _ = json_cmds.get.call_args
        assert args[0] == "tok-1"
        assert _path_str(args[1]) == "."

    @pytest.mark.asyncio
    async def test_get_chat_history_returns_none_when_missing(self, mock_json_client, json_cmds):
        cache = Cache(mock_json_client)
        json_cmds.get.return_value = None

        result = await cache.get_chat_history("tok-1")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_chat_history_stringifies_token(self, mock_json_client, json_cmds):
        cache = Cache(mock_json_client)
        json_cmds.get.return_value = None

        await cache.get_chat_history(12345)

        args, _ = json_cmds.get.call_args
        assert args[0] == "12345"


class TestCacheAddMessage:
    @pytest.mark.asyncio
    async def test_creates_new_key_with_human_prefix(self, mock_json_client, json_cmds):
        cache = Cache(mock_json_client)
        json_cmds.get.return_value = None  # root_path check -> key absent

        await cache.add_message_to_cache("tok-1", "Human", {"msg": "Hello"})

        json_cmds.set.assert_called_once()
        args, _ = json_cmds.set.call_args
        assert args[0] == "tok-1"
        assert _path_str(args[1]) == "."
        assert args[2] == {"messages": [{"msg": "Human: Hello"}]}

    @pytest.mark.asyncio
    async def test_creates_new_key_with_bot_prefix(self, mock_json_client, json_cmds):
        cache = Cache(mock_json_client)
        json_cmds.get.return_value = None

        await cache.add_message_to_cache("tok-1", "Bot", {"msg": "Reply"})

        args, _ = json_cmds.set.call_args
        assert args[2] == {"messages": [{"msg": "Bot: Reply"}]}

    @pytest.mark.asyncio
    async def test_source_prefix_is_case_insensitive_on_input(self, mock_json_client, json_cmds):
        cache = Cache(mock_json_client)
        json_cmds.get.return_value = None

        await cache.add_message_to_cache("tok-1", "hUmAn", {"msg": "Hi"})

        args, _ = json_cmds.set.call_args
        assert args[2] == {"messages": [{"msg": "Human: Hi"}]}

    @pytest.mark.asyncio
    async def test_unrecognized_source_gets_no_prefix(self, mock_json_client, json_cmds):
        cache = Cache(mock_json_client)
        json_cmds.get.return_value = None

        await cache.add_message_to_cache("tok-1", "System", {"msg": "note"})

        args, _ = json_cmds.set.call_args
        assert args[2] == {"messages": [{"msg": "note"}]}

    @pytest.mark.asyncio
    async def test_missing_msg_key_raises(self, mock_json_client, json_cmds):
        cache = Cache(mock_json_client)
        json_cmds.get.return_value = None

        with pytest.raises(ValueError, match="message_data must contain 'msg' key"):
            await cache.add_message_to_cache("tok-1", "Human", {"text": "oops"})

    @pytest.mark.asyncio
    async def test_appends_to_existing_key_with_messages(self, mock_json_client, json_cmds):
        cache = Cache(mock_json_client)
        # First .get() = existence check at root path; second = fetch .messages
        json_cmds.get.side_effect = [
            {"messages": [{"msg": "Human: hi"}]},
            [{"msg": "Human: hi"}],
        ]

        await cache.add_message_to_cache("tok-1", "Bot", {"msg": "reply"})

        json_cmds.arrappend.assert_called_once()
        args, _ = json_cmds.arrappend.call_args
        assert args[0] == "tok-1"
        assert _path_str(args[1]) == ".messages"
        assert args[2] == {"msg": "Bot: reply"}
        json_cmds.set.assert_not_called()

    @pytest.mark.asyncio
    async def test_existing_key_without_messages_field_sets_messages_path(self, mock_json_client, json_cmds):
        cache = Cache(mock_json_client)
        # Key exists at root, but .messages path returns None (unexpected shape)
        json_cmds.get.side_effect = [
            {"other_field": True},
            None,
        ]

        await cache.add_message_to_cache("tok-1", "Human", {"msg": "hi"})

        json_cmds.set.assert_called_once()
        args, _ = json_cmds.set.call_args
        assert args[0] == "tok-1"
        assert _path_str(args[1]) == ".messages"
        assert args[2] == [{"msg": "Human: hi"}]
        json_cmds.arrappend.assert_not_called()

    @pytest.mark.asyncio
    async def test_json_safe_converts_uuid_and_datetime(self, mock_json_client, json_cmds):
        from uuid import uuid4
        from datetime import datetime

        cache = Cache(mock_json_client)
        json_cmds.get.return_value = None
        msg_id = uuid4()
        ts = datetime(2026, 1, 1, 12, 0, 0)

        await cache.add_message_to_cache(
            "tok-1", "Human", {"msg": "hi", "id": msg_id, "timestamp": ts}
        )

        args, _ = json_cmds.set.call_args
        stored = args[2]["messages"][0]
        assert stored["id"] == str(msg_id)
        assert stored["timestamp"] == ts.isoformat()

    @pytest.mark.asyncio
    async def test_does_not_mutate_caller_dict(self, mock_json_client, json_cmds):
        cache = Cache(mock_json_client)
        json_cmds.get.return_value = None
        original = {"msg": "Hello"}

        await cache.add_message_to_cache("tok-1", "Human", original)

        assert original == {"msg": "Hello"}