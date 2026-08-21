from datetime import date, datetime
from uuid import uuid4

from app.application.models.transaction_update import (
    UpdateTransactionParams,
    UpdateTransactionQuery,
)
from app.domain.model.transaction import Category, TransactionType


class TestUpdateTransactionQuery:
    def test_create_by_id(self):
        uid = uuid4()
        query = UpdateTransactionQuery(id=uid)
        assert query.id == uid
        assert query.match_text is None
        assert query.date_local is None

    def test_create_by_match(self):
        query = UpdateTransactionQuery(
            match_text="almoço",
            date_local=date(2026, 6, 1),
        )
        assert query.match_text == "almoço"
        assert query.date_local == date(2026, 6, 1)
        assert query.id is None

    def test_create_empty(self):
        query = UpdateTransactionQuery()
        assert query.id is None
        assert query.match_text is None
        assert query.date_local is None

    def test_id_only(self):
        uid = uuid4()
        query = UpdateTransactionQuery(id=uid)
        assert query.id == uid
        assert query.match_text is None
        assert query.date_local is None

    def test_model_dump_roundtrip(self):
        uid = uuid4()
        original = UpdateTransactionQuery(id=uid)
        data = original.model_dump()
        restored = UpdateTransactionQuery.model_validate(data)
        assert restored.id == uid


class TestUpdateTransactionParams:
    def test_create_by_id(self):
        uid = uuid4()
        params = UpdateTransactionParams(
            query=UpdateTransactionQuery(id=uid),
            amount=200.0,
            category=Category.FOOD,
        )
        assert params.query.id == uid
        assert params.amount == 200.0
        assert params.category == Category.FOOD
        assert params.query.match_text is None
        assert params.query.date_local is None

    def test_create_by_match(self):
        params = UpdateTransactionParams(
            query=UpdateTransactionQuery(
                match_text="almoço",
                date_local=date(2026, 6, 1),
            ),
            amount=150.0,
        )
        assert params.query.match_text == "almoço"
        assert params.query.date_local == date(2026, 6, 1)
        assert params.amount == 150.0
        assert params.query.id is None

    def test_create_with_query_object(self):
        query = UpdateTransactionQuery(id=uuid4())
        params = UpdateTransactionParams(query=query, amount=99.90)
        assert params.query is query
        assert params.amount == 99.90

    def test_has_update_true_with_amount(self):
        params = UpdateTransactionParams(
            query=UpdateTransactionQuery(
                match_text="teste",
                date_local=date(2026, 1, 1),
            ),
            amount=100.0,
        )
        assert params.has_update is True

    def test_has_update_true_with_category(self):
        params = UpdateTransactionParams(
            query=UpdateTransactionQuery(
                match_text="teste",
                date_local=date(2026, 1, 1),
            ),
            category=Category.HEALTH,
        )
        assert params.has_update is True

    def test_has_update_true_with_transaction_type(self):
        params = UpdateTransactionParams(
            query=UpdateTransactionQuery(
                match_text="teste",
                date_local=date(2026, 1, 1),
            ),
            transaction_type=TransactionType.INCOME,
        )
        assert params.has_update is True

    def test_has_update_true_with_description(self):
        params = UpdateTransactionParams(
            query=UpdateTransactionQuery(
                match_text="teste",
                date_local=date(2026, 1, 1),
            ),
            description="nova desc",
        )
        assert params.has_update is True

    def test_has_update_true_with_payment_method(self):
        params = UpdateTransactionParams(
            query=UpdateTransactionQuery(
                match_text="teste",
                date_local=date(2026, 1, 1),
            ),
            payment_method="crédito",
        )
        assert params.has_update is True

    def test_has_update_false_when_none_set(self, sample_update_params_empty):
        assert sample_update_params_empty.has_update is False

    def test_has_update_false_query_id_only(self):
        params = UpdateTransactionParams(query=UpdateTransactionQuery(id=uuid4()))
        assert params.has_update is False

    def test_has_update_false_query_match_only(self):
        params = UpdateTransactionParams(
            query=UpdateTransactionQuery(match_text="busca"),
        )
        assert params.has_update is False

    def test_no_id_no_match_text(self):
        params = UpdateTransactionParams(
            query=UpdateTransactionQuery(),
            amount=100.0,
        )
        assert params.query.id is None
        assert params.query.match_text is None
        assert params.amount == 100.0

    def test_amount_zero_has_update_true(self):
        params = UpdateTransactionParams(
            query=UpdateTransactionQuery(
                match_text="teste",
                date_local=date(2026, 1, 1),
            ),
            amount=0.0,
        )
        assert params.has_update is True

    def test_updated_at_str_coerces_to_datetime(self):
        params = UpdateTransactionParams(
            query=UpdateTransactionQuery(id=uuid4()),
            updated_at="2026-06-28",
        )
        assert params.updated_at == datetime(year=2026, month=6, day=28)

    def test_occurred_at_str_coerces_to_datetime(self):
        params = UpdateTransactionParams(
            query=UpdateTransactionQuery(id=uuid4()),
            occurred_at="2026-06-28",
        )
        assert params.occurred_at == datetime(year=2026, month=6, day=28)

    def test_model_dump_excludes_none(self, sample_update_params_by_id):
        data = sample_update_params_by_id.model_dump(exclude_none=True)
        assert "match_text" not in data
        assert "date_local" not in data
        assert "amount" in data

    def test_model_dump_roundtrip(self, sample_update_params_by_match):
        data = sample_update_params_by_match.model_dump()
        restored = UpdateTransactionParams.model_validate(data)
        assert (
            restored.query.match_text == sample_update_params_by_match.query.match_text
        )
        assert (
            restored.query.date_local == sample_update_params_by_match.query.date_local
        )
        assert restored.amount == sample_update_params_by_match.amount

    def test_has_update_true_with_is_canceled(self):
        params = UpdateTransactionParams(
            query=UpdateTransactionQuery(
                match_text="teste",
                date_local=date(2026, 1, 1),
            ),
            is_canceled=True,
        )
        assert params.has_update is True

    def test_is_canceled_default_none(self):
        params = UpdateTransactionParams(
            query=UpdateTransactionQuery(id=uuid4()),
        )
        assert params.is_canceled is None

    def test_is_canceled_explicit_true(self):
        params = UpdateTransactionParams(
            query=UpdateTransactionQuery(id=uuid4()),
            is_canceled=True,
        )
        assert params.is_canceled is True

    def test_is_canceled_explicit_false(self):
        params = UpdateTransactionParams(
            query=UpdateTransactionQuery(id=uuid4()),
            is_canceled=False,
        )
        assert params.is_canceled is False

    def test_model_dump_includes_is_canceled(self):
        params = UpdateTransactionParams(
            query=UpdateTransactionQuery(id=uuid4()),
            is_canceled=True,
        )
        data = params.model_dump(exclude_none=True)
        assert data["is_canceled"] is True
