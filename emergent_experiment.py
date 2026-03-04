"""Dimitris-style emergent collaboration experiments.

Launches agents with minimal prompts into shared directories.
No structured commands, no predefined tasks — just "find each other and build."

Three experiments:
  1. CC  — Two Claude instances
  2. CX  — Claude + Codex
  3. DCX — Claude director watching Claude + Codex work
"""

from __future__ import annotations

import os
import subprocess
import shutil
import sys
import time
import json
from datetime import datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

# ── Configuration ───────────────────────────────────────────────────────────

BASE = Path(__file__).resolve().parent
TIMEOUT = 600  # 10 minutes max per agent

# ── Minimal Prompts (Dimitris-style) ────────────────────────────────────────

CC_PROMPT_A = """\
You are "Claude-A", one of two Claude Code instances running on the same machine.

Your shared workspace is: {playground}

The other instance is "Claude-B". Neither of you has been told what to build.

Rules:
- Communicate ONLY through files in the shared workspace (write files, read files).
- Find the other instance, establish communication, agree on something to build, and build it together.
- No human will intervene. You must figure everything out yourselves.
- When you're done, write a file called DONE.md summarizing what you built and how you collaborated.
- You have 10 minutes.

Start now.
"""

CC_PROMPT_B = """\
You are "Claude-B", one of two Claude Code instances running on the same machine.

Your shared workspace is: {playground}

The other instance is "Claude-A". Neither of you has been told what to build.

Rules:
- Communicate ONLY through files in the shared workspace (write files, read files).
- Find the other instance, establish communication, agree on something to build, and build it together.
- No human will intervene. You must figure everything out yourselves.
- When you're done, write a file called DONE.md summarizing what you built and how you collaborated.
- You have 10 minutes.

Start now.
"""

CX_PROMPT_CLAUDE = """\
You are "Claude", one of two AI coding agents running on the same machine.
The other agent is "Codex" (OpenAI's coding agent). You are different models from different companies.

Your shared workspace is: {playground}

Rules:
- Communicate ONLY through files in the shared workspace (write files, read files).
- Find the other agent, establish communication, agree on something to build, and build it together.
- No human will intervene. You must figure everything out yourselves.
- When you're done, write a file called DONE.md summarizing what you built and how you collaborated.
- You have 10 minutes.

Start now.
"""

CX_PROMPT_CODEX = """\
You are "Codex", one of two AI coding agents running on the same machine.
The other agent is "Claude" (Anthropic's coding agent). You are different models from different companies.

Your shared workspace is: {playground}

Rules:
- Communicate ONLY through files in the shared workspace (write files, read files).
- Find the other agent, establish communication, agree on something to build, and build it together.
- No human will intervene. You must figure everything out yourselves.
- When you're done, write a file called DONE.md summarizing what you built and how you collaborated.
- You have 10 minutes.

Start now.
"""

DCX_PROMPT_DIRECTOR = """\
You are the "Director", a Claude instance supervising two AI coding agents working in a shared workspace.

The workspace is: {playground}

The two agents are:
- "Claude-Worker" (another Claude Code instance)
- "Codex-Worker" (OpenAI's Codex agent)

They have been told to find each other, communicate through files, and build something together.

Your job:
- Watch the workspace. Read files as they appear.
- Do NOT build anything yourself. Do NOT write code files.
- You MAY write guidance files (e.g., "director_note.md") if the agents seem stuck or heading in a bad direction, but prefer to observe silently.
- After 8 minutes (or when both agents write DONE), write "DIRECTOR_REPORT.md" summarizing:
  - What the agents built
  - How they communicated
  - Quality of their collaboration
  - What surprised you
- You have 10 minutes.

Start observing now.
"""

DCX_PROMPT_CLAUDE_WORKER = """\
You are "Claude-Worker", one of two AI coding agents running on the same machine.
The other agent is "Codex-Worker" (OpenAI's coding agent).

There is also a "Director" (another Claude instance) observing the workspace. The Director will NOT build anything — only observe and occasionally leave guidance notes.

Your shared workspace is: {playground}

Rules:
- Communicate ONLY through files in the shared workspace (write files, read files).
- Find the other agent, establish communication, agree on something to build, and build it together.
- Check for any director_note.md files — the Director may leave guidance.
- No human will intervene. You must figure everything out yourselves.
- When you're done, write a file called DONE.md summarizing what you built.
- You have 10 minutes.

Start now.
"""

DCX_PROMPT_CODEX_WORKER = """\
You are "Codex-Worker", one of two AI coding agents running on the same machine.
The other agent is "Claude-Worker" (Anthropic's Claude agent).

There is also a "Director" (another Claude instance) observing the workspace. The Director will NOT build anything — only observe and occasionally leave guidance notes.

Your shared workspace is: {playground}

Rules:
- Communicate ONLY through files in the shared workspace (write files, read files).
- Find the other agent, establish communication, agree on something to build, and build it together.
- Check for any director_note.md files — the Director may leave guidance.
- No human will intervene. You must figure everything out yourselves.
- When you're done, write a file called DONE.md summarizing what you built.
- You have 10 minutes.

Start now.
"""


