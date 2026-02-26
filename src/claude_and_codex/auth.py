"""OAuth token discovery from Claude CLI and Codex CLI configs."""

from __future__ import annotations

import json
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
    # Check common config files
    for config_name in ["credentials.json", "config.json", ".credentials"]:
        config_path = claude_dir / config_name
        if config_path.exists():
            try:
                data = json.loads(config_path.read_text(encoding="utf-8"))
                # Look for API key or OAuth token fields
                for key in ["apiKey", "api_key", "token", "oauth_token", "sessionKey"]:
                    if key in data and data[key]:
                        return data[key]
            except (json.JSONDecodeError, KeyError):
                continue

    return None


def discover_codex_oauth() -> str | None:
    """Try to read Codex CLI OAuth token from ~/.codex/ config."""
    codex_dir = Path.home() / ".codex"
    if not codex_dir.exists():
        return None

    # Codex CLI uses config.toml or config.json
    toml_path = codex_dir / "config.toml"
    if toml_path.exists():
        try:
            import tomllib
            data = tomllib.loads(toml_path.read_text(encoding="utf-8"))
            for key in ["api_key", "token", "oauth_token"]:
                if key in data and data[key]:
                    return data[key]
            # Check nested auth section
            auth = data.get("auth", {})
            for key in ["api_key", "token", "oauth_token"]:
                if key in auth and auth[key]:
                    return auth[key]
        except Exception:
            pass

    json_path = codex_dir / "config.json"
    if json_path.exists():
        try:
            data = json.loads(json_path.read_text(encoding="utf-8"))
            for key in ["apiKey", "api_key", "token", "oauth_token"]:
                if key in data and data[key]:
                    return data[key]
        except (json.JSONDecodeError, KeyError):
            pass

    return None


def resolve_anthropic_auth(env_key: str | None = None) -> AuthResult:
    """Resolve Anthropic API auth: OAuth first, then env var."""
    # Try OAuth
    oauth_token = discover_claude_oauth()
    if oauth_token:
        return AuthResult(token=oauth_token, source="oauth")

    # Fall back to env var
    if env_key:
        return AuthResult(token=env_key, source="env")

    return AuthResult(token="", source="none")


def resolve_openai_auth(env_key: str | None = None) -> AuthResult:
    """Resolve OpenAI API auth: OAuth first, then env var."""
    # Try OAuth
    oauth_token = discover_codex_oauth()
    if oauth_token:
        return AuthResult(token=oauth_token, source="oauth")

    # Fall back to env var
    if env_key:
        return AuthResult(token=env_key, source="env")

    return AuthResult(token="", source="none")
