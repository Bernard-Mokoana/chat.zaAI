import pytest
from unittest.mock import MagicMock, patch
from fastapi import HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials

from backend.server.src.middlewares.jwt_validation import get_current_user
from backend.database.models.users import User

class TestHwtValidation:
    @pytest.fixture(autouse=True)
    def setup_method(self):
        self.mock_db = MagicMock()
        self.mock_user_id = "user-123"

    @patch("backend.server.src.middlewares.jwt_validation.token_util")
    def test_get_current_user_happy_patch(self, mock_token_util):
        mock_credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="valid.jwt.token")
        mock_token_util.decode_access_token.return_value = {"id": self.mock_user_id}

        excepted_user = User(id=self.mock_user_id, email="bernard@gmail.com")
        self.mock_db.query.return_value.filter.return_value.first.return_value = excepted_user

        user = get_current_user(credentials=mock_credentials, db=self.mock_db)

        assert user == excepted_user
        mock_token_util.decode_access_token.assert_called_once_with("valid.jwt.token")

    def test_get_current_user_error_missing_credentials(self):
        with pytest.raises(HTTPException) as exc_info:
            get_current_user(credentials=None, db=self.mock_db)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Invalid or expired credentials" in exc_info.value.detail

    def test_get_current_user_error_invalid_scheme(self):
        mock_credentials = HTTPAuthorizationCredentials(scheme="Basic", credentials="encoded:string")

        with pytest.raises(HTTPException) as exc_info:
            get_current_user(credentials=mock_credentials, db=self.mock_db)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

    @patch("backend.server.src.middlewares.jwt_validation.token_util")
    def test_get_current_user_error_missing_payload_id(self, mock_token_util):
        mock_credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="valid.jwt.token")
        mock_token_util.decode_access_token.return_value = {"email": "bernard@gmail.com"}

        with pytest.raises(HTTPException) as exc_info:
            get_current_user(credentials=mock_credentials, db=self.mock_db)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

    @patch("backend.server.src.middlewares.jwt_validation.token_util")
    def test_get_current_user_error_user_not_found(self, mock_token_util):
        mock_credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="valid.jwt.token")
        mock_token_util.decode_access_token.return_value = {"id": self.mock_user_id}

        self.mock_db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            get_current_user(credentials=mock_credentials, db=self.mock_db)
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