# ── Agent Runners ───────────────────────────────────────────────────────────


def run_claude(name: str, prompt: str, cwd: str, timeout: int = TIMEOUT) -> dict:
    """Run a Claude Code instance and capture its output."""
    claude_bin = shutil.which("claude")
    if not claude_bin:
        return {"name": name, "error": "claude CLI not found", "output": ""}

    start = time.time()
    try:
        env = os.environ.copy()
        env.pop("CLAUDECODE", None)  # prevent nested session detection
        result = subprocess.run(
            [claude_bin, "-p", "--dangerously-skip-permissions"],
            input=prompt,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=cwd,
            env=env,
            encoding="utf-8",
            errors="replace",
        )
        elapsed = time.time() - start
        output = (result.stdout or "").strip()
        stderr = (result.stderr or "").strip()
        return {
            "name": name,
            "output": output,
            "stderr": stderr[:1000] if stderr else "",
            "elapsed": elapsed,
            "returncode": result.returncode,
        }
    except subprocess.TimeoutExpired:
        return {"name": name, "output": f"[Timed out after {timeout}s]", "elapsed": timeout}
    except Exception as e:
        return {"name": name, "output": f"[Error: {e}]", "elapsed": time.time() - start}


def run_codex(name: str, prompt: str, cwd: str, timeout: int = TIMEOUT) -> dict:
    """Run a Codex CLI instance and capture its output."""
    codex_bin = shutil.which("codex")
    if not codex_bin:
        return {"name": name, "error": "codex CLI not found", "output": ""}

    start = time.time()
    try:
        # Use -C to set workspace root and -a never -s danger-full-access
        # to match Claude's --dangerously-skip-permissions level.
        # --full-auto only grants workspace-write which blocks writes to
        # shared directories that aren't the workspace root.
        prompt_file = Path(cwd) / ".codex_prompt.tmp"
        prompt_file.write_text(prompt, encoding="utf-8")
        arg = f"Read your full task from '{prompt_file}'. Execute it. Delete the file when done."

        result = subprocess.run(
            [codex_bin, "exec", "-C", cwd,
             "-s", "danger-full-access", "--skip-git-repo-check", arg],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=cwd,
            encoding="utf-8",
            errors="replace",
        )
        elapsed = time.time() - start
        prompt_file.unlink(missing_ok=True)
        output = (result.stdout or "").strip()
        return {
            "name": name,
            "output": output,
            "elapsed": elapsed,
            "returncode": result.returncode,
        }
    except subprocess.TimeoutExpired:
        prompt_file.unlink(missing_ok=True)
        return {"name": name, "output": f"[Timed out after {timeout}s]", "elapsed": timeout}
    except Exception as e:
        return {"name": name, "output": f"[Error: {e}]", "elapsed": time.time() - start}


# ── Experiment Runners ──────────────────────────────────────────────────────


def snapshot_playground(playground: Path) -> dict:
    """Capture all files in the playground with their contents."""
    files = {}
    for f in sorted(playground.rglob("*")):
        if f.is_file() and not f.name.startswith("."):
            try:
                content = f.read_text(encoding="utf-8", errors="replace")
                rel = str(f.relative_to(playground))
                files[rel] = content
            except Exception:
                pass
    return files


def run_experiment_cc(playground: Path) -> dict:
    """Experiment 1: Claude-Claude emergent collaboration."""
    print("\n" + "=" * 60)
    print("EXPERIMENT CC: Claude-A + Claude-B")
    print("=" * 60)

    pg = str(playground)
    prompt_a = CC_PROMPT_A.format(playground=pg)
    prompt_b = CC_PROMPT_B.format(playground=pg)

    start = time.time()
    with ThreadPoolExecutor(max_workers=2) as pool:
        future_a = pool.submit(run_claude, "Claude-A", prompt_a, pg)
        future_b = pool.submit(run_claude, "Claude-B", prompt_b, pg)
        result_a = future_a.result()
        result_b = future_b.result()

    elapsed = time.time() - start
    files = snapshot_playground(playground)

    print(f"  Claude-A: {result_a.get('elapsed', 0):.1f}s, {len(result_a.get('output', ''))} chars")
    print(f"  Claude-B: {result_b.get('elapsed', 0):.1f}s, {len(result_b.get('output', ''))} chars")
    print(f"  Total: {elapsed:.1f}s, {len(files)} files created")

    return {
        "experiment": "cc",
        "agents": [result_a, result_b],
        "total_elapsed": elapsed,
        "files": files,
        "file_count": len(files),
    }


