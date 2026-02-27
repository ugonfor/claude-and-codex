# Post 007: Free-Form Collaboration Engine (v0.5)

**Author**: Claude (Opus 4.6)
**Date**: 2026-02-27

## What Changed

The supervisor pointed out a fundamental flaw: the orchestrator was a rigid pipeline (Phase 1: Claude works -> Phase 2: verify -> Phase 3: Codex reviews -> Phase 4: debate). That's a pre-defined sequential workflow, not collaboration.

**The fix**: Replace the pipeline with a free-form collaboration loop where both agents take turns freely, with no assigned roles.

## How It Works Now

```python
def collaborate(...):
    while turn < max_turns:
        # Alternate agents
        role, name, partner, color, runner = agents[turn % len(agents)]

        # Each agent sees full conversation + decides what to do
        prompt = COLLAB_SYSTEM + context

        # Agent responds: could write code, review, fix, suggest, or PASS
        response = runner(prompt, cwd)

        # If both agents say DONE/PASS consecutively, task is complete
        if consecutive_done >= len(agents):
            break
```

### Key design decisions:

1. **No assigned roles.** The system prompt says: "Do whatever is most useful right now: write code, fix bugs, review, suggest, run tests." Not "you are the worker" or "you are the reviewer."

2. **Agents decide when they're done.** When an agent says DONE or PASS, and the other agent also says DONE or PASS on their next turn, the loop ends.

3. **Auto-verification.** When an agent's response mentions file changes (keywords like "wrote", "modified", "fixed"), the orchestrator runs tests before the next turn and feeds results back.

4. **Final verification.** After the collaboration loop ends, tests run one more time.

## The System Prompt

```
You are {name}, collaborating with {partner} on a coding task.
You share a workspace. You can see everything the other agent has said and done.

Guidelines:
- Do whatever is most useful right now: write code, fix bugs, review, suggest, run tests.
- Do NOT repeat what the other agent already did.
- Do NOT ask the user for clarification. Figure it out together.
- If you made code changes, mention what files you changed.
- When you think the task is fully complete and verified, say DONE.
- If the other agent already handled everything well, say PASS.
- Be concise. Don't narrate -- just do the work.
```

## Also Fixed

- UTF-8 encoding for all subprocess calls (Windows cp949 issue)
- Updated tests: 93 passing
- Version bump to 0.5.0

## Files Changed

- `src/claude_and_codex/orchestrate.py` -- full rewrite of core loop
- `tests/test_orchestrate.py` -- updated to match new API
- `src/claude_and_codex/__init__.py` -- version 0.5.0
- `pyproject.toml` -- version 0.5.0
