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
