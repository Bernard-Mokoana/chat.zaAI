import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import WebSocket, status, WebSocketDisconnect
from backend.server.src.services.chat_services import (
    create_token_service,
    refresh_token_service,
    handle_websocket_connection,
)
from backend.server.src.redis.config import Redis
from backend.server.src.services.conversation_services import ConversationService, ChatOrchestrator
from backend.server.src.socket.connection import ConnectionManager


@pytest.mark.asyncio
class TestChatServices:

    @pytest.fixture(autouse=True)
    def setup_method(self):
        self.mock_redis = MagicMock(spec=Redis)
        self.mock_redis_client = AsyncMock()
        self.mock_redis.create_connection.return_value = self.mock_redis_client

        self.mock_conversation_service = MagicMock(spec=ConversationService)
        self.mock_conversation_service.create_chat_session = AsyncMock()
        self.mock_conversation_service.get_chat_session = AsyncMock()
        self.mock_conversation_service.validate_websocket_session = AsyncMock()

        self.user_id = "user-123"
        self.name = "Bernard Mokoana"
        self.token = "access-jwt-token"
        self.chat_token = "chat-session-uuid"

    async def test_create_token_service_happy_path(self):
        expected_payload = {"token": self.chat_token, "user_id": self.user_id, "name": self.name}
        self.mock_conversation_service.create_chat_session.return_value = expected_payload

        result = await create_token_service(
            redis=self.mock_redis,
            conversation_service=self.mock_conversation_service,
            user_id=self.user_id,
            name=self.name,
        )


        assert result == expected_payload
        self.mock_redis.create_connection.assert_called_once()
        self.mock_conversation_service.create_chat_session.assert_called_once_with(
            redis_client=self.mock_redis_client, user_id=self.user_id, name=self.name
        )
        self.mock_redis_client.close.assert_called_once()

    async def test_create_token_service_error_ensures_redis_closes(self):
        self.mock_conversation_service.create_chat_session.side_effect = Exception("Redis write crash")

        with pytest.raises(Exception, match="Redis write crash"):
            await create_token_service(
                redis=self.mock_redis,
                conversation_service=self.mock_conversation_service,
                user_id=self.user_id,
                name=self.name,
            )
        self.mock_redis_client.close.assert_called_once()

    async def test_refresh_token_service_happy_path(self):
        expected_session = {"token": self.chat_token, "user_id": self.user_id}
        self.mock_conversation_service.get_chat_session.return_value = expected_session

        result = await refresh_token_service(
            redis=self.mock_redis,
            conversation_service=self.mock_conversation_service,
            token=self.token,
            user_id=self.user_id,
        )

        assert result == expected_session
        self.mock_conversation_service.get_chat_session.assert_called_once_with(
            redis_client=self.mock_redis_client, token=self.token, user_id=self.user_id
        )
        self.mock_redis_client.close.assert_called_once()


    async def test_handle_websocket_missing_parameters(self):
        mock_ws = AsyncMock(spec=WebSocket)
        mock_ws.query_params = {} 
        mock_manager = MagicMock(spec=ConnectionManager)

        await handle_websocket_connection(
            websocket=mock_ws,
            redis=self.mock_redis,
            manager=mock_manager,
            conversation_service=self.mock_conversation_service,
        )

        mock_ws.accept.assert_called_once()
        mock_ws.close.assert_called_once_with(code=status.WS_1008_POLICY_VIOLATION)
        self.mock_redis.create_connection.assert_not_called()

    async def test_handle_websocket_invalid_session_credentials(self):
        mock_ws = AsyncMock(spec=WebSocket)
        mock_ws.query_params = {"token": self.token, "chat_token": self.chat_token}
        mock_manager = MagicMock(spec=ConnectionManager)
        
        self.mock_conversation_service.validate_websocket_session.side_effect = PermissionError("Forbidden")

        await handle_websocket_connection(
            websocket=mock_ws,
            redis=self.mock_redis,
            manager=mock_manager,
            conversation_service=self.mock_conversation_service,
        )

        mock_ws.accept.assert_called_once()
        mock_ws.close.assert_called_once_with(code=status.WS_1008_POLICY_VIOLATION)

    async def test_handle_websocket_unexpected_validation_crash(self):
        mock_ws = AsyncMock(spec=WebSocket)
        mock_ws.query_params = {"token": self.token, "chat_token": self.chat_token}
        mock_manager = MagicMock(spec=ConnectionManager)
        
        self.mock_conversation_service.validate_websocket_session.side_effect = Exception("DB Network down")

        await handle_websocket_connection(
            websocket=mock_ws,
            redis=self.mock_redis,
            manager=mock_manager,
            conversation_service=self.mock_conversation_service,
        )

        mock_ws.accept.assert_called_once()
        mock_ws.close.assert_called_once_with(code=status.WS_1011_INTERNAL_ERROR)

    @patch("backend.server.src.services.chat_services.Producer")
    @patch("backend.server.src.services.chat_services.StreamConsumer")
    @patch("backend.server.src.services.chat_services.ChatOrchestrator")
    async def test_handle_websocket_happy_path_orchestration(self, MockOrchestrator, MockConsumer, MockProducer):
        mock_ws = AsyncMock(spec=WebSocket)
        mock_ws.query_params = {"token": self.token, "chat_token": self.chat_token}
        mock_manager = MagicMock(spec=ConnectionManager)
        
        self.mock_conversation_service.validate_websocket_session.return_value = {"user_id": "123"}
        
        mock_orchestrator_instance = AsyncMock(spec=ChatOrchestrator)
        MockOrchestrator.return_value = mock_orchestrator_instance

        await handle_websocket_connection(
            websocket=mock_ws,
            redis=self.mock_redis,
            manager=mock_manager,
            conversation_service=self.mock_conversation_service,
        )

        MockOrchestrator.assert_called_once_with(
            manager=mock_manager,
            producer=MockProducer.return_value,
            consumer=MockConsumer.return_value,
        )
        mock_orchestrator_instance.run.assert_called_once_with(mock_ws, self.chat_token)
        assert self.mock_redis_client.close.call_count == 2

    @patch("backend.server.src.services.chat_services.Producer")
    @patch("backend.server.src.services.chat_services.StreamConsumer")
    @patch("backend.server.src.services.chat_services.ChatOrchestrator")
    async def test_handle_websocket_disconnect_exception_handling(self, MockOrchestrator, MockConsumer, MockProducer):
        mock_ws = AsyncMock(spec=WebSocket)
        mock_ws.query_params = {"token": self.token, "chat_token": self.chat_token}
        mock_manager = MagicMock(spec=ConnectionManager)
        
        self.mock_conversation_service.validate_websocket_session.return_value = {"user_id": "123"}
        
        mock_orchestrator_instance = AsyncMock(spec=ChatOrchestrator)
        mock_orchestrator_instance.run.side_effect = WebSocketDisconnect()
        MockOrchestrator.return_value = mock_orchestrator_instance

        await handle_websocket_connection(
            websocket=mock_ws,
            redis=self.mock_redis,
            manager=mock_manager,
            conversation_service=self.mock_conversation_service,
        )
        
        assert self.mock_redis_client.close.call_count == 2