import logging

from pydantic import BaseModel, Field
from datetime import date, timedelta
from langchain.tools import tool
from src.infrastructure.db_connection import get_cursor
from src.model.common.tool_response import ToolResponse

logger = logging.getLogger(__name__)


class DailyBalanceArgs(BaseModel):
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


@tool("daily_balance", args_schema=DailyBalanceArgs)
def daily_balance(target_date: date) -> ToolResponse:
    """
    Retorna o saldo (INCOME - EXPENSES) do dia local informado em America/Sao_Paulo.
    Ignora TRANSFER (type=3)
    """
    logger.info("daily_balance tool called")
    query_date = target_date + timedelta(days=1)
    try:
        with get_cursor() as cur:
            cur.execute(
                """
                SELECT coalesce(sum(amount), 0) 
                FROM transactions 
                WHERE type = 1 
                AND occurred_at < %s""",
                (query_date,),
            )
            income = cur.fetchone()[0]
            logger.debug("Retreived income: %s", income)

            cur.execute(
                """
                SELECT coalesce(sum(amount), 0)
                FROM transactions
                WHERE type = 2
                AND occurred_at < %s""",
                (query_date,),
            )
            expenses = cur.fetchone()[0]
            logger.debug("Retreived expenses: %s", expenses)

            balance = income - expenses
            logger.info("Daily balance retreived successfully: %s", balance)
            return ToolResponse.ok({"saldo_diario": balance})
    except Exception as e:
        logger.exception("Exception raised while retreiving daily balance")
        return ToolResponse.exception(e)
