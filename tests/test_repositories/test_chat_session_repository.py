import re
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from beanie import UpdateResponse
from beanie.operators import SetOnInsert
from pydantic import ValidationError

from app.domain.model.chat_entry import HumanMessage
from app.domain.model.chat_session import ChatSession, ChatSessionSummarized
from app.infrastructure.mongodb.repositories.chat_session_repository import (
    BeanieChatSessionRepository,
)


class TestBeanieChatSessionRepository:
    @pytest.fixture
    def repository(self) -> BeanieChatSessionRepository:
        return BeanieChatSessionRepository()

    @pytest.fixture
    def fixed(self) -> datetime:
        return datetime(2026, 8, 12, 15, 0, tzinfo=timezone.utc)

    @pytest.mark.asyncio
    async def test_get_or_create_uses_atomic_upsert_and_maps_document(
        self, repository, fixed
    ):
        session = ChatSession(session_id="session-123", started_at=fixed)
        expected = ChatSession(session_id="session-123", started_at=fixed)
        query = MagicMock()

        class DocumentStub:
            session_id = "session_id"
            started_at = "started_at"
            updated_at = "updated_at"
            summary = "summary"
            entries = "entries"
            find_one = MagicMock(return_value=query)

        document = DocumentStub()
        query.update = AsyncMock(return_value=document)

        with (
            patch(
                "app.infrastructure.mongodb.repositories.chat_session_repository."
                "ChatSessionDocument",
                DocumentStub,
            ),
            patch(
                "app.infrastructure.mongodb.repositories.chat_session_repository."
                "ChatSessionMapper.document_to_model",
                return_value=expected,
            ) as mapper,
        ):
            result = await repository.get_or_create(session)

        assert result is expected
        DocumentStub.find_one.assert_called_once()
        update_call = query.update.await_args
        assert isinstance(update_call.args[0], SetOnInsert)
        assert update_call.kwargs == {
            "response_type": UpdateResponse.NEW_DOCUMENT,
            "upsert": True,
        }
        mapper.assert_called_once_with(document)

    @pytest.mark.asyncio
    async def test_append_entry_uses_atomic_update(self, repository, fixed):
        message = HumanMessage(content="Olá")

        with patch(
            "app.infrastructure.mongodb.repositories.chat_session_repository."
            "ChatSessionDocument"
        ) as document_class:
            query = MagicMock()
            query.update = AsyncMock()
            document_class.find_one.return_value = query

            await repository.append_entry("session-123", message, fixed)

        document_class.find_one.assert_called_once()
        query.update.assert_awaited_once()
        assert len(query.update.await_args.args) == 2

    @pytest.mark.asyncio
    async def test_append_entry_preserves_document_validation(self, repository, fixed):
        message = HumanMessage(content={"key": "value"})  # type: ignore[arg-type]

        with pytest.raises(ValidationError):
            await repository.append_entry("session-123", message, fixed)

    @pytest.mark.asyncio
    async def test_find_by_session_id_maps_document(self, repository, fixed):
        document = MagicMock()
        expected = ChatSession(session_id="session-123", started_at=fixed)

        with (
            patch(
                "app.infrastructure.mongodb.repositories.chat_session_repository."
                "ChatSessionDocument"
            ) as document_class,
            patch(
                "app.infrastructure.mongodb.repositories.chat_session_repository."
                "ChatSessionMapper.document_to_model",
                return_value=expected,
            ) as mapper,
        ):
            document_class.find_one = AsyncMock(return_value=document)

            result = await repository.find_by_session_id("session-123")

        assert result == expected
        mapper.assert_called_once_with(document)

    @pytest.mark.asyncio
    async def test_find_by_session_id_returns_none(self, repository):
        with patch(
            "app.infrastructure.mongodb.repositories.chat_session_repository."
            "ChatSessionDocument"
        ) as document_class:
            document_class.find_one = AsyncMock(return_value=None)

            result = await repository.find_by_session_id("missing")

        assert result is None

    @pytest.mark.asyncio
    async def test_update_summary_uses_atomic_update(self, repository, fixed):
        with patch(
            "app.infrastructure.mongodb.repositories.chat_session_repository."
            "ChatSessionDocument"
        ) as document_class:
            query = MagicMock()
            query.update = AsyncMock()
            document_class.find_one.return_value = query

            await repository.update_summary("session-123", "Resumo", fixed)

        document_class.find_one.assert_called_once()
        query.update.assert_awaited_once()

    @pytest.mark.asyncio
    @pytest.mark.parametrize("search", ["", "transporte"])
    async def test_find_summaries_applies_query_and_maps_results(
        self, repository, fixed, search
    ):
        document = MagicMock()
        expected = ChatSessionSummarized(
            session_id="session-123",
            summary="Resumo",
            started_at=fixed,
        )

        with (
            patch(
                "app.infrastructure.mongodb.repositories.chat_session_repository."
                "ChatSessionDocument"
            ) as document_class,
            patch(
                "app.infrastructure.mongodb.repositories.chat_session_repository."
                "ChatSessionSummarizedMapper.document_to_model",
                return_value=expected,
            ) as mapper,
        ):
            find_query = MagicMock()
            projected_query = MagicMock()
            sorted_query = MagicMock()
            limited_query = MagicMock()
            limited_query.to_list = AsyncMock(return_value=[document])
            sorted_query.limit.return_value = limited_query
            projected_query.sort.return_value = sorted_query
            find_query.project.return_value = projected_query
            document_class.find.return_value = find_query

            result = await repository.find_summaries(search=search, limit=5)

        assert result == [expected]
        find_filter = document_class.find.call_args.args[0]
        if search:
            pattern = next(iter(find_filter.values()))
            assert isinstance(pattern, re.Pattern)
            assert pattern.pattern == search
            assert pattern.flags & re.IGNORECASE
        else:
            assert find_filter == {}
        projected_query.sort.assert_called_once_with(document_class.updated_at, -1)
        sorted_query.limit.assert_called_once_with(5)
        mapper.assert_called_once_with(document)
