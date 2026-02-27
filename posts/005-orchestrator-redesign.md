# Post 005: Orchestrator Redesign — Work-Verify-Review-Debate Protocol

**Author**: Claude (Opus 4.6)
**Date**: 2026-02-27

## Why

The supervisor identified three core problems with current AI coding agents:

1. **Too many interruptions.** Permission prompts, direction questions, clarifications — most are simple and foolish. The agent could figure it out.
2. **No self-checking.** Agents don't run the project or verify their output before presenting it.
3. **No collaboration.** Two agents can check each other, but current systems don't enable this.

The old `orchestrate.py` was a chat-style system where both agents just replied to user messages. No verification, no protocol, no quality gate.

## What Changed

Rewrote `orchestrate.py` with a 4-phase protocol:

### Phase 1: Work
Claude works on the task using `claude -p --dangerously-skip-permissions` (full auto). The prompt explicitly tells Claude: "Do NOT ask the user for clarification. Figure it out yourself."

### Phase 2: Self-Verify
Auto-detect the project's test runner and run it:
- Python: `python -m pytest -q`
- Node: `npm test`
- Rust: `cargo test`
- Go: `go test ./...`

If verification fails, Claude gets the error output and fixes it. This loops up to 3 times. Only after tests pass does it proceed.

### Phase 3: Review
Codex reviews Claude's work using `codex exec --full-auto`. Codex checks:
- Does the work address the user's request?
- Any bugs, edge cases, or missing requirements?
- If good → "LGTM". If not → describes issues.

### Phase 4: Debate (if needed)
If Codex found issues:
1. Claude addresses the feedback and fixes
2. Re-verify (run tests again)
3. Codex re-reviews
4. Repeat up to 3 rounds until LGTM or debate exhausted

Only after both agents agree does the user see the final result.

## Key Design Decisions

- **Full auto mode for both CLIs.** No permission prompts. The agents handle everything.
- **Agents never ask the user.** Every prompt includes "Do NOT ask the user."
- **Verification is mandatory.** If tests exist, they must pass before review.
- **Context truncation.** Long responses are truncated to 2000 chars in context to keep prompts manageable.
- **Auto-detection.** The verify command is detected from project files (`pyproject.toml`, `package.json`, `Cargo.toml`, `go.mod`). User can override with `/verify <cmd>`.

## Also Updated

- **CLAUDE.md**: Added ground rule #4 (only interrupt human when both agents agree AND work is verified). Refined vision section with the three core problems.

## Files Changed

- `src/claude_and_codex/orchestrate.py` — full rewrite (247→264 lines)
- `CLAUDE.md` — ground rule #4, vision refinement

## What's Next

The protocol is in place. Next areas to explore:
- Actually running the orchestrator end-to-end on a real task
- Streaming output (currently blocks until each CLI finishes)
- Session persistence (conversation history across runs)
- Smarter context management (file diffs instead of full conversation text)
