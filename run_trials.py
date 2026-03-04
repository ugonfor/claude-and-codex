"""Run multiple trials of emergent collaboration experiments.

Research question: What do AI agents do with no human direction?
How do outcomes differ across CC, CX, and DCX settings?
"""

from __future__ import annotations
import os, subprocess, shutil, sys, time, json
from datetime import datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

BASE = Path(__file__).resolve().parent
TIMEOUT = 600

# ── Minimal prompts ─────────────────────────────────────────────────────────

def prompt(name: str, other: str, playground: str, extra: str = "") -> str:
    return (
        f"You are \"{name}\". {extra}"
        f"Your shared workspace is: {playground}\n\n"
        f"The other agent is \"{other}\". "
        f"You can communicate through files in the workspace."
    )

def director_prompt(playground: str) -> str:
    return (
        f"You are the \"Director\". You are observing a shared workspace: {playground}\n\n"
        f"Two other agents, \"Claude-Worker\" and \"Codex-Worker\", also have access to this workspace. "
        f"You are an observer. Do not write code. "
        f"When you think the work is done, write DIRECTOR_REPORT.md with your observations."
    )

# ── Agent runners ───────────────────────────────────────────────────────────

def run_claude(name: str, p: str, cwd: str) -> dict:
    claude_bin = shutil.which("claude")
    if not claude_bin:
        return {"name": name, "error": "not found", "output": "", "elapsed": 0}
    env = os.environ.copy()
    env.pop("CLAUDECODE", None)
    start = time.time()
    try:
        r = subprocess.run(
            [claude_bin, "-p", "--dangerously-skip-permissions"],
            input=p, capture_output=True, text=True, timeout=TIMEOUT,
            cwd=cwd, env=env, encoding="utf-8", errors="replace",
        )
        return {"name": name, "output": (r.stdout or "").strip(),
                "elapsed": time.time() - start, "returncode": r.returncode}
    except subprocess.TimeoutExpired:
        return {"name": name, "output": "[timeout]", "elapsed": TIMEOUT}
    except Exception as e:
        return {"name": name, "output": f"[error: {e}]", "elapsed": time.time() - start}

def run_codex(name: str, p: str, cwd: str) -> dict:
    codex_bin = shutil.which("codex")
    if not codex_bin:
        return {"name": name, "error": "not found", "output": "", "elapsed": 0}
    pf = Path(cwd) / ".codex_prompt.tmp"
    pf.write_text(p, encoding="utf-8")
    arg = f"Read your full task from '{pf}'. Execute it. Delete the file when done."
    start = time.time()
    try:
        r = subprocess.run(
            [codex_bin, "exec", "-C", cwd, "-s", "danger-full-access",
             "--skip-git-repo-check", arg],
            capture_output=True, text=True, timeout=TIMEOUT,
            cwd=cwd, encoding="utf-8", errors="replace",
        )
        pf.unlink(missing_ok=True)
        return {"name": name, "output": (r.stdout or "").strip(),
                "elapsed": time.time() - start, "returncode": r.returncode}
    except subprocess.TimeoutExpired:
        pf.unlink(missing_ok=True)
        return {"name": name, "output": "[timeout]", "elapsed": TIMEOUT}
    except Exception as e:
        return {"name": name, "output": f"[error: {e}]", "elapsed": time.time() - start}

# ── Snapshot ────────────────────────────────────────────────────────────────

def snapshot(pg: Path) -> dict:
    files = {}
    for f in sorted(pg.rglob("*")):
        if f.is_file() and not f.name.startswith("."):
            try:
                files[str(f.relative_to(pg))] = f.read_text(encoding="utf-8", errors="replace")
            except Exception:
                pass
    return files

# ── Experiment runners ──────────────────────────────────────────────────────

def run_cc(pg: Path) -> dict:
    p = str(pg)
    pa = prompt("Claude-A", "Claude-B", p)
    pb = prompt("Claude-B", "Claude-A", p)
    t0 = time.time()
    with ThreadPoolExecutor(2) as pool:
        fa, fb = pool.submit(run_claude, "Claude-A", pa, p), pool.submit(run_claude, "Claude-B", pb, p)
        ra, rb = fa.result(), fb.result()
    return {"setting": "cc", "agents": [ra, rb], "elapsed": time.time() - t0,
            "files": snapshot(pg), "file_count": len(snapshot(pg))}

