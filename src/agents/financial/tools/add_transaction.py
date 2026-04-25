from src.infrastructure.db_connection import get_cursor

from .utils import resolve_type_id, resolve_category_id
from .response import DatabaseToolResponse
from psycopg2.extensions import cursor
from pydantic import BaseModel, Field
from langchain.tools import tool
from typing import Optional, Tuple


class AddTransactionArgs(BaseModel):
    amount: float = Field(..., description="Valor da transação (use positivo).")
    source_text: str = Field(..., description="Texto original do usuário.")
    occurred_at: Optional[str] = Field(
        default=None,
        description="Data da transação segundo o prompt do usuário; se ausente, usa NOW() no banco.",
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
        description="Nome da categoria: comida | besteira | estudo | férias | transporte | moradia | saúde | lazer | contas | investimento | presente | outros",
    )
    description: Optional[str] = Field(
        default=None, description="Descrição (opcional)."
    )
    payment_method: Optional[str] = Field(
        default=None, description="Forma de pagamento (opcional)."
    )


def _insert_with_date(cur: cursor, *args: Tuple[float, int, int, str, str, str, str]):
    cur.execute(
        """
        INSERT INTO transactions
            (amount, type, category_id, description, payment_method, occurred_at, source_text)
        VALUES
            (%s, %s, %s, %s, %s, %s::timestamptz, %s)
        RETURNING id, occurred_at;
        """,
        args,
    )


def _insert_without_date(cur: cursor, *args: Tuple[float, int, int, str, str, str]):
    cur.execute(
        """
        INSERT INTO transactions
            (amount, type, category_id, description, payment_method, occurred_at, source_text)
        VALUES
            (%s, %s, %s, %s, %s, NOW(), %s)
        RETURNING id, occurred_at;
        """,
        args,
    )


@tool("add_transaction", args_schema=AddTransactionArgs)
def add_transaction(
    amount: float,
    source_text: str,
    occurred_at: Optional[str] = None,
    type_id: Optional[int] = None,
    type_name: Optional[str] = None,
    category_id: Optional[int] = None,
    category_name: Optional[str] = "outros",
    description: Optional[str] = None,
    payment_method: Optional[str] = None,
) -> DatabaseToolResponse:
    """Insere uma transação financeira no banco de dados Postgres."""  # docstring obrigatório da @tools do langchain (estranho, mas legal né?)
    try:
        with get_cursor() as cur:
            resolved_type_id = resolve_type_id(cur, type_id, type_name)
            if not resolved_type_id:
                return DatabaseToolResponse.error(
                    "Tipo inválido (use type_id ou type_name: INCOME/EXPENSES/TRANSFER)."
                )

            resolved_category_id = resolve_category_id(cur, category_id, category_name)
            if not resolved_category_id:
                return DatabaseToolResponse.error(
                    "Categoria inválida (use category_id ou category_name: comida/besteira/estudo/férias/transporte/moradia/saúde/lazer/contas/investimento/presente/outros)"
                )

            if occurred_at:
                _insert_with_date(
                    cur,
                    amount,
                    resolved_type_id,
                    resolved_category_id,
                    description,
                    payment_method,
                    occurred_at,
                    source_text,
                ),
            else:
                _insert_without_date(
                    cur,
                    amount,
                    resolved_type_id,
                    resolved_category_id,
                    description,
                    payment_method,
                    source_text,
                ),

            new_id, occurred = cur.fetchone()
            return DatabaseToolResponse.ok({"id": new_id, "occurred_at": str(occurred)})

    except Exception as e:
        return DatabaseToolResponse.exception(e)
