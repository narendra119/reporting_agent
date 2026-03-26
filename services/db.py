import os

try:
    import pyodbc
    _PYODBC_AVAILABLE = True
except ImportError:
    _PYODBC_AVAILABLE = False


def connect():
    """Build a pyodbc connection from environment variables.

    Required env vars:
      APP_DB_HOST    — hostname or host\\INSTANCE
      APP_DB_NAME    — database name
      APP_DB_USER    — SQL Server username
      APP_DB_SECRET  — SQL Server password
      APP_DB_PORT    — port (optional, defaults to 1433)
    """
    if not _PYODBC_AVAILABLE:
        raise RuntimeError("pyodbc is not installed. Run `pip install pyodbc`.")

    host     = os.environ["APP_DB_HOST"]
    database = os.environ["APP_DB_NAME"]
    username = os.environ["APP_DB_USER"]
    password = os.environ["APP_DB_SECRET"]
    port     = os.getenv("APP_DB_PORT", "1433")

    conn_str = (
        f"DRIVER={{ODBC Driver 18 for SQL Server}};"
        f"SERVER={host},{port};DATABASE={database};UID={username};PWD={password};"
    )
    return pyodbc.connect(conn_str, timeout=15)


def query_sqlserver(query: str, row_limit: int = 100) -> str:
    if query.strip().split()[0].upper() != "SELECT":
        return "Error: only SELECT queries are permitted."

    conn = connect()
    try:
        cursor = conn.cursor()
        cursor.execute(query)
        columns = [col[0] for col in cursor.description]
        rows = cursor.fetchmany(row_limit)
    finally:
        conn.close()

    if not rows:
        return "(query returned no rows)"

    col_widths = [max(len(c), max((len(str(r[i])) for r in rows), default=0)) for i, c in enumerate(columns)]
    sep    = "  ".join("-" * w for w in col_widths)
    header = "  ".join(c.ljust(col_widths[i]) for i, c in enumerate(columns))
    lines  = [header, sep]
    for row in rows:
        lines.append("  ".join(str(v).ljust(col_widths[i]) for i, v in enumerate(row)))

    return "\n".join(lines) + f"\n({len(rows)} row(s) shown, limit={row_limit})"
