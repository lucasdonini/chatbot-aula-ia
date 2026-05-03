import logging

from src.model.common.tool_response import ToolResponse
from src.infrastructure.db_connection import get_cursor
from .utils import resolve_type_id, resolve_category_id

from pydantic import BaseModel, Field
from typing import Optional, List, TypedDict
from datetime import date, timedelta
from psycopg2.extensions import cursor

from langchain.tools import tool

logger = logging.getLogger(__name__)


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


def _locate_target_ids(
    cur: cursor, match_text: Optional[str], date_local: Optional[date]
) -> List[int]:
    if not match_text or not date_local:
        logger.error("No unique identifier provided")
        raise ValueError(
            "Sem 'id': informe match_text E date_local para localizar o registro."
        )

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
    rows = cur.fetchall()
    if not rows or len(rows) < 1:
        logger.error("No matching transaction foud to update")
        raise ValueError("Nenhuma transação encontrada para os filtros fornecidos.")

    return [row[0] for row in rows]


class DynamicSet(TypedDict):
    query: str
    values: List[object]


def _prepare_dinamic_set(
    id: int,
    amount: Optional[float],
    type_id: Optional[int],
    category_id: Optional[int],
    description: Optional[str],
    payment_method: Optional[str],
    occurred_at: Optional[str],
) -> DynamicSet:
    sets = []
    params: List[object] = []
    if amount is not None:
        sets.append("amount = %s")
        params.append(amount)
        logger.debug("amount added to UPDATE: %s", amount)

    if type_id is not None:
        sets.append("type = %s")
        params.append(type_id)
        logger.debug("type id added to UPDATE: %s", type_id)

    if category_id is not None:
        sets.append("category_id = %s")
        params.append(category_id)
        logger.debug("category id added to UPDATE: %s", category_id)

    if description is not None:
        sets.append("description = %s")
        params.append(description)
        logger.debug("description added to UPDATE> %s", description)

    if payment_method is not None:
        sets.append("payment_method = %s")
        params.append(payment_method)
        logger.debug("payment_method added to UPDATE: %s", payment_method)

    if occurred_at is not None:
        sets.append("occurred_at = %s::timestamptz")
        params.append(occurred_at)
        logger.debug("occurred_at added to UPDATE: %s", occurred_at)

    if not sets:
        logger.error("Tried to update nothing")
        raise ValueError("Nenhum campo válido para atualizar.")

    query = f"UPDATE transactions SET {', '.join(sets)} WHERE id = %s;"
    params.append(id)

    return {"query": query, "values": params}


def _get_transaction_by_id(cur: cursor, id: int) -> dict:
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
        (id,),
    )
    r = cur.fetchone()
    return (
        None
        if not r
        else {
            "id": r[0],
            "occurred_at": str(r[1]),
            "amount": float(r[2]),
            "type": r[3],
            "category": r[4],
            "description": r[5],
            "payment_method": r[6],
            "source_text": r[7],
        }
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
) -> ToolResponse:
    """
    Atualiza uma transação existente.
    Estratégias:
      - Se 'id' for informado: atualiza diretamente por ID.
      - Caso contrário: localiza a transação mais recente que combine (match_text em source_text/description)
        E (date_local em America/Sao_Paulo), então atualiza.
    Retorna: status, rows_affected, id, e o registro atualizado.
    """
    logger.info("update_transaction tool called")
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
        logger.error("Tried to update nothing")
        return ToolResponse.error(
            "Nada para atualizar: forneça pelo menos um campo (amount, type, category, description, payment_method, occurred_at)."
        )

    try:
        with get_cursor() as cur:
            # Resolve target_id
            target_id = id
            if target_id is None:
                target_ids = _locate_target_ids(cur, match_text, date_local)
                if len(target_ids) > 1:
                    found_transactions = [
                        _get_transaction_by_id(id) for id in target_ids
                    ]
                    logger.error(
                        "More than one transaction located by update filters: ids=%s",
                        target_ids,
                    )
                    return ToolResponse.error(
                        msg="Mais de uma transação encontrada pelos filtros.",
                        details={"transacoes": found_transactions},
                    )
                target_id = target_ids[0]
                logger.debug("Update target transaction: id=%s", target_id)

            # Resolver type_id / category_id a partir de nomes, se fornecidos
            resolved_type_id = (
                resolve_type_id(cur, type_id, type_name)
                if (type_id or type_name)
                else None
            )
            logger.debug("Resolved type id: %s", resolved_type_id)

            resolved_category_id = category_id
            if category_name and not category_id:
                resolved_category_id = resolve_category_id(cur, category_name)
            logger.debug("Resolved category id: %s")

            # Montar SET dinâmico
            dynamic_set = _prepare_dinamic_set(
                id=target_id,
                amount=amount,
                type_id=resolved_type_id,
                category_id=resolved_category_id,
                description=description,
                payment_method=payment_method,
                occurred_at=occurred_at,
            )
            logger.debug("UPDATE query: %s", dynamic_set["query"])

            cur.execute(dynamic_set["query"], dynamic_set["values"])
            rows_affected = cur.rowcount
            logger.debug("Updated rows: %s", rows_affected)

            # Retornar o registro atualizado
            updated = _get_transaction_by_id(cur, target_id)
            logger.info("Transaction updated successfully: %s", updated)
            return ToolResponse.ok(
                {"rows_affected": rows_affected, "id": target_id, "updated": updated}
            )

    except Exception as e:
        logger.exception("Exception rasied while updating transaction")
        return ToolResponse.exception(e)
