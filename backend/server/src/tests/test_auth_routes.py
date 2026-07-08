from unittest.mock import ANY, patch
from uuid import uuid4

import pytest
from backend.database.models.users import User
from backend.server.main import api
from fastapi import status
from fastapi.testclient import TestClient


class TestAuthRoutes:

    @pytest.fixture(autouse=True)
    def setup_method(self):
        """Arrange a clean test client and suppress aggressive rate limiters/guards."""
        with patch.dict("os.environ", {"APP_ENV": "testing"}):
            self.client = TestClient(api)

        self.mock_user_id = str(uuid4())
        self.registration_payload = {
            "name": "Bernard Mokoana",
            "email": "bernard@example.com",
            "password": "securepassword123",
        }
        self.login_payload = {
            "email": "bernard@example.com",
            "password": "securepassword123",
        }

        yield
        api.dependency_overrides.clear()

    @patch("backend.server.src.routes.auth.AuthService.register_user")
    def test_register_user_endpoint_happy_path(self, mock_register_user):
        mock_created_user = User(
            id=self.mock_user_id,
            name=self.registration_payload["name"],
            email=self.registration_payload["email"],
            password_hash=self.registration_payload["password"],
        )
        mock_register_user.return_value = mock_created_user

        response = self.client.post(
            "/api/v1/auth/register", json=self.registration_payload
        )

        assert response.status_code == status.HTTP_201_CREATED
        mock_register_user.assert_called_once()

    @patch("backend.server.src.routes.auth.AuthService.authenticate_user")
    @patch("backend.server.src.routes.auth.AuthService.login")
    def test_login_endpoint_happy_path(self, mock_login, mock_authenticate_user):
        mock_user_instance = User(
            id=self.mock_user_id, email=self.login_payload["email"]
        )
        mock_authenticate_user.return_value = mock_user_instance

        expected_token_payload = {
            "access_token": "mocked.jwt.access_token",
            "token_type": "Bearer",
            "user": {"id": self.mock_user_id, "email": self.login_payload["email"]},
        }
        mock_login.return_value = expected_token_payload

        response = self.client.post("/api/v1/auth/login", json=self.login_payload)

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == expected_token_payload

        mock_login.assert_called_once_with(db=ANY, user=ANY, request=ANY, response=ANY)

    @patch("backend.server.src.routes.auth.AuthService.refresh_access_token")
    def test_refresh_token_endpoint_happy_path(self, mock_refresh_token):
        expected_refresh_payload = {
            "access_token": "new.mocked.access_token",
            "token_type": "Bearer",
        }
        mock_refresh_token.return_value = expected_refresh_payload

        response = self.client.post("/api/v1/auth/refresh")

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == expected_refresh_payload
        mock_refresh_token.assert_called_once_with(db=ANY, request=ANY, response=ANY)

    @patch("backend.server.src.routes.auth.AuthService.logout")
    def test_logout_endpoint_happy_path(self, mock_logout):
        mock_logout.return_value = {"message": "Logged out successfully"}

        response = self.client.post("/api/v1/auth/logout")

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {"message": "Logged out successfully"}
        mock_logout.assert_called_once_with(db=ANY, request=ANY, response=ANY)
