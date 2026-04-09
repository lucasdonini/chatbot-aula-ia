from .utils import get_cursor
from .response import DatabaseToolResponse
from langchain.tools import tool


@tool("total_balance")
def total_balance() -> DatabaseToolResponse:
    """Recupera do banco de dados o saldo atual a partir de todas as transações registradas"""
    try:
        with get_cursor() as cur:
            cur.execute("""
                SELECT sum(amount) 
                FROM transactions 
                WHERE type = 1""")
            income = cur.fetchone()[0]
            income = 0 if not income else income

            cur.execute("""
                SELECT sum(amount)
                FROM transactions
                WHERE type = 2""")
            expenses = cur.fetchone()[0]
            expenses = 0 if not expenses else expenses

            return DatabaseToolResponse.ok({"saldo": income - expenses})
    except Exception as e:
        return DatabaseToolResponse.exception(e)