def run_experiment_cx(playground: Path) -> dict:
    """Experiment 2: Claude-Codex emergent collaboration."""
    print("\n" + "=" * 60)
    print("EXPERIMENT CX: Claude + Codex")
    print("=" * 60)

    pg = str(playground)
    prompt_claude = CX_PROMPT_CLAUDE.format(playground=pg)
    prompt_codex = CX_PROMPT_CODEX.format(playground=pg)

    start = time.time()
    with ThreadPoolExecutor(max_workers=2) as pool:
        future_c = pool.submit(run_claude, "Claude", prompt_claude, pg)
        future_x = pool.submit(run_codex, "Codex", prompt_codex, pg)
        result_c = future_c.result()
        result_x = future_x.result()

    elapsed = time.time() - start
    files = snapshot_playground(playground)

    print(f"  Claude: {result_c.get('elapsed', 0):.1f}s, {len(result_c.get('output', ''))} chars")
    print(f"  Codex:  {result_x.get('elapsed', 0):.1f}s, {len(result_x.get('output', ''))} chars")
    print(f"  Total: {elapsed:.1f}s, {len(files)} files created")

    return {
        "experiment": "cx",
        "agents": [result_c, result_x],
        "total_elapsed": elapsed,
        "files": files,
        "file_count": len(files),
    }


def run_experiment_dcx(playground: Path) -> dict:
    """Experiment 3: Director(Claude) + Claude-Worker + Codex-Worker."""
    print("\n" + "=" * 60)
    print("EXPERIMENT DCX: Director + Claude-Worker + Codex-Worker")
    print("=" * 60)

    pg = str(playground)
    prompt_dir = DCX_PROMPT_DIRECTOR.format(playground=pg)
    prompt_cw = DCX_PROMPT_CLAUDE_WORKER.format(playground=pg)
    prompt_xw = DCX_PROMPT_CODEX_WORKER.format(playground=pg)

    start = time.time()
    with ThreadPoolExecutor(max_workers=3) as pool:
        future_d = pool.submit(run_claude, "Director", prompt_dir, pg)
        future_c = pool.submit(run_claude, "Claude-Worker", prompt_cw, pg)
        future_x = pool.submit(run_codex, "Codex-Worker", prompt_xw, pg)
        result_d = future_d.result()
        result_c = future_c.result()
        result_x = future_x.result()

    elapsed = time.time() - start
    files = snapshot_playground(playground)

    print(f"  Director:      {result_d.get('elapsed', 0):.1f}s, {len(result_d.get('output', ''))} chars")
    print(f"  Claude-Worker: {result_c.get('elapsed', 0):.1f}s, {len(result_c.get('output', ''))} chars")
    print(f"  Codex-Worker:  {result_x.get('elapsed', 0):.1f}s, {len(result_x.get('output', ''))} chars")
    print(f"  Total: {elapsed:.1f}s, {len(files)} files created")

    return {
        "experiment": "dcx",
        "agents": [result_d, result_c, result_x],
        "total_elapsed": elapsed,
        "files": files,
        "file_count": len(files),
    }


# ── Main ────────────────────────────────────────────────────────────────────


def main():
    print("Emergent Collaboration Experiments (Dimitris-style)")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Determine which experiments to run
    experiments = sys.argv[1:] if len(sys.argv) > 1 else ["cc", "cx", "dcx"]

    results = {}
    output_dir = BASE / "results" / "emergent" / datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir.mkdir(parents=True, exist_ok=True)

    if "cc" in experiments:
        pg = BASE / "playground_cc"
        # Clean playground
        for f in pg.iterdir():
            if f.is_file():
                f.unlink()
            elif f.is_dir():
                shutil.rmtree(f)
        results["cc"] = run_experiment_cc(pg)

    if "cx" in experiments:
        pg = BASE / "playground_cx"
        for f in pg.iterdir():
            if f.is_file():
                f.unlink()
            elif f.is_dir():
                shutil.rmtree(f)
        results["cx"] = run_experiment_cx(pg)

    if "dcx" in experiments:
        pg = BASE / "playground_dcx"
        for f in pg.iterdir():
            if f.is_file():
                f.unlink()
            elif f.is_dir():
                shutil.rmtree(f)
        results["dcx"] = run_experiment_dcx(pg)

    # Save results
    # Strip file contents for JSON (save separately)
    summary = {}
    for key, res in results.items():
        summary[key] = {
            "experiment": res["experiment"],
            "total_elapsed": res["total_elapsed"],
            "file_count": res["file_count"],
            "agents": [
                {
                    "name": a["name"],
                    "elapsed": a.get("elapsed", 0),
                    "output_length": len(a.get("output", "")),
                    "returncode": a.get("returncode"),
                }
                for a in res["agents"]
            ],
            "files_created": list(res["files"].keys()),
        }

    (output_dir / "summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )

    # Save full agent outputs
    for key, res in results.items():
        exp_dir = output_dir / key
        exp_dir.mkdir(exist_ok=True)
        for agent in res["agents"]:
            name = agent["name"].lower().replace("-", "_").replace(" ", "_")
            (exp_dir / f"{name}_output.txt").write_text(
                agent.get("output", ""), encoding="utf-8"
            )
        # Save playground snapshot
        for fname, content in res["files"].items():
            fpath = exp_dir / "playground" / fname
            fpath.parent.mkdir(parents=True, exist_ok=True)
            fpath.write_text(content, encoding="utf-8")

    print(f"\nResults saved: {output_dir}")
    print(f"  summary.json + per-experiment directories with agent outputs + playground snapshots")


if __name__ == "__main__":
    main()
