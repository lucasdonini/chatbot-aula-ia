import logging
from datetime import date, datetime, time, timedelta
from typing import List

from model.transaction_query_params import TransactionQueryParams
from src.infrastructure.execution_time_logger import log_execution_time
from src.infrastructure.repositories.transaction_repository import TransactionRepository
from src.model.transaction import Transaction, TransactionType

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
