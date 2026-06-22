import pytest
from unittest.mock import MagicMock, patch
from uuid import uuid4, UUID

from backend.server.src.utils.dbUtils import save_chat_message, get_conversation_history_from_db
from backend.database.models.conversations import Conversation
from backend.database.models.messages import Message

class TestDbUtils:
    @pytest.fixture(autouse=True)
    def setup_method(self):
        self.mock_db = MagicMock()
        self.user_id_str = str(uuid4())
        self.chat_token_str = str(uuid4())
        self.user_uuid = UUID(self.user_id_str)
        self.chat_uuid = UUID(self.chat_token_str)

    @patch("backend.server.src.utils.dbUtils.conversation_service")
    def test_save_chat_message_delegates_correctly(self, mock_conversation_service):
        mock_conversation_service.save_chat_message.return_value = "saved_message"

        result = save_chat_message(self.mock_db, self.user_id_str, self.chat_token_str, "user", "Hello")

        assert result == "saved_message"
        mock_conversation_service.save_chat_message.assert_called_once_with(
            db=self.mock_db,
            user_id=self.user_id_str,
            chat_token=self.chat_token_str,
            role="user",
            content="Hello"
        )

    def test_get_history_happy_path(self):
        mock_conversation = Conversation(id=self.chat_uuid, user_id=self.user_uuid)

        mock_messages = [
            Message(role="assistant", content="How can I help?"),
            Message(role="user", content="Hello"),
        ]

        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_conversation
        self.mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = mock_messages

        history = get_conversation_history_from_db(self.mock_db, self.user_id_str, self.chat_token_str)

        assert len(history) == 2
        assert history[0] == {"role": "user", "msg": "Hello"}
        assert history[1] == {"role": "assistant", "msg": "How can I help?"}

    def test_get_history_error_invalid_uuid(self):
        with pytest.raises(ValueError, match="Invalid conversation or user id"):
            get_conversation_history_from_db(self.mock_db, "invalid-user", self.chat_token_str)

    def test_get_history_edge_case_not_found(self):
        self.mock_db.query.return_value.filter.return_value.first.return_value = None

        history = get_conversation_history_from_db(self.mock_db, self.user_id_str, self.chat_token_str)

        assert history == []

    def test_get_history_error_permission_denied(self):
        stranger_uuid = UUID(int=0)
        mock_conversation = Conversation(id=self.chat_uuid, user_id=stranger_uuid)
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_conversation

        with pytest.raises(PermissionError, match="Conversation does not belong to user"):
            get_conversation_history_from_db(self.mock_db, self.user_id_str, self.chat_token_str)

        


