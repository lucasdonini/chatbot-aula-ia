from datetime import date

from app.domain.model.transaction import Category, TransactionType
from app.infrastructure.agents.schema.transaction_query_params import (
    TransactionQueryParams,
)


class TestTransactionQueryParams:
    def test_create_defaults(self):
        params = TransactionQueryParams()
        assert params.source_text is None
        assert params.occurred_at_start is None
        assert params.occurred_at_end is None
        assert params.updated_at_start is None
        assert params.updated_at_end is None
        assert params.transaction_type is None
        assert params.category is None
        assert params.description is None
        assert params.limit == 50

    def test_create_full(self, sample_query_params):
        assert sample_query_params.source_text == "almoço"
        assert sample_query_params.occurred_at_start == date(2026, 1, 1)
        assert sample_query_params.occurred_at_end == date(2026, 12, 31)
        assert sample_query_params.category == Category.FOOD
        assert sample_query_params.transaction_type == TransactionType.EXPENSE
        assert sample_query_params.limit == 10

    def test_limit_custom(self):
        params = TransactionQueryParams(limit=5)
        assert params.limit == 5

    def test_limit_zero(self):
        params = TransactionQueryParams(limit=0)
        assert params.limit == 0

    def test_limit_negative_is_accepted(self):
        params = TransactionQueryParams(limit=-1)
        assert params.limit == -1

    def test_only_source_text(self):
        params = TransactionQueryParams(source_text="mercado")
        assert params.source_text == "mercado"
        assert params.limit == 50

    def test_only_date_range(self):
        params = TransactionQueryParams(
            occurred_at_start=date(2026, 1, 1),
            occurred_at_end=date(2026, 3, 31),
        )
        assert params.occurred_at_start == date(2026, 1, 1)
        assert params.occurred_at_end == date(2026, 3, 31)

    def test_model_dump_roundtrip(self, sample_query_params):
        data = sample_query_params.model_dump()
        restored = TransactionQueryParams.model_validate(data)
        assert restored.source_text == sample_query_params.source_text
        assert restored.occurred_at_start == sample_query_params.occurred_at_start
        assert restored.limit == sample_query_params.limit

    def test_category_as_string(self):
        params = TransactionQueryParams(category="comida")
        assert params.category == "comida"

    def test_category_as_enum(self):
        params = TransactionQueryParams(category=Category.FOOD)
        assert params.category == Category.FOOD

    def test_is_canceled_default_false(self):
        params = TransactionQueryParams()
        assert params.is_canceled is False

    def test_is_canceled_explicit_true(self):
        params = TransactionQueryParams(is_canceled=True)
        assert params.is_canceled is True

    def test_is_canceled_explicit_none(self):
        params = TransactionQueryParams(is_canceled=None)
        assert params.is_canceled is None

    def test_is_canceled_model_dump_roundtrip(self):
        params = TransactionQueryParams(is_canceled=True)
        data = params.model_dump()
        restored = TransactionQueryParams.model_validate(data)
        assert restored.is_canceled is True
