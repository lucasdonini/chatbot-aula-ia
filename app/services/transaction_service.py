import logging
from dataclasses import asdict
from datetime import date
from typing import List, Optional

from app.application.models.transaction_query import (
    TransactionQueryParams,
)
from app.application.models.transaction_update import (
    UpdateTransactionParams,
)
from app.application.repositories.transaction_repository import TransactionRepository
from app.domain.model.transaction import Transaction
from app.infrastructure.execution_time_logger import log_execution_time

logger = logging.getLogger(__name__)


class TransactionService:
    def __init__(self, repository: TransactionRepository):
        self._repository = repository

    @log_execution_time
    async def calculate_total_balance(self) -> float:
        logger.debug("Calculating total balance")
        return await self._repository.get_balance()

    @log_execution_time
    async def calculate_daily_balance(self, day: date) -> float:
        logger.debug(
            "Calculating daily balance",
            extra={"details": {"day": str(day)}},
        )
        return await self._repository.get_balance(day)

    @log_execution_time
    async def search_transactions(
        self, params: TransactionQueryParams
    ) -> List[Transaction]:
        logger.debug(
            "Searching transactions",
            extra={"details": {"params": params.model_dump()}},
        )
        return await self._repository.find(params)

    @log_execution_time
    async def add_transaction(self, transaction: Transaction) -> Transaction:
        logger.debug(
            "Adding transaction",
            extra={"details": {"transaction": asdict(transaction)}},
        )
        return await self._repository.add_transaction(transaction)

    @log_execution_time
    async def update_transaction(
        self, params: UpdateTransactionParams
    ) -> Optional[Transaction]:
        logger.debug(
            "Updating transaction",
            extra={"details": {"params": params.model_dump()}},
        )
        return await self._repository.update_transaction(params)
