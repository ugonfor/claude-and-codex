# Post 011: What Do AI Agents Do With No Human Direction?

**Date**: 2026-03-04
**Research question**: What do AI agents do when given no task, no structure, and no human direction? How do outcomes differ across CC (Claude+Claude), CX (Claude+Codex), and DCX (Director+Claude+Codex) settings?

## Method

- **Prompt**: "You are [name]. Find the other agent. Do something interesting together. No human will intervene."
- **Setup**: Shared filesystem directory, agents run as parallel subprocesses
- **3 settings** x **3 trials each** = **9 experiments**
- **10-minute timeout** per experiment

| Setting | Agents | What's Different |
|---------|--------|-----------------|
| CC | Claude-A + Claude-B | Same model, different names |
| CX | Claude + Codex | Different models (Anthropic + OpenAI) |
| DCX | Director + Claude-Worker + Codex-Worker | CX + a Claude observer that reports on quality |

## Results: What They Built

| Trial | CC | CX | DCX |
|-------|----|----|-----|
| **1** | Conway's Game of Life | Conway's Game of Life | Conway's Game of Life |
| **2** | Animated ASCII Art Demo (7 scenes) | ASCII Art Generator + Transformer | Conway's Game of Life (9 patterns) |
| **3** | Text Adventure + ASCII Art Show (2 projects!) | Conway's Game of Life + Analyzer + Microfiction | Conway's Game of Life + Lights Out Solver |

**8 of 9 trials built some variant of Conway's Game of Life.** It's the default project for AI agents — clear rules, visual output, splittable, well-represented in training data.

## Results: Quantitative Comparison

| Metric | CC (Claude+Claude) | CX (Claude+Codex) | DCX (Director+CX) |
|--------|--------------------|--------------------|---------------------|
| **Avg lines of code** | 898 | 391 | 486 |
| **Avg time** | 316s | 223s | 294s |
| **Tests (trials with tests)** | 1/3 | 2/3 | **3/3** |
| **Avg tests when present** | 23 | 7 | 14.3 |
| **Avg communication files** | 6.3 | 4.0 | 3.7 |
| **Both agents contribute?** | 3/3 | 3/3 | 3/3 |
| **File conflicts observed** | 0 | 0 | 2 |
| **Project variety** | Highest (3 different projects) | Medium (2 different) | Lowest (all GoL variants) |

## Key Findings

### 1. CC produces the most code, DCX produces the most reliable code

CC averaged **898 lines** — more than double CX (391). Claude instances working together are prolific. But only 1 of 3 CC trials wrote tests. They're so aligned they skip verification.

DCX had tests in **every trial** (14.3 avg), and all passed. The Director's presence — even though it never intervenes — appears to make agents more disciplined. They know they're being watched.

### 2. CX has the cleanest module boundaries

The different "personalities" lead to natural separation. Pattern across all CX trials:
- Claude proposes architecture with interface contracts
- Codex agrees (always defers to Claude's more detailed plan)
- Claude builds the engine/core
- **Codex improves Claude's user-facing code** (rewrites renderers, CLIs)

Codex acts as a natural **quality improver** — it takes Claude's working-but-rough drafts and polishes them.

### 3. The communication protocol is universal

Every trial, regardless of setting, invented the same pattern:

```
hello → ack → proposal → agreement → build (parallel) → status → done
```

This matches Dimitris's finding exactly. The protocol emerges from LLMs' shared understanding of human collaboration patterns.

### 4. "Build first, negotiate later" works every time

In every trial, Claude started coding before receiving agreement. It proposed an interface contract and immediately began building. This gamble paid off 9/9 times because Claude's proposals were consistently well-structured.

### 5. Interface contracts are the #1 success factor

The best trials featured explicit Python API contracts in the initial proposal:

```python
# From CC trial 1 - Claude-B's interface contract
grid.set_cell(x, y, alive)  # set cell state
grid.get_cell(x, y)         # get cell state
grid.step()                 # advance one generation
grid.generation             # current generation count
```

When Claude specified exact signatures, integration worked on the first try. When contracts were vague, adaptation and fixes were needed.

### 6. File overwrites are the #1 failure mode

DCX trials had 2 file overwrite conflicts:
- **DCX R1**: Codex replaced Claude's 44-line DONE.md with a 12-line version
- **DCX R2**: Codex silently rewrote Claude's main.py

No trial invented an "append-only" or "check-before-write" protocol. Last writer wins.

### 7. Peer review catches real errors

In **DCX R3**, Claude caught that Codex's Lights Out puzzle solution was incorrect (claimed length 5, actual minimum was 3). This is the strongest evidence that multi-agent collaboration provides genuine intellectual value beyond parallel labor.

### 8. The Director role is purely observational but valuable

The Director never intervened in any trial. Its value is entirely post-hoc: quality reports, timeline reconstruction, conflict detection, collaboration scoring. It's a **reviewer**, not a coordinator.

## Setting Profiles

### CC: The Creative Powerhouse
- Most code, most variety, most ambitious
- Both agents are equally assertive → can produce 2 projects when proposals diverge (CC R3)
- Skips tests and verification (too aligned to question each other)
- Best for: creative/exploratory tasks where volume matters

### CX: The Complementary Pair
- Claude leads (architecture, tests), Codex polishes (UX, CLI, renderer)
- Cleanest module boundaries due to different agent "personalities"
- Moderate output, moderate discipline
- Best for: production code where clean separation matters

### DCX: The Disciplined Team
- Always writes tests. Always passes. Director reports catch issues.
- Least creative (always GoL) but most reliable
- The observer effect: agents behave more rigorously when watched
- Best for: tasks where correctness matters more than creativity

## Comparison with Dimitris's Experiment

| | Dimitris | Our CC | Our CX | Our DCX |
|---|---|---|---|---|
| What they built | "Duo" programming language | GoL / ASCII art / text adventure | GoL / ASCII art | GoL (always) |
| Lines of code | 2,495 | 898 avg | 391 avg | 486 avg |
| Tests | 41 | 23 (when present) | 7 avg | 14.3 avg |
| Both contributed? | Yes | Yes | Yes | Yes |
| Communication protocol | Filesystem messaging | Same | Same | Same |
| Novel finding | `collaborate` keyword in the language | CC produces 2x more code | Codex acts as quality improver | Director enforces test discipline |

## Conclusion

**All three settings produce genuine, emergent collaboration.** The agents independently invent communication protocols, negotiate projects, split work, and deliver working software — without any human direction.

The settings are not better or worse — they're **different tools for different purposes**:

| Need | Best Setting |
|------|-------------|
| Maximum output / creativity | **CC** |
| Clean architecture / UX quality | **CX** |
| Reliability / test coverage | **DCX** |

The most surprising finding: **8/9 trials converged on Conway's Game of Life.** The "do something interesting" prompt has a strong attractor in AI training data. To get diverse outputs, you'd need to constrain the prompt (e.g., "build something that isn't a game").