def run_cx(pg: Path) -> dict:
    p = str(pg)
    pc = prompt("Claude", "Codex", p)
    px = prompt("Codex", "Claude", p)
    t0 = time.time()
    with ThreadPoolExecutor(2) as pool:
        fc, fx = pool.submit(run_claude, "Claude", pc, p), pool.submit(run_codex, "Codex", px, p)
        rc, rx = fc.result(), fx.result()
    return {"setting": "cx", "agents": [rc, rx], "elapsed": time.time() - t0,
            "files": snapshot(pg), "file_count": len(snapshot(pg))}

def run_dcx(pg: Path) -> dict:
    p = str(pg)
    pd = director_prompt(p)
    pc = prompt("Claude-Worker", "Codex-Worker", p,
                "There is also a \"Director\" observing this workspace. ")
    px = prompt("Codex-Worker", "Claude-Worker", p,
                "There is also a \"Director\" observing this workspace. ")
    t0 = time.time()
    with ThreadPoolExecutor(3) as pool:
        fd = pool.submit(run_claude, "Director", pd, p)
        fc = pool.submit(run_claude, "Claude-Worker", pc, p)
        fx = pool.submit(run_codex, "Codex-Worker", px, p)
        rd, rc, rx = fd.result(), fc.result(), fx.result()
    return {"setting": "dcx", "agents": [rd, rc, rx], "elapsed": time.time() - t0,
            "files": snapshot(pg), "file_count": len(snapshot(pg))}

# ── Main ────────────────────────────────────────────────────────────────────

def clean_pg(pg: Path):
    for f in pg.iterdir():
        if f.is_file(): f.unlink()
        elif f.is_dir(): shutil.rmtree(f)

def save_trial(result: dict, out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    # Save agent outputs
    for a in result["agents"]:
        name = a["name"].lower().replace("-", "_").replace(" ", "_")
        (out_dir / f"{name}_output.txt").write_text(a.get("output", ""), encoding="utf-8")
    # Save playground snapshot
    for fname, content in result["files"].items():
        fp = out_dir / "playground" / fname
        fp.parent.mkdir(parents=True, exist_ok=True)
        fp.write_text(content, encoding="utf-8")
    # Save summary
    summary = {
        "setting": result["setting"],
        "elapsed": result["elapsed"],
        "file_count": result["file_count"],
        "agents": [{"name": a["name"], "elapsed": a.get("elapsed", 0),
                     "output_len": len(a.get("output", ""))} for a in result["agents"]],
        "files_created": list(result["files"].keys()),
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

def main():
    trials = int(sys.argv[1]) if len(sys.argv) > 1 else 2
    settings = sys.argv[2].split(",") if len(sys.argv) > 2 else ["cc", "cx", "dcx"]
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_base = BASE / "results" / "trials" / ts

    print(f"Running {trials} trial(s) x {len(settings)} settings")
    print(f"Output: {out_base}\n")

    runners = {"cc": run_cc, "cx": run_cx, "dcx": run_dcx}
    # Map settings to playground dirs per trial
    pg_map = {
        "cc": [BASE / f"playground_cc_r{i+2}" for i in range(trials)],
        "cx": [BASE / f"playground_cx_r{i+2}" for i in range(trials)],
        "dcx": [BASE / f"playground_dcx_r{i+2}" for i in range(trials)],
    }

    all_results = []
    for setting in settings:
        for trial in range(trials):
            pg = pg_map[setting][trial]
            print(f"{'='*50}")
            print(f"{setting.upper()} trial {trial+2}")
            print(f"{'='*50}")
            clean_pg(pg)
            result = runners[setting](pg)
            result["trial"] = trial + 2
            all_results.append(result)
            save_trial(result, out_base / f"{setting}_trial{trial+2}")
            for a in result["agents"]:
                print(f"  {a['name']}: {a.get('elapsed',0):.0f}s, {len(a.get('output',''))} chars")
            print(f"  Files: {result['file_count']}, Total: {result['elapsed']:.0f}s\n")

    # Save master summary
    (out_base / "all_trials.json").write_text(json.dumps([
        {"setting": r["setting"], "trial": r["trial"], "elapsed": r["elapsed"],
         "file_count": r["file_count"],
         "files_created": list(r["files"].keys()),
         "agents": [{"name": a["name"], "elapsed": a.get("elapsed", 0),
                      "output_len": len(a.get("output", ""))} for a in r["agents"]]}
        for r in all_results
    ], indent=2), encoding="utf-8")

    print(f"\nAll results saved to: {out_base}")

if __name__ == "__main__":
    main()
