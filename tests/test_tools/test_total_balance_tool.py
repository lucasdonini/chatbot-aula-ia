import pytest

from src.agents.financial.tools.total_balance import TotalBalanceTool
from src.model.tool_response import LegacyToolResponse
from src.services.transaction_service import TransactionService


class TestTotalBalanceTool:
    @pytest.fixture
    def tool(self):
        service = TransactionService.__new__(TransactionService)
        object.__setattr__(service, "_repository", None)
        return TotalBalanceTool(service=service)

    def test_returns_balance(self, tool):
        tool.service.calculate_total_balance = lambda: 5000.0

        result = tool._run()

        assert isinstance(result, LegacyToolResponse)
        assert result.status == "ok"
        assert result.data["saldo"] == 5000.0

    def test_returns_zero(self, tool):
        tool.service.calculate_total_balance = lambda: 0.0

        result = tool._run()

        assert result.status == "ok"
        assert result.data["saldo"] == 0.0

    def test_returns_negative(self, tool):
        tool.service.calculate_total_balance = lambda: -500.0

        result = tool._run()

        assert result.status == "ok"
        assert result.data["saldo"] == -500.0

    def test_handles_exception(self, tool):
        def raise_error():
            raise Exception("DB error")

        tool.service.calculate_total_balance = raise_error

        result = tool._run()

        assert result.status == "error"
        assert "DB error" in result.data["message"]
