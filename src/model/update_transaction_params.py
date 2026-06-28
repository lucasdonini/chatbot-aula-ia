from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, ValidationError, field_validator

from .transaction import Category, TransactionType


class UpdateTransactionParams(BaseModel):
    id: Optional[UUID] = Field(
        default=None,
        description=(
            "ID da transação a atualizar. "
            "Se ausente, será feita uma busca por (match_text + date_local)."
        ),
    )

    match_text: Optional[str] = Field(
        default=None,
        description=(
            "Texto para localizar transação quando id não "
            "for informado (busca em source_text/description)."
        ),
    )

    date_local: Optional[date] = Field(
        default=None,
        description=(
            "Data local (YYYY-MM-DD); usado em conjunto "
            "com match_text quando id ausente."
        ),
    )

    amount: Optional[float] = Field(default=None, description="Novo valor.")

    transaction_type: Optional[TransactionType] = Field(
        default=None, description=f"Novo tipo: {' | '.join(TransactionType)}"
    )

    category: Optional[Category] = Field(
        default=None, description=f"Nova categoria: {' | '.join(Category)}."
    )

    description: Optional[str] = Field(default=None, description="Nova descrição.")

    payment_method: Optional[str] = Field(
        default=None, description="Novo meio de pagamento."
    )

    occurred_at: Optional[datetime] = Field(
        default=None, description="Timestamp ISO 8601 da nova data de ocorrência."
    )

    updated_at: Optional[datetime] = Field(
        default=None,
        description=(
            "Timestamp ISO 8601 da data da atualização mais recente da transação. "
            "Inclua APENAS se tiver motivo explícito para definir arbitáriamente "
            "a data de atualização. Por padrão, mantenha vazio. Será preenchido "
            "automaticamente pelo banco de dados ao atualizar."
        ),
    )

    @field_validator("occurred_at", "updated_at", mode="before")
    @classmethod
    def coerce_datetime(cls, v) -> Optional[datetime]:
        if v is None:
            return None
        if isinstance(v, str):
            return datetime.fromisoformat(v)
        if isinstance(v, datetime):
            return v
        raise ValidationError(
            "Invalid type for date. "
            f"Espected str or datetime, received: {type(v).__name__!r}"
        )

    @property
    def has_update(self) -> bool:
        return any(
            [
                self.amount,
                self.transaction_type,
                self.category,
                self.description,
                self.payment_method,
                self.occurred_at,
                self.updated_at,
            ]
        )
