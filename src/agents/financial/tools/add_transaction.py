import logging

from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from src.model.tool_response import ToolResponse
from src.model.transaction import Transaction
from src.services.transaction_service import TransactionService

logger = logging.getLogger(__name__)


class AddTransactionTool(BaseTool):
    name: str = "add_transaction"
    args_schema: type[BaseModel] = Transaction
    description: str = "Insere uma transação financeira no banco de dados PosthreSQL."

    service: TransactionService = Field(exclude=True)

    def _run(self, *args, **kwargs) -> ToolResponse:
        transaction = args[0] if args else Transaction(**kwargs)
        logger.info("%s tool called. Transaction: %s", self.name, transaction)
        try:
            added = self.service.add_transaction(transaction)
            logger.debug("Transaction added successfully: %s", added)
            return ToolResponse.ok({"transaction": added})
        except Exception as e:
            logger.exception(
                "Exception raised while trying to add trying to "
                "add transaction to database"
            )
            return ToolResponse.exception(e)
