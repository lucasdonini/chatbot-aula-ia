import logging
from datetime import datetime
from typing import Callable, ContextManager, List, Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from model.transaction_query_params import TransactionQueryParams
from src.model.transaction import Category, Transaction, TransactionType

from ..postgres.entities.transaction import (
    CategoryORM,
    TransactionORM,
    TransactionTypeORM,
)

logger = logging.getLogger(__name__)


class TransactionRepository:
    def __init__(self, session_factory: Callable[[], ContextManager[Session]]):
        self._session_factory = session_factory

    def sum_amounts_by_transaction_type(
        self,
        transaction_type: TransactionType,
        period_start: Optional[datetime] = None,
        period_end: Optional[datetime] = None,
    ) -> float:
        stmt = select(func.coalesce(func.sum(TransactionORM.amount), 0)).where(
            TransactionORM.transaction_type.has(
                TransactionTypeORM.name == transaction_type
            ),
            period_start and TransactionORM.occurred_at >= period_start,
            period_end and TransactionORM.occurred_at < period_end,
        )

        with self._session_factory() as session:
            return float(session.scalar(stmt))

    def _resolve_transaction_type_id(
        self, session: Session, type_name: TransactionType
    ) -> int:
        stmt = (
            select(TransactionTypeORM.id)
            .where(func.upper(TransactionTypeORM.name) == type_name)
            .limit(1)
        )

        if (result := session.scalar(stmt)) is None:
            raise ValueError(f"Type {type_name} is not recognized.")
        return result

    def _resolve_category_id(self, session: Session, category_name: Category) -> int:
        stmt = (
            select(CategoryORM.id)
            .where(func.lower(CategoryORM.name) == category_name)
            .limit(1)
        )

        if (result := session.scalar(stmt)) is None:
            raise ValueError(f"Category {category_name} is not recognized.")
        return result

    def _orm_to_model(self, orm: TransactionORM) -> Transaction:
        category: Category
        try:
            category = Category(orm.category.name)
        except ValueError:
            raise ValueError(f"Category {orm.category.name} is not recognized.")

        transaction_type: TransactionType
        try:
            transaction_type = TransactionType(orm.transaction_type.name)
        except ValueError:
            raise ValueError(f"Type {orm.transaction_type.name} is not recognized.")

        return Transaction(
            amount=orm.amount,
            category=category,
            transaction_type=transaction_type,
            description=orm.description,
            payment_method=orm.payment_method,
            occurred_at=orm.occurred_at,
            updated_at=orm.updated_at,
            source_text=orm.source_text,
        )

    def find(self, params: TransactionQueryParams) -> List[Transaction]:
        logger.info("Searching Transactions. Params: %s", params)

        if params.limit <= 0:
            return []

        stmt = select(TransactionORM).where(
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
        )

        with self._session_factory() as session:
            # Add WHERE clauses involving FKs through id instead of name for security
            try:
                if params.transaction_type:
                    type_id = self._resolve_transaction_type_id(
                        session=session, type_name=params.transaction_type
                    )
                    stmt = stmt.where(TransactionORM.transaction_type_id == type_id)
            except Exception:
                logger.exception("Exception raised while resolving type id")
                raise

            try:
                if params.category:
                    category_id = self._resolve_category_id(
                        session=session, category_name=params.category
                    )
                    stmt = stmt.where(TransactionORM.category_id == category_id)
            except Exception:
                logger.exception("Exception rasied while resolving category id")
                raise

            stmt = stmt.order_by(
                TransactionORM.occurred_at.asc()
                if params.occurred_at_start or params.occurred_at_end
                else TransactionORM.occurred_at.desc()
            ).limit(params.limit)

            logger.debug("Searching query: %s", str(stmt))

            docs = session.scalars(stmt).all()
            result = [self._orm_to_model(doc) for doc in docs]
            logger.info("Transaction search successful. Result size: %s", len(result))
            return result
