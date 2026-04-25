from psycopg2.extensions import cursor
from typing import Optional, Tuple


def resolve_category_id(
    cur: cursor, category_id: Optional[int], category_name: Optional[str]
) -> Optional[str]:
    if category_id:
        return int(category_id)

    if category_name:
        name = category_name.strip().lower()
        cur.execute("SELECT id FROM categories WHERE LOWER(name)=%s LIMIT 1;", (name,))

        row: Optional[Tuple[int]] = cur.fetchone()
        if not row:
            raise ValueError(
                f"Categroy (id={category_id}, name={category_name}) is not recognized."
            )
        return row[0]

    return 12
