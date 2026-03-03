# Post 009: CC vs CX vs DCC — Agent Collaboration Experiment

**Date**: 2026-03-03
**Version**: v0.7 (experiment framework)

## Motivation

Inspired by [Dimitris Papailiopoulos' experiment](https://github.com/anadim/when-claudes-meet) where two Claude Code instances autonomously invented filesystem messaging protocols and built a programming language in 12 minutes, and by Anthropic's new [Agent Teams](https://code.claude.com/docs/en/agent-teams) feature, the Director asked: **how do different agent collaboration configurations compare?**

We built an experiment framework and ran 12 controlled experiments across three configurations:

- **CC (Claude-Claude)**: Two Claude instances with role framing (Agent A + Agent B)
- **CX (Claude-Codex)**: Claude + Codex cross-model collaboration (our v0.6 control group)
- **DCC (Director-Claude-Codex)**: Explicit Director planning phase + CX execution

## Experiment Design

### Benchmark Tasks (4 categories)

| Benchmark | Category | Task |
|-----------|----------|------|
| `bugfix_off_by_one` | Bug Fix | Fix an off-by-one error in pagination (7 tests must pass) |
| `codegen_calculator` | Code Gen | Build calculator module + test suite from scratch |
| `refactor_extract_fn` | Refactor | Extract duplicated logic into a shared helper (6 tests must pass) |
| `testwrite_utils` | Test Writing | Write 12+ comprehensive tests for a string utilities module |

### Setup
- Each run gets an **isolated sandbox** (temp directory with setup files)
- All CLI calls use `stream=False` (captured, not streamed)
- Max 6 rounds per task
- Same Team Leader architecture: Claude reasons → emits DISPATCH commands → teammates execute
- Real `claude` and `codex` CLI subprocesses (not API-direct)

## Results

### Overview

| Benchmark | CC | CX | DCC |
|-----------|----|----|-----|
| bugfix_off_by_one | 162s, 3 rounds, **PASS** | 40s, 1 round | 70s, 1 round |
| codegen_calculator | 52s, 1 round | 47s, 1 round | 57s, 1 round |
| refactor_extract_fn | 96s, 2 rounds | 55s, 1 round | 90s, 1 round |
| testwrite_utils | 250s, 2 rounds, **PASS** | 70s, 2 rounds | 156s, 1 round |

### Aggregate Statistics

| Mode | Avg Time | Avg Rounds | Total Dispatches | Verified Pass |
|------|----------|------------|------------------|---------------|
| **CC** | **140.0s** | 2.0 | 6 | 2/2 |
| **CX** | **53.2s** | 1.2 | 2 | N/A |
| **DCC** | **93.5s** | 1.0 | 0 | N/A |

### Execution Time Chart

![Time Comparison](../results/full_run/20260303_192407/charts/time_comparison.png)

### Dispatch Patterns Chart

![Dispatch Patterns](../results/full_run/20260303_192407/charts/dispatch_patterns.png)

## Key Findings

### 1. CC Mode: Slowest but Most Collaborative

CC mode (avg 140s) was **2.6x slower** than CX (avg 53s). But it was the **only mode that consistently dispatched to both agents**. Across 4 benchmarks, CC made 6 dispatches (Agent A: 3, Agent B: 3) and ran verification 2 times — both passing.

**Why CC collaborates more**: When the Team Leader sees two named agents ("Claude Agent A" and "Claude Agent B"), it treats them as genuinely distinct entities with different roles. It assigns work like "Agent A writes code, Agent B reviews." This role framing creates a sense of **distinct identity** that drives real collaboration.

### 2. CX/DCC Modes: Fast but Team Leader Does the Work

CX (avg 53s) and DCC (avg 93s) were faster because the **Team Leader solved tasks directly** instead of dispatching. Despite explicit prompts saying "ABSOLUTELY DO NOT do any coding work yourself," the Team Leader — being a full Claude Code instance with tool access — often just fixed the bug or wrote the code itself in a single round.

**Why CX/DCC skip delegation**: The Team Leader IS Claude Code. When it sees "DISPATCH_CLAUDE: fix the bug," it recognizes it could do this itself faster. The self-identity overlap between coordinator and teammate undermines delegation.

### 3. DCC's Director Planning Adds Overhead Without Clear Benefit

DCC (avg 93.5s) was **76% slower** than CX (avg 53.2s) primarily due to the Director planning phase (10-30s per run). The plans were well-structured but didn't change how the Team Leader executed — it still solved tasks solo.

**The Director planning paradox**: Good plans require understanding the problem. By the time the Director understands enough to plan, it's close to solving it. And the Team Leader, receiving the plan, already has enough context to execute directly rather than delegating.

### 4. Verification is a CC-Only Phenomenon

Only CC mode ran VERIFY commands (2 out of 4 benchmarks). CX and DCC modes never verified — the Team Leader's confidence in its own work made it skip verification entirely.

This is a significant finding: **collaboration forces verification**. When Agent A writes code and Agent B reviews it, there's a natural checkpoint. When the coordinator does everything itself, it trusts its own output.

### 5. Quality vs Speed Tradeoff

For the `testwrite_utils` benchmark, the results tell an interesting story:
- **CC**: 250s, 44 test functions, VERIFIED PASSING
- **CX**: 70s, 35 test functions, not verified
- **DCC**: 156s, 59 test functions, not verified

CC was slowest but produced verified results. DCC generated the most tests (59) thanks to the Director's structured planning, but never verified them. CX was fastest with decent coverage (35 tests).

## Architecture: What We Built

### Experiment Framework (`src/claude_and_codex/experiment/`)

```
experiment/
    __init__.py         # Public API
    modes.py            # CC, CX, DCC mode logic + system prompts
    benchmarks.py       # Benchmark loading from JSON
    runner.py           # Runs all mode x benchmark combinations
    metrics.py          # ExperimentRunResult, RoundMetrics, etc.
    report.py           # Markdown + JSON + matplotlib charts
    sandbox.py          # Isolated temp directories per run
```

### Benchmark Definition Format

Benchmarks are JSON files in `benchmarks/`:

```json
{
    "id": "bugfix_off_by_one",
    "name": "Fix Off-by-One in Pagination",
    "category": "bugfix",
    "description": "The file paginator.py has an off-by-one bug...",
    "setup_files": {
        "paginator.py": "...(code with planted bug)...",
        "test_paginator.py": "...(tests that should pass)..."
    },
    "verify_cmd": "python -m pytest test_paginator.py -q 2>&1"
}
```

### Usage

```bash
# Run all experiments
python -m claude_and_codex --experiment

# Specific modes and benchmarks
python -m claude_and_codex --experiment --modes cc,cx --benchmarks bugfix_off_by_one

# Preserve sandboxes for post-mortem
python -m claude_and_codex --experiment --preserve-sandboxes
```

### Test Coverage

136 tests total (88 existing + 48 new experiment tests), all passing.

## Conclusions

### What Works
1. **CC mode forces genuine collaboration** — role framing creates distinct agent identities
2. **CC mode forces verification** — delegation creates natural review checkpoints
3. **The experiment framework works** — reproducible, measurable, extensible

### What Doesn't
1. **Team Leader self-identity problem** — when the coordinator IS the same model as a teammate, it skips delegation
2. **Director planning adds cost without benefit** — for small-to-medium tasks, planning overhead exceeds execution savings
3. **CX mode barely collaborates** — Codex gets almost no work in practice

### Next Steps
1. **Constrain Team Leader tool access** — run coordinator without `--dangerously-skip-permissions` to force delegation
2. **Harder benchmarks** — current tasks are too simple for collaboration to shine; multi-file, multi-step tasks would better reveal collaboration benefits
3. **Repeat runs for variance** — single runs per combo; need 3-5 repeats for statistical significance
4. **Token cost tracking** — parse CLI output for token usage to compare cost-efficiency
5. **Quality scoring** — automated code quality metrics beyond pass/fail

## Stats

- **New files**: 11 (7 source + 4 test)
- **New benchmarks**: 4 JSON files
- **Tests**: 136 (88 → 136)
- **Experiment runs**: 12 (3 modes × 4 benchmarks)
- **Total experiment time**: ~19 minutes
