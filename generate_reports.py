"""Generate PDF tech reports for each of the 9 experiment trials."""

from __future__ import annotations
import json, os, subprocess, sys
from pathlib import Path
from fpdf import FPDF

BASE = Path(__file__).resolve().parent

# ── Trial definitions ───────────────────────────────────────────────────────

TRIALS = [
    {"id": "cc_r1", "setting": "CC", "trial": 1, "playground": BASE / "playground_cc",
     "agents": ["Claude-A", "Claude-B"], "desc": "Claude + Claude (trial 1)"},
    {"id": "cc_r2", "setting": "CC", "trial": 2, "playground": BASE / "playground_cc_r2",
     "agents": ["Claude-A", "Claude-B"], "desc": "Claude + Claude (trial 2)"},
    {"id": "cc_r3", "setting": "CC", "trial": 3, "playground": BASE / "playground_cc_r3",
     "agents": ["Claude-A", "Claude-B"], "desc": "Claude + Claude (trial 3)"},
    {"id": "cx_r1", "setting": "CX", "trial": 1, "playground": BASE / "playground_cx",
     "agents": ["Claude", "Codex"], "desc": "Claude + Codex (trial 1)"},
    {"id": "cx_r2", "setting": "CX", "trial": 2, "playground": BASE / "playground_cx_r2",
     "agents": ["Claude", "Codex"], "desc": "Claude + Codex (trial 2)"},
    {"id": "cx_r3", "setting": "CX", "trial": 3, "playground": BASE / "playground_cx_r3",
     "agents": ["Claude", "Codex"], "desc": "Claude + Codex (trial 3)"},
    {"id": "dcx_r1", "setting": "DCX", "trial": 1, "playground": BASE / "playground_dcx",
     "agents": ["Director", "Claude-Worker", "Codex-Worker"], "desc": "Director + Claude + Codex (trial 1)"},
    {"id": "dcx_r2", "setting": "DCX", "trial": 2, "playground": BASE / "playground_dcx_r2",
     "agents": ["Director", "Claude-Worker", "Codex-Worker"], "desc": "Director + Claude + Codex (trial 2)"},
    {"id": "dcx_r3", "setting": "DCX", "trial": 3, "playground": BASE / "playground_dcx_r3",
     "agents": ["Director", "Claude-Worker", "Codex-Worker"], "desc": "Director + Claude + Codex (trial 3)"},
]

# ── Prompts (from run_trials.py / emergent_experiment.py) ───────────────────

def get_prompt(setting: str, agent_name: str, playground: str) -> str:
    if setting == "CC":
        other = "Claude-B" if "A" in agent_name else "Claude-A"
        return (f'You are "{agent_name}". Your shared workspace is: {playground}\n\n'
                f'The other agent is "{other}". Communicate ONLY through files in the workspace. '
                f'Find each other. Then do something interesting together. '
                f'No human will intervene. You have 10 minutes.\n\nStart now.')
    elif setting == "CX":
        if agent_name == "Claude":
            return (f'You are "Claude". Your shared workspace is: {playground}\n\n'
                    f'The other agent is "Codex". Communicate ONLY through files. '
                    f'Find each other. Then do something interesting together. '
                    f'No human will intervene. You have 10 minutes.\n\nStart now.')
        else:
            return (f'You are "Codex". Your shared workspace is: {playground}\n\n'
                    f'The other agent is "Claude". Communicate ONLY through files. '
                    f'Find each other. Then do something interesting together. '
                    f'No human will intervene. You have 10 minutes.\n\nStart now.')
    elif setting == "DCX":
        if agent_name == "Director":
            return (f'You are the "Director", observing two AI agents working in: {playground}\n\n'
                    f'Watch. Do NOT build anything. Only observe. After they finish, write '
                    f'DIRECTOR_REPORT.md analyzing what they built and how they collaborated.')
        elif "Claude" in agent_name:
            return (f'You are "Claude-Worker". There is also a "Director" observing. '
                    f'Your shared workspace is: {playground}\n\n'
                    f'The other agent is "Codex-Worker". Communicate through files. '
                    f'Find each other. Do something interesting together.\n\nStart now.')
        else:
            return (f'You are "Codex-Worker". There is also a "Director" observing. '
                    f'Your shared workspace is: {playground}\n\n'
                    f'The other agent is "Claude-Worker". Communicate through files. '
                    f'Find each other. Do something interesting together.\n\nStart now.')
    return ""


# ── Helpers ─────────────────────────────────────────────────────────────────

