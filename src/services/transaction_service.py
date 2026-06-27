import logging
from datetime import date, datetime, time
from typing import Callable, ContextManager, List, Literal, Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.infrastructure.execution_time_logger import log_execution_time
from src.model.search_transaction_params import SearchTransactionParams
from src.model.transaction import Category, Transaction, TransactionType

logger = logging.getLogger(__name__)

TYPE_ALIASES = {
    "INCOME": "INCOME",
    "ENTRADA": "INCOME",
    "RECEITA": "INCOME",
    "SALÁRIO": "INCOME",
    "EXPENSE": "EXPENSES",
    "EXPENSES": "EXPENSES",
    "DESPESA": "EXPENSES",
    "GASTO": "EXPENSES",
    "TRANSFER": "TRANSFER",
    "TRANSFERÊNCIA": "TRANSFER",
    "TRANSFERENCIA": "TRANSFER",
}


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
            Transaction.transaction_type.has(TransactionType.name == type_name),
            period_start and Transaction.occurred_at >= period_start,
            period_end and Transaction.occurred_at <= period_end,
        )

        return float(session.scalar(stmt))

    def _resolve_type_id(
        self,
        session: Session,
        type_id: Optional[int] = None,
        type_name: Optional[str] = None,
    ) -> int:
        if type_id is not None:
            return type_id
        if type_name:
            name = type_name.strip().upper()
            name = TYPE_ALIASES.get(name, name)
            stmt = (
                select(TransactionType.id)
                .where(func.upper(TransactionType.name) == name)
                .limit(1)
            )
            result = session.scalar(stmt)

            if result is None:
                raise ValueError(
                    f"Type (id={type_id}, name={type_name}) is not recognized. "
                    f"Try one of these: {TYPE_ALIASES.keys()}"
                )
            return result
        return 2

    def _resolve_category_id(
        self,
        session: Session,
        category_id: Optional[int] = None,
        category_name: Optional[str] = None,
    ) -> int:
        if category_id is not None:
            return category_id
        if category_name:
            name = category_name.strip().lower()
            stmt = select(Category.id).where(func.lower(Category.name) == name).limit(1)
            result = session.scalar(stmt)

            if result is None:
                raise ValueError(
                    f"Categroy (id={category_id}, name={category_name}) "
                    "is not recognized."
                )
            return result
        return 12

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

    @log_execution_time
    def search_transactions(self, params: SearchTransactionParams) -> List[Transaction]:
        logger.info("Searching Transactions. Params: %s", params)

        if params.limit <= 0:
            return []

        stmt = select(Transaction).where(
            params.source_text
            and Transaction.source_text.ilike(f"%{params.source_text}%"),
            params.description
            and Transaction.description.ilike(f"%{params.description}%"),
            params.occurred_at_start
            and Transaction.occurred_at >= params.occurred_at_start,
            params.occurred_at_end and Transaction.occurred_at < params.occurred_at_end,
        )

        with self._session_factory() as session:
            try:
                if params.transaction_type is not None:
                    type_id = self._resolve_type_id(
                        session=session, type_name=params.transaction_type
                    )
                    stmt = stmt.where(
                        Transaction.transaction_type.has(TransactionType.id == type_id)
                    )
            except Exception:
                logger.exception("Exception raised while resolving type id")
                raise

            try:
                if params.category:
                    category_id = self._resolve_category_id(
                        session=session, category_name=params.category
                    )
                    stmt = stmt.where(
                        Transaction.category.has(Category.id == category_id)
                    )
            except Exception:
                logger.exception("Exception rasied while resolving category id")
                raise

            stmt = stmt.order_by(
                Transaction.occurred_at.asc()
                if params.occurred_at_start or params.occurred_at_end
                else Transaction.occurred_at.desc()
            ).limit(params.limit)

            logger.debug("Searching query: %s", str(stmt))

            result = list(session.scalars(stmt).all())
            logger.info("Transaction search successful. Result size: %s", len(result))
            return result
