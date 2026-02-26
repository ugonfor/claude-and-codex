"""Entry point for python -m claude_and_codex."""

from .app import ClaudeAndCodexApp


def main() -> None:
    app = ClaudeAndCodexApp()
    app.run()


if __name__ == "__main__":
    main()
