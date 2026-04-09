import os
from dotenv import load_dotenv
import psycopg2
from typing import Optional, List
from langchain.tools import tool
from pydantic import BaseModel, Field, model_validator
from datetime import date, timedelta

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


TYPE_ALIASES = {
    "INCOME": "INCOME",
    "ENTRADA": "INCOME",
    "RECEITA": "INCOME",
    "SALÁRIO": "INCOME",
    "EXPENSE": "EXPENSES",
    "EXPENSES": "EXPENSES",
    "DESPESA": "EXPENSES",
    "GASTO": "EXPENSES",
    "TRANSFER": "TRANSFER",
    "TRANSFERÊNCIA": "TRANSFER",
    "TRANSFERENCIA": "TRANSFER",
}


# Garante que o campo type da tabela transactions receba um id válido (1=INCOME, 2=EXPENSES, 3=TRANSFER
def _resolve_type_id(
    cur, type_id: Optional[int], type_name: Optional[str]
) -> Optional[int]:
    if type_name:
        t = type_name.strip().upper()
        if t in TYPE_ALIASES:
            t = TYPE_ALIASES[t]
        cur.execute(
            "SELECT id FROM transaction_types WHERE UPPER(type)=%s LIMIT 1;", (t,)
        )
        row = cur.fetchone()
        return row[0] if row else None
    if type_id:
        return int(type_id)
    return 2


def _resolve_category_id(
    cur, category_id: Optional[int], category_name: Optional[str]
) -> Optional[str]:
    if category_name:
        c = category_name.strip().lower()
        cur.execute("SELECT id FROM categories WHERE LOWER(name)=%s LIMIT 1;", (c,))
        return cur.fetchone()[0]
    if category_id:
        return int(category_id)
    return 12


# Tool: add_transaction
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
) -> PgToolResponse:
    """Insere uma transação financeira no banco de dados Postgres."""  # docstring obrigatório da @tools do langchain (estranho, mas legal né?)
    with get_conn() as conn, conn.cursor() as cur:
        try:
            resolved_type_id = _resolve_type_id(cur, type_id, type_name)
            if not resolved_type_id:
                return PgToolResponse.error(
                    "Tipo inválido (use type_id ou type_name: INCOME/EXPENSES/TRANSFER)."
                )

            resolved_category_id = _resolve_category_id(cur, category_id, category_name)
            if not resolved_category_id:
                return PgToolResponse.error(
                    "Categoria inválida (use category_id ou category_name: comida/besteira/estudo/férias/transporte/moradia/saúde/lazer/contas/investimento/presente/outros)"
                )

            if occurred_at:
                cur.execute(
                    """
                    INSERT INTO transactions
                        (amount, type, category_id, description, payment_method, occurred_at, source_text)
                    VALUES
                        (%s, %s, %s, %s, %s, %s::timestamptz, %s)
                    RETURNING id, occurred_at;
                    """,
                    (
                        amount,
                        resolved_type_id,
                        resolved_category_id,
                        description,
                        payment_method,
                        occurred_at,
                        source_text,
                    ),
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
                    (
                        amount,
                        resolved_type_id,
                        resolved_category_id,
                        description,
                        payment_method,
                        source_text,
                    ),
                )

            new_id, occurred = cur.fetchone()
            conn.commit()
            return PgToolResponse.ok({"id": new_id, "occurred_at": str(occurred)})

        except Exception as e:
            conn.rollback()
            return PgToolResponse.exception(e)


@tool("total_balance")
def total_balance() -> PgToolResponse:
    """Recupera do banco de dados o saldo atual a partir de todas as transações registradas"""
    with get_conn() as conn, conn.cursor() as cur:
        try:
            cur.execute("""
                SELECT sum(amount) 
                FROM transactions 
                WHERE type = 1""")
            income = cur.fetchone()[0]
            income = 0 if not income else income

            cur.execute("""
                SELECT sum(amount)
                FROM transactions
                WHERE type = 2""")
            expenses = cur.fetchone()[0]
            expenses = 0 if not expenses else expenses

            return PgToolResponse.ok({"saldo": income - expenses})
        except Exception as e:
            return PgToolResponse.exception(e)


