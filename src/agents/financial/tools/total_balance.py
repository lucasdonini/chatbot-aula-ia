import logging

from src.infrastructure.db_connection import get_cursor
from .response import DatabaseToolResponse
from langchain.tools import tool

logger = logging.getLogger(__name__)


# TODO: use coalesce() in database query instead of treating null in the backend
@tool("total_balance")
def total_balance() -> DatabaseToolResponse:
    """Recupera do banco de dados o saldo atual a partir de todas as transações registradas"""
    logger.info("total_balance tool called")
    try:
        with get_cursor() as cur:
            cur.execute("""
                SELECT sum(amount) 
                FROM transactions 
                WHERE type = 1""")
            income = cur.fetchone()[0]
            income = 0 if not income else income
            logger.debug("Income retreived: %s", income)

            cur.execute("""
                SELECT sum(amount)
                FROM transactions
                WHERE type = 2""")
            expenses = cur.fetchone()[0]
            expenses = 0 if not expenses else expenses
            logger.debug("Expenses retreived: %s", expenses)

            balance = income - expenses
            logger.info("Total balance retreived successfully: %s", balance)
            return DatabaseToolResponse.ok({"saldo": balance})
    except Exception as e:
        logger.exception("Exception raised white retreiving total balance")
        return DatabaseToolResponse.exception(e)