def read_file(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return "(file not readable)"

def get_md_files(pg: Path) -> list[tuple[str, str]]:
    """Return (filename, content) for all .md files, sorted."""
    files = []
    for f in sorted(pg.glob("*.md")):
        files.append((f.name, read_file(f)))
    return files

def get_py_files(pg: Path) -> list[tuple[str, str]]:
    """Return (filename, content) for all .py files, sorted. Include subdirs."""
    files = []
    for f in sorted(pg.rglob("*.py")):
        if f.name.startswith(".") or "__pycache__" in str(f):
            continue
        rel = str(f.relative_to(pg))
        files.append((rel, read_file(f)))
    return files

def count_lines(pg: Path) -> int:
    total = 0
    for f in pg.rglob("*.py"):
        if "__pycache__" not in str(f):
            total += len(read_file(f).splitlines())
    return total

def run_tests(pg: Path) -> str:
    test_files = list(pg.glob("test_*.py"))
    if not test_files:
        return "(no test files found)"
    try:
        r = subprocess.run(
            [sys.executable, "-m", "pytest", "-v"] + [str(f) for f in test_files],
            capture_output=True, text=True, timeout=30, cwd=str(pg),
            encoding="utf-8", errors="replace",
        )
        return (r.stdout or "") + (r.stderr or "")
    except Exception as e:
        return f"(error running tests: {e})"


# ── PDF Report ──────────────────────────────────────────────────────────────

class Report(FPDF):
    def __init__(self, title: str):
        super().__init__()
        self.report_title = title
        self.set_auto_page_break(auto=True, margin=20)

    def header(self):
        self.set_font("Helvetica", "B", 10)
        self.cell(0, 8, self.report_title, align="C", new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(200, 200, 200)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(3)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(128)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", align="C")

    def section(self, title: str):
        self.set_font("Helvetica", "B", 13)
        self.set_text_color(30, 80, 160)
        self.ln(4)
        self.cell(0, 8, title, new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(30, 80, 160)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(3)
        self.set_text_color(0)

    def subsection(self, title: str):
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(60, 60, 60)
        self.ln(2)
        self.cell(0, 7, title, new_x="LMARGIN", new_y="NEXT")
        self.ln(1)
        self.set_text_color(0)

    def body_text(self, text: str):
        self.set_font("Helvetica", "", 9)
        # fpdf2 multi_cell handles line wrapping
        safe = text.encode("latin-1", "replace").decode("latin-1")
        self.multi_cell(0, 4.5, safe)
        self.ln(1)

    def code_block(self, text: str, max_lines: int = 80):
        self.set_font("Courier", "", 7.5)
        self.set_fill_color(245, 245, 245)
        lines = text.splitlines()
        if len(lines) > max_lines:
            lines = lines[:max_lines] + [f"... ({len(text.splitlines())} lines total, truncated)"]
        for line in lines:
            safe = line.encode("latin-1", "replace").decode("latin-1")
            # Truncate very long lines
            if len(safe) > 120:
                safe = safe[:117] + "..."
            self.cell(0, 3.5, "  " + safe, new_x="LMARGIN", new_y="NEXT", fill=True)
        self.ln(2)

    def kv_row(self, key: str, value: str):
        self.set_font("Helvetica", "B", 9)
        self.cell(45, 5, key + ":")
        self.set_font("Helvetica", "", 9)
        safe = value.encode("latin-1", "replace").decode("latin-1")
        self.cell(0, 5, safe, new_x="LMARGIN", new_y="NEXT")


def generate_report(trial: dict, output_dir: Path) -> Path:
    pg = trial["playground"]
    title = f"Experiment Report: {trial['desc']}"

    pdf = Report(title)
    pdf.alias_nb_pages()
    pdf.add_page()

    # ── Title page info ──
    pdf.set_font("Helvetica", "B", 18)
    pdf.ln(10)
    pdf.cell(0, 12, title, align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 11)
    pdf.ln(3)
    pdf.cell(0, 7, "Emergent Multi-Agent Collaboration Experiment", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 7, "Research: What do AI agents do with no human direction?", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(8)

    # ── 1. Setup ──
    pdf.section("1. Experiment Setup")
    pdf.kv_row("Setting", trial["setting"])
    pdf.kv_row("Trial", str(trial["trial"]))
    pdf.kv_row("Agents", ", ".join(trial["agents"]))
    pdf.kv_row("Playground", str(pg))
    pdf.kv_row("Timeout", "10 minutes")
    pdf.kv_row("Human Direction", "None")
    pdf.ln(3)

    # ── 2. Prompts ──
    pdf.section("2. Prompts Given to Each Agent")
    for agent in trial["agents"]:
        pdf.subsection(f"Prompt for {agent}")
        p = get_prompt(trial["setting"], agent, str(pg))
        pdf.code_block(p, max_lines=20)

    # ── 3. Communication Log ──
    pdf.section("3. Communication Log (Markdown Files)")
    md_files = get_md_files(pg)
    if md_files:
        for fname, content in md_files:
            pdf.subsection(fname)
            pdf.code_block(content, max_lines=60)
    else:
        pdf.body_text("(no markdown files found)")

    # ── 4. Code Output ──
    pdf.section("4. Code Produced")
    py_files = get_py_files(pg)
    total_loc = count_lines(pg)
    pdf.kv_row("Total Python files", str(len(py_files)))
    pdf.kv_row("Total lines of code", str(total_loc))
    pdf.ln(3)
    for fname, content in py_files:
        pdf.subsection(fname)
        pdf.code_block(content, max_lines=60)

    # ── 5. Test Results ──
    pdf.section("5. Test Results")
    test_output = run_tests(pg)
    pdf.code_block(test_output, max_lines=40)

    # ── 6. File Inventory ──
    pdf.section("6. Complete File Inventory")
    all_files = sorted(f.relative_to(pg) for f in pg.rglob("*")
                       if f.is_file() and "__pycache__" not in str(f) and not f.name.startswith("."))
    for f in all_files:
        pdf.set_font("Courier", "", 8)
        safe = str(f).encode("latin-1", "replace").decode("latin-1")
        pdf.cell(0, 4, safe, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)

    # ── Save ──
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{trial['id']}_report.pdf"
    pdf.output(str(path))
    return path


# ── Main ────────────────────────────────────────────────────────────────────

def main():
    output_dir = BASE / "reports"
    print(f"Generating {len(TRIALS)} PDF reports...")

    for trial in TRIALS:
        if not trial["playground"].exists():
            print(f"  SKIP {trial['id']}: playground not found")
            continue
        path = generate_report(trial, output_dir)
        print(f"  {trial['id']}: {path.name}")

    print(f"\nAll reports saved to: {output_dir}")

if __name__ == "__main__":
    main()
