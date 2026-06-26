import logging
from datetime import date

from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from src.model.tool_response import ToolResponse
from src.services.transaction_service import TransactionService

logger = logging.getLogger(__name__)


class DailyBalanceArgsSchema(BaseModel):
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


class DailyBalanceTool(BaseTool):
    name: str = "daily_balance"
    args_schema: type[BaseModel] = DailyBalanceArgsSchema
    description: str = (
        "Retorna o saldo (INCOME - EXPENSES) do dia local informado "
        "em America/Sao_Paulo. Ignora TRANSFER (type=3)"
    )

    service: TransactionService = Field(exclude=True)

    def _run(self, target_date: date, *args, **kwargs) -> ToolResponse:
        logger.info("%s tool called: (target_date=%s)", self.name, target_date)
        try:
            balance = self.service.calculate_daily_balance(target_date)
            logger.info("Daily balance retreived successfully: %s", balance)
            return ToolResponse.ok({"saldo_diario": balance})
        except Exception as e:
            logger.exception("Exception raised while retreiving daily balance")
            return ToolResponse.exception(e)
