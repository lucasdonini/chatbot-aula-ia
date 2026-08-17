import pytest

from app.infrastructure.agents.financial.tools.total_balance import TotalBalanceTool
from app.infrastructure.agents.schema.tool_response import ToolFailure, ToolSuccess
from app.services.transaction_service import TransactionService


class TestTotalBalanceTool:
    @pytest.fixture
    def tool(self):
        service = TransactionService.__new__(TransactionService)
        object.__setattr__(service, "_repository", None)
        return TotalBalanceTool(service=service)

    def test_returns_balance(self, tool):
        tool.service.calculate_total_balance = lambda: 5000.0

        result = tool._run()

        assert isinstance(result, ToolSuccess)
        assert result.data.balance == 5000.0

    def test_returns_zero(self, tool):
        tool.service.calculate_total_balance = lambda: 0.0

        result = tool._run()

        assert isinstance(result, ToolSuccess)
        assert result.data.balance == 0.0

    def test_returns_negative(self, tool):
        tool.service.calculate_total_balance = lambda: -500.0

        result = tool._run()

        assert isinstance(result, ToolSuccess)
        assert result.data.balance == -500.0

    def test_handles_exception(self, tool):
        def raise_error():
            raise Exception("DB error")

        tool.service.calculate_total_balance = raise_error

        result = tool._run()

        assert isinstance(result, ToolFailure)
        assert "DB error" in result.details["exception"]
