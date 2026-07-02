from datetime import date
from importlib import util
from pathlib import Path
from unittest.mock import MagicMock, patch


def _load_dbhelper_module():
    module_path = Path(__file__).resolve().parents[1] / "utils" / "dbHelper.py"
    spec = util.spec_from_file_location("worker_dbHelper", module_path)
    module = util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


dbHelper = _load_dbhelper_module()


class TestDbHelper:
    def test_log_worker_usage_builds_upsert_and_commits(self):
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

        with patch.object(dbHelper, "insert", mock_insert), patch.object(
            dbHelper, "date"
        ) as mock_date, patch.object(dbHelper.func, "now", return_value="now"):
            mock_date.today.return_value = date(2026, 7, 2)
            dbHelper.log_worker_usage(
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
            model_name="gpt-4o",
            total_tokens=12,
            message_count=1,
        )
        mock_base_stmt.on_conflict_do_update.assert_called_once()
        mock_db.execute.assert_called_once_with(mock_upsert_stmt)
        mock_db.commit.assert_called_once()
