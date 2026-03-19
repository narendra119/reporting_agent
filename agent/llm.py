from __future__ import annotations

import json
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Iterator

import anthropic
from dotenv import load_dotenv

load_dotenv()

Message = dict  # {"role": "user"|"assistant", "content": str | list}

# ---------------------------------------------------------------------------
# Normalized types returned by all backends
# ---------------------------------------------------------------------------

@dataclass
class ContentBlock:
    type: str          # "text" or "tool_use"
    text: str | None = None
    id: str | None = None
    name: str | None = None
    input: dict | None = None


@dataclass
class LLMResponse:
    stop_reason: str   # "end_turn" or "tool_use"
    content: list[ContentBlock]


# ---------------------------------------------------------------------------
# Registry + factory
# ---------------------------------------------------------------------------

_REGISTRY: dict[str, type[BaseLLM]] = {}


def _register(*prefixes: str):
    """Class decorator that registers a backend for one or more model-name prefixes."""
    def decorator(cls: type[BaseLLM]) -> type[BaseLLM]:
        for prefix in prefixes:
            _REGISTRY[prefix] = cls
        return cls
    return decorator


def LLM(model: str = "claude-opus-4-6", **kwargs) -> BaseLLM:
    """Factory: returns the right backend based on the model name prefix."""
    for prefix, cls in _REGISTRY.items():
        if model.startswith(prefix):
            return cls(model=model, **kwargs)
    raise ValueError(f"No LLM backend registered for model {model!r}")


# ---------------------------------------------------------------------------
# Abstract base
# ---------------------------------------------------------------------------

class BaseLLM(ABC):
    def __init__(
        self,
        model: str,
        system: str | None = None,
        max_tokens: int = 4096,
        temperature: float = 0,
    ) -> None:
        self.model = model
        self.system = system
        self.max_tokens = max_tokens
        self.temperature = temperature

    @abstractmethod
    def chat(self, messages: list[Message]) -> str: ...

    @abstractmethod
    def stream(self, messages: list[Message]) -> Iterator[str]: ...

    @abstractmethod
    def stream_respond(self, messages: list[Message], tools: list | None = None) -> LLMResponse: ...

    @abstractmethod
    def respond(self, messages: list[Message], tools: list | None = None) -> LLMResponse: ...


# ---------------------------------------------------------------------------
# Anthropic backend
# ---------------------------------------------------------------------------

@_register("claude")
class AnthropicLLM(BaseLLM):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._client = anthropic.Anthropic()

    # -- format helpers ------------------------------------------------------

    def _to_api_messages(self, messages: list[Message]) -> list:
        """Convert normalized messages (may contain ContentBlock objects) to Anthropic wire format."""
        result = []
        for m in messages:
            content = m["content"]
            if not isinstance(content, list):
                result.append(m)
                continue
            converted = []
            for item in content:
                if isinstance(item, ContentBlock):
                    if item.type == "text":
                        converted.append({"type": "text", "text": item.text})
                    elif item.type == "tool_use":
                        converted.append({"type": "tool_use", "id": item.id, "name": item.name, "input": item.input})
                else:
                    converted.append(item)  # tool_result dicts pass through unchanged
            result.append({"role": m["role"], "content": converted})
        return result

    def _from_api_response(self, message: anthropic.types.Message) -> LLMResponse:
        blocks = []
        for block in message.content:
            if block.type == "text":
                blocks.append(ContentBlock(type="text", text=block.text))
            elif block.type == "tool_use":
                blocks.append(ContentBlock(type="tool_use", id=block.id, name=block.name, input=block.input))
        stop = "end_turn" if message.stop_reason == "end_turn" else "tool_use"
        return LLMResponse(stop_reason=stop, content=blocks)

    # -- public interface ----------------------------------------------------

    def chat(self, messages: list[Message]) -> str:
        with self._client.messages.stream(
            model=self.model, max_tokens=self.max_tokens, temperature=self.temperature,
            system=self.system, messages=self._to_api_messages(messages),
        ) as stream:
            return stream.get_final_message().content[0].text

    def stream(self, messages: list[Message]) -> Iterator[str]:
        with self._client.messages.stream(
            model=self.model, max_tokens=self.max_tokens, temperature=self.temperature,
            system=self.system, messages=self._to_api_messages(messages),
        ) as stream:
            yield from stream.text_stream

    def stream_respond(self, messages: list[Message], tools: list | None = None) -> LLMResponse:
        with self._client.messages.stream(
            model=self.model, max_tokens=self.max_tokens, temperature=self.temperature,
            system=self.system, messages=self._to_api_messages(messages),
            **({"tools": tools} if tools else {}),
        ) as stream:
            for text in stream.text_stream:
                print(text, end="", flush=True)
            return self._from_api_response(stream.get_final_message())

    def respond(self, messages: list[Message], tools: list | None = None) -> LLMResponse:
        msg = self._client.messages.create(
            model=self.model, max_tokens=self.max_tokens, temperature=self.temperature,
            system=self.system, messages=self._to_api_messages(messages),
            **({"tools": tools} if tools else {}),
        )
        return self._from_api_response(msg)