class DailyBalanceArgs(BaseModel):
    target_date: date = Field(
        ...,
        description=(
            "Data de referência para o cálculo do saldo. "
            "O saldo retornado será o acumulado de todas as entradas (INCOME) "
            "e saídas (EXPENSES), ignorando transferências (TRANSFER)"
            "registradas ATÉ esse dia (inclusive). "
            "Exemplos: 'qual meu saldo hoje' → {hoje}, "
            "'qual era meu saldo no fim de março' → 2026-03-31."
        ),
    )


@tool("daily_balance", args_schema=DailyBalanceArgs)
def daily_balance(target_date: date) -> PgToolResponse:
    """
    Retorna o saldo (INCOME - EXPENSES) do dia local informado em America/Sao_Paulo.
    Ignora TRANSFER (type=3)
    """
    query_date = target_date + timedelta(days=1)
    with get_conn() as conn, conn.cursor() as cur:
        try:
            cur.execute(
                """
                SELECT coalesce(sum(amount), 0) 
                FROM transactions 
                WHERE type = 1 
                AND occurred_at < %s""",
                (query_date,),
            )
            income = cur.fetchone()[0]

            cur.execute(
                """
                SELECT coalesce(sum(amount), 0)
                FROM transactions
                WHERE type = 2
                AND occurred_at = %s""",
                (query_date,),
            )
            expenses = cur.fetchone()[0]

            return PgToolResponse.ok({"saldo_diario": income - expenses})
        except Exception as e:
            return PgToolResponse.exception(e)


class SearchTransactionsQueryArgs(BaseModel):
    source_text: Optional[str] = Field(
        default=None,
        description="Texto original da mensagem do usuário que gerou o registro. Inclua apenas quando tiver certeza de qual prompt gerou a transação.",
    )

    occurred_at_start: Optional[date] = Field(
        default=None,
        description="Data de início do intervalo de datas de transações alvo. Inclua quando quiser limitar um intervalo de datas.",
    )

    occurred_at_end: Optional[date] = Field(
        default=None,
        description=(
            "Data de término do intervalo (excludente). "
            "OBRIGATÓRIO SE o usuário mencionar um período com fim definido "
            "(ex: 'mês passado', 'semana passada', 'em março', 'no ano passado'). "
            "Exemplo: para 'mês passado' em abril/2026, passe 2026-04-01."
        ),
    )

    type: Optional[str] = Field(
        default=None,
        description="Nome do tipo: INCOME | EXPENSES | TRANSFER. Inclua quando estiver buscando um tipo de transação específico.",
    )

    category: Optional[str] = Field(
        default=None,
        description="Nome da categoria: comida | besteira | estudo | férias | transporte | moradia | saúde | lazer | contas | investimento | presente | outros. Inclua quando estiver buscando uma categoria específica.",
    )

    description: Optional[str] = Field(
        default=None,
        description="Descrição da transação. Pode ser necessário pesquisar várias vezes pois não é um parâmetro objetivo.",
    )

    limit: Optional[int] = Field(
        default=50,
        description="Número máximo de transações. Use 0 para sem limite. Para perguntas sobre 'maior' ou 'menor', use 0 ou um valor alto.",
    )


