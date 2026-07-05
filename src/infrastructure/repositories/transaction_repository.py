import logging
from datetime import datetime, time, timedelta
from typing import Callable, ContextManager, List, Optional

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from src.model.transaction import Transaction, TransactionType
from src.model.transaction_query_params import TransactionQueryParams
from src.model.update_transaction_params import UpdateTransactionParams

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
            ~TransactionORM.is_canceled,
        )

        if period_start:
            stmt = stmt.where(TransactionORM.occurred_at >= period_start)

        if period_end:
            stmt = stmt.where(TransactionORM.occurred_at < period_end)

        with self._session_factory() as session:
            return float(session.scalar(stmt))

    def find(self, params: TransactionQueryParams) -> List[Transaction]:
        logger.info("Searching Transactions. Params: %s", params)

        if params.limit is not None and params.limit <= 0:
            return []

        stmt = select(TransactionORM)
        if params.source_text:
            stmt = stmt.where(
                TransactionORM.source_text.ilike(f"%{params.source_text}%")
            )
        if params.description:
            stmt = stmt.where(
                TransactionORM.description.ilike(f"%{params.description}%")
            )
        if params.occurred_at_start:
            stmt = stmt.where(TransactionORM.occurred_at >= params.occurred_at_start)
        if params.occurred_at_end:
            stmt = stmt.where(TransactionORM.occurred_at < params.occurred_at_end)
        if params.updated_at_start:
            stmt = stmt.where(TransactionORM.updated_at >= params.updated_at_start)
        if params.updated_at_end:
            stmt = stmt.where(TransactionORM.updated_at < params.updated_at_end)
        if params.category:
            stmt = stmt.where(TransactionORM.category == params.category)
        if params.is_canceled is not None:
            stmt = stmt.where(TransactionORM.is_canceled.is_(params.is_canceled))
        if params.transaction_type:
            stmt = stmt.where(
                TransactionORM.transaction_type == params.transaction_type
            )
        stmt = stmt.order_by(
            TransactionORM.occurred_at.asc()
            if params.occurred_at_start or params.occurred_at_end
            else TransactionORM.occurred_at.desc()
        )

        if params.limit is not None:
            stmt = stmt.limit(params.limit)

        logger.debug("Searching query: %s", str(stmt))
        result: List[Transaction]
        with self._session_factory() as session:
            docs = session.scalars(stmt).all()
            result = [self._orm_to_model(doc) for doc in docs]
        logger.info("Transaction search successful. Result size: %s", len(result))
        return result

    def add_transaction(self, transaction: Transaction) -> Transaction:
        orm = self._model_to_orm(transaction)
        with self._session_factory() as session:
            session.add(orm)
            session.commit()
            session.refresh(orm)
        return self._orm_to_model(orm)

    def update_transaction(
        self, params: UpdateTransactionParams
    ) -> Optional[Transaction]:
        logger.info("Updating transaction. Params: %s", params)

        if not params.has_update:
            logger.warning("Nothing to update.")
            return None

        stmt = select(TransactionORM)
        if id := params.query.id:
            stmt = stmt.where(TransactionORM.id == id)
        elif (match_text := params.query.match_text) and (
            date_local := params.query.date_local
        ):
            period_start = datetime.combine(date_local, time.min)
            period_end = datetime.combine(date_local + timedelta(days=1), time.min)
            stmt = stmt.where(
                or_(
                    TransactionORM.source_text.ilike(f"%{match_text}%"),
                    TransactionORM.description.ilike(f"%{match_text}%"),
                ),
                TransactionORM.occurred_at >= period_start,
                TransactionORM.occurred_at < period_end,
            )
        else:
            logger.error("Update called without any reference.")
            raise ValueError(
                "You cannot update without a reference. "
                "Please inform either the id or both match_text and date_local"
            )

        stmt = stmt.order_by(TransactionORM.occurred_at).limit(1)
        to_update = params.model_dump(
            exclude_none=True,
            exclude={"query"},
        )

        logger.debug("Locate update target query: %s", str(stmt))
        with self._session_factory() as session:
            target = session.scalar(stmt)

            if not target:
                return None

            for attr, val in to_update.items():
                setattr(target, attr, val)
            session.commit()
            session.refresh(target)

            logger.debug("Updated: %s", target)
            return self._orm_to_model(target)
