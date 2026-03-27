import os
from dotenv import load_dotenv
import psycopg2
from typing import Optional
from langchain.tools import tool
from pydantic import BaseModel, Field, model_validator

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

class PgToolResponse(BaseModel):
    _allow_direct: bool = False
    status: str
    data: dict
    
    @model_validator(mode="wrap")
    @classmethod
    def _block_direct(cls, values, handler):
        raise TypeError("Use PgToolResponse.ok() or PgToolResponse.error()")
    
    @classmethod
    def ok(cls, data: dict) -> "PgToolResponse":
        return cls.model_construct(status="ok", data=data)
    
    @classmethod
    def error(cls, msg: str) -> "PgToolResponse":
        return cls.model_construct(status="error", data={"message": msg})
    
    @classmethod
    def exception(cls, e: Exception) -> "PgToolResponse":
        return cls.error(str(e))



def get_conn():
    return psycopg2.connect(DATABASE_URL)


# Essa classe garante que o objeto de Python passe todos esses campos
class AddTransactionArgs(BaseModel):
    amount: float = Field(..., description="Valor da transação (use positivo).")
    source_text: str = Field(..., description="Texto original do usuário.")
    occurred_at: Optional[str] = Field(
        default=None,
        description="Timestamp ISO 8601; se ausente, usa NOW() no banco."
    )
    type_id: Optional[int] = Field(default=None, description="ID em transaction_types (1=INCOME, 2=EXPENSES, 3=TRANSFER).")
    type_name: Optional[str] = Field(default=None, description="Nome do tipo: INCOME | EXPENSES | TRANSFER.")
    category_id: Optional[int] = Field(default=None, description="FK de categories (opcional).")
    description: Optional[str] = Field(default=None, description="Descrição (opcional).")
    payment_method: Optional[str] = Field(default=None, description="Forma de pagamento (opcional).")


TYPE_ALIASES = {
    "INCOME": "INCOME", "ENTRADA": "INCOME", "RECEITA": "INCOME", "SALÁRIO": "INCOME",
    "EXPENSE": "EXPENSES", "EXPENSES": "EXPENSES", "DESPESA": "EXPENSES", "GASTO": "EXPENSES",
    "TRANSFER": "TRANSFER", "TRANSFERÊNCIA": "TRANSFER", "TRANSFERENCIA": "TRANSFER",
}


#Garante que o campo type da tabela transactions receba um id válido (1=INCOME, 2=EXPENSES, 3=TRANSFER
def _resolve_type_id(cur, type_id: Optional[int], type_name: Optional[str]) -> Optional[int]:
    if type_name:
        t = type_name.strip().upper()
        if t in TYPE_ALIASES:
            t = TYPE_ALIASES[t]
        cur.execute("SELECT id FROM transaction_types WHERE UPPER(type)=%s LIMIT 1;", (t,))
        row = cur.fetchone()
        return row[0] if row else None
    if type_id:
        return int(type_id)
    return 2


# Tool: add_transaction
@tool("add_transaction", args_schema=AddTransactionArgs)
def add_transaction(
    amount: float,
    source_text: str,
    occurred_at: Optional[str] = None,
    type_id: Optional[int] = None,
    type_name: Optional[str] = None,
    category_id: Optional[int] = None,
    description: Optional[str] = None,
    payment_method: Optional[str] = None,
) -> PgToolResponse:
    """Insere uma transação financeira no banco de dados Postgres.""" # docstring obrigatório da @tools do langchain (estranho, mas legal né?)
    with get_conn() as conn, conn.cursor() as cur:
        try:
            resolved_type_id = _resolve_type_id(cur, type_id, type_name)
            if not resolved_type_id:
                return PgToolResponse.error("Tipo inválido (use type_id ou type_name: INCOME/EXPENSES/TRANSFER).")

            if occurred_at:
                cur.execute(
                    """
                    INSERT INTO transactions
                        (amount, type, category_id, description, payment_method, occurred_at, source_text)
                    VALUES
                        (%s, %s, %s, %s, %s, %s::timestamptz, %s)
                    RETURNING id, occurred_at;
                    """,
                    (amount, resolved_type_id, category_id, description, payment_method, occurred_at, source_text),
                )
            else:
                cur.execute(
                    """
                    INSERT INTO transactions
                        (amount, type, category_id, description, payment_method, occurred_at, source_text)
                    VALUES
                        (%s, %s, %s, %s, %s, NOW(), %s)
                    RETURNING id, occurred_at;
                    """,
                    (amount, resolved_type_id, category_id, description, payment_method, source_text),
                )

            new_id, occurred = cur.fetchone()
            conn.commit()
            return PgToolResponse.ok({"id": new_id, "occurred_at": str(occurred)})

        except Exception as e:
            conn.rollback()
            return PgToolResponse.exception(e)

@tool("get_balance")
def get_balance() -> PgToolResponse:
    """Recupera do banco de dados o saldo atual a partir de todas as transações registradas"""
    with get_conn() as conn, conn.cursor() as cur:
        try:
            cur.execute('SELECT sum(amount) FROM transactions;')
            balance = cur.fetchone()[0]
            return PgToolResponse.ok({"balance": balance})
        except Exception as e:
            return PgToolResponse.exception(e)

# Exporta a lista de tools
TOOLS = [add_transaction, get_balance]
