from datetime import date
from typing import Protocol

from app.application.models.transaction_query import TransactionQueryParams
from app.application.models.transaction_update import UpdateTransactionParams
from app.domain.model.transaction import Transaction


class TransactionRepository(Protocol):
    def get_balance(self, day: date | None = None) -> float: ...

    def find(self, params: TransactionQueryParams) -> list[Transaction]: ...

    def add_transaction(self, transaction: Transaction) -> Transaction: ...

    def update_transaction(
        self,
        params: UpdateTransactionParams,
    ) -> Transaction | None: ...
