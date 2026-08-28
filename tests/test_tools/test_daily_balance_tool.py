from datetime import date
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.application.ports.logger import Logger
from app.infrastructure.agents.financial.schemas.tool_response import (
    ToolFailure,
    ToolSuccess,
)
from app.infrastructure.agents.financial.tools.daily_balance import DailyBalanceTool
from app.services.transaction_service import TransactionService

pytestmark = pytest.mark.asyncio


class TestDailyBalanceTool:
    @pytest.fixture
    def tool(self):
        service = TransactionService.__new__(TransactionService)
        object.__setattr__(service, "_repository", None)
        return DailyBalanceTool(service=service, logger_factory=MagicMock(spec=Logger))

    async def test_returns_daily_balance(self, tool):
        tool.service.calculate_daily_balance = AsyncMock(return_value=300.0)

        result = await tool._arun(target_date=date(2026, 6, 1))

        assert isinstance(result, ToolSuccess)
        assert result.data.balance == 300.0

    async def test_passes_date_correctly(self, tool):
        calculate_balance = AsyncMock(return_value=0.0)
        tool.service.calculate_daily_balance = calculate_balance

        await tool._arun(target_date=date(2026, 6, 15))

        calculate_balance.assert_awaited_once_with(date(2026, 6, 15))

    async def test_handles_exception(self, tool):
        tool.service.calculate_daily_balance = AsyncMock(side_effect=Exception("fail"))

        result = await tool._arun(target_date=date(2026, 6, 1))

        assert isinstance(result, ToolFailure)
