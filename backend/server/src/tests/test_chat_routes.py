from unittest.mock import ANY, AsyncMock, MagicMock, patch  # Added ANY here
from uuid import uuid4

import pytest
from backend.database.config.databaseConfig import get_read_db
from backend.database.models.users import User
from backend.server.main import api
from backend.server.src.middlewares.jwt_validation import get_current_user
from fastapi import status
from fastapi.testclient import TestClient


class TestChatRoutes:

    @pytest.fixture(autouse=True)
    def setup_method(self):
        self.client = TestClient(api)

        self.mock_user = MagicMock(spec=User)
        self.mock_user.id = uuid4()
        self.mock_user.email = "bernard@example.com"
        self.mock_user.name = "Bernard Mokoana"

        self.mock_db = MagicMock()

        api.dependency_overrides[get_current_user] = lambda: self.mock_user
        api.dependency_overrides[get_read_db] = lambda: self.mock_db

        yield

        api.dependency_overrides.clear()

    @patch("backend.server.src.routes.chat.create_token_service")
    def test_token_generator_happy_path(self, mock_create_token_service):
        mock_response_payload = {
            "token": "mocked-redis-chat-token",
            "user_id": str(self.mock_user.id),
        }
        mock_create_token_service.return_value = mock_response_payload

        response = self.client.post("/api/v1/chat/token?name=SystemArchitectureSession")

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == mock_response_payload

        mock_create_token_service.assert_called_once_with(
            redis=ANY,
            conversation_service=ANY,
            user_id=str(self.mock_user.id),
            name="SystemArchitectureSession",
        )

    def test_token_generator_edge_case_missing_query_param(self):
        response = self.client.post("/api/v1/chat/token")

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
