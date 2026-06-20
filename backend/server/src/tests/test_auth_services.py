import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone, timedelta
from fastapi import HTTPException, status, Request, Response
from sqlalchemy.orm import Session

from backend.server.src.services.auth_services import AuthService
from backend.database.models.users import User
from backend.database.models.refresh_token import RefreshToken
from backend.database.models.reset_password_token import ResetPasswordToken
from backend.database.models.email_verification_token import EmailVerificationToken
from backend.database.models.tiers import Tier as TierModel


class TestAuthService:
    @pytest.fixture(autouse=True)
    def setup_method(self):
        with patch("backend.server.src.services.auth_services.Token") as MockTokenClass:
            self.mock_token_util = MockTokenClass.return_value
            self.auth_service = AuthService()
            
        self.db = MagicMock(spec=Session)
    
    def test_register_user_success(self):
        self.db.query.return_value.filter.return_value.first.side_effect = [
            None,  
            TierModel(id=1, name="free") 
        ]
        self.mock_token_util.create_jti.return_value = "mocked-jti"
        self.mock_token_util.sign_email_verification_token.return_value = "mocked-verify-token"

        with patch("backend.server.src.services.auth_services.send_email_verification") as mock_send_email:
            user = self.auth_service.register_user(
                db=self.db, name="Bernard Mokoana", email="bernardmokoana@gmail.com", password="39156117@Mokoana"
            )

            assert user.name == "Bernard Mokoana"
            assert user.email == "bernardmokoana@gmail.com"
            self.db.add.assert_called_once_with(user)
            assert self.db.commit.call_count == 2
            mock_send_email.assert_called_once_with("bernardmokoana@gmail.com", "mocked-verify-token")

    @pytest.mark.parametrize("name, email, password", [
        ("", "test@example.com", "password123"),
        ("Name", "", "password123"),
        ("Name", "test@example.com", ""),
    ])
    def test_register_user_missing_fields(self, name, email, password):
        with pytest.raises(HTTPException) as exc_info:
            self.auth_service.register_user(self.db, name, email, password)
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "All fields are required" in exc_info.value.detail

    def test_register_user_invalid_email_format(self):
        with pytest.raises(HTTPException) as exc_info:
            self.auth_service.register_user(self.db, "Bernard", "invalid-email-format", "password123")
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "Invalid email format" in exc_info.value.detail

    def test_register_user_email_already_registered(self):
        self.db.query.return_value.filter.return_value.first.return_value = User(id=1, email="bernardmokoana@gmail.com")

        with pytest.raises(HTTPException) as exc_info:
            self.auth_service.register_user(self.db, "Bernard", "bernardmokoana@gmail.com", "password123")
        assert exc_info.value.status_code == status.HTTP_409_CONFLICT
        assert "Email is already registered" in exc_info.value.detail

    def test_register_user_password_too_short(self):
        self.db.query.return_value.filter.return_value.first.return_value = None 

        with pytest.raises(HTTPException) as exc_info:
            self.auth_service.register_user(self.db, "Bernard", "test@example.com", "short")
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "Password must at least be 8 characters long" in exc_info.value.detail

    def test_authenticate_user_invalid_email(self):
        self.db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            self.auth_service.authenticate_user(db=self.db, email="bernarddira@gmail.com", password="39156117@Mokoana")

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Invalid credentials" in exc_info.value.detail
    
    def test_login_unverified_email(self):
        mock_user = MagicMock(spec=User)
        mock_user.is_verified = False
        
        mock_request = MagicMock(spec=Request)
        mock_response = MagicMock(spec=Response)

        with pytest.raises(HTTPException) as exc_info:
            self.auth_service.login(self.db, mock_user, mock_request, mock_response)
        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert "Email not verified" in exc_info.value.detail

    def test_login_success(self):
        mock_user = MagicMock(spec=User)
        mock_user.id = "user-uuid"
        mock_user.email = "bernarddira@gmail.com"
        mock_user.name = "Bernard Mokoana"
        mock_user.is_verified = True

        mock_request = MagicMock(spec=Request)
        mock_response = MagicMock(spec=Response)

        self.mock_token_util.create_jti.return_value = "session-jti"
        self.mock_token_util.sign_access_token.return_value = "access-token-string"
        self.mock_token_util.sign_refresh_token.return_value = "refresh-token-string"

        result = self.auth_service.login(self.db, mock_user, mock_request, mock_response)

        assert result["access_token"] == "access-token-string"
        assert result["user"]["id"] == "user-uuid"
        self.mock_token_util.set_refresh_cookie.assert_called_once_with(mock_response, "refresh-token-string")
        self.db.commit.assert_called_once()

    def test_verify_email_token_expired(self):
        fixed_now = datetime(2026, 6, 19, 12, 0, 0, tzinfo=timezone.utc)
        expired_time = fixed_now - timedelta(hours=1)

        self.mock_token_util.decode_email_verification_token.return_value = {
            "email": "test@example.com", 
            "jti": "jti-123"
        }
        
        mock_user = User(id=1, email="test@example.com")
        mock_db_token = EmailVerificationToken(
            id=1, 
            user_id=1,
            jwt_id="jti-123",
            is_revoked=False, 
            is_verified=False, 
            expires_at=expired_time
        )
        self.db.query.return_value.filter.return_value.first.side_effect = [mock_user, mock_db_token]

        with patch("backend.server.src.services.auth_services.datetime") as mock_datetime:
            mock_datetime.now.return_value = fixed_now
            
            with pytest.raises(HTTPException) as exc_info:
                self.auth_service.verify_email_token(self.db, "expired-token-string")
                
            assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
            assert "Verification token expired" in exc_info.value.detail
                    
    def test_request_password_reset_user_not_found(self):
        self.db.query.return_value.filter.return_value.first.return_value = None

        result = self.auth_service.request_password_reset(self.db, "nonexistent@example.com")
        assert "link has been sent" in result["message"]

    def test_request_password_reset_success(self):
        mock_user = User(id=1, email="bernarddira@gmail.com")
        self.db.query.return_value.filter.return_value.first.return_value = mock_user
        self.mock_token_util.create_jti.return_value = "reset-jti"
        self.mock_token_util.sign_forgot_password_token.return_value = "reset-token-string"

        with patch("backend.server.src.services.auth_services.send_password_reset_email") as mock_email:
            result = self.auth_service.request_password_reset(self.db, "bernarddira@gmail.com")

            self.mock_token_util.invalidate_reset_password_tokens.assert_called_once_with(self.db, mock_user.id)
            mock_email.assert_called_once_with("bernarddira@gmail.com", "reset-token-string")
            assert "link has been sent" in result["message"]
    
    def test_refresh_access_token_missing_cookie(self):
        mock_request = MagicMock(spec=Request)
        mock_request.cookies.get.return_value = None
        mock_response = MagicMock(spec=Response)

        with pytest.raises(HTTPException) as exc_info:
            self.auth_service.refresh_access_token(self.db, mock_request, mock_response)
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Missing refresh token" in exc_info.value.detail
    
    def test_logout_clears_cookie_and_revokes_token(self):
        mock_request = MagicMock(spec=Request)
        mock_request.cookies.get.return_value = "active-refresh-token"
        mock_response = MagicMock(spec=Response)

        self.mock_token_util.decode_refresh_token.return_value = {"id": "user-uuid", "jti": "jti-123"}
        mock_db_token = MagicMock(spec=RefreshToken)
        mock_db_token.is_revoked = False
        self.db.query.return_value.filter.return_value.first.return_value = mock_db_token

        result = self.auth_service.logout(self.db, mock_request, mock_response)

        assert mock_db_token.is_revoked is True
        self.db.commit.assert_called_once()
        self.mock_token_util.clear_refresh_cookie.assert_called_once_with(mock_response)
        assert result == {"message": "Logged out successfully"}