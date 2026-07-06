import logging
from datetime import date, datetime, time, timedelta
from typing import List, Optional

from src.infrastructure.execution_time_logger import log_execution_time
from src.infrastructure.repositories.transaction_repository import TransactionRepository
from src.model.transaction import Transaction, TransactionType
from src.model.transaction_query_params import TransactionQueryParams
from src.model.update_transaction_params import UpdateTransactionParams

logger = logging.getLogger(__name__)


class TransactionService:
    def __init__(self, repository: TransactionRepository):
        self._repository = repository

    @log_execution_time
    def calculate_total_balance(self) -> float:
        logger.debug("Calculating total balance")
        income = self._repository.sum_amounts_by_transaction_type(
            TransactionType.INCOME
        )
        expenses = self._repository.sum_amounts_by_transaction_type(
            TransactionType.EXPENSE
        )
        return income - expenses

    @log_execution_time
    def calculate_daily_balance(self, day: date) -> float:
        logger.debug(
            "Calculating daily balance",
            extra={"details": {"day": str(day)}},
        )
        day_datetime = datetime.combine(day + timedelta(days=1), time.min)
        income = self._repository.sum_amounts_by_transaction_type(
            TransactionType.INCOME, period_end=day_datetime
        )
        expenses = self._repository.sum_amounts_by_transaction_type(
            TransactionType.EXPENSE, period_end=day_datetime
        )
        return income - expenses

    @log_execution_time
    def search_transactions(self, params: TransactionQueryParams) -> List[Transaction]:
        logger.debug(
            "Searching transactions",
            extra={"details": {"params": params.model_dump()}},
        )
        return self._repository.find(params)

    @log_execution_time
    def add_transaction(self, transaction: Transaction) -> Transaction:
        logger.debug(
            "Adding transaction",
            extra={"details": {"transaction": transaction.model_dump()}},
        )
        return self._repository.add_transaction(transaction)

    @log_execution_time
    def update_transaction(
        self, params: UpdateTransactionParams
    ) -> Optional[Transaction]:
        logger.debug(
            "Updating transaction",
            extra={"details": {"params": params.model_dump()}},
        )
        return self._repository.update_transaction(params)
