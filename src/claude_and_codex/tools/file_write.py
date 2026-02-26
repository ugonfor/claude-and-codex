"""File write tool for agents."""

from __future__ import annotations

from pathlib import Path

from .registry import ToolDefinition


async def write_file(path: str, content: str) -> str:
    """Write content to a file, creating directories as needed."""
    target = Path(path).resolve()
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return f"Successfully wrote {len(content)} characters to {path}"
    except Exception as e:
        return f"Error writing file: {e}"


file_write_tool = ToolDefinition(
    name="write_file",
    description="Write content to a file. Creates parent directories if needed.",
    parameters={
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "File path to write to",
            },
            "content": {
                "type": "string",
                "description": "Content to write to the file",
            },
        },
        "required": ["path", "content"],
    },
    execute=write_file,
)
