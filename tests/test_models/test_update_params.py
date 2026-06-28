from datetime import date, datetime
from uuid import uuid4

from src.model.transaction import Category, TransactionType
from src.model.update_transaction_params import UpdateTransactionParams


class TestUpdateTransactionParams:
    def test_create_by_id(self):
        uid = uuid4()
        params = UpdateTransactionParams(
            id=uid,
            amount=200.0,
            category=Category.FOOD,
        )
        assert params.id == uid
        assert params.amount == 200.0
        assert params.category == Category.FOOD
        assert params.match_text is None
        assert params.date_local is None

    def test_create_by_match(self):
        params = UpdateTransactionParams(
            match_text="almoço",
            date_local=date(2026, 6, 1),
            amount=150.0,
        )
        assert params.match_text == "almoço"
        assert params.date_local == date(2026, 6, 1)
        assert params.amount == 150.0
        assert params.id is None

    def test_has_update_true_with_amount(self):
        params = UpdateTransactionParams(
            match_text="teste",
            date_local=date(2026, 1, 1),
            amount=100.0,
        )
        assert params.has_update is True

    def test_has_update_true_with_category(self):
        params = UpdateTransactionParams(
            match_text="teste",
            date_local=date(2026, 1, 1),
            category=Category.HEALTH,
        )
        assert params.has_update is True

    def test_has_update_true_with_transaction_type(self):
        params = UpdateTransactionParams(
            match_text="teste",
            date_local=date(2026, 1, 1),
            transaction_type=TransactionType.INCOME,
        )
        assert params.has_update is True

    def test_has_update_true_with_description(self):
        params = UpdateTransactionParams(
            match_text="teste",
            date_local=date(2026, 1, 1),
            description="nova desc",
        )
        assert params.has_update is True

    def test_has_update_true_with_payment_method(self):
        params = UpdateTransactionParams(
            match_text="teste",
            date_local=date(2026, 1, 1),
            payment_method="crédito",
        )
        assert params.has_update is True

    def test_has_update_false_when_none_set(self, sample_update_params_empty):
        assert sample_update_params_empty.has_update is False

    def test_has_update_false_id_only(self):
        params = UpdateTransactionParams(id=uuid4())
        assert params.has_update is False

    def test_has_update_false_match_text_only(self):
        params = UpdateTransactionParams(match_text="busca")
        assert params.has_update is False

    def test_no_id_no_match_text(self):
        params = UpdateTransactionParams(amount=100.0)
        assert params.id is None
        assert params.match_text is None
        assert params.amount == 100.0

    def test_amount_zero_has_update_true(self):
        params = UpdateTransactionParams(
            match_text="teste",
            date_local=date(2026, 1, 1),
            amount=0.0,
        )
        assert params.has_update is True

    def test_updated_at_str_coerces_to_datetime(self):
        params = UpdateTransactionParams(updated_at="2026-06-28")
        assert params.updated_at == datetime(year=2026, month=6, day=28)

    def test_occurred_at_str_coerces_to_datetime(self):
        params = UpdateTransactionParams(occurred_at="2026-06-28")
        assert params.occurred_at == datetime(year=2026, month=6, day=28)

    def test_model_dump_excludes_none(self, sample_update_params_by_id):
        data = sample_update_params_by_id.model_dump(exclude_none=True)
        assert "match_text" not in data
        assert "date_local" not in data
        assert "amount" in data

    def test_model_dump_roundtrip(self, sample_update_params_by_match):
        data = sample_update_params_by_match.model_dump()
        restored = UpdateTransactionParams.model_validate(data)
        assert restored.match_text == sample_update_params_by_match.match_text
        assert restored.date_local == sample_update_params_by_match.date_local
        assert restored.amount == sample_update_params_by_match.amount
