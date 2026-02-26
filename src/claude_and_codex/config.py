"""Configuration management for claude-and-codex."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from .auth import resolve_anthropic_auth, resolve_openai_auth


@dataclass
class Config:
    anthropic_api_key: str = ""
    anthropic_auth_source: str = "none"
    openai_api_key: str = ""
    openai_auth_source: str = "none"
    claude_model: str = "claude-sonnet-4-20250514"
    codex_model: str = "gpt-4o"
    working_directory: Path = field(default_factory=Path.cwd)
    max_consecutive_agent_turns: int = 3
    agent_cooldown_seconds: float = 1.0
    max_tool_output_chars: int = 10000

    @classmethod
    def from_env(cls) -> Config:
        # Resolve auth with OAuth-first priority
        anthropic_auth = resolve_anthropic_auth(
            env_key=os.environ.get("ANTHROPIC_API_KEY"),
        )
        openai_auth = resolve_openai_auth(
            env_key=os.environ.get("OPENAI_API_KEY"),
        )

        return cls(
            anthropic_api_key=anthropic_auth.token,
            anthropic_auth_source=anthropic_auth.source,
            openai_api_key=openai_auth.token,
            openai_auth_source=openai_auth.source,
            claude_model=os.environ.get("CLAUDE_MODEL", "claude-sonnet-4-20250514"),
            codex_model=os.environ.get("CODEX_MODEL", "gpt-4o"),
            working_directory=Path(os.environ.get("WORKING_DIR", str(Path.cwd()))),
            max_consecutive_agent_turns=int(os.environ.get("MAX_AGENT_TURNS", "3")),
        )

    def validate(self) -> list[str]:
        errors = []
        if not self.anthropic_api_key:
            errors.append(
                "Anthropic API key not found. "
                "Set ANTHROPIC_API_KEY env var or login with `claude` CLI."
            )
        if not self.openai_api_key:
            errors.append(
                "OpenAI API key not found. "
                "Set OPENAI_API_KEY env var or login with `codex login`."
            )
        return errors

    def auth_summary(self) -> str:
        """Return a human-readable summary of auth sources."""
        parts = []
        parts.append(f"Claude: {self.anthropic_auth_source}")
        parts.append(f"Codex: {self.openai_auth_source}")
        return " | ".join(parts)
