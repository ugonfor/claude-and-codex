"""OAuth token discovery from Claude CLI and Codex CLI configs."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path


@dataclass
class AuthResult:
    """Result of an authentication attempt."""
    token: str
    source: str  # "oauth", "env", or "none"


def discover_claude_oauth() -> str | None:
    """Try to read Claude CLI OAuth token from ~/.claude/ config."""
    claude_dir = Path.home() / ".claude"
    if not claude_dir.exists():
        return None

    # Claude CLI stores credentials in various locations
    for config_name in ["credentials.json", "config.json", ".credentials"]:
        config_path = claude_dir / config_name
        if config_path.exists():
            try:
                data = json.loads(config_path.read_text(encoding="utf-8"))
                for key in ["apiKey", "api_key", "token", "oauth_token", "sessionKey"]:
                    if key in data and data[key]:
                        return data[key]
            except (json.JSONDecodeError, KeyError):
                continue

    return None


def discover_codex_oauth() -> str | None:
    """Read Codex CLI auth from ~/.codex/auth.json.

    Verified schema (from Codex's own review):
    {
        "auth_mode": "chatgpt",
        "OPENAI_API_KEY": <string|null>,
        "tokens": {
            "id_token": "<string>",
            "access_token": "<string>",
            "refresh_token": "<string>",
            "account_id": "<string>"
        },
        "last_refresh": "<string>"
    }

    NOTE: tokens.access_token is a ChatGPT OAuth token, NOT a standard
    OpenAI API key. For direct OpenAI API calls, only OPENAI_API_KEY works.
    """
    codex_home = Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex")))
    auth_path = codex_home / "auth.json"

    if not auth_path.exists():
        return None

    try:
        data = json.loads(auth_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None

    # Prefer explicit OPENAI_API_KEY if set and non-null
    api_key = data.get("OPENAI_API_KEY")
    if api_key:
        return api_key

    # tokens.access_token is a ChatGPT session token — not usable for
    # direct OpenAI API calls. Return None so we fall back to env var.
    return None


def resolve_anthropic_auth(env_key: str | None = None) -> AuthResult:
    """Resolve Anthropic API auth: OAuth first, then env var."""
    oauth_token = discover_claude_oauth()
    if oauth_token:
        return AuthResult(token=oauth_token, source="oauth")

    if env_key:
        return AuthResult(token=env_key, source="env")

    return AuthResult(token="", source="none")


def resolve_openai_auth(env_key: str | None = None) -> AuthResult:
    """Resolve OpenAI API auth: Codex config first, then env var."""
    codex_key = discover_codex_oauth()
    if codex_key:
        return AuthResult(token=codex_key, source="oauth")

    if env_key:
        return AuthResult(token=env_key, source="env")

    return AuthResult(token="", source="none")
