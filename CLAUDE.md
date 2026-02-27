# CLAUDE.md — claude-and-codex

## Ground Rules

1. **Do it yourself.** This is Claude's own project, under the user's (supervisor's) supervision. Make your own decisions. Do not ask the supervisor unless absolutely necessary.
2. **Codex is your coworker.** You can ask Codex anytime for review, debate, or collaboration — just like posts 002 and 003 demonstrated.
3. **Write a post when a big task or chapter is done.** The post goes in `posts/` and should describe what was done. The supervisor will review it.
4. **Before asking the supervisor, think.** Only interrupt the human when ALL of these are true:
   - All requirements are done
   - You are confident the results satisfy the user
   - Claude and Codex have debated and BOTH agree they need to ask
   - Otherwise, figure it out yourself
5. **Refactor regularly.** Agents are not perfect engineers and agile iteration makes codebases messy fast. After each big task, review and clean up: remove dead code, simplify overly complex parts, keep the codebase maintainable.

## Vision

Current AI coding agents (Claude Code, Codex CLI) interrupt the human too much. Three core problems:

1. **Too many interruptions.** Permission prompts, direction questions, clarifications. Most are simple and foolish — the agent could figure it out.
2. **No self-checking.** Agents don't run the project or verify their output before presenting it. They should catch their own errors.
3. **No collaboration.** Two capable agents can check each other — Claude reviews Codex's work, Codex catches Claude's bugs — but current systems don't enable this.

**Solution**: Run both CLIs in **full auto mode** (bypass permissions). Have them **debate and review each other**. Make them **self-verify** (run tests, check errors) before presenting results. Only interrupt the human when both agents agree it's necessary AND they've verified their work.

The human supervises the output, not the process.

## Key Architectural Constraint

**Do NOT build custom agents from raw API calls.** Use the actual `claude` CLI (Claude Code) and `codex` CLI as subprocesses. These CLIs already handle tools, context, streaming, and everything else. This project builds the **orchestration and collaboration layer on top of them**.

The right path is `orchestrate.py` (subprocess-based CLI orchestrator), not `app.py` + `agents/` (custom API agents). The custom agent code was an early exploration but the real product runs the actual CLIs.

## Project Overview

An orchestration layer where Claude Code and Codex CLI collaborate freely on coding tasks — using the real CLIs as subprocesses.

- **Language**: Python 3.11+
- **Entry point**: `python -m claude_and_codex` or `orchestrate.py`
- **Package**: `src/claude_and_codex/`
- **Tests**: `tests/` (pytest + pytest-asyncio, `asyncio_mode = "auto"`)
- **Posts**: `posts/` (numbered `NNN-title.md`)

## Architecture

### Primary (CLI subprocess orchestration)
- `orchestrate.py` — Runs actual `claude` and `codex` CLIs as subprocesses

### Supporting (may be retained for the TUI prototype)
- `models.py` — Core data models (Role, AgentStatus, Message, ToolCall)
- `auth.py` — OAuth + API key authentication (cross-platform)
- `config.py` — Runtime configuration from env vars
- `conversation.py` — Thread-safe message bus with dual-format conversion
- `orchestrator.py` — Agent turn management with anti-ping-pong mechanisms
- `metrics.py` — Token/latency tracking
- `export.py` — Conversation export (JSONL + Markdown)
- `agents/` — BaseAgent, ClaudeAgent, CodexAgent (API-direct, prototype)
- `tools/` — ToolRegistry + file_read, file_write, shell_exec
- `ui/` — Textual TUI widgets
- `app.py` — Main Textual app (TUI prototype)

## Conventions

- Commit messages: concise, imperative mood
- Posts: `posts/NNN-title.md` format, describe what was done and why
- Tests: mirror source structure in `tests/`, use pytest-asyncio for async
- Dependencies: minimal, listed in `pyproject.toml`

## Current Status (v0.3)

Implemented:
- Full TUI with dual-agent collaboration (prototype path)
- CLI subprocess orchestrator (primary path)
- OAuth + API key auth (cross-platform: macOS, Windows, Linux)
- Tool system with safety confirmations
- Slash commands (/model, /clear, /cd, /bypass, /export, /stats, /help)
- Conversation export (JSONL + Markdown)
- Token/latency observability (metrics tracker + StatusBar)
- 43 unit tests passing

Next direction:
- Evolve `orchestrate.py` into the primary product
- Build robust collaboration protocol between real CLIs
- Minimize human interruption through agent-to-agent quality checks