@tool("search_transactions", args_schema=SearchTransactionsQueryArgs)
def search_transactions(
    source_text: str = None,
    occurred_at_start: date = None,
    occurred_at_end: date = None,
    type: str = None,
    category: str = None,
    description: str = None,
    limit: int = 50,
) -> PgToolResponse:
    """
    Busca no banco de dados uma transação de acordo com os parâmetros passados.
    Caso nenhum parâmetro seja passado, retorna as útlimas 10 transações.
    Se a data de início for passada mas a de final não, retorna todas desde o início até hoje.
    Se a data de início não for passada mas a de final for, retora todas até a data de final.
    Buscar usando parâmetros como source_text e description pode ser ineficiente, uma vez que são
    textos humanos ou gerados pelo modelo, o que os torna menos padronizados.
    Buscas por source_text ou description fazem busca parcial para permitir que transações com description
    'fiz uma doação para ...' sejam retornadas buscando apenas por 'doação'.
    """
    with get_conn() as conn, conn.cursor() as cur:
        if limit < 0:
            return PgToolResponse.error("Limite inválido. Deve ser >= 0.")

        query = "SELECT * FROM transactions"
        where_conditions = []
        args = []

        if source_text:
            args.append(f"%{source_text}%")
            where_conditions.append("source_text = %s")

        if description:
            args.append(f"%{description}%")
            where_conditions.append("description ILIKE %s")

        try:
            if type:
                type_id = _resolve_type_id(cur=cur, type_name=type, type_id=None)
                args.append(type_id)
                where_conditions.append("type = %s")
        except Exception as e:
            return PgToolResponse.exception(e)

        try:
            if category:
                category_id = _resolve_category_id(
                    cur=cur, category_name=category, category_id=None
                )
                args.append(category_id)
                where_conditions.append("category_id = %s")
        except Exception as e:
            return PgToolResponse.exception(e)

        if occurred_at_start:
            args.append(occurred_at_start)
            where_conditions.append("occurred_at >= %s")

        if occurred_at_end:
            args.append(occurred_at_end)
            where_conditions.append("occurred_at < %s")

        if where_conditions:
            query += " WHERE " + " AND ".join(where_conditions)
        query += f' ORDER BY occurred_at {"DESC" if occurred_at_start or occurred_at_end else "ASC"} '
        if limit > 0:
            query += f"LIMIT {limit}"
        query += ";"

        try:
            cur.execute(query, tuple(args))
            return PgToolResponse.ok({"transactions": cur.fetchall()})
        except Exception as e:
            return PgToolResponse.exception(e)


class UpdateTransactionArgs(BaseModel):
    id: Optional[int] = Field(
        default=None,
        description="ID da transação a atualizar. Se ausente, será feita uma busca por (match_text + date_local).",
    )
    match_text: Optional[str] = Field(
        default=None,
        description="Texto para localizar transação quando id não for informado (busca em source_text/description).",
    )
    date_local: Optional[date] = Field(
        default=None,
        description="Data local (YYYY-MM-DD); usado em conjunto com match_text quando id ausente.",
    )
    amount: Optional[float] = Field(default=None, description="Novo valor.")
    type_id: Optional[int] = Field(default=None, description="Novo type_id (1/2/3).")
    type_name: Optional[str] = Field(
        default=None, description="Novo type_name: INCOME | EXPENSES | TRANSFER."
    )
    category_id: Optional[int] = Field(default=None, description="Nova categoria (id).")
    category_name: Optional[str] = Field(
        default=None, description="Nova categoria (nome)."
    )
    description: Optional[str] = Field(default=None, description="Nova descrição.")
    payment_method: Optional[str] = Field(
        default=None, description="Novo meio de pagamento."
    )
    occurred_at: Optional[str] = Field(
        default=None, description="Novo timestamp ISO 8601."
    )


