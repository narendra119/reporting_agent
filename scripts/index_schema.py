"""
index_schema.py — Fetch SQL Server schema and index it into Qdrant.

Run once at setup, and again whenever the schema changes:
    uv run python scripts/index_schema.py
"""

import sys
from collections import defaultdict
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# Allow imports from the project root
sys.path.insert(0, str(Path(__file__).parent.parent))

from services import db, memory

SCHEMA_QUERY = """
SELECT
    t.TABLE_SCHEMA,
    t.TABLE_NAME,
    c.COLUMN_NAME,
    c.DATA_TYPE,
    c.CHARACTER_MAXIMUM_LENGTH,
    c.IS_NULLABLE,
    ep_t.value  AS table_description,
    ep_c.value  AS column_description
FROM
    INFORMATION_SCHEMA.TABLES  t
    JOIN INFORMATION_SCHEMA.COLUMNS c
        ON  c.TABLE_SCHEMA = t.TABLE_SCHEMA
        AND c.TABLE_NAME   = t.TABLE_NAME
    -- table-level extended properties
    LEFT JOIN sys.extended_properties ep_t
        ON  ep_t.major_id   = OBJECT_ID(t.TABLE_SCHEMA + '.' + t.TABLE_NAME)
        AND ep_t.minor_id   = 0
        AND ep_t.name       = 'MS_Description'
    -- column-level extended properties
    LEFT JOIN sys.extended_properties ep_c
        ON  ep_c.major_id   = OBJECT_ID(t.TABLE_SCHEMA + '.' + t.TABLE_NAME)
        AND ep_c.minor_id   = COLUMNPROPERTY(
                                  OBJECT_ID(t.TABLE_SCHEMA + '.' + t.TABLE_NAME),
                                  c.COLUMN_NAME, 'ColumnId')
        AND ep_c.name       = 'MS_Description'
WHERE
    t.TABLE_TYPE = 'BASE TABLE'
ORDER BY
    t.TABLE_SCHEMA, t.TABLE_NAME, c.ORDINAL_POSITION
"""


def _col_type(data_type: str, max_len) -> str:
    if max_len and max_len != -1:
        return f"{data_type}({max_len})"
    return data_type


def fetch_schema() -> dict[str, dict]:
    """
    Returns a dict keyed by 'schema.table', each value:
        {
            "description": str | None,
            "columns": [{"name": str, "type": str, "nullable": bool, "description": str | None}]
        }
    """
    conn = db.connect()
    try:
        cursor = conn.cursor()
        cursor.execute(SCHEMA_QUERY)
        rows = cursor.fetchall()
    finally:
        conn.close()

    tables: dict[str, dict] = defaultdict(lambda: {"description": None, "columns": []})

    for row in rows:
        schema, table, col, dtype, max_len, nullable, tbl_desc, col_desc = row
        key = f"{schema}.{table}"
        if tables[key]["description"] is None and tbl_desc:
            tables[key]["description"] = str(tbl_desc)
        tables[key]["columns"].append({
            "name":        col,
            "type":        _col_type(dtype, max_len),
            "nullable":    nullable == "YES",
            "description": str(col_desc) if col_desc else None,
        })

    return tables


def format_chunk(table_key: str, info: dict) -> str:
    lines = [f"Table: {table_key}"]
    if info["description"]:
        lines.append(f"Description: {info['description']}")
    lines.append("Columns:")
    for col in info["columns"]:
        nullable = "" if col["nullable"] else " NOT NULL"
        desc     = f"  — {col['description']}" if col["description"] else ""
        lines.append(f"  - {col['name']}  {col['type']}{nullable}{desc}")
    return "\n".join(lines)


def main():
    print("Fetching schema from SQL Server...")
    tables = fetch_schema()
    print(f"Found {len(tables)} tables. Indexing into Qdrant...")

    chunks = [format_chunk(key, info) for key, info in tables.items()]
    indexed = memory.save(chunks)

    print(f"Done. {indexed} table(s) indexed.")


if __name__ == "__main__":
    main()
