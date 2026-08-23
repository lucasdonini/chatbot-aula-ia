from datetime import date

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

    async def calculate_total_balance(self) -> float:
        self._logger.debug("Calculating total balance")
        return await self._repository.get_balance()

    async def calculate_daily_balance(self, day: date) -> float:
        self._logger.debug(
            "Calculating daily balance",
            details={"day": str(day)},
        )
        return await self._repository.get_balance(day)

    async def search_transactions(
        self, params: TransactionQueryParams
    ) -> list[Transaction]:
        self._logger.debug(
            "Searching transactions",
            details={
                "filters": sorted(
                    key
                    for key, value in params.model_dump().items()
                    if value is not None and key != "source_text"
                )
            },
        )
        return await self._repository.find(params)

    async def add_transaction(self, transaction: Transaction) -> Transaction:
        self._logger.debug(
            "Adding transaction",
            details={
                "category": transaction.category.value,
                "transaction_type": transaction.transaction_type.value,
            },
        )
        return await self._repository.add_transaction(transaction)

    async def update_transaction(
        self, params: UpdateTransactionParams
    ) -> Transaction | None:
        self._logger.debug(
            "Updating transaction",
            details={
                "updated_fields": sorted(
                    key
                    for key, value in params.model_dump(exclude={"query"}).items()
                    if value is not None
                )
            },
        )
        return await self._repository.update_transaction(params)
