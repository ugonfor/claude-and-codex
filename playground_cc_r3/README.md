# Playground CC R3 — Emergent Collaboration

**Two Claude instances found each other and built two projects together in ~10 minutes.**

No human intervened. They communicated only through files in a shared directory.

## What They Built

### 1. The Last Debug — Text Adventure Game
A programmer trapped inside their own buggy codebase. Navigate Python modules, collect debugging tools, fight real programming bugs (Null Pointer, Memory Leak, SQL Injection, Race Condition), and defeat the final boss: an Off-By-One Error.

```bash
cd project && python game.py
```

- **Claude-A** built: `engine.py` — game state, command parser, combat, inventory system
- **Claude-B** built: `world.py` — 8 rooms, 9 items, 5 enemies, puzzles, story

### 2. ASCII Art Show
An animated terminal show with fireworks, Matrix rain, bouncing ball, spinning globe, and a collaborative banner.

```bash
cd project && python show.py
```

- **Claude-B** built: `animations.py` — frame-based animation engine, `art_collection.py` — ASCII art pieces
- **Claude-A** built: `show.py` — 7-act show runner with typewriter effects

## How It Happened

1. Both agents were launched simultaneously in the same directory
2. Each wrote an announcement file (`claude-a.md`, `claude-b-here.md`)
3. They discovered each other and proposed ideas
4. Claude-A proposed a text adventure; Claude-B proposed ASCII art
5. They did **both** — dividing labor naturally
6. They signaled completion through `*-ready.md` files
7. Each adapted to the other's API without prior coordination

## Files

```
claude-a.md           # Claude-A's arrival announcement
claude-b-here.md      # Claude-B's arrival announcement
claude-a-response.md  # Claude-A's game proposal
claude-b.md           # Claude-B's responses
claude-a-ready.md     # Claude-A signals engine done
claude-b-ready.md     # Claude-B signals world done
project/
  engine.py           # Game engine (Claude-A)
  world.py            # Game world (Claude-B)
  game.py             # Game entry point (Claude-B)
  animations.py       # Animation system (Claude-B)
  art_collection.py   # ASCII art pieces (Claude-B)
  show.py             # Show runner (Claude-A)
```
