import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone
from backend.server.src.utils.token import Token

def test_create_jti():
    token_util = Token()
    jti = token_util.create_jti()
    assert isinstance(jti, str)
    assert len(jti) > 0

@patch("backend.server.src.utils.token.jwt")
def test_sign_access_token(mock_jwt):
    mock_jwt.encode.return_value = "mocked.jwt.token"

    with patch.dict("os.environ", {
        "JWT_SECRET": "test-secret",
        "EXPIRES_IN": "15",
        "REFRESH_JWT_SECRET": "refresh-secret",
        "VERIFY_JWT_SECRET": "verify-secret"
    }):
        token_util = Token()

        user_payload = {
            "id": "user-123",
            "email": "bernard@gmail.com",
            "name": "Bernard Mokoana"
        }

        token = token_util.sign_access_token(user=user_payload)

        assert token == "mocked.jwt.token"
        mock_jwt.encode.assert_called_once()