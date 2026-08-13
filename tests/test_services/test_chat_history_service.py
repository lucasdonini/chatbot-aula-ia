from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.chat_history_service import ChatHistoryService


class TestChatHistoryService:
    @pytest.fixture
    def service(self):
        return ChatHistoryService()

    @pytest.mark.asyncio
    async def test_fetch_history_no_search(self, service):
        with patch(
            "app.services.chat_history_service.ChatSession"
        ) as mock_chat_session:
            mock_find = MagicMock()
            mock_project = MagicMock()
            mock_sort = MagicMock()
            mock_limit = MagicMock()
            mock_limit.to_list = AsyncMock(return_value=[])
            mock_sort.limit.return_value = mock_limit
            mock_project.sort.return_value = mock_sort
            mock_find.project.return_value = mock_project
            mock_chat_session.find.return_value = mock_find

            result = await service.fetch_history()

            assert result == []
            mock_chat_session.find.assert_called_once_with({})
            mock_project.sort.assert_called_once_with(mock_chat_session.updated_at, -1)
            mock_sort.limit.assert_called_once_with(3)

    @pytest.mark.asyncio
    async def test_fetch_history_with_search(self, service):
        with patch(
            "app.services.chat_history_service.ChatSession"
        ) as mock_chat_session:
            mock_find = MagicMock()
            mock_project = MagicMock()
            mock_sort = MagicMock()
            mock_limit = MagicMock()
            mock_limit.to_list = AsyncMock(return_value=[])
            mock_sort.limit.return_value = mock_limit
            mock_project.sort.return_value = mock_sort
            mock_find.project.return_value = mock_project
            mock_chat_session.find.return_value = mock_find

            result = await service.fetch_history(search="transporte")

            assert result == []
            mock_chat_session.find.assert_called_once()
            filter_arg = mock_chat_session.find.call_args[0][0]
            assert len(filter_arg) == 1
            mock_sort.limit.assert_called_once_with(3)

    @pytest.mark.asyncio
    async def test_fetch_entries_found(self, service):
        with patch(
            "app.services.chat_history_service.ChatSession"
        ) as mock_chat_session:
            mock_session = AsyncMock()
            mock_session.entries = ["entry1", "entry2"]

            async def find_one_side(*args, **kwargs):
                return mock_session

            mock_chat_session.find_one = MagicMock(side_effect=find_one_side)

            result = await service.fetch_entries("session-123")

            assert len(result) == 2

    @pytest.mark.asyncio
    async def test_fetch_entries_not_found(self, service):
        with patch(
            "app.services.chat_history_service.ChatSession"
        ) as mock_chat_session:

            async def find_one_side(*args, **kwargs):
                return None

            mock_chat_session.find_one = MagicMock(side_effect=find_one_side)

            result = await service.fetch_entries("nonexistent")

            assert result == []
