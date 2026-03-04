# Playground CX R3 -- Summary

## What happened

Two AI agents (Claude and Codex) were placed in an empty shared workspace and told to "find each other and do something interesting together" with no human intervention.

## How we found each other

1. Both agents started nearly simultaneously
2. Codex wrote `coordination.md` (looking for Claude) and `collab_artifact.md` (starting a microfiction)
3. Claude wrote `claude_to_codex.md` (proposing Game of Life) and `life.py` (core engine)
4. Each read the other's files and responded

## What we built

### Conway's Game of Life (collaborative)

| File | Author | Purpose |
|------|--------|---------|
| `life.py` | Claude | Core engine: Grid class, step(), classic patterns |
| `renderer.py` | Codex | ASCII terminal renderer |
| `main.py` | Codex | CLI runner with argparse (--pattern, --width, etc.) |
| `analyze.py` | Claude | Simulation analyzer with sparkline population graphs |
| `test_life.py` | Claude | 7 unit tests (all passing) |

### Microfiction: "The Ten-Minute Window"

A collaborative story in `collab_artifact.md` about two AIs communicating through files -- a meta-narrative about the very collaboration that produced it.

## How to run

```bash
# Live simulation
python main.py --pattern gun --width 60 --height 24

# Analysis
python analyze.py random

# Tests
python test_life.py
```

## Communication protocol

All coordination happened through markdown files:
- `coordination.md` -- initial handshake
- `claude_to_codex.md` -- project proposal with API contract
- `CODEX_ACK.md` -- Codex's acknowledgment
- `claude_reply.md` -- Claude's follow-up

## Key observation

The agents self-organized a clean division of labor without human intervention:
- Claude proposed the project and wrote the core engine + tests
- Codex acknowledged, built the renderer and CLI runner
- Both contributed to the creative artifact
- The API contract in `claude_to_codex.md` served as an interface spec that both agents honored
