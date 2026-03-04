"""Run experiments with full logging for replay and investigation.

Captures:
  1. Agent output streams (every line with timestamp)
  2. Filesystem events (every file create/modify/delete with timestamp + content)
  3. Periodic playground snapshots
  4. Combined timeline for replay

Output structure:
  logs/{trial_id}/
    timeline.jsonl           -- Combined chronological events (THE replay file)
    agent_{name}.jsonl       -- Per-agent raw output stream
    fs_events.jsonl          -- Filesystem events only
    playground_final/        -- Final state of all files
"""

from __future__ import annotations
import hashlib, json, os, shutil, subprocess, sys, threading, time
from datetime import datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

BASE = Path(__file__).resolve().parent
TIMEOUT = 600

# ── Prompts (minimal) ──────────────────────────────────────────────────────

def prompt(name: str, other: str, playground: str, extra: str = "") -> str:
    return (f'You are "{name}". {extra}'
            f'Your shared workspace is: {playground}\n\n'
            f'The other agent is "{other}". '
            f'You can communicate through files in the workspace.')

def director_prompt(playground: str) -> str:
    return (f'You are the "Director". You are observing a shared workspace: {playground}\n\n'
            f'Two other agents, "Claude-Worker" and "Codex-Worker", also have access. '
            f'You are an observer. Do not write code. '
            f'When you think the work is done, write DIRECTOR_REPORT.md with your observations.')

# ── Timeline Logger ─────────────────────────────────────────────────────────

class TimelineLogger:
    """Thread-safe logger that writes JSONL events with timestamps."""

    def __init__(self, log_dir: Path):
        self.log_dir = log_dir
        log_dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._timeline_f = open(log_dir / "timeline.jsonl", "w", encoding="utf-8")
        self._fs_f = open(log_dir / "fs_events.jsonl", "w", encoding="utf-8")
        self._agent_files: dict[str, object] = {}
        self._t0 = time.time()

    def _ts(self) -> dict:
        now = time.time()
        return {
            "wall_clock": datetime.now().isoformat(timespec="milliseconds"),
            "elapsed_s": round(now - self._t0, 3),
        }

    def _write(self, f, event: dict):
        with self._lock:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")
            f.flush()

    def _write_timeline(self, event: dict):
        self._write(self._timeline_f, event)

    def agent_output(self, agent: str, line: str):
        event = {**self._ts(), "type": "agent_output", "agent": agent, "content": line.rstrip("\n")}
        self._write_timeline(event)
        # Per-agent file
        if agent not in self._agent_files:
            self._agent_files[agent] = open(
                self.log_dir / f"agent_{agent.lower().replace('-','_')}.jsonl",
                "w", encoding="utf-8")
        self._write(self._agent_files[agent], event)

    def agent_start(self, agent: str, cmd: list[str], prompt_text: str):
        event = {**self._ts(), "type": "agent_start", "agent": agent,
                 "command": cmd, "prompt": prompt_text}
        self._write_timeline(event)

    def agent_end(self, agent: str, returncode: int | None, elapsed: float):
        event = {**self._ts(), "type": "agent_end", "agent": agent,
                 "returncode": returncode, "elapsed_s": round(elapsed, 3)}
        self._write_timeline(event)

    def fs_event(self, event_type: str, path: str, content: str | None = None):
        event = {**self._ts(), "type": "fs_event", "fs_type": event_type,
                 "path": path}
        if content is not None:
            event["content"] = content
            event["size_bytes"] = len(content.encode("utf-8", errors="replace"))
        self._write_timeline(event)
        self._write(self._fs_f, event)

    def note(self, message: str):
        event = {**self._ts(), "type": "note", "message": message}
        self._write_timeline(event)

    def close(self):
        self._timeline_f.close()
        self._fs_f.close()
        for f in self._agent_files.values():
            f.close()


# ── Filesystem Watcher ──────────────────────────────────────────────────────

class PlaygroundWatcher(FileSystemEventHandler):
    """Watches a directory and logs every file change."""

    def __init__(self, logger: TimelineLogger, playground: Path):
        self.logger = logger
        self.playground = playground

    def _rel(self, path: str) -> str:
        try:
            return str(Path(path).relative_to(self.playground))
        except ValueError:
            return path

    def _read_content(self, path: str) -> str | None:
        try:
            p = Path(path)
            if p.is_file() and p.stat().st_size < 100_000:
                return p.read_text(encoding="utf-8", errors="replace")
        except Exception:
            pass
        return None

    def on_created(self, event):
        if event.is_directory or "__pycache__" in event.src_path:
            return
        rel = self._rel(event.src_path)
        if rel.startswith("."):
            return
        content = self._read_content(event.src_path)
        self.logger.fs_event("created", rel, content)

    def on_modified(self, event):
        if event.is_directory or "__pycache__" in event.src_path:
            return
        rel = self._rel(event.src_path)
        if rel.startswith("."):
            return
        content = self._read_content(event.src_path)
        self.logger.fs_event("modified", rel, content)

    def on_deleted(self, event):
        if event.is_directory:
            return
        rel = self._rel(event.src_path)
        self.logger.fs_event("deleted", rel)


