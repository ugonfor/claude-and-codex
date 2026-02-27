# Post 006 — Orchestrator Hardening & Completion

## What happened

The orchestrator (`orchestrate.py`) was crashing with `'NoneType' object has no attribute 'strip'` errors when running both Claude and Codex CLIs. The root cause was identified and fixed, and the orchestrator was completed with missing features.

## Root cause of the crash

**The prompt was passed as a command-line argument to `subprocess.run`.** On Windows, `cmd.exe` has an ~8 KB command-line length limit, and `CreateProcess` has a ~32 KB limit. The orchestrator builds prompts that include full conversation context — easily exceeding these limits. When the subprocess creation failed, it threw an exception caught by the generic handler, producing the cryptic `'NoneType' object has no attribute 'strip'` error.

**Fix**: Claude CLI's `-p` flag reads from stdin when no positional argument follows. Changed `run_claude()` to pipe the prompt via `stdin_text` parameter instead of appending it to the args list. This removes the OS-imposed size constraint entirely.

```python
# Before (broken on long prompts):
args=[claude_bin, "-p", "--dangerously-skip-permissions", full_prompt]

# After (no size limit):
args=[claude_bin, "-p", "--dangerously-skip-permissions"]
stdin_text=full_prompt
```

## Other fixes

1. **`is_lgtm(None)` crash** — Added null guard. Previously would throw `AttributeError` on None input.
2. **Better error messages** — `run_cli` now catches `FileNotFoundError` and `PermissionError` separately, includes exception type in generic errors.
3. **Null-safe subprocess output** — Explicitly handles `result.stdout`/`result.stderr` being `None` with local variables instead of inline `or` chains.
4. **ANSI color disable** — Colors now auto-disable when stdout is not a TTY (piped/redirected output).
5. **Prompt truncation** — Added `PROMPT_MAX_CHARS = 50_000` safety limit.

## New features

1. **`/help`** — Shows all available commands
2. **`/cd <path>`** — Changes working directory, auto-re-detects verify command
3. **`/export [md|jsonl|both]`** — Exports conversation history to file
4. **`/status`** — Shows current configuration (CLIs, verify cmd, images, etc.)
5. **`/clear`** — Clears conversation history
6. **Unknown command catch-all** — `/anything` now shows a helpful error instead of being treated as a task
7. **Phase timing** — Each phase shows elapsed time
8. **Total task time** — Shown at the end of each protocol run
9. **Graceful single-agent mode** — Works properly when only Claude OR only Codex is available:
   - Work phase falls back to available agent
   - Verify phase uses available agent for fixes
   - Review phase does self-review instead of cross-review
   - Debate phase uses available agent for both roles

## New tests

Added `tests/test_orchestrate.py` with 56 tests covering:
- `is_lgtm` — None, empty, LGTM, "looks good", negatives
- `truncate` — Short text, exact length, long text, defaults
- `build_context` — Empty, single entry, role labels, max entries, truncation
- `detect_verify_command` — Python, Node, Rust, Go, unknown, edge cases
- `run_cli` — Simple command, stderr, timeout, file not found, env overrides, stdin, no output
- `run_verify` — No command, passing, failing
- `export_conversation` — Empty, markdown, JSONL, unknown format
- `resolve_image_path` — Valid, relative, nonexistent
- `elapsed_str` — Seconds, minutes
- `handle_command` — All slash commands, unknown commands, non-commands

## Additional fix

**KeyboardInterrupt during protocol execution** — Ctrl+C during a long agent call would crash the orchestrator because the interrupt was only caught around `input()`, not the phase execution. Wrapped the entire protocol run in a `try/except KeyboardInterrupt` so the user can abort a running task without losing the session.

## Test count

43 → 104 tests, all passing.
