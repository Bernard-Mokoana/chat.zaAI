import pytest
from unittest.mock import patch, MagicMock
from fastapi import HTTPException
from jwt import ExpiredSignatureError, InvalidTokenError

from backend.server.src.utils.token import Token
from backend.database.models.refresh_token import RefreshToken
from backend.database.models.reset_password_token import ResetPasswordToken

class TestTokenUtils:

    @pytest.fixture(autouse=True)
    def setup_method(self):
        self.env_patcher = patch.dict("os.environ", {
            "JWT_SECRET": "a_very_secure_mock_secret_key_that_is_at_least_32_bytes",
            "EXPIRES_IN": "15",  
            "REFRESH_JWT_SECRET": "another_very_secure_mock_secret_key_for_refresh_tokens",
            "VERIFY_JWT_SECRET": "yet_another_very_secure_mock_secret_key_for_verification"
        })
        self.env_patcher.start()
        
        self.token_util = Token()
        self.mock_db = MagicMock()
        self.user = {"id": "user-123", "email": "test@test.com", "name": "Bernard"}
        
        yield
        self.env_patcher.stop()

    def test_token_init_missing_env_vars(self):
        with patch.dict("os.environ", clear=True):
            with pytest.raises(ValueError, match="JWT_SECRET environment variable is required"):
                Token()

    def test_sign_and_decode_access_token(self):
        token = self.token_util.sign_access_token(self.user)
        assert isinstance(token, str)
        
        decoded = self.token_util.decode_access_token(token)
        assert decoded["id"] == "user-123"
        assert "exp" in decoded

    @patch("backend.server.src.utils.token.jwt.decode")
    def test_decode_token_exceptions(self, mock_jwt_decode):
        mock_jwt_decode.side_effect = ExpiredSignatureError()
        with pytest.raises(HTTPException) as exc:
            self.token_util.decode_access_token("expired-token")
        assert exc.value.status_code == 401
        
        mock_jwt_decode.side_effect = InvalidTokenError()
        with pytest.raises(HTTPException) as exc:
            self.token_util.decode_refresh_token("tampered-token")
        assert exc.value.status_code == 401


    def test_sign_and_decode_specialized_tokens(self):
        email_token = self.token_util.sign_email_verification_token(self.user, "jti-1")
        decoded_email = self.token_util.decode_email_verification_token(email_token)
        assert decoded_email["email"] == self.user["email"]

        pwd_token = self.token_util.sign_forgot_password_token(self.user, "jti-2")
        decoded_pwd = self.token_util.decode_forgot_password_verification_token(pwd_token)
        assert decoded_pwd["email"] == self.user["email"]

    def test_cookie_management(self):
        mock_response = MagicMock()
        
        self.token_util.set_refresh_cookie(mock_response, "new-refresh-token")
        mock_response.set_cookie.assert_called_once()
        
        self.token_util.clear_refresh_cookie(mock_response)
        mock_response.delete_cookie.assert_called_once()

    def test_persist_refresh_token(self):
        mock_request = MagicMock()
        mock_request.headers.get.return_value = "192.168.1.1"
        
        result = self.token_util.persist_refresh_token(
            db=self.mock_db, 
            user=self.user, 
            refresh_token="raw-token-string", 
            jti="jti-123", 
            request=mock_request
        )
        
        assert isinstance(result, RefreshToken)
        assert result.user_id == "user-123"
        self.mock_db.add.assert_called_once_with(result)
        self.mock_db.flush.assert_called_once()

    @patch.object(Token, 'persist_refresh_token')
    def test_rotate_refresh_token(self, mock_persist):
        mock_response = MagicMock()
        
        new_access = self.token_util.rotate_refresh_token(
            db=self.mock_db, 
            user=self.user, 
            request=None, 
            response=mock_response
        )
        
        assert isinstance(new_access, str)
        mock_persist.assert_called_once()
        mock_response.set_cookie.assert_called_once()
        
    def test_persist_reset_password_token(self):
        result = self.token_util.persist_reset_password_token(
            db=self.mock_db, user=self.user, reset_token="token", jti="jti-123"
        )
        assert isinstance(result, ResetPasswordToken)
        self.mock_db.add.assert_called_once_with(result)

    def test_invalidate_reset_password_tokens(self):
        self.token_util.invalidate_reset_password_tokens(self.mock_db, "user-123")
        self.mock_db.query.return_value.filter.return_value.update.assert_called_once()

    def test_revoke_email_verification_tokens(self):
        self.token_util.revoke_email_verification_tokens(self.mock_db, "user-123")
        self.mock_db.query.return_value.filter.return_value.update.assert_called_once()