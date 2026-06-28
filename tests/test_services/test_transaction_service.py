from datetime import date, datetime

import pytest

from src.model.transaction import Category, TransactionType
from src.model.transaction_query_params import TransactionQueryParams


class TestCalculateTotalBalance:
    def test_positive_balance(self, service, mock_repository):
        def side_effect(tx_type, **kw):
            return 5000.0 if tx_type == TransactionType.INCOME else 2000.0

        mock_repository.sum_amounts_by_transaction_type.side_effect = side_effect

        balance = service.calculate_total_balance()

        assert balance == 3000.0
        mock_repository.sum_amounts_by_transaction_type.assert_any_call(
            TransactionType.INCOME
        )
        mock_repository.sum_amounts_by_transaction_type.assert_any_call(
            TransactionType.EXPENSE
        )

    def test_negative_balance(self, service, mock_repository):
        def side_effect(tx_type, **kw):
            return 1000.0 if tx_type == TransactionType.INCOME else 3000.0

        mock_repository.sum_amounts_by_transaction_type.side_effect = side_effect

        balance = service.calculate_total_balance()

        assert balance == -2000.0

    def test_zero_balance(self, service, mock_repository):
        mock_repository.sum_amounts_by_transaction_type.return_value = 0.0

        balance = service.calculate_total_balance()

        assert balance == 0.0

    def test_calls_repository_twice(self, service, mock_repository):
        mock_repository.sum_amounts_by_transaction_type.return_value = 0.0

        service.calculate_total_balance()

        assert mock_repository.sum_amounts_by_transaction_type.call_count == 2


class TestCalculateDailyBalance:
    def test_daily_balance(self, service, mock_repository):
        mock_repository.sum_amounts_by_transaction_type.side_effect = (
            lambda tx_type, **kw: 500.0 if tx_type == TransactionType.INCOME else 200.0
        )

        balance = service.calculate_daily_balance(date(2026, 6, 1))

        assert balance == 300.0
        assert mock_repository.sum_amounts_by_transaction_type.call_count == 2

    def test_daily_balance_passes_period_end(self, service, mock_repository):
        mock_repository.sum_amounts_by_transaction_type.return_value = 0.0

        service.calculate_daily_balance(date(2026, 6, 1))

        for call_args in mock_repository.sum_amounts_by_transaction_type.call_args_list:
            kwargs = call_args[1]
            assert "period_end" in kwargs
            assert kwargs["period_end"] == datetime(2026, 6, 2, 0, 0, 0)

    def test_daily_balance_no_period_start(self, service, mock_repository):
        mock_repository.sum_amounts_by_transaction_type.return_value = 0.0

        service.calculate_daily_balance(date(2026, 6, 1))

        for call_args in mock_repository.sum_amounts_by_transaction_type.call_args_list:
            kwargs = call_args[1]
            assert "period_start" not in kwargs

    def test_daily_balance_negative(self, service, mock_repository):
        mock_repository.sum_amounts_by_transaction_type.side_effect = (
            lambda tx_type, **kw: 100.0 if tx_type == TransactionType.INCOME else 500.0
        )

        balance = service.calculate_daily_balance(date(2026, 6, 1))

        assert balance == -400.0


class TestSearchTransactions:
    def test_search(self, service, mock_repository, sample_transactions_list):
        mock_repository.find.return_value = sample_transactions_list

        params = TransactionQueryParams(category=Category.FOOD)
        result = service.search_transactions(params)

        assert result == sample_transactions_list
        mock_repository.find.assert_called_once_with(params)

    def test_search_empty(self, service, mock_repository):
        mock_repository.find.return_value = []

        params = TransactionQueryParams(source_text="inexistente")
        result = service.search_transactions(params)

        assert result == []

    def test_search_passthrough_params(self, service, mock_repository):
        mock_repository.find.return_value = []
        params = TransactionQueryParams(limit=5)

        service.search_transactions(params)

        mock_repository.find.assert_called_once_with(params)


class TestAddTransaction:
    def test_add(
        self, service, mock_repository, sample_transaction, sample_transaction_with_id
    ):
        mock_repository.add_transaction.return_value = sample_transaction_with_id

        result = service.add_transaction(sample_transaction)

        assert result == sample_transaction_with_id
        mock_repository.add_transaction.assert_called_once_with(sample_transaction)

    def test_add_returns_from_repository(
        self, service, mock_repository, sample_transaction
    ):
        mock_repository.add_transaction.return_value = sample_transaction

        result = service.add_transaction(sample_transaction)

        assert result == sample_transaction

    def test_add_raises(self, service, mock_repository, sample_transaction):
        mock_repository.add_transaction.side_effect = Exception("fail")

        with pytest.raises(Exception):
            service.add_transaction(sample_transaction)


class TestUpdateTransaction:
    def test_update(
        self,
        service,
        mock_repository,
        sample_update_params_by_id,
        sample_transaction_with_id,
    ):
        mock_repository.update_transaction.return_value = sample_transaction_with_id

        result = service.update_transaction(sample_update_params_by_id)

        assert result is not None
        mock_repository.update_transaction.assert_called_once_with(
            sample_update_params_by_id
        )

    def test_update_nothing(self, service, mock_repository, sample_update_params_empty):
        mock_repository.update_transaction.return_value = None

        result = service.update_transaction(sample_update_params_empty)

        assert result is None

    def test_update_raises(self, service, mock_repository, sample_update_params_by_id):
        mock_repository.update_transaction.side_effect = ValueError("no reference")

        with pytest.raises(ValueError):
            service.update_transaction(sample_update_params_by_id)
