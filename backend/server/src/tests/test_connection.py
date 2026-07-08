from unittest.mock import AsyncMock

import pytest
from backend.server.src.socket.connection import ConnectionManager
from fastapi import WebSocket


@pytest.mark.asyncio
class TestConnectionManager:
    @pytest.fixture(autouse=True)
    def setup_method(self):
        self.manager = ConnectionManager()
        self.mock_ws = AsyncMock(spec=WebSocket)

    async def test_connect_happy_path(self):
        await self.manager.connect(self.mock_ws)

        self.mock_ws.accept.assert_called_once()
        assert self.mock_ws in self.manager.active_connections

    async def test_disconnect_happy_path_removes_socket(self):
        self.manager.active_connections.append(self.mock_ws)

        await self.manager.disconnect(self.mock_ws)

        assert self.mock_ws not in self.manager.active_connections

    async def test_disconnect_edge_case_not_in_pool(self):
        await self.manager.disconnect(self.mock_ws)

        assert len(self.manager.active_connections) == 0

    async def test_send_personal_message_happy_path(self):
        message = "AI is typing..."

        await self.manager.send_personal_message(message, self.mock_ws)

        self.mock_ws.send_text.assert_called_once_with("AI is typing...")

    async def test_send_personal_message_error_condition_drops_connection(self):
        self.manager.active_connections.append(self.mock_ws)

        self.mock_ws.send_text.side_effect = Exception("Broken pipe")

        await self.manager.send_personal_message("Failed message", self.mock_ws)

        assert self.mock_ws not in self.manager.active_connections
