# Post 008: v0.6 — Director-Team Leader-Teammate Architecture

**Date**: 2026-02-27
**Version**: 0.6.0

## What Changed

v0.6 replaces the free-form collaboration loop (v0.5) with a structured **Director-Team Leader-Teammate** model.

### The problem with free-form

v0.5's free-form loop let Claude and Codex take turns freely, but lacked coordination intelligence. The loop didn't know *when* to dispatch which agent, *what* to verify, or *when* to stop. It was a round-robin, not a team.

### The solution: a thinking Team Leader

A dedicated Claude instance (`claude -p`, non-streaming) acts as the **Team Leader**. It:

1. Receives the Director's (user's) request
2. Reasons about the task — what to do, who should do it
3. Emits structured commands: `DISPATCH_CLAUDE`, `DISPATCH_CODEX`, `VERIFY`, `DONE`
4. Reviews teammate output and decides next steps
5. Loops until work is complete or max rounds reached

The Team Leader's reasoning is *captured* (not streamed) because it's coordination overhead, not user-facing work. Teammate output *streams* to the terminal so the Director can observe progress.

### Architecture diagram

```
Director (User)
    ↓
Team Leader (claude -p, captured)
    ├── DISPATCH_CLAUDE → Claude Code (streamed)
    ├── DISPATCH_CODEX  → Codex CLI (streamed)
    ├── VERIFY          → auto-detected test suite
    └── DONE            → result panel to Director
```

## Key Design Decisions

**Why Claude as Team Leader?** It already understands code, can reason about task decomposition, and the `claude -p` interface makes it easy to use non-interactively. No need for a separate orchestration model.

**Why structured commands?** Free-text parsing is fragile. Simple line-prefix commands (`DISPATCH_CLAUDE:`, `DISPATCH_CODEX:`, `VERIFY`, `DONE:`) are easy to parse and unambiguous.

**Why cap rounds?** To prevent infinite loops. Default is 8 rounds, configurable via `/rounds <n>`.

**Why clear images after each task?** Images are task-specific context. Carrying them across tasks wastes tokens and confuses teammates.

## Bug Fixes in This Release

- **Dependencies**: Added `rich` to `pyproject.toml` (was imported but not declared)
- **TUI deps separated**: `textual`, `anthropic`, `openai` moved to `[tui]` optional group since the primary CLI path only needs `rich` + `python-dotenv`

## Test Status

88 tests passing. Test distribution:
- `test_orchestrate.py`: 56 tests (primary product)
- `test_tools.py`: 15 tests
- `test_export.py`: 8 tests
- `test_config.py`: 7 tests
- `test_conversation_formats.py`: 2 tests

## What's Next

- End-to-end testing with actual CLIs on real tasks
- Session persistence (save/resume across runs)
- Smarter context management (diffs instead of full output)
- Possibly parallel teammate dispatch (both Claude + Codex on same task)
