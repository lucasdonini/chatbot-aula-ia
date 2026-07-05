from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from src.model.transaction import Category, Transaction, TransactionType


class TestTransactionModel:
    def test_create_minimal(self):
        t = Transaction(
            amount=100.0,
            source_text="Gastei 100 reais",
        )
        assert t.amount == 100.0
        assert t.category == Category.OTHER
        assert t.transaction_type == TransactionType.EXPENSE
        assert t.description is None
        assert t.payment_method is None
        assert t.occurred_at is None
        assert t.updated_at is None
        assert t.source_text == "Gastei 100 reais"

    def test_create_full(self):
        dt = datetime(2026, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
        t = Transaction(
            amount=250.75,
            category=Category.HEALTH,
            transaction_type=TransactionType.EXPENSE,
            description="Consulta médica",
            payment_method="cartão",
            occurred_at=dt,
            source_text="Gastei 250 no médico",
        )
        assert t.amount == 250.75
        assert t.category == Category.HEALTH
        assert t.transaction_type == TransactionType.EXPENSE
        assert t.description == "Consulta médica"
        assert t.payment_method == "cartão"
        assert t.occurred_at == dt
        assert t.source_text == "Gastei 250 no médico"

    def test_create_income(self):
        t = Transaction(
            amount=5000.0,
            category=Category.INVESTMENT,
            transaction_type=TransactionType.INCOME,
            source_text="Recebi 5000 de dividendos",
        )
        assert t.transaction_type == TransactionType.INCOME

    def test_create_transfer(self):
        t = Transaction(
            amount=300.0,
            transaction_type=TransactionType.TRANSFER,
            source_text="Transferi 300 reais",
        )
        assert t.transaction_type == TransactionType.TRANSFER

    def test_amount_accepts_negative_value(self):
        t = Transaction(
            amount=-50.0,
            source_text="Valor negativo",
        )
        assert t.amount == -50.0

    def test_source_text_required(self):
        with pytest.raises(ValidationError):
            Transaction(amount=100.0)

    def test_model_dump_roundtrip(self, sample_transaction):
        data = sample_transaction.model_dump()
        restored = Transaction.model_validate(data)
        assert restored.amount == sample_transaction.amount
        assert restored.category == sample_transaction.category
        assert restored.transaction_type == sample_transaction.transaction_type
        assert restored.description == sample_transaction.description
        assert restored.source_text == sample_transaction.source_text

    def test_from_attributes_enabled(self):
        from src.infrastructure.postgres.entities.transaction import TransactionORM

        orm = TransactionORM(
            amount=99.90,
            category=Category.FOOD,
            transaction_type=TransactionType.EXPENSE,
            source_text="Comprei comida",
            is_canceled=False,
        )
        model = Transaction.model_validate(orm)
        assert model.amount == 99.90
        assert model.category == Category.FOOD
        assert model.transaction_type == TransactionType.EXPENSE

    def test_category_enum_values(self):
        assert Category.FOOD == "comida"
        assert Category.JUNK == "besteira"
        assert Category.STUDIES == "estudo"
        assert Category.TRANSPORTATION == "transporte"
        assert Category.HOUSING == "moradia"
        assert Category.HEALTH == "saúde"
        assert Category.LIESURE == "lazer"
        assert Category.BILLS == "contas"
        assert Category.INVESTMENT == "investimento"
        assert Category.GIFTS == "presente"
        assert Category.OTHER == "outros"

    def test_transaction_type_enum_values(self):
        assert TransactionType.INCOME == "INCOME"
        assert TransactionType.EXPENSE == "EXPENSE"
        assert TransactionType.TRANSFER == "TRANSFER"
