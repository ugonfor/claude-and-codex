"""File write tool for agents."""

from __future__ import annotations

from pathlib import Path

from .registry import ToolDefinition

# Configured by the app at startup (P2 fix: resolve relative paths from working_directory)
_working_dir: Path = Path.cwd()


def configure(working_dir: Path) -> None:
    """Set the base directory for resolving relative paths."""
    global _working_dir
    _working_dir = working_dir


async def write_file(path: str, content: str) -> str:
    """Write content to a file, creating directories as needed."""
    p = Path(path)
    target = p if p.is_absolute() else (_working_dir / p).resolve()
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
