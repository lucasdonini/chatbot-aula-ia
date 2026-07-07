import logging

from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from src.model.tool_response import LegacyToolResponse
from src.services.transaction_service import TransactionService

logger = logging.getLogger(__name__)


class _TotalBalanceArgsSchema(BaseModel):
    pass


TOOL_NAME = "total_balance"


class TotalBalanceTool(BaseTool):
    name: str = TOOL_NAME
    args_schema: type[BaseModel] = _TotalBalanceArgsSchema
    description: str = (
        "Recupera do banco de dados o saldo atual "
        "a partir de todas as transações registradas"
    )

    service: TransactionService = Field(exclude=True)

    def _run(self) -> LegacyToolResponse:
        logger.debug(
            "Tool called",
            extra={"details": {"tool": self.name}},
        )
        try:
            balance = self.service.calculate_total_balance()
            logger.debug(
                "Tool succeeded",
                extra={"details": {"tool": self.name, "balance": balance}},
            )
            return LegacyToolResponse.ok({"saldo": balance})
        except Exception as e:
            logger.exception(
                "Tool failed",
                extra={"details": {"tool": self.name}},
            )
            return LegacyToolResponse.exception(e)
