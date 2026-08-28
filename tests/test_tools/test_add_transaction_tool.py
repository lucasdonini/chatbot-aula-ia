from unittest.mock import AsyncMock, MagicMock

import pytest

from app.application.ports.logger import Logger
from app.domain.model.transaction import Category, TransactionType
from app.infrastructure.agents.financial.schemas.tool_response import (
    ToolFailure,
    ToolSuccess,
)
from app.infrastructure.agents.financial.schemas.transaction import (
    TransactionInput,
    TransactionOutput,
)
from app.infrastructure.agents.financial.tools.add_transaction import AddTransactionTool
from app.services.transaction_service import TransactionService

pytestmark = pytest.mark.asyncio


class TestAddTransactionTool:
    @pytest.fixture
    def tool(self):
        service = TransactionService.__new__(TransactionService)
        object.__setattr__(service, "_repository", None)
        return AddTransactionTool(
            service=service, logger_factory=MagicMock(spec=Logger)
        )

    async def test_adds_and_returns_ok(self, tool):
        t = TransactionInput(
            amount=100.0,
            category=Category.FOOD,
            transaction_type=TransactionType.EXPENSE,
            source_text="test",
        )
        tool.service.add_transaction = AsyncMock(
            side_effect=lambda transaction: transaction
        )

        result = await tool._arun(t)

        assert isinstance(result, ToolSuccess)
        assert result.data.transaction is not None
        assert result.data.transaction.amount == 100.0
        assert isinstance(result.data.transaction, TransactionOutput)

    async def test_handles_exception(self, tool):
        tool.service.add_transaction = AsyncMock(side_effect=Exception("fail"))

        t = TransactionInput(
            amount=100.0,
            source_text="test",
        )
        result = await tool._arun(t)

        assert isinstance(result, ToolFailure)
