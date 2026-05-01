import logging

from src.infrastructure.db_connection import get_cursor

from .utils import resolve_type_id, resolve_category_id
from .response import DatabaseToolResponse
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, timedelta
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
) -> DatabaseToolResponse:
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
        return DatabaseToolResponse.error(
            "Nada para atualizar: forneça pelo menos um campo (amount, type, category, description, payment_method, occurred_at)."
        )

    try:
        with get_cursor() as cur:
            # Resolve target_id
            target_id = id
            if target_id is None:
                if not match_text or not date_local:
                    logger.error("No unique identifier provided")
                    return DatabaseToolResponse.error(
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
                row = cur.fetchone()
                if not row:
                    logger.error("No matching transaction foud to update")
                    return DatabaseToolResponse.error(
                        "Nenhuma transação encontrada para os filtros fornecidos."
                    )
                target_id = row[0]
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
            sets = []
            params: List[object] = []
            if amount is not None:
                sets.append("amount = %s")
                params.append(amount)
                logger.debug("amount added to UPDATE: %s", amount)

            if resolved_type_id is not None:
                sets.append("type = %s")
                params.append(resolved_type_id)
                logger.debug(
                    "type added to UPDATE: (%s, %s)", resolved_type_id, type_name
                )

            if resolved_category_id is not None:
                sets.append("category_id = %s")
                params.append(resolved_category_id)
                logger.debug(
                    "category added to UPDATE: (%s, %s)",
                    resolved_category_id,
                    category_name,
                )

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
                return DatabaseToolResponse.error("Nenhum campo válido para atualizar.")

            params.append(target_id)

            query = f"UPDATE transactions SET {', '.join(sets)} WHERE id = %s;"
            logger.debug("UPDATE query: %s", query)

            cur.execute(query, params)
            rows_affected = cur.rowcount
            logger.debug("Updated rows: %s", rows_affected)

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

            logger.info("Transaction updated successfully: %s", updated)
            return DatabaseToolResponse.ok(
                {"rows_affected": rows_affected, "id": target_id, "updated": updated}
            )

    except Exception as e:
        logger.exception("Exception rasied while updating transaction")
        return DatabaseToolResponse.exception(e)
