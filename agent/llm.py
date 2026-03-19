from __future__ import annotations

from typing import Iterator

import anthropic
from dotenv import load_dotenv

load_dotenv()

Message = dict[str, str]  # {"role": "user"|"assistant"|"system", "content": "..."}


class LLM:
    def __init__(
        self,
        model: str = "claude-opus-4-6",
        system: str | None = None,
        max_tokens: int = 4096,
        temperature: float = 0,
    ) -> None:
        self.model = model
        self.system = system
        self.max_tokens = max_tokens
        self.temperature = temperature
        self._client = anthropic.Anthropic()

    def chat(self, messages: list[Message]) -> str:
        """Send messages and return the full response as a string."""
        with self._client.messages.stream(
            model=self.model,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            system=self.system,
            messages=messages,
        ) as stream:
            return stream.get_final_message().content[0].text

    def stream(self, messages: list[Message]) -> Iterator[str]:
        """Send messages and yield response text chunks as they arrive."""
        with self._client.messages.stream(
            model=self.model,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            system=self.system,
            messages=messages,
        ) as stream:
            yield from stream.text_stream

    def stream_respond(self, messages: list[Message], tools: list | None = None) -> anthropic.types.Message:
        """Stream text to stdout as it arrives, then return the full message (including tool use blocks)."""
        with self._client.messages.stream(
            model=self.model,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            system=self.system,
            messages=messages,
            **({"tools": tools} if tools else {}),
        ) as stream:
            for text in stream.text_stream:
                print(text, end="", flush=True)
            return stream.get_final_message()

    def respond(self, messages: list[Message], tools: list | None = None) -> anthropic.types.Message:
        """Return the raw API response. Used when tool use or stop_reason inspection is needed."""
        return self._client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            system=self.system,
            messages=messages,
            **({"tools": tools} if tools else {}),
        )
