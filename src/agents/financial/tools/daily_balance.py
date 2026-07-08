import logging
from datetime import date

from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from src.model.tool_response import ToolFailure, ToolResponse, ToolSuccess
from src.services.transaction_service import TransactionService

logger = logging.getLogger(__name__)


class _DailyBalanceArgsSchema(BaseModel):
    target_date: date = Field(
        ...,
        description=(
            "Data de referência para o cálculo do saldo. "
            "O saldo retornado será o acumulado de todas as entradas (INCOME) "
            "e saídas (EXPENSES), ignorando transferências (TRANSFER)"
            "registradas ATÉ esse dia (inclusive). "
            "Exemplos: 'qual meu saldo hoje' → {hoje}, "
            "'qual era meu saldo no fim de março' → 2026-03-31."
        ),
    )


class _DailyBalanceResponse(BaseModel):
    balance: float
    date: date


TOOL_NAME = "daily_balance"


class DailyBalanceTool(BaseTool):
    name: str = TOOL_NAME
    args_schema: type[BaseModel] = _DailyBalanceArgsSchema
    description: str = (
        "Retorna o saldo (INCOME - EXPENSES) do dia local informado "
        "em America/Sao_Paulo. Ignora TRANSFER (type=3)"
    )

    service: TransactionService = Field(exclude=True)

    def _run(self, target_date: date) -> ToolResponse[_DailyBalanceResponse]:
        logger.debug(
            "Tool called",
            extra={"details": {"tool": self.name, "target_date": str(target_date)}},
        )
        try:
            balance = self.service.calculate_daily_balance(target_date)
            logger.debug(
                "Tool succeeded",
                extra={"details": {"tool": self.name, "balance": balance}},
            )
            response = _DailyBalanceResponse(balance=balance, date=target_date)
            return ToolSuccess(data=response)
        except Exception as e:
            logger.exception(
                "Tool failed",
                extra={"details": {"tool": self.name}},
            )
            return ToolFailure.exception(e)
