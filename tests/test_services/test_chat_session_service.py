from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from langchain_core.messages import AIMessage, HumanMessage

from src.model.chat_session import ChatMessage
from src.services import chat_session_service
from src.services.chat_session_service import ChatSessionService


class TestChatSessionService:
    @pytest.fixture
    def summary_service(self):
        return MagicMock()

    @pytest.fixture
    def service(self, summary_service):
        chat_session_service._active_sessions.clear()
        return ChatSessionService(service=summary_service)

    @pytest.mark.asyncio
    async def test_init_session(self, service, summary_service):
        with patch("src.services.chat_session_service.ChatSession") as mock_chat:
            mock_instance = AsyncMock()
            mock_chat.return_value = mock_instance
            mock_instance.insert = AsyncMock()

            await service.init_session("session-123")

            mock_instance.insert.assert_called_once()
            assert "session-123" in chat_session_service._active_sessions

    @pytest.mark.asyncio
    async def test_save_message_human(self, service, summary_service):
        with patch("src.services.chat_session_service.ChatSession") as mock_chat:
            chat_session_service._active_sessions["session-123"] = "doc-id"
            mock_query = MagicMock()
            mock_query.update = AsyncMock()
            mock_chat.find_one = MagicMock(return_value=mock_query)

            await service.save_message("session-123", HumanMessage(content="Olá"))

            mock_chat.find_one.assert_called_once()
            mock_query.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_save_message_ai(self, service, summary_service):
        with patch("src.services.chat_session_service.ChatSession") as mock_chat:
            chat_session_service._active_sessions["session-123"] = "doc-id"
            mock_query = MagicMock()
            mock_query.update = AsyncMock()
            mock_chat.find_one = MagicMock(return_value=mock_query)

            await service.save_message("session-123", AIMessage(content="Resposta"))

            mock_chat.find_one.assert_called_once()
            mock_query.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_finalize_session_with_summary(self, service, summary_service):
        summary_service.sumarize = AsyncMock(return_value="Resumo da sessão")

        with patch("src.services.chat_session_service.ChatSession") as mock_chat:
            chat_session_service._active_sessions["session-123"] = "doc-id"

            async def find_one_side(*args, **kwargs):
                session = AsyncMock()
                session.messages = [MagicMock(spec=ChatMessage)]
                return session

            mock_chat.find_one = MagicMock(side_effect=find_one_side)

            result = await service.finalize_session("session-123")

            assert result == "Resumo da sessão"
            assert "session-123" not in chat_session_service._active_sessions
            summary_service.sumarize.assert_called_once()

    @pytest.mark.asyncio
    async def test_finalize_session_no_active(self, service, summary_service):
        result = await service.finalize_session("unknown")
        assert result == ""

    @pytest.mark.asyncio
    async def test_finalize_no_messages(self, service, summary_service):
        with patch("src.services.chat_session_service.ChatSession") as mock_chat:
            chat_session_service._active_sessions["session-123"] = "doc-id"

            async def find_one_side(*args, **kwargs):
                session = AsyncMock()
                session.messages = []
                return session

            mock_chat.find_one = MagicMock(side_effect=find_one_side)

            result = await service.finalize_session("session-123")

            assert result == ""

    def test_get_active_sessions_returns_copy(self, service, summary_service):
        chat_session_service._active_sessions["s1"] = "d1"
        sessions = service.get_active_sessions()
        sessions["new"] = "d2"
        assert "new" not in chat_session_service._active_sessions
