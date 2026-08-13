from datetime import date

import pytest

from app.agents.financial.tools.daily_balance import DailyBalanceTool
from app.model.tool_response import ToolFailure, ToolSuccess
from app.services.transaction_service import TransactionService


class TestDailyBalanceTool:
    @pytest.fixture
    def tool(self):
        service = TransactionService.__new__(TransactionService)
        object.__setattr__(service, "_repository", None)
        return DailyBalanceTool(service=service)

    def test_returns_daily_balance(self, tool):
        tool.service.calculate_daily_balance = lambda d: 300.0

        result = tool._run(target_date=date(2026, 6, 1))

        assert isinstance(result, ToolSuccess)
        assert result.data.balance == 300.0

    def test_passes_date_correctly(self, tool):
        captured = []

        def capture(d):
            captured.append(d)
            return 0.0

        tool.service.calculate_daily_balance = capture

        tool._run(target_date=date(2026, 6, 15))

        assert captured == [date(2026, 6, 15)]

    def test_handles_exception(self, tool):
        def raise_error():
            raise Exception("fail")

        tool.service.calculate_daily_balance = raise_error

        result = tool._run(target_date=date(2026, 6, 1))

        assert isinstance(result, ToolFailure)
