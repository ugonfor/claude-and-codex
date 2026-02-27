# claude-and-codex

An orchestrator where Claude Code and Codex CLI collaborate autonomously on coding tasks.

## How It Works

```
User gives task -> Claude works (full auto) -> Self-verify (run tests)
    -> Codex reviews -> Debate if needed -> Present verified result
```

Both agents run in full-auto mode. They never ask the user for clarification -- they figure it out themselves. Only verified, reviewed results are presented.

## Requirements

- `claude` CLI (Claude Code) on PATH
- `codex` CLI on PATH
- Python 3.11+

## Setup

```bash
pip install -e .
```

## Usage

```bash
# Run the orchestrator (outside of any claude/codex session)
python -m claude_and_codex
```

### Commands

- `/quit` -- exit
- `/turns <n>` -- set max debate rounds (default: 3)
- `/verify <cmd>` -- set custom verification command

### Auto-detected verification

The orchestrator auto-detects your project's test runner:
- Python: `python -m pytest -q`
- Node: `npm test`
- Rust: `cargo test`
- Go: `go test ./...`

## TUI Prototype

The original TUI prototype (Textual-based) is still available:

```bash
python -m claude_and_codex --tui
```
