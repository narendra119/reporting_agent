# Core Imports
import glob as glob_module
import os
import subprocess

# Third-Party Imports
from dotenv import load_dotenv
load_dotenv()

try:
    import pyodbc
    _PYODBC_AVAILABLE = True
except ImportError:
    _PYODBC_AVAILABLE = False

# Local Imports
from . import memory as _memory

TOOLS = [
    {
        "name": "read_file",
        "description": "Read the contents of a file.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path to the file"},
            },
            "required": ["path"],
        },
    },
    {
        "name": "write_file",
        "description": "Create or overwrite a file with the given content.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path to the file"},
                "content": {"type": "string", "description": "Content to write"},
            },
            "required": ["path", "content"],
        },
    },
    {
        "name": "edit_file",
        "description": "Replace an exact string in a file with new text.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "old_string": {"type": "string", "description": "Exact text to replace"},
                "new_string": {"type": "string", "description": "Replacement text"},
            },
            "required": ["path", "old_string", "new_string"],
        },
    },
    {
        "name": "delete_file",
        "description": "Delete a file.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
            },
            "required": ["path"],
        },
    },
    {
        "name": "list_files",
        "description": "List files in a directory.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Directory path (defaults to '.')"},
            },
            "required": [],
        },
    },
    {
        "name": "run_shell",
        "description": "Run a shell command and return its stdout and stderr. Use for executing code, running tests, installing packages, git operations, etc.",
        "input_schema": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "The shell command to run"},
                "cwd": {"type": "string", "description": "Working directory for the command (defaults to '.')"},
                "timeout": {"type": "integer", "description": "Timeout in seconds (defaults to 30)"},
            },
            "required": ["command"],
        },
    },
    {
        "name": "update_memory",
        "description": (
            "Save important facts about the project to long-term vector memory. "
            "Each fact is embedded and stored separately for semantic retrieval. "
            "Call this when you learn something worth remembering across sessions — "
            "e.g. tech stack, entry points, test commands, conventions, known issues. "
            "Pass concise, self-contained facts as individual list items."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "facts": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of concise facts to remember, e.g. ['Uses pytest for testing', 'Entry point is main.py', 'Python 3.10+']",
                },
            },
            "required": ["facts"],
        },
    },
    {
        "name": "glob_files",
        "description": "Find files matching a glob pattern (e.g. '**/*.py', 'src/**/*.ts'). Returns matching file paths sorted by modification time.",
        "input_schema": {
            "type": "object",
            "properties": {
                "pattern": {"type": "string", "description": "Glob pattern to match files against"},
                "directory": {"type": "string", "description": "Root directory to search from (defaults to '.')"},
            },
            "required": ["pattern"],
        },
    },
    {
        "name": "search_files",
        "description": "Recursively search for a string within files in a directory. Returns matching file paths, line numbers, and line content.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "String to search for"},
                "directory": {"type": "string", "description": "Directory to search in (defaults to '.')"},
                "extension": {"type": "string", "description": "Only search files with this extension, e.g. '.py' (optional)"},
            },
            "required": ["query"],
        },
    },
    {
        "name": "query_sqlserver",
        "description": (
            "Connect to a SQL Server database and execute a SELECT query. "
            "Use this to fetch, inspect, or analyze data from SQL Server. "
            "Only SELECT statements are permitted — no INSERT, UPDATE, DELETE, or DDL."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query":     {"type": "string",  "description": "The SELECT query to execute"},
                "row_limit": {"type": "integer", "description": "Max rows to return (default 100)"},
            },
            "required": ["query"],
        },
    },
    {
        "name": "ask_user",
        "description": (
            "Ask the user a clarifying question and wait for their response. "
            "Use this when you need additional information, context, or confirmation "
            "that cannot be inferred from the task or existing files — e.g. ambiguous requirements, "
            "missing credentials, preference between options, or unknown intent."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "question": {
                    "type": "string",
                    "description": "The question to ask the user. Be specific and concise.",
                },
            },
            "required": ["question"],
        },
    },
]


def read_file(path: str) -> str:
    with open(path) as f:
        return f.read()


def write_file(path: str, content: str) -> str:
    os.makedirs(os.path.dirname(path), exist_ok=True) if os.path.dirname(path) else None
    with open(path, "w") as f:
        f.write(content)
    return f"Written to {path}"


