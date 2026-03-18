import json

from services import memory
from dotenv import load_dotenv

from .llm import LLM
from .tools import TOOLS, execute_tool
from .system_prompt import SYSTEM_PROMPT

load_dotenv()

llm = LLM(system=SYSTEM_PROMPT)

DESTRUCTIVE_TOOLS: set[str] = set()


def confirm(block) -> bool:
    """Prompt the user to confirm a destructive tool call. Returns True to proceed."""
    try:
        answer = input(f"  Allow {block.name}? [y/N] ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        answer = "n"
    return answer == "y"


MAX_ITERATIONS = 20


def _build_user_content(user_prompt: str) -> str:
    """Prepend relevant memory facts (if any) to the user message."""
    try:
        facts = memory.search(user_prompt, top_k=10)
    except Exception as e:
        facts = []
    if not facts:
        return user_prompt
    schema_block = "\n\n".join(facts)
    return f"## Relevant table schemas\n{schema_block}\n\n## Request\n{user_prompt}"


def run_agent(user_prompt: str, messages: list) -> list:
    messages.append({"role": "user", "content": _build_user_content(user_prompt)})

    for _ in range(MAX_ITERATIONS):
        print("\nAgent: ", end="", flush=True)
        response = llm.stream_respond(messages, tools=TOOLS)
        print()  # newline after streamed text

        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason == "end_turn":
            break

        if response.stop_reason == "tool_use":
            tool_results = []
            for block in response.content:
                if block.type != "tool_use":
                    continue
                print(f"  [tool] {block.name}({json.dumps(block.input)})")
                if block.name in DESTRUCTIVE_TOOLS and not confirm(block):
                    result = "User denied this action."
                else:
                    result = execute_tool(block.name, block.input)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result,
                })

            messages.append({"role": "user", "content": tool_results})
    else:
        print(f"\n[agent stopped: reached max iterations ({MAX_ITERATIONS})]")

    return messages


def main():
    print("Reporting Agent (type 'exit' to quit)\n")
    messages = []
    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not user_input:
            continue
        if user_input.lower() == "exit":
            print("Goodbye!")
            break

        messages = run_agent(user_input, messages)


if __name__ == "__main__":
    main()
