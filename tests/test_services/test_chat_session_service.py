from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, create_autospec

import pytest

from app.application.ports.logger import Logger
from app.application.repositories.chat_session_repository import (
    ChatSessionRepository,
)
from app.domain.model.chat_entry import AssistantMessage, HumanMessage
from app.domain.model.chat_session import ChatSession
from app.infrastructure.clock import FixedClock
from app.services import chat_session_service
from app.services.chat_session_service import ChatSessionService


class TestChatSessionService:
    @pytest.fixture
    def summary_service(self):
        return MagicMock()

    @pytest.fixture
    def repository(self):
        return create_autospec(ChatSessionRepository, instance=True)

    @pytest.fixture
    def service(self, summary_service, repository):
        chat_session_service._active_sessions.clear()
        return ChatSessionService(
            service=summary_service,
            repository=repository,
            logger=MagicMock(spec=Logger),
            clock=FixedClock(
                datetime(2026, 8, 12, 15, 0, tzinfo=timezone.utc),
                "America/Sao_Paulo",
            ),
        )

    @pytest.mark.asyncio
    async def test_init_session(self, service, repository):
        fixed = datetime(2026, 8, 12, 15, 0, tzinfo=timezone.utc)

        await service.init_session("session-123")

        repository.create.assert_awaited_once_with(
            ChatSession(
                session_id="session-123",
                started_at=fixed,
                updated_at=fixed,
                summary="",
                entries=[],
            )
        )
        assert "session-123" in chat_session_service._active_sessions

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "message",
        [
            HumanMessage(content="Olá"),
            AssistantMessage(content="Resposta"),
        ],
    )
    async def test_save_message(self, service, repository, message):
        fixed = datetime(2026, 8, 12, 15, 0, tzinfo=timezone.utc)
        chat_session_service._active_sessions["session-123"] = "session-123"

        await service.save_message("session-123", message)

        repository.append_entry.assert_awaited_once_with(
            "session-123",
            message,
            fixed,
        )

    @pytest.mark.asyncio
    async def test_save_error(self, service, summary_service, repository):
        summary_service.summarize_exception = AsyncMock(
            return_value="Ocorreu um erro interno."
        )
        chat_session_service._active_sessions["session-123"] = "session-123"
        error = ValueError("Algo deu errado")

        await service.save_error("session-123", error)

        repository.append_entry.assert_awaited_once()
        saved_entry = repository.append_entry.await_args.args[1]
        assert saved_entry.exception == "ValueError"
        assert saved_entry.summary == "Ocorreu um erro interno."
        summary_service.summarize_exception.assert_awaited_once_with(error)

    @pytest.mark.asyncio
    async def test_save_error_logs_secondary_failure_without_raising(
        self, service, summary_service
    ):
        original_error = ValueError("original")
        persistence_error = RuntimeError("summary unavailable")
        summary_service.summarize_exception = AsyncMock(side_effect=persistence_error)

        await service.save_error("session-123", original_error)

        service._logger.exception.assert_called_once_with(
            "Failed to save chat error",
            exception=persistence_error,
            details={"original_exception_type": "ValueError"},
        )

    @pytest.mark.asyncio
    async def test_finalize_session_with_summary(
        self, service, summary_service, repository
    ):
        fixed = datetime(2026, 8, 12, 15, 0, tzinfo=timezone.utc)
        entries = [HumanMessage(content="Olá")]
        summary_service.summarize_session = AsyncMock(return_value="Resumo da sessão")
        repository.find_by_session_id.return_value = ChatSession(
            session_id="session-123",
            started_at=fixed,
            updated_at=fixed,
            entries=entries,
        )
        chat_session_service._active_sessions["session-123"] = "session-123"

        result = await service.finalize_session("session-123")

        assert result is None
        assert "session-123" not in chat_session_service._active_sessions
        summary_service.summarize_session.assert_awaited_once_with(entries)
        repository.update_summary.assert_awaited_once_with(
            "session-123",
            "Resumo da sessão",
            fixed,
        )

    @pytest.mark.asyncio
    async def test_finalize_session_no_active(self, service, repository):
        result = await service.finalize_session("unknown")

        assert result is None
        repository.find_by_session_id.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_finalize_no_messages(self, service, repository):
        fixed = datetime(2026, 8, 12, 15, 0, tzinfo=timezone.utc)
        repository.find_by_session_id.return_value = ChatSession(
            session_id="session-123",
            started_at=fixed,
            entries=[],
        )
        chat_session_service._active_sessions["session-123"] = "session-123"

        result = await service.finalize_session("session-123")

        assert result is None
        repository.update_summary.assert_not_awaited()

    def test_get_active_sessions_returns_copy(self, service):
        chat_session_service._active_sessions["s1"] = "s1"
        sessions = service.get_active_sessions()
        sessions["new"] = "new"

        assert "new" not in chat_session_service._active_sessions
