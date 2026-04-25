from src.infrastructure.db_connection import get_cursor

from .utils import resolve_category_id, resolve_type_id
from .response import DatabaseToolResponse
from pydantic import BaseModel, Field
from typing import Optional
from datetime import date
from langchain.tools import tool


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
) -> DatabaseToolResponse:
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
    try:
        with get_cursor() as cur:
            if limit < 0:
                return DatabaseToolResponse.error("Limite inválido. Deve ser >= 0.")

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
                    type_id = resolve_type_id(cur=cur, type_name=type, type_id=None)
                    args.append(type_id)
                    where_conditions.append("type = %s")
            except Exception as e:
                return DatabaseToolResponse.exception(e)

            try:
                if category:
                    category_id = resolve_category_id(
                        cur=cur, category_name=category, category_id=None
                    )
                    args.append(category_id)
                    where_conditions.append("category_id = %s")
            except Exception as e:
                return DatabaseToolResponse.exception(e)

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

            cur.execute(query, tuple(args))
            return DatabaseToolResponse.ok({"transactions": cur.fetchall()})
    except Exception as e:
        return DatabaseToolResponse.exception(e)
