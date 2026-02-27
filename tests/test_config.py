"""Tests for configuration and validation."""

from __future__ import annotations

from claude_and_codex.config import Config


class TestConfigValidation:
    def test_valid_config(self) -> None:
        cfg = Config(anthropic_api_key="sk-ant-xxx", openai_api_key="sk-xxx")
        errors = cfg.validate()
        assert errors == []

    def test_missing_anthropic_key(self) -> None:
        cfg = Config(anthropic_api_key="", openai_api_key="sk-xxx")
        errors = cfg.validate()
        assert len(errors) == 1
        assert "Anthropic" in errors[0]

    def test_missing_openai_key(self) -> None:
        cfg = Config(anthropic_api_key="sk-ant-xxx", openai_api_key="")
        errors = cfg.validate()
        assert len(errors) == 1
        assert "OpenAI" in errors[0]

    def test_missing_both_keys(self) -> None:
        cfg = Config(anthropic_api_key="", openai_api_key="")
        errors = cfg.validate()
        assert len(errors) == 2

    def test_is_chatgpt_oauth(self) -> None:
        cfg = Config(openai_auth_source="chatgpt_oauth")
        assert cfg.is_chatgpt_oauth is True

    def test_not_chatgpt_oauth(self) -> None:
        cfg = Config(openai_auth_source="env_var")
        assert cfg.is_chatgpt_oauth is False

    def test_auth_summary(self) -> None:
        cfg = Config(
            anthropic_auth_source="keychain",
            openai_auth_source="chatgpt_oauth",
        )
        summary = cfg.auth_summary()
        assert "Claude: keychain" in summary
        assert "Codex: chatgpt_oauth" in summary
