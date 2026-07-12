import sys
from pathlib import Path
from datetime import date
from importlib import util
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID

import pytest

_dbhelper_path = Path(__file__).resolve().parent.parent / "utils" / "db_helper.py"
spec = util.spec_from_file_location("worker_dbHelper", _dbhelper_path)
_dbhelper = util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(_dbhelper)

USER_ID = "11111111-1111-1111-1111-111111111111"
OTHER_USER_ID = "22222222-2222-2222-2222-222222222222"
CONV_ID = "33333333-3333-3333-3333-333333333333"

class TestLogWorkerUsage:
    def test_builds_upsert_and_commits(self):
        mock_db = MagicMock()
        session_factory = MagicMock()
        session_factory.return_value.__enter__.return_value = mock_db
        session_factory.return_value.__exit__.return_value = False

        mock_base_stmt = MagicMock()
        mock_upsert_stmt = MagicMock()
        mock_excluded = MagicMock()
        mock_base_stmt.excluded = mock_excluded
        mock_base_stmt.on_conflict_do_update.return_value = mock_upsert_stmt
        mock_base_stmt.values.return_value = mock_base_stmt
        mock_insert = MagicMock(return_value=mock_base_stmt)

        with patch.object(_dbhelper, "insert", mock_insert), patch.object(
            _dbhelper, "date"
        ) as mock_date, patch.object(_dbhelper.func, "now", return_value="now"):
            mock_date.today.return_value = date(2026, 7, 2)
            _dbhelper.log_worker_usage(
                session_factory=session_factory,
                user_id="user-123",
                model="gpt-4o",
                total_tokens=12,
                message_count=1,
            )

        mock_insert.assert_called_once()
        mock_base_stmt.values.assert_called_once_with(
            user_id="user-123",
            log_date=date(2026, 7, 2),
            model="gpt-4o",
            total_tokens=12,
            message_count=1,
        )
        mock_base_stmt.on_conflict_do_update.assert_called_once()
        mock_db.execute.assert_called_once_with(mock_upsert_stmt)
        mock_db.commit.assert_called_once()

    def test_none_model_defaults_to_unknown(self):
        mock_db = MagicMock()
        session_factory = MagicMock()
        session_factory.return_value.__enter__.return_value = mock_db
        session_factory.return_value.__exit__.return_value = False

        mock_base_stmt = MagicMock()
        mock_upsert_stmt = MagicMock()
        mock_base_stmt.excluded = MagicMock()
        mock_base_stmt.on_conflict_do_update.return_value = mock_upsert_stmt
        mock_base_stmt.values.return_value = mock_base_stmt
        mock_insert = MagicMock(return_value=mock_base_stmt)

        with patch.object(_dbhelper, "insert", mock_insert), patch.object(_dbhelper, "date") as mock_date:
            mock_date.today.return_value = date(2026, 7, 2)
            _dbhelper.log_worker_usage(
                session_factory=session_factory,
                user_id="u1",
                model=None,
                total_tokens=None,
                message_count=None,
            )

        mock_base_stmt.values.assert_called_once_with(
            user_id="u1",
            log_date=date(2026, 7, 2),
            model="unknown",
            total_tokens=0,
            message_count=0,
        )

    def test_database_exception_is_logged(self):
        mock_db = MagicMock()
        session_factory = MagicMock()
        session_factory.return_value.__enter__.return_value = mock_db
        session_factory.return_value.__exit__.return_value = False
        mock_db.commit.side_effect = RuntimeError("db down")

        with patch.object(_dbhelper.func, "now", return_value="now"), patch.object(
            _dbhelper, "logger"
        ) as mock_logger:
            _dbhelper.log_worker_usage(
                session_factory=session_factory,
                user_id="u1",
                model="gpt-4o",
                total_tokens=5,
                message_count=1,
            )
        mock_logger.error.assert_called_once()


