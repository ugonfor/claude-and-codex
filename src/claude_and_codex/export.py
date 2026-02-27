"""Conversation export to JSONL and Markdown formats."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from .models import Message, Role


def to_jsonl(messages: list[Message]) -> str:
    """Export messages as JSONL (one JSON object per line)."""
    lines: list[str] = []
    for msg in messages:
        obj = {
            "role": msg.role.value,
            "content": msg.content,
            "timestamp": msg.timestamp.isoformat(),
            "message_id": msg.message_id,
            "is_complete": msg.is_complete,
        }
        if msg.tool_calls:
            obj["tool_calls"] = [
                {
                    "id": tc.id,
                    "name": tc.name,
                    "arguments": tc.arguments,
                    "result": tc.result,
                    "error": tc.error,
                }
                for tc in msg.tool_calls
            ]
        if msg.tool_owner is not None:
            obj["tool_owner"] = msg.tool_owner.value
        lines.append(json.dumps(obj, ensure_ascii=False))
    return "\n".join(lines)


_ROLE_LABELS = {
    Role.USER: "User",
    Role.CLAUDE: "Claude",
    Role.CODEX: "Codex",
    Role.SYSTEM: "System",
    Role.TOOL: "Tool",
}


def to_markdown(messages: list[Message]) -> str:
    """Export messages as human-readable Markdown."""
    parts: list[str] = []
    parts.append("# Conversation Export")
    if messages:
        parts.append(f"\n*Exported at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n")
    parts.append("---\n")

    for msg in messages:
        label = _ROLE_LABELS.get(msg.role, msg.role.value)
        ts = msg.timestamp.strftime("%H:%M:%S")
        parts.append(f"### {label} [{ts}]\n")
        if msg.content:
            parts.append(msg.content + "\n")

        for tc in msg.tool_calls:
            parts.append(f"\n> **Tool call**: `{tc.name}`")
            if tc.arguments:
                args_str = json.dumps(tc.arguments, indent=2, ensure_ascii=False)
                parts.append(f"> ```json\n> {args_str}\n> ```")
            if tc.result:
                preview = tc.result[:500]
                parts.append(f"> **Result**: {preview}")
            if tc.error:
                parts.append(f"> **Error**: {tc.error}")
            parts.append("")

        parts.append("---\n")

    return "\n".join(parts)


def export_conversation(
    messages: list[Message],
    output_dir: Path,
    fmt: str = "both",
) -> list[Path]:
    """Export conversation to file(s).

    Args:
        messages: Messages to export.
        output_dir: Directory to write files into.
        fmt: "jsonl", "markdown", or "both".

    Returns:
        List of created file paths.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    created: list[Path] = []

    if fmt in ("jsonl", "both"):
        path = output_dir / f"conversation_{stamp}.jsonl"
        path.write_text(to_jsonl(messages), encoding="utf-8")
        created.append(path)

    if fmt in ("markdown", "both"):
        path = output_dir / f"conversation_{stamp}.md"
        path.write_text(to_markdown(messages), encoding="utf-8")
        created.append(path)

    return created