def edit_file(path: str, old_string: str, new_string: str) -> str:
    with open(path) as f:
        content = f.read()
    if old_string not in content:
        raise ValueError(f"String not found in {path}")
    with open(path, "w") as f:
        f.write(content.replace(old_string, new_string, 1))
    return f"Edited {path}"


def delete_file(path: str) -> str:
    os.remove(path)
    return f"Deleted {path}"


def list_files(path: str = ".") -> str:
    entries = []
    for root, dirs, files in os.walk(path):
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        level = root.replace(path, "").count(os.sep)
        indent = "  " * level
        entries.append(f"{indent}{os.path.basename(root)}/")
        for file in files:
            entries.append(f"{indent}  {file}")
    return "\n".join(entries)


def search_files(query, directory=".", extension=None):
    """
    Recursively searches for a string within files in a directory.
    Returns a list of matches with file paths and line numbers.
    """
    results = []
    for root, _, files in os.walk(directory):
        for file in files:
            if extension and not file.endswith(extension):
                continue

            file_path = os.path.join(root, file)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    for i, line in enumerate(f, 1):
                        if query in line:
                            results.append({
                                "file": file_path,
                                "line": i,
                                "content": line.strip()
                            })
            except (UnicodeDecodeError, PermissionError):
                continue
    return results


def update_memory(facts: list[str]) -> str:
    n = _memory.save(facts)
    return f"Saved {n} fact(s) to vector memory."


def glob_files(pattern: str, directory: str = ".") -> str:
    matches = glob_module.glob(os.path.join(directory, pattern), recursive=True)
    matches.sort(key=lambda p: os.path.getmtime(p), reverse=True)
    return "\n".join(matches) if matches else "(no matches)"


def _sqlserver_connect():
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
    # Safety: only allow SELECT statements
    if query.strip().split()[0].upper() != "SELECT":
        return "Error: only SELECT queries are permitted."

    conn = _sqlserver_connect()
    try:
        cursor = conn.cursor()
        cursor.execute(query)
        columns = [col[0] for col in cursor.description]
        rows = cursor.fetchmany(row_limit)
    finally:
        conn.close()

    if not rows:
        return "(query returned no rows)"

    # Format as a plain text table
    col_widths = [max(len(c), max((len(str(r[i])) for r in rows), default=0)) for i, c in enumerate(columns)]
    sep    = "  ".join("-" * w for w in col_widths)
    header = "  ".join(c.ljust(col_widths[i]) for i, c in enumerate(columns))
    lines  = [header, sep]
    for row in rows:
        lines.append("  ".join(str(v).ljust(col_widths[i]) for i, v in enumerate(row)))

    return "\n".join(lines) + f"\n({len(rows)} row(s) shown, limit={row_limit})"


def ask_user(question: str) -> str:
    print(f"\n[Agent needs clarification]\n{question}")
    answer = input("Your answer: ").strip()
    return answer or "(no answer provided)"


def run_shell(command: str, cwd: str = ".", timeout: int = 30) -> str:
    result = subprocess.run(
        command,
        shell=True,
        cwd=cwd,
        timeout=timeout,
        text=True,
        capture_output=True,
    )
    output = ""
    if result.stdout:
        output += result.stdout
    if result.stderr:
        output += result.stderr
    if result.returncode != 0:
        output += f"\n[exit code {result.returncode}]"
    return output or "(no output)"


def execute_tool(name: str, inputs: dict) -> str:
    try:
        match name:
            case "read_file":   return read_file(**inputs)
            case "write_file":  return write_file(**inputs)
            case "edit_file":   return edit_file(**inputs)
            case "delete_file": return delete_file(**inputs)
            case "update_memory": return update_memory(**inputs)
            case "glob_files":    return glob_files(**inputs)
            case "run_shell":     return run_shell(**inputs)
            case "list_files":    return list_files(**inputs)
            case "search_files":    return str(search_files(**inputs))
            case "query_sqlserver": return query_sqlserver(**inputs)
            case "ask_user":        return ask_user(**inputs)
            case _:               return f"Unknown tool: {name}"
    except Exception as e:
        return f"Error: {e}"
