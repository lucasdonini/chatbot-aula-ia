from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from langchain_core.messages import AIMessage, HumanMessage

from app.infrastructure.clock import FixedClock, get_clock, set_clock
from app.model.chat_session import ChatMessage
from app.services import chat_session_service
from app.services.chat_session_service import ChatSessionService


class TestChatSessionService:
    @pytest.fixture(autouse=True)
    def restore_clock(self):
        original_clock = get_clock()
        yield
        set_clock(original_clock)

    @pytest.fixture
    def summary_service(self):
        return MagicMock()

    @pytest.fixture
    def service(self, summary_service):
        chat_session_service._active_sessions.clear()
        return ChatSessionService(service=summary_service)

    @pytest.mark.asyncio
    async def test_init_session(self, service, summary_service):
        fixed = datetime(2026, 8, 12, 15, 0, tzinfo=timezone.utc)
        set_clock(FixedClock(fixed))

        with patch("app.services.chat_session_service.ChatSession") as mock_chat:
            mock_instance = AsyncMock()
            mock_chat.return_value = mock_instance
            mock_instance.insert = AsyncMock()

            await service.init_session("session-123")

            mock_instance.insert.assert_called_once()
            assert mock_chat.call_args.kwargs["started_at"] == fixed
            assert mock_chat.call_args.kwargs["updated_at"] == fixed
            assert "session-123" in chat_session_service._active_sessions

    @pytest.mark.asyncio
    async def test_save_message_human(self, service, summary_service):
        with patch("app.services.chat_session_service.ChatSession") as mock_chat:
            chat_session_service._active_sessions["session-123"] = "doc-id"
            mock_query = MagicMock()
            mock_query.update = AsyncMock()
            mock_chat.find_one = MagicMock(return_value=mock_query)

            await service.save_message("session-123", HumanMessage(content="Olá"))

            mock_chat.find_one.assert_called_once()
            mock_query.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_save_message_ai(self, service, summary_service):
        with patch("app.services.chat_session_service.ChatSession") as mock_chat:
            chat_session_service._active_sessions["session-123"] = "doc-id"
            mock_query = MagicMock()
            mock_query.update = AsyncMock()
            mock_chat.find_one = MagicMock(return_value=mock_query)

            await service.save_message("session-123", AIMessage(content="Resposta"))

            mock_chat.find_one.assert_called_once()
            mock_query.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_save_message_non_text_content(self, service, summary_service):
        message = MagicMock(spec=HumanMessage)
        message.content = {"key": "value"}

        with pytest.raises(TypeError, match="Received message with non-text content"):
            await service.save_message("session-123", message)

    @pytest.mark.asyncio
    async def test_save_error(self, service, summary_service):
        summary_service.summarize_exception = AsyncMock(
            return_value="Ocorreu um erro interno."
        )

        with patch("app.services.chat_session_service.ChatSession") as mock_chat:
            chat_session_service._active_sessions["session-123"] = "doc-id"
            mock_query = MagicMock()
            mock_query.update = AsyncMock()
            mock_chat.find_one = MagicMock(return_value=mock_query)

            exc = ValueError("Algo deu errado")
            await service.save_error("session-123", exc)

            mock_chat.find_one.assert_called_once()
            mock_query.update.assert_called_once()
            summary_service.summarize_exception.assert_called_once_with(exc)

    @pytest.mark.asyncio
    async def test_finalize_session_with_summary(self, service, summary_service):
        summary_service.summarize_session = AsyncMock(return_value="Resumo da sessão")

        with patch("app.services.chat_session_service.ChatSession") as mock_chat:
            chat_session_service._active_sessions["session-123"] = "doc-id"

            async def find_one_side(*args, **kwargs):
                session = AsyncMock()
                session.entries = [MagicMock(spec=ChatMessage)]
                return session

            mock_chat.find_one = MagicMock(side_effect=find_one_side)

            result = await service.finalize_session("session-123")

            assert result is None
            assert "session-123" not in chat_session_service._active_sessions
            summary_service.summarize_session.assert_called_once()

    @pytest.mark.asyncio
    async def test_finalize_session_no_active(self, service, summary_service):
        result = await service.finalize_session("unknown")
        assert result is None

    @pytest.mark.asyncio
    async def test_finalize_no_messages(self, service, summary_service):
        with patch("app.services.chat_session_service.ChatSession") as mock_chat:
            chat_session_service._active_sessions["session-123"] = "doc-id"

            async def find_one_side(*args, **kwargs):
                session = AsyncMock()
                session.entries = []
                return session

            mock_chat.find_one = MagicMock(side_effect=find_one_side)

            result = await service.finalize_session("session-123")

            assert result is None

    def test_get_active_sessions_returns_copy(self, service, summary_service):
        chat_session_service._active_sessions["s1"] = "d1"
        sessions = service.get_active_sessions()
        sessions["new"] = "d2"
        assert "new" not in chat_session_service._active_sessions
