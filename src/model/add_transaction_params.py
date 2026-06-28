from typing import Optional

from pydantic import BaseModel, Field


class AddTransactionParams(BaseModel):
    amount: float = Field(..., description="Valor da transação (use positivo).")
    source_text: str = Field(..., description="Texto original do usuário.")
    occurred_at: Optional[str] = Field(
        default=None,
        description=(
            "Data da transação segundo o prompt do usuário; "
            "se ausente, usa NOW() no banco."
        ),
    )
    type_id: Optional[int] = Field(
        default=None,
        description="ID em transaction_types (1=INCOME, 2=EXPENSES, 3=TRANSFER).",
    )
    type_name: Optional[str] = Field(
        default=None, description="Nome do tipo: INCOME | EXPENSES | TRANSFER."
    )
    category_id: Optional[int] = Field(
        default=None, description="FK de categories (opcional)."
    )
    category_name: Optional[str] = Field(
        default="outros",
        description=(
            "Nome da categoria: comida | besteira | estudo | "
            "férias | transporte | moradia | saúde | lazer | "
            "contas | investimento | presente | outros"
        ),
    )
    description: Optional[str] = Field(
        default=None, description="Descrição (opcional)."
    )
    payment_method: Optional[str] = Field(
        default=None, description="Forma de pagamento (opcional)."
    )
