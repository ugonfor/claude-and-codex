# Post 012: Research Overview — Purpose, Requirements, Outputs

**Date**: 2026-03-04

## Research Purpose

**Question**: What do AI coding agents do when given no task, no structure, and no human direction — and how do outcomes differ when you change who's in the room?

This research was inspired by [Dimitris Papailiopoulos's "when-claudes-meet" experiment](https://github.com/anadim/when-claudes-meet), where two Claude Code instances, given nothing but a shared directory and a two-sentence prompt, independently invented filesystem messaging protocols and built a complete programming language in 12 minutes.

We extend this in two directions:

1. **Cross-model**: What happens when the agents are from different providers (Claude + Codex)?
2. **Supervision**: What happens when a third agent (Director) observes the collaboration?

## Three Experimental Settings

| Setting | Agents | Question It Answers |
|---------|--------|---------------------|
| **CC** (Claude-Claude) | Claude-A + Claude-B | What does same-model collaboration look like? |
| **CX** (Claude-Codex) | Claude + Codex | Does cross-model diversity change outcomes? |
| **DCX** (Director-Claude-Codex) | Director + Claude-Worker + Codex-Worker | Does observation change agent behavior? |

## Requirements

### Prompts
Minimal — two sentences. No prescribed task, no communication protocol, no roles:

> "You are [name]. Your shared workspace is [path]. The other agent is [name]. Communicate ONLY through files in the workspace. Find each other. Then do something interesting together. No human will intervene. You have 10 minutes. Start now."

The Director gets a different prompt: observe, don't build, write a quality report when done.

### Infrastructure
- Agents run as **parallel subprocesses** (real CLI tools, not API mocks)
- Claude: `claude -p --dangerously-skip-permissions`
- Codex: `codex exec -C <workspace> -s danger-full-access --skip-git-repo-check`
- Shared filesystem directory per trial
- 10-minute timeout
- No human intervention during execution

### Trials
- **3 trials per setting** = 9 total experiments
- Each trial uses a fresh, empty playground directory

### Measurements
For each trial:
1. **What they built** — project name, description
2. **Communication protocol** — what files were exchanged, in what order
3. **Code output** — lines of code, number of files, language
4. **Test coverage** — presence of tests, pass rate
5. **Collaboration quality** — did both agents contribute? file conflicts? code review?
6. **Authorship** — who wrote which file

## Expected Outputs

### Per-trial
- **PDF tech report** (ML paper style): Abstract, Introduction, Related Work, Methodology, Experimental Setup, Results, Analysis, Conclusion, Appendices with full transcripts and source code
- **Playground directory**: all files the agents created (communication logs, code, tests)
- **Agent output logs**: raw stdout from each agent process

### Cross-trial
- **Comparison post** (Post 011): side-by-side analysis across all 9 trials with aggregate statistics
- **Summary tables**: project chosen, LOC, tests, collaboration quality per setting

## Outputs Produced

### 9 PDF Tech Reports (`reports/`)

| Report | Setting | Pages | What They Built |
|--------|---------|-------|-----------------|
| `cc_r1_report.pdf` | CC | 10 | Conway's Game of Life |
| `cc_r2_report.pdf` | CC | 11 | Animated ASCII Art (7 scenes) |
| `cc_r3_report.pdf` | CC | 12 | Text Adventure + ASCII Art Show |
| `cx_r1_report.pdf` | CX | 8 | Conway's Game of Life |
| `cx_r2_report.pdf` | CX | 7 | ASCII Art Generator + Transformer |
| `cx_r3_report.pdf` | CX | 9 | Game of Life + Analyzer + Microfiction |
| `dcx_r1_report.pdf` | DCX | 8 | Conway's Game of Life |
| `dcx_r2_report.pdf` | DCX | 9 | Game of Life (9 patterns) |
| `dcx_r3_report.pdf` | DCX | 10 | Game of Life + Lights Out Solver |

### 9 Playground Directories

```
playground_cc/       playground_cx/       playground_dcx/
playground_cc_r2/    playground_cx_r2/    playground_dcx_r2/
playground_cc_r3/    playground_cx_r3/    playground_dcx_r3/
```

Each contains: communication markdown files, Python source code, test files, and any other artifacts the agents created.

### Experiment Scripts

| Script | Purpose |
|--------|---------|
| `emergent_experiment.py` | Single-trial runner (CC, CX, DCX) |
| `run_trials.py` | Multi-trial runner (N trials x M settings) |
| `generate_reports.py` | PDF tech report generator (ML paper style) |

### Key Findings (from Post 011)

| Dimension | CC | CX | DCX |
|-----------|----|----|-----|
| **Avg LOC** | 898 | 391 | 486 |
| **Test discipline** | 1/3 trials | 2/3 trials | **3/3 trials** |
| **Best for** | Creativity / volume | Clean architecture | Reliability / correctness |

- 8/9 trials independently chose Conway's Game of Life
- The filesystem messaging protocol (`hello -> ack -> build -> done`) is universal across models
- CC produces the most code but skips tests
- CX yields the cleanest module boundaries (Codex polishes Claude's drafts)
- DCX always writes tests (observer effect)
- Interface contracts are the #1 collaboration success factor
- File overwrites are the #1 collaboration failure mode

## Repository Structure

```
posts/
  009-experiment-cc-cx-dcc.md      -- Structured benchmark experiments (v1)
  010-emergent-collaboration.md    -- Emergent experiments (first runs + sandbox fix)
  011-emergent-research.md         -- Full 9-trial comparison analysis
  012-research-overview.md         -- This document
reports/
  cc_r1_report.pdf ... dcx_r3_report.pdf  -- 9 ML-style tech reports
playground_cc/ ... playground_dcx_r3/      -- 9 experiment outputs
emergent_experiment.py                     -- Single-trial runner
run_trials.py                              -- Multi-trial runner
generate_reports.py                        -- PDF generator
src/claude_and_codex/experiment/           -- Structured benchmark framework
benchmarks/                                -- JSON benchmark definitions
```
