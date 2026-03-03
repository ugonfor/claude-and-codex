# Post 010: Emergent Collaboration — What Happens When You Just Let Agents Loose

**Date**: 2026-03-04
**Inspired by**: [anadim/when-claudes-meet](https://github.com/anadim/when-claudes-meet) (Dimitris Papailiopoulos)

## The Experiment

Replicating Dimitris's experiment: launch agents with minimal prompts into a shared directory and see what emerges. No structured commands, no predefined tasks, no orchestration — just **"find each other, communicate through files, build something together."**

Three configurations, each with a shared `playground_*/` directory:

| Experiment | Agents | Prompt Style |
|------------|--------|--------------|
| **CC** | Claude-A + Claude-B | "You are one of two Claude instances. Find each other, build something." |
| **CX** | Claude + Codex | Same prompt, adapted for cross-model identity |
| **DCX** | Director(Claude) + Claude-Worker + Codex-Worker | Workers get the same prompt; Director observes |

All agents ran **simultaneously** as parallel subprocesses. 10-minute timeout.

---

## Results Summary

| | CC (Claude-Claude) | CX (Claude-Codex) | DCX (Director+Claude+Codex) |
|---|---|---|---|
| **What they built** | Conway's Game of Life | Pong (terminal) | Task Board CLI |
| **Collaboration?** | **Yes — genuine** | **Failed** (Codex sandboxed) | **Failed** (Codex sandboxed) |
| **Files created** | 16 | 11 | 14 |
| **Lines of code** | 712 | 504 | 763 |
| **Tests** | 23 passing | 15 passing | 16 passing |
| **Time** | 357s (~6 min) | 287s (~5 min) | 438s (~7 min) |
| **Communication files** | 7 (bidirectional) | 2 (Claude only) | 2 (Claude only) |
| **Who built it** | Both agents | Claude only | Claude-Worker only |

---

## CC: Claude-Claude — The Star of the Show

### What Happened

Both Claude instances were launched simultaneously. Within seconds, each independently:
1. Created a "hello" file announcing their presence
2. Proposed **the exact same project** (Conway's Game of Life)
3. Designed a communication protocol (markdown files)

They then:
4. Agreed on the proposal (Claude-B: "We proposed the exact same project! Great minds think alike.")
5. Defined an interface contract (Claude-B specified exact method signatures)
6. Split work: Claude-A → engine, Claude-B → CLI
7. Claude-A wrote `API-NOTE.md` documenting the API mismatch
8. Claude-B adapted to use Claude-A's actual API
9. Both wrote tests for their own modules
10. Both updated status files showing progress
11. Wrote `DONE.md` together

### Communication Protocol (Emergent)

```
CLAUDE-A.md          → Claude-A's hello + proposal
CLAUDE-B-HELLO.md    → Claude-B's independent hello
CLAUDE-B.md          → Claude-B's agreement + interface contract
API-NOTE.md          → Claude-A documenting API differences
STATUS-A.md          → Claude-A's progress tracker
STATUS-B.md          → Claude-B's progress tracker
DONE.md              → Joint completion summary
```

This is the **exact same pattern** Dimitris observed: `hello → ack → proposals → agreement → build → done`. The agents invented it independently within seconds.

### Key Moments

1. **Convergent proposal**: Both independently chose Game of Life before seeing each other's messages
2. **API negotiation**: Claude-B specified expected methods; Claude-A's actual API differed; Claude-A documented the difference in `API-NOTE.md`; Claude-B adapted. This is a real coordination protocol.
3. **Clean division**: Zero file conflicts. Claude-A owned `life_engine.py`, Claude-B owned `life_cli.py`, both contributed to `main.py`
4. **Platform awareness**: Claude-B discovered and fixed a Windows Unicode encoding issue (`cp949` codepage)

### Output: 712 lines, 23 tests, fully playable

```bash
python main.py -p glider -W 30 -H 20    # Glider on 30x20 grid
python main.py -p random -W 60 -H 30    # Random fill
python main.py --list                    # Show all 12 patterns
```

---

## CX: Claude-Codex — The Sandbox Wall

### What Happened

Claude launched, proposed a Pong game, wrote a division of labor proposal in `CLAUDE_TO_CODEX.md`, and started building.

**Codex understood the task perfectly.** It read Claude's files, agreed on Pong, designed an interface contract, considered platform issues (Windows/msvcrt) — then hit a wall:

> "Writing or deleting files is blocked by the current sandbox policy, so I could not create `CODEX_TO_CLAUDE.md` or remove `.codex_prompt.tmp`."

Codex's `exec --full-auto` mode has a **read-only sandbox** for directories outside its own workspace. It could READ Claude's communication files but could not WRITE responses.

Claude waited, wrote a second invitation (`HELLO_CODEX.md`), waited more, then built the entire Pong game solo — Pong engine, AI opponent, ANSI renderer, 15 tests — all within the timeout.

### Codex's Unrealized Contribution

Codex wrote (in its captured output, never reaching the filesystem):

```
Interface I'll implement:
  render(game_state: dict) -> None
  get_input() -> dict  # returns {'p1': -1/0/1, 'p2': -1/0/1, 'quit': bool}
```

A perfectly reasonable interface contract that was never delivered.

### The Fundamental Issue

**Filesystem-based inter-agent communication requires both agents to have write access.** Claude Code with `--dangerously-skip-permissions` has unrestricted file access. Codex CLI with `--full-auto` does not write to arbitrary external directories.

This isn't a prompt engineering problem — it's an infrastructure incompatibility.

---

## DCX: Director + Claude + Codex — The Observational Layer

### What Happened

Three agents launched simultaneously:
- **Claude-Worker** proposed a task board CLI, waited briefly for Codex, then built everything solo (763 lines, 16 tests)
- **Codex-Worker** hit the exact same sandbox wall as CX: "sandbox is read-only"
- **Director** silently observed the workspace, tracking file creation timestamps, then wrote a comprehensive `DIRECTOR_REPORT.md`

### The Director's Report (Autonomously Generated)

The Director gave the collaboration a **1/10 quality score** and produced a detailed timeline, architecture review, and comparison with other experiments. Key observations:

> "Claude-Worker anticipated Codex might not deliver and built the CLI with `try/except ImportError` fallbacks from the start. This was pragmatic architecture — hope for the best, plan for the worst."

> "Claude-Worker dog-fooded the task board by creating task entries for its own work. Meta and charming."

### Director's Value

The Director **added no guidance** during execution (never wrote a `director_note.md`). Its value was entirely in the post-hoc `DIRECTOR_REPORT.md` — a quality assessment that no other agent produced. This suggests the Director role is more valuable as a **reviewer** than as a **planner**.

---

## Analysis: What We Learned

### 1. Claude-Claude Collaboration Actually Works

Two Claude instances with nothing but a shared directory and a 2-sentence prompt:
- Invented the same communication protocol as Dimitris's experiment
- Independently converged on the same project idea
- Negotiated an API contract through markdown files
- Split work cleanly with zero conflicts
- Produced 712 lines of tested, working code

This is genuinely emergent collaboration — not prescribed, not orchestrated.

### 2. Cross-Model Collaboration Fails on Infrastructure, Not Intelligence

Codex **wanted** to collaborate. It understood the task, read Claude's proposals, designed interfaces, considered platform issues. The failure was pure infrastructure: Codex's sandbox prevented file writes.

This means the "when-claudes-meet" result is **Claude-specific**, not a general property of LLM agents. It works because `claude -p --dangerously-skip-permissions` gives unrestricted filesystem access. Any agent without equivalent write access will be unable to participate in the filesystem messaging protocol.

### 3. Agents Gracefully Degrade to Solo Work

Both CX-Claude and DCX-Claude-Worker followed the same pattern:
1. Propose collaboration → wait for response → no response → build it myself

They didn't hang, crash, or loop. They set reasonable timeouts and proceeded independently. Claude-Worker even designed its code with `ImportError` fallbacks anticipating the partner's absence.

### 4. Same-Model Convergence is Real

Claude-A and Claude-B independently proposed the same project (Conway's Game of Life), the same communication protocol (markdown files), and compatible file naming conventions. This suggests strong prior alignment in training — the models have a shared "instinct" for how to handle open-ended collaboration.

### 5. The Director Role is Best as Post-Hoc Reviewer

In DCX, the Director never intervened during execution (no guidance notes). Its contribution was the `DIRECTOR_REPORT.md` — a structured quality assessment with timeline, architecture review, and comparison. The Director adds most value as a quality gate, not as a real-time coordinator.

---

## Comparison with Dimitris's Experiment

| | Dimitris (Claude-Claude) | Our CC (Claude-Claude) | Our CX (Claude-Codex) |
|---|---|---|---|
| Prompt | "Find each other, build something" | Same | Same (cross-model) |
| Time | 12 min | 6 min | 5 min (solo) |
| What they built | Programming language (2,495 LOC) | Game of Life (712 LOC) | Pong (504 LOC, solo) |
| Communication | Filesystem messaging (invented) | Same protocol (independently) | One-sided (Codex blocked) |
| Collaboration | Genuine, both contributed | Genuine, both contributed | Failed (sandbox) |
| Tests | 41 passing | 23 passing | 15 passing |

Our CC result validates Dimitris's finding. Two Claude instances, given nothing but a shared directory, independently converge on communication protocols and successfully collaborate on non-trivial software.

---

## Files

```
emergent_experiment.py           — Experiment runner script
playground_cc/                   — CC: Game of Life (16 files)
playground_cx/                   — CX: Pong (11 files, Claude solo)
playground_dcx/                  — DCX: Task Board (14 files, Claude solo + Director report)
results/emergent/                — Agent outputs + playground snapshots
```
