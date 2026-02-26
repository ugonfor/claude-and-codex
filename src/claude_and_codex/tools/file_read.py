"""File read tool for agents."""

from __future__ import annotations

from pathlib import Path

from .registry import ToolDefinition


async def read_file(path: str, offset: int = 0, limit: int = 2000) -> str:
    """Read contents of a file with line numbers."""
    target = Path(path).resolve()
    if not target.exists():
        return f"Error: File not found: {path}"
    if not target.is_file():
        return f"Error: Not a file: {path}"
    try:
        lines = target.read_text(encoding="utf-8", errors="replace").splitlines()
        selected = lines[offset : offset + limit]
        numbered = [f"{i + offset + 1}: {line}" for i, line in enumerate(selected)]
        result = "\n".join(numbered)
        if len(lines) > offset + limit:
            result += f"\n... ({len(lines) - offset - limit} more lines)"
        return result
    except Exception as e:
        return f"Error reading file: {e}"


file_read_tool = ToolDefinition(
    name="read_file",
    description="Read the contents of a file. Returns numbered lines.",
    parameters={
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Absolute or relative file path to read",
            },
            "offset": {
                "type": "integer",
                "description": "Line offset to start from (0-based)",
                "default": 0,
            },
            "limit": {
                "type": "integer",
                "description": "Maximum number of lines to read",
                "default": 2000,
            },
        },
        "required": ["path"],
    },
    execute=read_file,
)
