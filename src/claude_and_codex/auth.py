"""OAuth token discovery from Claude CLI and Codex CLI configs."""

from __future__ import annotations

import json
import os
import platform
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass
class AuthResult:
    """Result of an authentication attempt."""
    token: str
    source: str  # "keychain", "oauth", "env", or "none"


@dataclass
class CodexAuthResult:
    """Codex uses ChatGPT OAuth which requires special handling."""
    access_token: str
    account_id: str
    source: str  # "chatgpt_oauth", "env", or "none"

    @property
    def is_chatgpt_oauth(self) -> bool:
        return self.source == "chatgpt_oauth"


def discover_claude_keychain() -> str | None:
    """Read Claude Code API key from OS credential store.

    - macOS: Keychain via `security` CLI
    - Windows: Windows Credential Manager via PowerShell
    - Linux: libsecret via `secret-tool` CLI
    """
    system = platform.system()

    if system == "Darwin":
        try:
            result = subprocess.run(
                ["security", "find-generic-password", "-s", "Claude Code", "-w"],
                capture_output=True, text=True, timeout=5,
            )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
        except (subprocess.SubprocessError, FileNotFoundError):
            pass

    elif system == "Windows":
        # Windows Credential Manager via PowerShell
        ps_cmd = (
            "(Get-StoredCredential -Target 'Claude Code' "
            "-ErrorAction SilentlyContinue).Password | "
            "ConvertFrom-SecureString -AsPlainText"
        )
        try:
            result = subprocess.run(
                ["powershell", "-NoProfile", "-Command", ps_cmd],
                capture_output=True, text=True, timeout=5,
            )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
        except (subprocess.SubprocessError, FileNotFoundError):
            pass

        # Fallback: try cmdkey-based approach
        try:
            result = subprocess.run(
                ["cmdkey", "/list:Claude Code"],
                capture_output=True, text=True, timeout=5,
            )
            # cmdkey lists but can't retrieve passwords; if credential exists,
            # the user likely has ANTHROPIC_API_KEY set or uses file-based auth
        except (subprocess.SubprocessError, FileNotFoundError):
            pass

    elif system == "Linux":
        # libsecret via secret-tool (GNOME Keyring / KDE Wallet)
        try:
            result = subprocess.run(
                ["secret-tool", "lookup", "service", "Claude Code"],
                capture_output=True, text=True, timeout=5,
            )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
        except (subprocess.SubprocessError, FileNotFoundError):
            pass

    return None


def discover_codex_chatgpt_oauth() -> tuple[str, str] | None:
    """Read Codex CLI ChatGPT OAuth tokens from ~/.codex/auth.json.

    Returns (access_token, account_id) or None.

    The Codex CLI with chatgpt auth uses:
    - Base URL: https://chatgpt.com/backend-api/codex
    - Bearer token: tokens.access_token
    - Header: ChatGPT-Account-ID: tokens.account_id
    - API: OpenAI Responses API (streaming only)
    """
    # Check multiple possible Codex config locations
    candidates = [
        Path(os.environ["CODEX_HOME"]) if "CODEX_HOME" in os.environ else None,
        Path.home() / ".codex",
    ]
    if platform.system() == "Windows":
        appdata = os.environ.get("APPDATA", "")
        if appdata:
            candidates.append(Path(appdata) / "codex")

    for codex_home in candidates:
        if codex_home is None:
            continue
        auth_path = codex_home / "auth.json"
        if not auth_path.exists():
            continue

        try:
            data = json.loads(auth_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue

        if data.get("auth_mode") != "chatgpt":
            continue

        tokens = data.get("tokens", {})
        access_token = tokens.get("access_token")
        account_id = tokens.get("account_id")

        if access_token and account_id:
            return (access_token, account_id)

    return None


def discover_codex_api_key() -> str | None:
    """Read explicit OPENAI_API_KEY from Codex config (non-ChatGPT mode)."""
    codex_home = Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex")))
    auth_path = codex_home / "auth.json"

    if not auth_path.exists():
        return None

    try:
        data = json.loads(auth_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None

    api_key = data.get("OPENAI_API_KEY")
    if api_key:
        return api_key
    return None


def resolve_anthropic_auth(env_key: str | None = None) -> AuthResult:
    """Resolve Anthropic API auth: Keychain first, then env var."""
    keychain_key = discover_claude_keychain()
    if keychain_key:
        return AuthResult(token=keychain_key, source="keychain")

    if env_key:
        return AuthResult(token=env_key, source="env")

    return AuthResult(token="", source="none")


def resolve_openai_auth(env_key: str | None = None) -> CodexAuthResult:
    """Resolve OpenAI/Codex auth.

    Priority:
    1. ChatGPT OAuth (from Codex CLI login) — uses Responses API
    2. API key from Codex config
    3. OPENAI_API_KEY env var
    """
    # Try ChatGPT OAuth
    chatgpt = discover_codex_chatgpt_oauth()
    if chatgpt:
        access_token, account_id = chatgpt
        return CodexAuthResult(
            access_token=access_token,
            account_id=account_id,
            source="chatgpt_oauth",
        )

    # Try API key from Codex config
    codex_key = discover_codex_api_key()
    if codex_key:
        return CodexAuthResult(
            access_token=codex_key, account_id="", source="env",
        )

    # Fall back to env var
    if env_key:
        return CodexAuthResult(
            access_token=env_key, account_id="", source="env",
        )

    return CodexAuthResult(access_token="", account_id="", source="none")