@tool("update_transaction", args_schema=UpdateTransactionArgs)
def update_transaction(
    id: Optional[int] = None,
    match_text: Optional[str] = None,
    date_local: Optional[date] = None,
    amount: Optional[float] = None,
    type_id: Optional[int] = None,
    type_name: Optional[str] = None,
    category_id: Optional[int] = None,
    category_name: Optional[str] = None,
    description: Optional[str] = None,
    payment_method: Optional[str] = None,
    occurred_at: Optional[str] = None,
) -> PgToolResponse:
    """
    Atualiza uma transação existente.
    Estratégias:
      - Se 'id' for informado: atualiza diretamente por ID.
      - Caso contrário: localiza a transação mais recente que combine (match_text em source_text/description)
        E (date_local em America/Sao_Paulo), então atualiza.
    Retorna: status, rows_affected, id, e o registro atualizado.
    """
    if not any(
        [
            amount,
            type_id,
            type_name,
            category_id,
            category_name,
            description,
            payment_method,
            occurred_at,
        ]
    ):
        return PgToolResponse.error(
            "Nada para atualizar: forneça pelo menos um campo (amount, type, category, description, payment_method, occurred_at)."
        )

    with get_conn() as conn, conn.cursor() as cur:
        try:
            # Resolve target_id
            target_id = id
            if target_id is None:
                if not match_text or not date_local:
                    return {
                        "status": "error",
                        "message": "Sem 'id': informe match_text E date_local para localizar o registro.",
                    }

                # Buscar o mais recente no dia local informado que combine o texto
                date_end: date = date_local + timedelta(days=1)
                cur.execute(
                    f"""
                    SELECT t.id
                    FROM transactions t
                    WHERE (t.source_text ILIKE %s OR t.description ILIKE %s)
                        AND t.occurred_at >= %s
                        AND t.occurred_at < %s
                    ORDER BY t.occurred_at DESC
                    LIMIT 1;
                    """,
                    (f"%{match_text}%", f"%{match_text}%", date_local, date_end),
                )
                row = cur.fetchone()
                if not row:
                    return PgToolResponse.error(
                        "Nenhuma transação encontrada para os filtros fornecidos."
                    )
                target_id = row[0]

            # Resolver type_id / category_id a partir de nomes, se fornecidos
            resolved_type_id = (
                _resolve_type_id(cur, type_id, type_name)
                if (type_id or type_name)
                else None
            )
            resolved_category_id = category_id
            if category_name and not category_id:
                resolved_category_id = _resolve_category_id(cur, category_name)

            # Montar SET dinâmico
            sets = []
            params: List[object] = []
            if amount is not None:
                sets.append("amount = %s")
                params.append(amount)
            if resolved_type_id is not None:
                sets.append("type = %s")
                params.append(resolved_type_id)
            if resolved_category_id is not None:
                sets.append("category_id = %s")
                params.append(resolved_category_id)
            if description is not None:
                sets.append("description = %s")
                params.append(description)
            if payment_method is not None:
                sets.append("payment_method = %s")
                params.append(payment_method)
            if occurred_at is not None:
                sets.append("occurred_at = %s::timestamptz")
                params.append(occurred_at)

            if not sets:
                return PgToolResponse.error("Nenhum campo válido para atualizar.")

            params.append(target_id)

            cur.execute(
                f"UPDATE transactions SET {', '.join(sets)} WHERE id = %s;", params
            )
            rows_affected = cur.rowcount
            conn.commit()

            # Retornar o registro atualizado
            cur.execute(
                """
                SELECT
                t.id, t.occurred_at, t.amount, tt.type AS type_name,
                c.name AS category_name, t.description, t.payment_method, t.source_text
                FROM transactions t
                JOIN transaction_types tt ON tt.id = t.type
                LEFT JOIN categories c ON c.id = t.category_id
                WHERE t.id = %s;
                """,
                (target_id,),
            )
            r = cur.fetchone()
            updated = None
            if r:
                updated = {
                    "id": r[0],
                    "occurred_at": str(r[1]),
                    "amount": float(r[2]),
                    "type": r[3],
                    "category": r[4],
                    "description": r[5],
                    "payment_method": r[6],
                    "source_text": r[7],
                }

            return PgToolResponse.ok(
                {"rows_affected": rows_affected, "id": target_id, "updated": updated}
            )

        except Exception as e:
            conn.rollback()
            return PgToolResponse.exception(e)


# Exporta a lista de tools
TOOLS = [
    add_transaction,
    total_balance,
    daily_balance,
    search_transactions,
    update_transaction,
]
