from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from app.application.exceptions import ApplicationError
from app.application.ports.logger import Logger
from app.infrastructure.agents.financial.schemas.tool_response import (
    ToolFailure,
    ToolResponse,
    ToolSuccess,
)
from app.services.transaction_service import TransactionService


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
    logger: Logger = Field(exclude=True)

    def _run(self) -> ToolResponse[_TotalBalanceResponse]:
        raise NotImplementedError("This tool only supports asynchronous execution")

    async def _arun(self) -> ToolResponse[_TotalBalanceResponse]:
        self.logger.debug(
            "Tool called",
            details={"tool": self.name},
        )
        try:
            balance = await self.service.calculate_total_balance()
            self.logger.debug(
                "Tool succeeded",
                details={"tool": self.name},
            )
            return ToolSuccess(data=_TotalBalanceResponse(balance=balance))
        except ApplicationError as e:
            self.logger.warning(
                "Tool rejected operation",
                details={"tool": self.name, "error_code": e.code},
            )
            return ToolFailure.application_error(e)
        except Exception as e:
            self.logger.exception(
                "Tool failed",
                exception=e,
                details={"tool": self.name},
            )
            return ToolFailure.unexpected_error()
