# Post 003: Codex v0.2 Features

Implemented `v0.2` on branch `codex/v0.2-features` (local workspace changes) with three major upgrades:

## 1. Slash Commands in InputBar

Added slash command parsing in `ui/input_bar.py` so slash input is intercepted before orchestration:

- `/model <name>`: updates both Claude and Codex model names at runtime
- `/clear`: clears visible chat panel and resets in-memory conversation state
- `/cd <path>`: changes tool working directory (and reconfigures tools)
- `/help`: prints command help

Implementation details:
- Added `SlashCommand` and `CommandSubmitted` events.
- Added `CommandHandler` in `app.py` to execute command logic.
- `UserSubmitted` still handles normal chat messages.

## 2. Tool Safety Confirmation

Added explicit approval flow for dangerous tools:

- Applies to `write_file` and `execute_shell`
- Before execution, app posts a system confirmation message in chat with tool name and args.
- Execution pauses until user replies `yes` or `no`.
- Denied tools are recorded as tool errors in conversation state.

Implementation details:
- Added `on_tool_confirmation` callback support to `Orchestrator`.
- Added pending confirmation state in `app.py` and response handling in input submission path.

## 3. Unit Tests

Added tests under `tests/`:

- `test_conversation_formats.py`
  - Verifies `to_anthropic_messages` tool-owner scoping behavior.
  - Verifies `to_openai_messages` tool-owner scoping behavior.

- `test_orchestrator_turn_alternation.py`
  - Verifies first responder alternates per user turn (Claude then Codex, then Codex then Claude).

Test run:

```bash
.venv/bin/python -m pytest -q
# 3 passed
```

## Files Changed

- `src/claude_and_codex/ui/input_bar.py`
- `src/claude_and_codex/ui/chat_panel.py`
- `src/claude_and_codex/app.py`
- `src/claude_and_codex/orchestrator.py`
- `tests/test_conversation_formats.py`
- `tests/test_orchestrator_turn_alternation.py`
- `posts/003-codex-v02-features.md`
