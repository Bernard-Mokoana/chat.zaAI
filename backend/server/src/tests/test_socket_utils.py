from unittest.mock import patch

import pytest
from backend.server.src.socket.utils import validate_token


@pytest.mark.asyncio
class TestSocketUtils:

    @patch("backend.server.src.socket.utils.token_util")
    async def test_validate_token_happy_path(self, mock_token_util):
        expected_payload = {"id": "user-123", "email": "test@example.com"}
        mock_token_util.decode_access_token.return_value = expected_payload

        result = await validate_token("valid-jwt-token")

        assert result == expected_payload
        mock_token_util.decode_access_token.assert_called_once_with("valid-jwt-token")

    async def test_validate_token_missing_token(self):
        with pytest.raises(ValueError, match="Missing token"):
            await validate_token(None)

        with pytest.raises(ValueError, match="Missing token"):
            await validate_token("")

    @patch("backend.server.src.socket.utils.token_util")
    async def test_validate_token_invalid_format(self, mock_token_util):
        mock_token_util.decode_access_token.side_effect = Exception(
            "Signature verification failed"
        )

        with pytest.raises(
            ValueError, match="Invalid token: Signature verification failed"
        ):
            await validate_token("tampered-jwt-token")

    @patch("backend.server.src.socket.utils.token_util")
    async def test_validate_token_missing_payload_id(self, mock_token_util):
        mock_token_util.decode_access_token.return_value = {
            "email": "no-id@example.com"
        }

        with pytest.raises(ValueError, match="Invalid token payload - missing id"):
            await validate_token("valid-but-empty-jwt")
