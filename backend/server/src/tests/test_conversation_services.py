import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from uuid import uuid4, UUID
from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
import redis.exceptions

from backend.server.src.services.conversation_services import ConversationService
from backend.database.models.conversations import Conversation
from backend.database.models.messages import Message


class TestConversationService:
    @pytest.fixture(autouse=True)
    def setup_method(self):
        self.db = MagicMock(spec=Session)
        self.redis_client = MagicMock()
        self.redis_client.json = MagicMock()
        self.redis_client.json().set = AsyncMock()
        self.redis_client.json().get = AsyncMock()
        self.redis_client.expire = AsyncMock()

        self.service = ConversationService()
        self.mock_user_id = str(uuid4())
        self.mock_chat_token = str(uuid4())

    def test_save_chat_message_happy_path_new_conversation(self):
        self.db.query.return_value.filter.return_value.first.return_value = None 
        content = "Hello AI! How do decoupled architectures work?"

        result = self.service.save_chat_message(
            db=self.db, 
            user_id=self.mock_user_id, 
            chat_token=self.mock_chat_token, 
            role="user", 
            content=content
        )

        assert isinstance(result, Message)
        assert result.content == content
        assert result.role == "user"
        self.db.add.assert_any_call(result)
        self.db.commit.assert_called_once()

    def test_save_chat_message_happy_path_existing_conversation(self):
        existing_chat = Conversation(id=UUID(self.mock_chat_token), user_id=UUID(self.mock_user_id), title="Tech Chat")
        self.db.query.return_value.filter.return_value.first.return_value = existing_chat

        result = self.service.save_chat_message(
            db=self.db, 
            user_id=self.mock_user_id, 
            chat_token=self.mock_chat_token, 
            role="assistant", 
            content="Decoupled networks scale horizontally."
        )

        assert result.conversation_id == existing_chat.id
        assert result.role == "assistant"
        self.db.commit.assert_called_once()

    def test_save_chat_message_error_condition_invalid_token_format(self):
        invalid_token = "not-a-valid-uuid"

        with pytest.raises(ValueError) as exc_info:
            self.service.save_chat_message(self.db, self.mock_user_id, invalid_token, "user", "Hi")
        assert "Invalid chat_token format" in str(exc_info.value)

    def test_save_chat_message_error_condition_forbidden_user(self):
        stranger_id = uuid4()
        existing_chat = Conversation(id=UUID(self.mock_chat_token), user_id=stranger_id, title="Secret Chat")
        self.db.query.return_value.filter.return_value.first.return_value = existing_chat

        with pytest.raises(PermissionError) as exc_info:
            self.service.save_chat_message(self.db, self.mock_user_id, self.mock_chat_token, "user", "Hi")
        assert "Conversation does not belong to user" in str(exc_info.value)

    def test_save_chat_message_error_condition_database_rollback(self):
        self.db.query.return_value.filter.return_value.first.side_effect = SQLAlchemyError("DB Connection Timed Out")

        with pytest.raises(SQLAlchemyError):
            self.service.save_chat_message(self.db, self.mock_user_id, self.mock_chat_token, "user", "Hi")
        self.db.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_chat_session_happy_path(self):
        result = await self.service.create_chat_session(
            redis_client=self.redis_client, 
            user_id=self.mock_user_id, 
            name="Bernard Mokoana"
        )

        assert result["user_id"] == self.mock_user_id
        assert result["name"] == "Bernard Mokoana"
        assert result["messages"] == []
        self.redis_client.json().set.assert_called_once()
        self.redis_client.expire.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_chat_session_error_condition_redis_failure(self):
        self.redis_client.json().set.side_effect = redis.exceptions.RedisError("Cluster unreachable")

        with pytest.raises(redis.exceptions.RedisError):
            await self.service.create_chat_session(self.redis_client, self.mock_user_id, "Bernard")

    @pytest.mark.asyncio
    async def test_get_chat_session_happy_path(self):
        mock_payload = [{"token": self.mock_chat_token, "user_id": self.mock_user_id, "name": "Bernard"}]
        self.redis_client.json().get.return_value = mock_payload

        session = await self.service.get_chat_session(self.redis_client, self.mock_chat_token, self.mock_user_id)

        assert session["name"] == "Bernard"
        assert session["user_id"] == self.mock_user_id

    @pytest.mark.asyncio
    async def test_get_chat_session_error_condition_expired(self):
        self.redis_client.json().get.return_value = None

        with pytest.raises(ValueError) as exc_info:
            await self.service.get_chat_session(self.redis_client, self.mock_chat_token, self.mock_user_id)
        assert "Session expired or does not exist" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_chat_session_error_condition_unauthorized(self):
        stranger_payload = [{"token": self.mock_chat_token, "user_id": "someone-else-id", "name": "Stranger"}]
        self.redis_client.json().get.return_value = stranger_payload

        with pytest.raises(PermissionError) as exc_info:
            await self.service.get_chat_session(self.redis_client, self.mock_chat_token, self.mock_user_id)
        assert "Forbidden" in str(exc_info.value)