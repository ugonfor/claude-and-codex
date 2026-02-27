# claude-and-codex

An orchestrator where Claude Code and Codex CLI collaborate autonomously on coding tasks, using a **Director-Team Leader-Teammate** model.

## How It Works

```
Director (You)
    ↓  give task
Team Leader (Claude -p, non-streaming)
    ├─ Reasons about the task
    ├─ Dispatches work via commands:
    │   DISPATCH_CLAUDE: <instruction>
    │   DISPATCH_CODEX: <instruction>
    │   VERIFY
    │   DONE: <summary>
    ↓
Teammates (streamed to terminal)
    ├─ Claude Code (claude -p --dangerously-skip-permissions)
    └─ Codex (codex exec --full-auto)
    ↓
Results presented to Director
```

Both agents run in **full-auto mode** — no permission prompts, no clarification questions. The Team Leader coordinates, verifies, and only reports when work is complete.

## Requirements

- `claude` CLI (Claude Code) on PATH — **required** (also used as Team Leader)
- `codex` CLI on PATH — optional (enables second teammate)
- Python 3.9+

## Setup

```bash
pip install -e .
```

## Usage

```bash
# Run the orchestrator (in your terminal, NOT inside a claude/codex session)
python -m claude_and_codex
# or after pip install:
claude-and-codex
```

You'll see a `Director >` prompt. Type your task and the Team Leader takes over — dispatching work, reviewing output, running verification, and reporting the result.

### Commands

| Command | Description |
|---------|-------------|
| `/help` | Show available commands |
| `/quit` | Exit |
| `/status` | Show configuration (CLIs found, working dir, etc.) |
| `/clear` | Clear conversation history |
| `/rounds <n>` | Set max Team Leader rounds per task (default: 8) |
| `/verify <cmd>` | Set custom verification command (empty = auto-detect) |
| `/cd <path>` | Change working directory |
| `/image <path>` | Attach image(s) for the next task |
| `/images` | List attached images |
| `/clearimages` | Remove all attached images |

### Auto-detected verification

The orchestrator auto-detects your project's test runner:

| Project type | Detection | Command |
|-------------|-----------|---------|
| Python | `pyproject.toml`/`setup.py` + `tests/` dir | `python -m pytest -q` |
| Node.js | `package.json` with `test` script | `npm test` |
| Rust | `Cargo.toml` | `cargo test` |
| Go | `go.mod` | `go test ./...` |

### Image support

Attach images for vision-capable tasks:

```
Director > /image screenshot.png
Director > What's wrong with this UI layout?
```

Images are passed to the first teammate dispatch and auto-cleared after each task.

## TUI Prototype

The original TUI prototype (Textual-based, API-direct agents) is still available:

```bash
pip install -e ".[tui]"
python -m claude_and_codex --tui
```

This is a legacy path — the CLI orchestrator above is the primary product.

## Architecture

See [CLAUDE.md](CLAUDE.md) for the full project vision, conventions, and architectural decisions. Evolution posts are in `posts/`.
