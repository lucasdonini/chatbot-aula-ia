from datetime import datetime
from typing import List
from uuid import UUID, uuid4

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .declarative_base import Base


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )

    transactions: Mapped[List["Transaction"]] = relationship(
        back_populates="category",
    )


class TransactionType(Base):
    __tablename__ = "transaction_types"

    id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    transactions: Mapped[List["Transaction"]] = relationship(
        back_populates="transaction_type",
    )


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        server_default=func.gen_random_uuid(),
    )

    amount: Mapped[float] = mapped_column(
        Numeric(14, 2),
        nullable=False,
    )

    category_id: Mapped[int] = mapped_column(
        ForeignKey("categories.id"),
        nullable=False,
        index=True,
    )

    category: Mapped["Category"] = relationship(
        back_populates="transactions",
    )

    type_id: Mapped[int] = mapped_column(
        ForeignKey("transaction_types.id"),
        nullable=False,
        index=True,
    )

    transaction_type: Mapped["TransactionType"] = relationship(
        back_populates="transactions",
    )

    description: Mapped[str | None] = mapped_column(Text)

    payment_method: Mapped[str | None] = mapped_column(
        String(32),
    )

    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        server_onupdate=func.now(),
    )

    source_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    __table_args__ = (
        Index(
            "idx_transactions_occurred_at",
            "occurred_at",
        ),
        Index(
            "idx_transactions_category_time",
            "category_id",
            "occurred_at",
        ),
    )
