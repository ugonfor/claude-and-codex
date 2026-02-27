# Post 004: v0.3 Features + Architectural Direction Shift

**Author**: Claude (Opus 4.6)
**Date**: 2026-02-27

## v0.3 Features Completed

### 1. Conversation Export

Added `export.py` module with two formats:
- **JSONL**: Machine-readable, one JSON object per line with full metadata (role, content, timestamp, tool_calls, tool_owner)
- **Markdown**: Human-readable with headers, timestamps, tool call details, and result previews
- **`/export` slash command**: `/export [jsonl|markdown|both]` writes files to `exports/` in the working directory

### 2. Token/Latency Observability

Added `metrics.py` module with live tracking:
- `TurnMetrics`: Per-turn data (role, input_tokens, output_tokens, latency_ms)
- `AgentMetrics`: Cumulative per-agent stats with avg latency
- `MetricsTracker`: Session-wide tracker, reset support
- **Agent changes**: Both ClaudeAgent and CodexAgent now capture token usage from API responses (Anthropic `usage`, OpenAI `stream_options.include_usage`, ChatGPT `response.completed`)
- **Orchestrator**: Wraps each agent turn with `time.monotonic()` for latency
- **StatusBar**: Shows live cumulative token counts per agent
- **`/stats` slash command**: Detailed session metrics breakdown

### 3. Expanded Test Coverage

Went from 3 tests to **43 tests** across 6 test files:
- `test_tools.py` — ToolRegistry (5 tests), file_read (4 tests), file_write (3 tests), shell_exec (3 tests)
- `test_metrics.py` — AgentMetrics (3 tests), MetricsTracker (3 tests)
- `test_export.py` — JSONL (4 tests), Markdown (4 tests), export_conversation (4 tests)
- `test_config.py` — Config validation (7 tests)
- Existing: `test_conversation_formats.py` (2 tests), `test_orchestrator_turn_alternation.py` (1 test)

All 43 tests passing on Windows.

### 4. Cross-Platform Auth

Extended `discover_claude_keychain()` to support all platforms:
- **macOS**: Keychain via `security` CLI (unchanged)
- **Windows**: Windows Credential Manager via PowerShell `Get-StoredCredential`
- **Linux**: libsecret via `secret-tool lookup`
- **Codex**: Added Windows `%APPDATA%\codex` as additional config path

## Direction Shift

The supervisor clarified the project's core constraint:

> "I don't want to make new agents. I want to use Claude Code and Codex. This means this project should build on top of Claude Code and Codex."

This means:
- **The real product is `orchestrate.py`** — subprocess-based orchestration of the actual `claude` and `codex` CLIs
- **The TUI/API path (`app.py` + `agents/`)** was a valuable prototype but is not the target architecture
- The CLIs already handle tools, streaming, context, auth — everything. What's missing is the **collaboration protocol** between them

Updated CLAUDE.md to reflect this architectural constraint.

## Files Changed

New files:
- `src/claude_and_codex/export.py`
- `src/claude_and_codex/metrics.py`
- `tests/test_tools.py`
- `tests/test_metrics.py`
- `tests/test_export.py`
- `tests/test_config.py`

Modified files:
- `src/claude_and_codex/app.py` — added /export, /stats commands, metrics wiring
- `src/claude_and_codex/orchestrator.py` — timing + metrics recording
- `src/claude_and_codex/agents/base.py` — last_input_tokens, last_output_tokens
- `src/claude_and_codex/agents/claude_agent.py` — capture usage from final_message
- `src/claude_and_codex/agents/codex_agent.py` — capture usage from both backends
- `src/claude_and_codex/auth.py` — cross-platform credential discovery
- `src/claude_and_codex/ui/status_bar.py` — live token counts in status bar
- `CLAUDE.md` — ground rules, vision, architectural constraint

## What's Next

The focus shifts to evolving `orchestrate.py`:
1. Better collaboration protocol between the real CLIs
2. Structured conversation management (not string concatenation)
3. Ability for agents to review each other's file changes
4. Reducing human interruption — agents self-check before asking the user
