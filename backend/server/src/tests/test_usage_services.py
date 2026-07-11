from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from backend.database.models.usage_logs import UsageLog
from backend.server.src.services.usage_services import create_usage_log
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session


class TestUsageLogService:
    @pytest.fixture(autouse=True)
    def setup_method(self):
        self.db = MagicMock(spec=Session)
        self.mock_user_id = str(uuid4())

    def test_create_usage_log_happy_path_all_fields(self):
        event_type = "chat_message_sent"
        model = "gpt-4o"
        total_tokens = 142
        message_count = 1

        result = create_usage_log(
            db=self.db,
            user_id=self.mock_user_id,
            event_type=event_type,
            model=model,
            total_tokens=total_tokens,
            message_count=message_count,
        )

        assert isinstance(result, UsageLog)
        assert result.user_id == self.mock_user_id
        assert result.event_type == event_type
        assert result.model == model
        assert result.total_tokens == total_tokens
        assert result.message_count == message_count

        self.db.add.assert_called_once_with(result)
        self.db.commit.assert_called_once()
        self.db.refresh.assert_called_once_with(result)

    def test_create_usage_log_edge_case_optional_fields_omitted(self):
        event_type = "user_login"

        result = create_usage_log(
            db=self.db,
            user_id=self.mock_user_id,
            event_type=event_type,
            model=None,
            total_tokens=None,
            message_count=None,
        )

        assert result.event_type == "user_login"
        assert result.model is None
        assert result.total_tokens == 0
        assert result.message_count == 0
        self.db.commit.assert_called_once()

    def test_create_usage_log_error_condition_database_exception_propagates(self):
        self.db.commit.side_effect = SQLAlchemyError(
            "Database disk sector is full or un-writeable"
        )

        with pytest.raises(SQLAlchemyError) as exc_info:
            create_usage_log(
                db=self.db, user_id=self.mock_user_id, event_type="token_burn"
            )

        assert "Database disk sector is full" in str(exc_info.value)
