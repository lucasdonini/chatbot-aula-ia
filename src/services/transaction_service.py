import logging
from datetime import date, datetime, time
from typing import Callable, ContextManager, Literal, Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.infrastructure.execution_time_logger import log_execution_time
from src.model.transaction import Transaction, TransactionType

logger = logging.getLogger(__name__)


class TransactionService:
    def __init__(self, session_factory: Callable[[], ContextManager[Session]]):
        self._session_factory = session_factory

    def _sum_amounts_by_transaction_type_name(
        self,
        session: Session,
        type_name: Literal["INCOME", "EXPENSES", "TRANSFER"],
        period_start: Optional[datetime] = None,
        period_end: Optional[datetime] = None,
    ) -> float:
        stmt = select(func.coalesce(func.sum(Transaction.amount), 0)).where(
            Transaction.transaction_type.has(TransactionType.name == type_name)
        )

        if period_start:
            stmt = stmt.where(Transaction.occurred_at >= period_start)

        if period_end:
            stmt = stmt.where(Transaction.occurred_at <= period_end)

        return float(session.scalar(stmt))

    @log_execution_time
    def calculate_total_balance(self) -> float:
        with self._session_factory() as session:
            income = self._sum_amounts_by_transaction_type_name(
                session=session, type_name="INCOME"
            )
            expenses = self._sum_amounts_by_transaction_type_name(
                session=session, type_name="EXPENSES"
            )
        return income - expenses

    @log_execution_time
    def calculate_daily_balance(self, day: date) -> float:
        day_datetime = datetime.combine(day, time.max)
        with self._session_factory() as session:
            income = self._sum_amounts_by_transaction_type_name(
                session=session, type_name="INCOME", period_end=day_datetime
            )
            expenses = self._sum_amounts_by_transaction_type_name(
                session=session, type_name="EXPENSES", period_end=day_datetime
            )
        return income - expenses
