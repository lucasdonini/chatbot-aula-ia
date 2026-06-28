from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class Category(str, Enum):
    """
    Contains default categories used in the database.
    If you change any key, create a new migration
    so that the database and the enum keep consistent.
    This has to be made manually, alembic does not handle that.
    """

    FOOD = "comida"
    JUNK = "besteira"
    STUDIES = "estudo"
    VACATION = "férias"
    TRANSPORTATION = "transporte"
    HOUSING = "moradia"
    HEALTH = "saúde"
    LIESURE = "lazer"
    BILLS = "contas"
    INVESTMENT = "investimento"
    GIFTS = "presente"
    OTHER = "outros"


class TransactionType(str, Enum):
    """
    Contains default types used in the database.
    If you change any key, create a new migration
    so that the database and the enum keep consistent.
    This has to be made manually, alembic does not handle that.
    """

    INCOME = "INCOME"
    EXPENSE = "EXPENSE"
    TRANSFER = "TRANSFER"


class Transaction(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    amount: float = Field(..., description="Valor da transação (use positivo).")

    category: Category = Field(
        default=Category.OTHER, description=f"Nome da categoria: {' | '.join(Category)}"
    )

    transaction_type: TransactionType = Field(
        default=TransactionType.EXPENSE,
        description=f"Tipo da transação: {' | '.join(TransactionType)}",
    )

    description: Optional[str] = Field(
        default=None, description="Descrição (opcional)."
    )

    payment_method: Optional[str] = Field(
        default=None, description="Forma de pagamento (opcional)."
    )

    occurred_at: Optional[datetime] = Field(
        default=None,
        description=(
            "Data da transação segundo o prompt do usuário; "
            "se ausente, usa NOW() no banco."
        ),
    )

    updated_at: Optional[datetime] = Field(
        default=None,
        description=(
            "Data da útlima modificação do registro. "
            "Default None porque o banco é responsável por preencher."
            "Preencha somente se tiver um motivo claro para querer um "
            "valor diferente da data real de modificação no banco"
        ),
    )

    source_text: str = Field(..., description="Texto original do usuário.")
