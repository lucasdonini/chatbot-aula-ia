from psycopg2.extensions import cursor
from typing import Optional, Tuple

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


def resolve_type_id(
    cur: cursor, type_id: Optional[int] = None, type_name: Optional[str] = None
) -> int:
    if type_id:
        return int(type_id)

    if type_name:
        name: str = type_name.strip().upper()
        if name in TYPE_ALIASES:
            name = TYPE_ALIASES[name]

        cur.execute(
            "SELECT id FROM transaction_types WHERE UPPER(type)=%s LIMIT 1;", (name,)
        )
        row: Optional[Tuple[int]] = cur.fetchone()

        if not row:
            raise ValueError(
                f"Type (id={type_id}, name={type_name}) is not recognized. Try one of these: {TYPE_ALIASES.keys()}"
            )
        return row[0]

    return 2
