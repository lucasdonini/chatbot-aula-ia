import logging

from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from app.infrastructure.agents.financial.schemas.tool_response import (
    ToolFailure,
    ToolResponse,
    ToolSuccess,
)
from app.services.transaction_service import TransactionService

logger = logging.getLogger(__name__)


class _TotalBalanceArgsSchema(BaseModel):
    pass


class _TotalBalanceResponse(BaseModel):
    balance: float


TOOL_NAME = "total_balance"


class TotalBalanceTool(BaseTool):
    name: str = TOOL_NAME
    args_schema: type[BaseModel] = _TotalBalanceArgsSchema
    description: str = (
        "Recupera do banco de dados o saldo atual "
        "a partir de todas as transações registradas"
    )

    service: TransactionService = Field(exclude=True)

    def _run(self) -> ToolResponse[_TotalBalanceResponse]:
        raise NotImplementedError("This tool only supports asynchronous execution")

    async def _arun(self) -> ToolResponse[_TotalBalanceResponse]:
        logger.debug(
            "Tool called",
            extra={"details": {"tool": self.name}},
        )
        try:
            balance = await self.service.calculate_total_balance()
            logger.debug(
                "Tool succeeded",
                extra={"details": {"tool": self.name, "balance": balance}},
            )
            return ToolSuccess(data=_TotalBalanceResponse(balance=balance))
        except Exception as e:
            logger.exception(
                "Tool failed",
                extra={"details": {"tool": self.name}},
            )
            return ToolFailure.exception(e)