# ---------------------------------------------------------------------------
# Grok (xAI) backend  —  OpenAI-compatible API
# ---------------------------------------------------------------------------

@_register("grok")
class GrokLLM(BaseLLM):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        from openai import OpenAI
        self._client = OpenAI(
            base_url="https://api.x.ai/v1",
            api_key=os.environ["XAI_API_KEY"],
        )

    # -- format helpers ------------------------------------------------------

    def _to_api_messages(self, messages: list[Message]) -> list:
        """Convert normalized messages to OpenAI wire format."""
        result = []
        if self.system:
            result.append({"role": "system", "content": self.system})
        for m in messages:
            role, content = m["role"], m["content"]
            if isinstance(content, str):
                result.append({"role": role, "content": content})
                continue
            # user message carrying tool results
            if role == "user" and all(isinstance(i, dict) and i.get("type") == "tool_result" for i in content):
                for item in content:
                    result.append({"role": "tool", "tool_call_id": item["tool_use_id"], "content": item["content"]})
                continue
            # assistant message with ContentBlock list
            text_parts, tool_calls = [], []
            for item in content:
                if isinstance(item, ContentBlock):
                    if item.type == "text" and item.text:
                        text_parts.append(item.text)
                    elif item.type == "tool_use":
                        tool_calls.append({
                            "id": item.id,
                            "type": "function",
                            "function": {"name": item.name, "arguments": json.dumps(item.input or {})},
                        })
            msg: dict = {"role": "assistant", "content": " ".join(text_parts) or ""}
            if tool_calls:
                msg["tool_calls"] = tool_calls
            result.append(msg)
        return result

    def _to_api_tools(self, tools: list) -> list:
        """Convert Anthropic-style tool defs to OpenAI function format."""
        return [
            {
                "type": "function",
                "function": {
                    "name": t["name"],
                    "description": t.get("description", ""),
                    "parameters": t.get("input_schema", {}),
                },
            }
            for t in tools
        ]

    def _from_api_response(self, response) -> LLMResponse:
        choice = response.choices[0]
        msg = choice.message
        blocks = []
        if msg.content:
            blocks.append(ContentBlock(type="text", text=msg.content))
        for tc in msg.tool_calls or []:
            blocks.append(ContentBlock(
                type="tool_use", id=tc.id,
                name=tc.function.name,
                input=json.loads(tc.function.arguments),
            ))
        stop = "tool_use" if choice.finish_reason == "tool_calls" else "end_turn"
        return LLMResponse(stop_reason=stop, content=blocks)

    # -- public interface ----------------------------------------------------

    def chat(self, messages: list[Message]) -> str:
        response = self._client.chat.completions.create(
            model=self.model, max_tokens=self.max_tokens, temperature=self.temperature,
            messages=self._to_api_messages(messages),
        )
        return response.choices[0].message.content

    def stream(self, messages: list[Message]) -> Iterator[str]:
        stream = self._client.chat.completions.create(
            model=self.model, max_tokens=self.max_tokens, temperature=self.temperature,
            messages=self._to_api_messages(messages), stream=True,
        )
        for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta

    def stream_respond(self, messages: list[Message], tools: list | None = None) -> LLMResponse:
        stream = self._client.chat.completions.create(
            model=self.model, max_tokens=self.max_tokens, temperature=self.temperature,
            messages=self._to_api_messages(messages),
            **({"tools": self._to_api_tools(tools)} if tools else {}),
            stream=True,
        )
        text_buf = ""
        tool_calls_buf: list[dict] = []
        finish_reason = None

        for chunk in stream:
            choice = chunk.choices[0]
            if choice.delta.content:
                print(choice.delta.content, end="", flush=True)
                text_buf += choice.delta.content
            for tc_delta in choice.delta.tool_calls or []:
                while len(tool_calls_buf) <= tc_delta.index:
                    tool_calls_buf.append({"id": "", "name": "", "arguments": ""})
                entry = tool_calls_buf[tc_delta.index]
                if tc_delta.id:
                    entry["id"] = tc_delta.id
                if tc_delta.function.name:
                    entry["name"] = tc_delta.function.name
                if tc_delta.function.arguments:
                    entry["arguments"] += tc_delta.function.arguments
            if choice.finish_reason:
                finish_reason = choice.finish_reason

        blocks = []
        if text_buf:
            blocks.append(ContentBlock(type="text", text=text_buf))
        for tc in tool_calls_buf:
            blocks.append(ContentBlock(type="tool_use", id=tc["id"], name=tc["name"], input=json.loads(tc["arguments"])))
        stop = "tool_use" if finish_reason == "tool_calls" else "end_turn"
        return LLMResponse(stop_reason=stop, content=blocks)

    def respond(self, messages: list[Message], tools: list | None = None) -> LLMResponse:
        response = self._client.chat.completions.create(
            model=self.model, max_tokens=self.max_tokens, temperature=self.temperature,
            messages=self._to_api_messages(messages),
            **({"tools": self._to_api_tools(tools)} if tools else {}),
        )
        return self._from_api_response(response)
