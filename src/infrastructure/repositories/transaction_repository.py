import logging
from datetime import datetime
from typing import Callable, ContextManager, List, Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from model.transaction_query_params import TransactionQueryParams
from src.model.transaction import Transaction, TransactionType

from ..postgres.entities.transaction import TransactionORM

logger = logging.getLogger(__name__)


class TransactionRepository:
    def __init__(self, session_factory: Callable[[], ContextManager[Session]]):
        self._session_factory = session_factory

    def _orm_to_model(self, orm: TransactionORM) -> Transaction:
        return Transaction.model_validate(orm)

    def _model_to_orm(self, model: Transaction) -> TransactionORM:
        data = model.model_dump(exclude_unset=True)
        return TransactionORM(**data)

    def sum_amounts_by_transaction_type(
        self,
        transaction_type: TransactionType,
        period_start: Optional[datetime] = None,
        period_end: Optional[datetime] = None,
    ) -> float:
        stmt = select(func.coalesce(func.sum(TransactionORM.amount), 0)).where(
            TransactionORM.transaction_type == transaction_type,
            period_start and TransactionORM.occurred_at >= period_start,
            period_end and TransactionORM.occurred_at < period_end,
        )

        with self._session_factory() as session:
            return float(session.scalar(stmt))

    def find(self, params: TransactionQueryParams) -> List[Transaction]:
        logger.info("Searching Transactions. Params: %s", params)

        if params.limit <= 0:
            return []

        stmt = (
            select(TransactionORM)
            .where(
                (not params.source_text)
                or TransactionORM.source_text.ilike(f"%{params.source_text}%"),
                (not params.description)
                or TransactionORM.description.ilike(f"%{params.description}%"),
                (not params.occurred_at_start)
                or TransactionORM.occurred_at >= params.occurred_at_start,
                (not params.occurred_at_end)
                or TransactionORM.occurred_at < params.occurred_at_end,
                (not params.updated_at_start)
                or TransactionORM.updated_at >= params.updated_at_start,
                (not params.updated_at_end)
                or TransactionORM.updated_at < params.updated_at_end,
                (not params.category) or TransactionORM.category == params.category,
                (not params.transaction_type)
                or TransactionORM.transaction_type == params.transaction_type,
            )
            .order_by(
                TransactionORM.occurred_at.asc()
                if params.occurred_at_start or params.occurred_at_end
                else TransactionORM.occurred_at.desc()
            )
            .limit(params.limit)
        )

        logger.debug("Searching query: %s", str(stmt))
        result: List[Transaction]
        with self._session_factory() as session:
            docs = session.scalars(stmt).all()
            result = [self._orm_to_model(doc) for doc in docs]
        logger.info("Transaction search successful. Result size: %s", len(result))
        return result
