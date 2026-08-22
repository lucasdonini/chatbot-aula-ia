from dataclasses import asdict
from datetime import date
from typing import List, Optional

from app.application.log_execution_time import log_execution_time
from app.application.models.transaction_query import (
    TransactionQueryParams,
)
from app.application.models.transaction_update import (
    UpdateTransactionParams,
)
from app.application.ports.logger import Logger
from app.application.repositories.transaction_repository import TransactionRepository
from app.domain.model.transaction import Transaction


class TransactionService:
    def __init__(self, repository: TransactionRepository, logger: Logger) -> None:
        self._repository = repository
        self._logger = logger

    @log_execution_time
    async def calculate_total_balance(self) -> float:
        self._logger.debug("Calculating total balance")
        return await self._repository.get_balance()

    @log_execution_time
    async def calculate_daily_balance(self, day: date) -> float:
        self._logger.debug(
            "Calculating daily balance",
            details={"day": str(day)},
        )
        return await self._repository.get_balance(day)

    @log_execution_time
    async def search_transactions(
        self, params: TransactionQueryParams
    ) -> List[Transaction]:
        self._logger.debug(
            "Searching transactions",
            details={"params": params.model_dump()},
        )
        return await self._repository.find(params)

    @log_execution_time
    async def add_transaction(self, transaction: Transaction) -> Transaction:
        self._logger.debug(
            "Adding transaction",
            details={"transaction": asdict(transaction)},
        )
        return await self._repository.add_transaction(transaction)

    @log_execution_time
    async def update_transaction(
        self, params: UpdateTransactionParams
    ) -> Optional[Transaction]:
        self._logger.debug(
            "Updating transaction",
            details={"params": params.model_dump()},
        )
        return await self._repository.update_transaction(params)
