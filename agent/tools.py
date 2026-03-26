import os

from services import db, memory as _memory

TOOLS = [
    {
        "name": "search",
        "description": (
            "Search for data across different sources. "
            "Set type='db' to run a SELECT query against SQL Server. "
            "Only SELECT statements are permitted for db searches."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "type":      {"type": "string",  "description": "The search source. Supported values: 'db'"},
                "query":     {"type": "string",  "description": "The search query (e.g. a SELECT statement for type='db')"},
                "row_limit": {"type": "integer", "description": "Max rows to return for db searches (default 100)"},
            },
            "required": ["type", "query"],
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


def search(type: str, query: str, row_limit: int = 100) -> str:
    match type:
        case "db": return db.query_sqlserver(query, row_limit)
        case _:    return f"Error: unsupported search type '{type}'"


def ask_user(question: str) -> str:
    print(f"\n[Agent needs clarification]\n{question}")
    answer = input("Your answer: ").strip()
    return answer or "(no answer provided)"


def execute_tool(name: str, inputs: dict) -> str:
    try:
        match name:
            case "search":          return search(**inputs)
            case "write_file":      return write_file(**inputs)
            case "read_file":       return read_file(**inputs)
            case "update_memory":   return update_memory(**inputs)
            case "ask_user":        return ask_user(**inputs)
            case _:                 return f"Unknown tool: {name}"
    except Exception as e:
        return f"Error: {e}"
