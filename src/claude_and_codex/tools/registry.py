"""Tool registry with dual-format export for Anthropic and OpenAI APIs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Awaitable


@dataclass
class ToolDefinition:
    name: str
    description: str
    parameters: dict[str, Any]  # JSON Schema
    execute: Callable[..., Awaitable[str]]

    def to_anthropic(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.parameters,
        }

    def to_openai(self) -> dict:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, ToolDefinition] = {}

    def register(self, tool: ToolDefinition) -> None:
        self._tools[tool.name] = tool

    def get(self, name: str) -> ToolDefinition | None:
        return self._tools.get(name)

    def all_anthropic(self) -> list[dict]:
        return [t.to_anthropic() for t in self._tools.values()]

    def all_openai(self) -> list[dict]:
        return [t.to_openai() for t in self._tools.values()]

    async def execute(self, name: str, arguments: dict[str, Any]) -> str:
        tool = self._tools.get(name)
        if tool is None:
            return f"Error: Unknown tool '{name}'"
        try:
            return await tool.execute(**arguments)
        except Exception as e:
            return f"Error executing {name}: {e}"
