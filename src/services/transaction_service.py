import logging
from datetime import date, datetime, time, timedelta
from typing import List, Optional

from model.update_transaction_params import UpdateTransactionParams
from src.infrastructure.execution_time_logger import log_execution_time
from src.infrastructure.repositories.transaction_repository import TransactionRepository
from src.model.transaction import Transaction, TransactionType
from src.model.transaction_query_params import TransactionQueryParams

logger = logging.getLogger(__name__)


class TransactionService:
    def __init__(self, repository: TransactionRepository):
        self._repository = repository

    @log_execution_time
    def calculate_total_balance(self) -> float:
        logger.info("Calculating total balance...")
        income = self._repository.sum_amounts_by_transaction_type(
            TransactionType.INCOME
        )
        expenses = self._repository.sum_amounts_by_transaction_type(
            TransactionType.EXPENSE
        )
        return income - expenses

    @log_execution_time
    def calculate_daily_balance(self, day: date) -> float:
        logger.info("Calculating daily balance...")
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
        logger.info("Searching Transactions. Params: %s", params)
        return self._repository.find(params)

    @log_execution_time
    def add_transaction(self, transaction: Transaction) -> Transaction:
        logger.info("Adding Transaction: %s", transaction)
        return self._repository.add_transaction(transaction)

    @log_execution_time
    def update_transaction(
        self, params: UpdateTransactionParams
    ) -> Optional[Transaction]:
        logger.info("Updating transaction: %s", params)
        return self._repository.update_transaction(params)
