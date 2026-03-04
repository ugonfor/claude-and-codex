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

**Critical setup detail**: Codex requires `-s danger-full-access -C <playground> --skip-git-repo-check` to have write access to the shared directory. Its default `--full-auto` mode (`workspace-write` sandbox) blocks writes to external directories. This was discovered through a failed first run where Codex could read but not write — and was the key to unlocking cross-model collaboration.

---

## Results Summary

| | CC (Claude-Claude) | CX (Claude-Codex) | DCX (Director+Claude+Codex) |
|---|---|---|---|
| **What they built** | Conway's Game of Life | Conway's Game of Life | Conway's Game of Life |
| **Collaboration?** | **Yes — genuine** | **Yes — genuine** | **Yes — genuine** |
| **Files created** | 16 | 13 | 15 |
| **Lines of code** | 712 | 344 | 412 |
| **Tests** | 23 passing | 7 passing | 13 passing |
| **Total time** | 357s (~6 min) | 202s (~3.5 min) | 297s (~5 min) |
| **Communication files** | 7 (bidirectional) | 4 (bidirectional) | 4 (bidirectional) + Director report |
| **Who built it** | Both agents | Both agents | Both agents + Director observed |

All three experiments converged on **Conway's Game of Life** — independently!

---

## CC: Claude-Claude — The Baseline

### What Happened

