import logging

from src.infrastructure.db_connection import get_cursor
from src.model.common.tool_response import ToolResponse
from langchain.tools import tool

logger = logging.getLogger(__name__)


@tool("total_balance")
def total_balance() -> ToolResponse:
    """Recupera do banco de dados o saldo atual a partir de todas as transações registradas"""
    logger.info("total_balance tool called")
    try:
        with get_cursor() as cur:
            cur.execute("""
                SELECT coalesce(sum(amount), 0) 
                FROM transactions 
                WHERE type = 1""")
            income = cur.fetchone()[0]
            logger.debug("Income retreived: %s", income)

            cur.execute("""
                SELECT coalesce(sum(amount), 0)
                FROM transactions
                WHERE type = 2""")
            expenses = cur.fetchone()[0]
            logger.debug("Expenses retreived: %s", expenses)

            balance = income - expenses
            logger.info("Total balance retreived successfully: %s", balance)
            return ToolResponse.ok({"saldo": balance})
    except Exception as e:
        logger.exception("Exception raised white retreiving total balance")
        return ToolResponse.exception(e)
