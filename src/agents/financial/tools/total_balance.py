import logging

from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from src.model.tool_response import ToolResponse
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

    def _run(self) -> ToolResponse:
        logger.debug("%s tool called.", self.name)
        try:
            balance = self.service.calculate_total_balance()
            logger.debug("Total balance retreived successfully: %s", balance)
            return ToolResponse.ok({"saldo": balance})
        except Exception as e:
            logger.exception("Exception raised white retreiving total balance")
            return ToolResponse.exception(e)