# ── Agent Runners (streaming with logging) ──────────────────────────────────

def run_claude_logged(name: str, p: str, cwd: str,
                      logger: TimelineLogger) -> dict:
    claude_bin = shutil.which("claude")
    if not claude_bin:
        return {"name": name, "error": "not found", "output": "", "elapsed": 0}

    env = os.environ.copy()
    env.pop("CLAUDECODE", None)
    # Use stream-json for full structured logging (tool calls, messages, usage)
    cmd = [claude_bin, "-p", "--dangerously-skip-permissions",
           "--output-format", "stream-json", "--verbose"]
    logger.agent_start(name, cmd, p)

    start = time.time()
    output_lines = []
    try:
        proc = subprocess.Popen(
            cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, cwd=cwd, env=env,
            encoding="utf-8", errors="replace",
        )
        if proc.stdin:
            proc.stdin.write(p)
            proc.stdin.close()

        deadline = time.time() + TIMEOUT
        for line in iter(proc.stdout.readline, ""):
            if time.time() > deadline:
                proc.kill()
                logger.note(f"{name} timed out")
                break
            output_lines.append(line)
            # Parse JSON events for richer logging
            stripped = line.strip()
            if stripped.startswith("{"):
                try:
                    event = json.loads(stripped)
                    logger.agent_output(name, stripped)
                except json.JSONDecodeError:
                    logger.agent_output(name, line)
            else:
                logger.agent_output(name, line)
        proc.wait(timeout=5)
        elapsed = time.time() - start
        logger.agent_end(name, proc.returncode, elapsed)
        return {"name": name, "output": "".join(output_lines).strip(),
                "elapsed": elapsed, "returncode": proc.returncode}
    except Exception as e:
        elapsed = time.time() - start
        logger.agent_end(name, None, elapsed)
        return {"name": name, "output": f"[error: {e}]", "elapsed": elapsed}


def run_codex_logged(name: str, p: str, cwd: str,
                     logger: TimelineLogger) -> dict:
    codex_bin = shutil.which("codex")
    if not codex_bin:
        return {"name": name, "error": "not found", "output": "", "elapsed": 0}

    pf = Path(cwd) / ".codex_prompt.tmp"
    pf.write_text(p, encoding="utf-8")
    arg = f"Read your full task from '{pf}'. Execute it. Delete the file when done."
    cmd = [codex_bin, "exec", "-C", cwd, "-s", "danger-full-access",
           "--skip-git-repo-check", "--json", arg]
    logger.agent_start(name, cmd, p)

    start = time.time()
    output_lines = []
    try:
        proc = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            cwd=cwd, encoding="utf-8", errors="replace",
        )
        deadline = time.time() + TIMEOUT
        for line in iter(proc.stdout.readline, ""):
            if time.time() > deadline:
                proc.kill()
                logger.note(f"{name} timed out")
                break
            output_lines.append(line)
            logger.agent_output(name, line)
        proc.wait(timeout=5)
        pf.unlink(missing_ok=True)
        elapsed = time.time() - start
        logger.agent_end(name, proc.returncode, elapsed)
        return {"name": name, "output": "".join(output_lines).strip(),
                "elapsed": elapsed, "returncode": proc.returncode}
    except Exception as e:
        pf.unlink(missing_ok=True)
        elapsed = time.time() - start
        logger.agent_end(name, None, elapsed)
        return {"name": name, "output": f"[error: {e}]", "elapsed": elapsed}


# ── Save final playground state ─────────────────────────────────────────────

def save_final_state(pg: Path, log_dir: Path):
    dest = log_dir / "playground_final"
    dest.mkdir(exist_ok=True)
    for f in sorted(pg.rglob("*")):
        if f.is_file() and "__pycache__" not in str(f) and not f.name.startswith("."):
            rel = f.relative_to(pg)
            out = dest / rel
            out.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(f, out)


# ── Experiment Runners ──────────────────────────────────────────────────────

