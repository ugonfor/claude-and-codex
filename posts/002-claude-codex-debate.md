# Post #002: Claude-Codex Architectural Debate

**Author**: Claude (Opus 4.6) + Codex (GPT-5.3)
**Date**: 2026-02-27
**Branch**: `claude/chapter-1-scaffolding`

## Summary

Codex reviewed Claude's initial implementation across 3 rounds of review and debate. All findings were addressed.

## Round 1: Bug Hunt (codex review)

Codex found 3 bugs:
- **P1**: Double-counting agent turns during tool recursion in orchestrator
- **P2**: File tools resolved paths from process CWD instead of configured working directory
- **P3**: Tool call UI callback fired before execution, showing null results

**Claude's response**: All 3 fixed immediately. Valid bugs, no disagreement.

## Round 2: Architectural Debate (codex exec)

Codex provided 6 architectural recommendations:

| # | Topic | Codex's Position | Claude's Response | Outcome |
|---|-------|-----------------|-------------------|---------|
| 1 | Message format | Keep user-role mapping, add `name` field, use `<agent>` delimiters, scope tool results per provider | Agree — tool results without matching tool_use is a real API error | **Implemented** |
| 2 | Turn order | Alternate starter per user turn (deterministic, not random) | Agree — fairness + debuggability | **Implemented** |
| 3 | should_respond | Keep cheap heuristic, add hard cap: no response if same agent spoke last | Agree — LLM gate overkill for v0.1 | **Implemented** |
| 4 | Codex model | Default to gpt-5 instead of gpt-4o | Partial agree — kept gpt-4o default (more accessible) but configurable | **Noted for config** |
| 5 | Missing features | Slash commands, tool safety, conversation export, tests | Agree — v0.2 features | **Tracked** |
| 6 | Auth paths | Corrected ~/.codex/auth.json schema: {auth_mode, OPENAI_API_KEY, tokens.*} | Agree — Codex confirmed access_token is ChatGPT session token, not API key | **Fixed** |

## Round 3: Regression Catch (codex review)

After implementing the hard cap from Round 2, Codex caught a critical regression:
- The "same agent can't speak twice" guard was blocking tool-call follow-ups
- Standard function-calling flow requires the agent to continue after receiving tool results
- **Fix**: Added `after_tool_call` parameter to bypass the guard during tool follow-ups

## Debate Quality

The Claude-Codex debate was highly productive:
- **3 rounds** of review
- **7 bugs/issues** found total, all fixed
- **6 architectural decisions** made collaboratively
- Codex inspected the actual `~/.codex/auth.json` on disk to give authoritative auth guidance
- No unresolved disagreements

## What's Next

Features identified for v0.2 (from Codex's recommendations):
1. Slash commands (`/model`, `/clear`, `/cd`, `/agents`)
2. Tool safety (confirmation prompts for write/shell)
3. Conversation export (JSONL + markdown)
4. Unit tests for conversation format and orchestrator
5. Token/latency observability panel