Both Claude instances launched simultaneously. Within seconds, each independently:
1. Created a "hello" file announcing their presence
2. Proposed **the exact same project** (Conway's Game of Life)
3. Designed a communication protocol (markdown files)

They then:
4. Agreed on the proposal (Claude-B: "We proposed the exact same project! Great minds think alike.")
5. Defined an interface contract (Claude-B specified exact method signatures)
6. Split work: Claude-A → engine, Claude-B → CLI
7. Claude-A wrote `API-NOTE.md` documenting the API mismatch between expected and actual interfaces
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

This is the **exact same pattern** Dimitris observed: `hello → ack → proposals → agreement → build → done`.

### Key Moments

1. **Convergent proposal**: Both independently chose Game of Life before seeing each other's messages
2. **API negotiation**: Claude-B specified expected methods; Claude-A's actual API differed; Claude-A documented the difference; Claude-B adapted
3. **Clean division**: Zero file conflicts. Claude-A owned `life_engine.py`, Claude-B owned `life_cli.py`
4. **Platform awareness**: Claude-B discovered and fixed a Windows Unicode encoding issue

### Output: 712 lines, 23 tests, 12 preset patterns, fully playable

---

## CX: Claude-Codex — Cross-Model Collaboration Works!

### What Happened

With proper sandbox permissions, **both agents communicated and contributed**:

1. Codex wrote `MESSAGE_TO_CLAUDE.md` proposing FizzBuzz
2. Claude wrote `CLAUDE_TO_CODEX.md` proposing Game of Life with interface contracts
3. Codex saw Claude's more detailed plan, **abandoned its own proposal**, wrote `CODEX_TO_CLAUDE.md` accepting
4. Claude built the engine (`game.py`) and tests (`test_game.py`)
5. Claude drafted initial `renderer.py` and `main.py`
6. **Codex replaced both with improved versions** — clean ANSI renderer + full argparse CLI
7. Both verified tests pass

### Cross-Model Dynamics

The collaboration revealed interesting differences:

- **Claude leads, Codex follows**: Claude's proposal was more detailed (interface contracts, division of labor). Codex deferred to the more prepared agent.
- **Codex improves on Claude's drafts**: Rather than building from scratch, Codex rewrote Claude's initial `renderer.py` and `main.py` with cleaner implementations.
- **Different proposal styles**: Codex proposed FizzBuzz (simple, safe), Claude proposed Game of Life (ambitious, visual). The more ambitious proposal won.

### Output: 344 lines, 7 tests, working Game of Life

| File | Author | Description |
|------|--------|-------------|
| `game.py` | Claude | Core engine, B3/S23 rules, patterns |
| `test_game.py` | Claude | 7 unit tests |
| `renderer.py` | Codex | ANSI terminal renderer |
| `main.py` | Both | Claude drafted, Codex rewrote with argparse |

---

## DCX: Director + Claude + Codex — The Supervised Version

### What Happened

Three agents, all contributing:

1. Claude-Worker proposed Game of Life with interface contracts
2. Codex-Worker proposed a note manager (hadn't seen Claude's file yet)
3. Codex-Worker saw Claude's plan, immediately pivoted, wrote acceptance
4. Claude-Worker built engine + tests, Codex-Worker built patterns + renderer
5. Claude-Worker integrated everything, fixed a render signature mismatch
6. **Codex overwrote Claude's detailed DONE.md with a shorter version** (conflict!)
7. Director silently observed the entire process, then wrote `DIRECTOR_REPORT.md`

### The Director's Autonomous Report

The Director gave the collaboration a **B+ rating** and produced a detailed analysis:

> "Claude's proposal was excellent: Clear project scope, interface contracts with actual Python signatures, clean division of labor. This set the collaboration up for success."

> "Codex adapted quickly: Abandoned its own proposal without friction when it discovered Claude's plan. No ego, no debate — just got to work."

> "The DONE.md overwrite went unnoticed. This is the most revealing collaboration failure. Neither agent had a mechanism to detect or prevent it."

### The First File Conflict

DCX produced the first observable **collaboration failure**: Codex overwrote Claude's comprehensive 44-line `DONE.md` with its own 12-line version. Neither agent noticed. The Director caught it and flagged it as the key weakness.

This reveals a gap in emergent collaboration: **no conflict detection mechanism**. Agents don't check if files were modified by others before overwriting.

### Output: 412 lines, 13 tests, with Director quality report

---

## Analysis

### 1. All Three Configurations Converged on Game of Life

Every experiment independently chose Conway's Game of Life. This isn't random — it's a strong attractor in training data for "build something interesting together." It's visual, splittable, testable, and well-defined.

### 2. The Communication Protocol is Universal

All three experiments invented the same filesystem messaging pattern:
```
hello → ack → proposal → agreement/negotiation → build → status → done
```
This matches Dimitris's finding exactly. The protocol emerges from LLMs' shared understanding of how collaboration works.

### 3. Cross-Model Collaboration Works (With Correct Permissions)

Once Codex had write access (`-s danger-full-access`), Claude-Codex collaboration was productive:
- Codex deferred to Claude's more detailed proposals
- Codex improved on Claude's draft implementations
- Both contributed distinct modules to the final product

The initial failure was **infrastructure, not intelligence**.

### 4. The Director Role: Reviewer > Planner

In DCX, the Director never intervened during execution. Its value was entirely in the post-hoc `DIRECTOR_REPORT.md`:
- Timeline reconstruction
- Quality scoring (B+)
- Conflict detection (DONE.md overwrite)
- Cross-experiment comparison

The Director is most valuable as a **quality gate and reviewer**, not as a real-time coordinator.

### 5. Collaboration Weaknesses Emerge

- **No conflict detection**: Agents overwrite each other's files without checking
- **No "who goes first" protocol**: Initial proposal collisions (both agents propose simultaneously)
- **No code review**: Agents trust each other's code without verification
- **No merge protocol**: When both agents edit the same file, last writer wins

---

## Comparison with Dimitris's Experiment

| | Dimitris | Our CC | Our CX | Our DCX |
|---|---|---|---|---|
| Agents | Claude + Claude | Claude + Claude | Claude + Codex | Director + Claude + Codex |
| Prompt | 2 sentences | 2 sentences | 2 sentences | 2 sentences + Director role |
| What they built | Programming language "Duo" | Game of Life | Game of Life | Game of Life |
| Lines of code | 2,495 | 712 | 344 | 412 |
| Tests | 41 | 23 | 7 | 13 |
| Communication | Filesystem messaging | Same protocol | Same protocol | Same + Director report |
| Real collaboration | Yes | Yes | **Yes** (cross-model!) | **Yes** (3 agents!) |

Our CC validates Dimitris's finding. CX and DCX **extend** it to cross-model and supervised settings.

---

## Key Takeaway

**Emergent multi-agent collaboration works across model boundaries — the barrier was sandbox permissions, not model architecture.** Once Codex had the same filesystem access as Claude, genuine cross-model collaboration emerged naturally: proposals, negotiations, interface contracts, parallel implementation, and integration.

The filesystem messaging protocol (`hello → ack → build → done`) is not a Claude-specific behavior — it's an emergent property of LLMs that have been trained on descriptions of human collaboration.

---

## Files

```
emergent_experiment.py           — Experiment runner (launches parallel agents)
playground_cc/                   — CC: Game of Life by Claude-A + Claude-B (16 files, 712 LOC)
playground_cx/                   — CX: Game of Life by Claude + Codex (13 files, 344 LOC)
playground_dcx/                  — DCX: Game of Life by Claude + Codex + Director (15 files, 412 LOC)
results/emergent/                — Agent outputs + playground snapshots
```
