"""Shell command execution tool for agents."""

from __future__ import annotations

import asyncio
from pathlib import Path

from .registry import ToolDefinition

# Will be set by the app at startup
_working_dir: Path = Path.cwd()
_max_output_chars: int = 10000


def configure(working_dir: Path, max_output_chars: int = 10000) -> None:
    """Configure the shell tool's working directory and output limits."""
    global _working_dir, _max_output_chars
    _working_dir = working_dir
    _max_output_chars = max_output_chars


async def execute_shell(command: str, timeout: int = 30) -> str:
    """Execute a shell command and return stdout + stderr."""
    try:
        proc = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(_working_dir),
        )
        stdout, stderr = await asyncio.wait_for(
            proc.communicate(), timeout=timeout
        )
        output = ""
        if stdout:
            output += stdout.decode(errors="replace")
        if stderr:
            output += "\n[stderr]\n" + stderr.decode(errors="replace")
        output += f"\n[exit code: {proc.returncode}]"
        return output[:_max_output_chars]
    except asyncio.TimeoutError:
        proc.kill()  # type: ignore[possibly-undefined]
        await proc.wait()  # type: ignore[possibly-undefined]
        return f"Error: Command timed out after {timeout}s"
    except Exception as e:
        return f"Error executing command: {e}"


shell_exec_tool = ToolDefinition(
    name="execute_shell",
    description="Execute a shell command. Returns stdout, stderr, and exit code.",
    parameters={
        "type": "object",
        "properties": {
            "command": {
                "type": "string",
                "description": "Shell command to execute",
            },
            "timeout": {
                "type": "integer",
                "description": "Timeout in seconds (default 30)",
                "default": 30,
            },
        },
        "required": ["command"],
    },
    execute=execute_shell,
)