class TestNormalizeMessageRole:
    def test_user_variants(self):
        assert _dbhelper._normalize_message_role("user") == "user"
        assert _dbhelper._normalize_message_role("human") == "user"
        assert _dbhelper._normalize_message_role("  USER  ") == "user"

    def test_assistant_variants(self):
        assert _dbhelper._normalize_message_role("assistant") == "assistant"
        assert _dbhelper._normalize_message_role("bot") == "assistant"
        assert _dbhelper._normalize_message_role("  BOT  ") == "assistant"

    def test_system(self):
        assert _dbhelper._normalize_message_role("system") == "system"

    def test_invalid_role_raises(self):
        with pytest.raises(ValueError, match="Invalid message role"):
            _dbhelper._normalize_message_role("alien")


class TestSaveWorkerMessage:
    def test_new_conversation_created_when_token_missing(self):
        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = None
        session_factory = MagicMock(return_value=mock_session)
        
        _dbhelper.save_worker_message(session_factory, USER_ID, CONV_ID, "user", "Hello world")
        
        assert mock_session.add.call_count == 2
        added_types = [type(call.args[0]).__name__ for call in mock_session.add.call_args_list]
        assert added_types == ["Conversation", "Message"]
        mock_session.commit.assert_called_once()
        mock_session.close.assert_called_once()

    def test_existing_conversation_appends_message(self):
        mock_session = MagicMock()
        conversation = MagicMock()
        conversation.id = CONV_ID
        conversation.user_id = UUID(USER_ID)  
        mock_session.query.return_value.filter.return_value.first.return_value = conversation
        session_factory = MagicMock(return_value=mock_session)

        _dbhelper.save_worker_message(session_factory, USER_ID, CONV_ID, "assistant", "Reply")

        assert mock_session.add.call_count == 1
        mock_session.commit.assert_called_once()
        mock_session.close.assert_called_once()

    def test_wrong_user_raises_permission_error(self):
        mock_session = MagicMock()
        conversation = MagicMock()
        conversation.user_id = UUID(OTHER_USER_ID)  
        mock_session.query.return_value.filter.return_value.first.return_value = conversation
        session_factory = MagicMock(return_value=mock_session)

        with pytest.raises(PermissionError, match="does not belong to user"):
            _dbhelper.save_worker_message(session_factory, USER_ID, CONV_ID, "user", "Hello")

    def test_invalid_uuid_raises_value_error(self):
        session_factory = MagicMock()
        with pytest.raises(ValueError, match="Invalid token or user_id format"):
            _dbhelper.save_worker_message(session_factory, "bad-uuid", "conv-uuid", "user", "Hello")


class TestGetConversationHistoryFromDb:
    def test_returns_formatted_messages(self):
        mock_session = MagicMock()
        conversation = MagicMock()
        conversation.user_id = UUID(USER_ID)
        mock_session.query.return_value.filter.return_value.first.return_value = conversation
        
        msg_new = MagicMock(role="assistant", content="Bot reply")
        msg_old = MagicMock(role="user", content="Human ask")
        mock_session.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [
            msg_new, msg_old
            ]
        
        result = _dbhelper.get_conversation_history_from_db(mock_session, USER_ID, CONV_ID, limit=2)
        assert result == [{"role": "user", "msg": "Human ask"}, {"role": "assistant", "msg": "Bot reply"}]

    def test_empty_conversation_returns_empty_list(self):
        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = None
        assert _dbhelper.get_conversation_history_from_db(mock_session, USER_ID, CONV_ID) == []

    def test_wrong_user_raises_permission_error(self):
        mock_session = MagicMock()
        conversation = MagicMock()
        conversation.user_id = UUID(OTHER_USER_ID)
        mock_session.query.return_value.filter.return_value.first.return_value = conversation
        with pytest.raises(PermissionError):
            _dbhelper.get_conversation_history_from_db(mock_session, USER_ID, CONV_ID)

    def test_invalid_uuid_returns_empty_list(self):
        mock_session = MagicMock()
        result = _dbhelper.get_conversation_history_from_db(mock_session, "bad-uuid", "conv-uuid")
        assert result == []