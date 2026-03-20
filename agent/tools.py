import os

from services import db, memory as _memory

TOOLS = [
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
        "name": "write_file",
        "description": "Save report output to a file.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path":    {"type": "string", "description": "Path to the file"},
                "content": {"type": "string", "description": "Content to write"},
            },
            "required": ["path", "content"],
        },
    },
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
        "name": "update_memory",
        "description": (
            "Save important facts to long-term vector memory for retrieval in future sessions. "
            "Use this when you learn something worth remembering — "
            "e.g. table names, schema details, business definitions, known data quirks, preferred report formats. "
            "Pass concise, self-contained facts as individual list items."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "facts": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of concise facts to remember.",
                },
            },
            "required": ["facts"],
        },
    },
    {
        "name": "ask_user",
        "description": (
            "Ask the user a clarifying question and wait for their response. "
            "Use this when the request is ambiguous, a date range is unspecified, "
            "or a preference between options is needed."
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


def update_memory(facts: list[str]) -> str:
    n = _memory.save(facts)
    return f"Saved {n} fact(s) to vector memory."


def query_sqlserver(query: str, row_limit: int = 100) -> str:
    if query.strip().split()[0].upper() != "SELECT":
        return "Error: only SELECT queries are permitted."

    conn = db.connect()
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


def ask_user(question: str) -> str:
    print(f"\n[Agent needs clarification]\n{question}")
    answer = input("Your answer: ").strip()
    return answer or "(no answer provided)"


def execute_tool(name: str, inputs: dict) -> str:
    try:
        match name:
            case "query_sqlserver": return query_sqlserver(**inputs)
            case "write_file":      return write_file(**inputs)
            case "read_file":       return read_file(**inputs)
            case "update_memory":   return update_memory(**inputs)
            case "ask_user":        return ask_user(**inputs)
            case _:                 return f"Unknown tool: {name}"
    except Exception as e:
        return f"Error: {e}"
