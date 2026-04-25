from pydantic import BaseModel, Field
from datetime import date, timedelta
from langchain.tools import tool
from src.infrastructure.db_connection import get_cursor
from .response import DatabaseToolResponse


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
def daily_balance(target_date: date) -> DatabaseToolResponse:
    """
    Retorna o saldo (INCOME - EXPENSES) do dia local informado em America/Sao_Paulo.
    Ignora TRANSFER (type=3)
    """
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

            cur.execute(
                """
                SELECT coalesce(sum(amount), 0)
                FROM transactions
                WHERE type = 2
                AND occurred_at < %s""",
                (query_date,),
            )
            expenses = cur.fetchone()[0]

            return DatabaseToolResponse.ok({"saldo_diario": income - expenses})
    except Exception as e:
        return DatabaseToolResponse.exception(e)