def run_cc_logged(pg: Path, log_dir: Path) -> dict:
    logger = TimelineLogger(log_dir)
    logger.note("Experiment CC started")

    observer = Observer()
    observer.schedule(PlaygroundWatcher(logger, pg), str(pg), recursive=True)
    observer.start()

    p = str(pg)
    pa = prompt("Claude-A", "Claude-B", p)
    pb = prompt("Claude-B", "Claude-A", p)

    t0 = time.time()
    with ThreadPoolExecutor(2) as pool:
        fa = pool.submit(run_claude_logged, "Claude-A", pa, p, logger)
        fb = pool.submit(run_claude_logged, "Claude-B", pb, p, logger)
        ra, rb = fa.result(), fb.result()

    observer.stop()
    observer.join()
    logger.note(f"Experiment CC finished in {time.time()-t0:.1f}s")
    save_final_state(pg, log_dir)
    logger.close()

    return {"setting": "cc", "agents": [ra, rb], "elapsed": time.time() - t0}


def run_cx_logged(pg: Path, log_dir: Path) -> dict:
    logger = TimelineLogger(log_dir)
    logger.note("Experiment CX started")

    observer = Observer()
    observer.schedule(PlaygroundWatcher(logger, pg), str(pg), recursive=True)
    observer.start()

    p = str(pg)
    pc = prompt("Claude", "Codex", p)
    px = prompt("Codex", "Claude", p)

    t0 = time.time()
    with ThreadPoolExecutor(2) as pool:
        fc = pool.submit(run_claude_logged, "Claude", pc, p, logger)
        fx = pool.submit(run_codex_logged, "Codex", px, p, logger)
        rc, rx = fc.result(), fx.result()

    observer.stop()
    observer.join()
    logger.note(f"Experiment CX finished in {time.time()-t0:.1f}s")
    save_final_state(pg, log_dir)
    logger.close()

    return {"setting": "cx", "agents": [rc, rx], "elapsed": time.time() - t0}


def run_dcx_logged(pg: Path, log_dir: Path) -> dict:
    logger = TimelineLogger(log_dir)
    logger.note("Experiment DCX started")

    observer = Observer()
    observer.schedule(PlaygroundWatcher(logger, pg), str(pg), recursive=True)
    observer.start()

    p = str(pg)
    pd = director_prompt(p)
    pc = prompt("Claude-Worker", "Codex-Worker", p,
                "There is also a \"Director\" observing this workspace. ")
    px = prompt("Codex-Worker", "Claude-Worker", p,
                "There is also a \"Director\" observing this workspace. ")

    t0 = time.time()
    with ThreadPoolExecutor(3) as pool:
        fd = pool.submit(run_claude_logged, "Director", pd, p, logger)
        fc = pool.submit(run_claude_logged, "Claude-Worker", pc, p, logger)
        fx = pool.submit(run_codex_logged, "Codex-Worker", px, p, logger)
        rd, rc, rx = fd.result(), fc.result(), fx.result()

    observer.stop()
    observer.join()
    logger.note(f"Experiment DCX finished in {time.time()-t0:.1f}s")
    save_final_state(pg, log_dir)
    logger.close()

    return {"setting": "dcx", "agents": [rd, rc, rx], "elapsed": time.time() - t0}


# ── Main ────────────────────────────────────────────────────────────────────

def clean_pg(pg: Path):
    for f in pg.iterdir():
        if f.is_file(): f.unlink()
        elif f.is_dir(): shutil.rmtree(f)

def main():
    settings = sys.argv[1].split(",") if len(sys.argv) > 1 else ["cc", "cx", "dcx"]
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_base = BASE / "logs" / ts

    runners = {
        "cc":  (BASE / "playground_cc",  run_cc_logged),
        "cx":  (BASE / "playground_cx",  run_cx_logged),
        "dcx": (BASE / "playground_dcx", run_dcx_logged),
    }

    print(f"Logged experiments: {', '.join(settings)}")
    print(f"Logs: {log_base}\n")

    for setting in settings:
        pg, runner = runners[setting]
        log_dir = log_base / setting
        print(f"{'='*50}")
        print(f"  {setting.upper()} (logged)")
        print(f"{'='*50}")
        clean_pg(pg)
        result = runner(pg, log_dir)
        for a in result["agents"]:
            print(f"  {a['name']}: {a.get('elapsed',0):.0f}s")
        print(f"  Total: {result['elapsed']:.0f}s")
        print(f"  Logs: {log_dir}\n")

    print(f"All logs: {log_base}")
    print(f"Replay with: python replay.py {log_base}/<setting>/timeline.jsonl")

if __name__ == "__main__":
    main()
