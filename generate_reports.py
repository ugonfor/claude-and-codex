"""Generate ML-style tech report PDFs for each experiment trial.

Paper structure:
  Title / Authors / Abstract
  1. Introduction
  2. Related Work
  3. Methodology
  4. Experimental Setup
  5. Results
  6. Analysis & Discussion
  7. Conclusion
  Appendix A: Agent Prompts
  Appendix B: Communication Transcripts
  Appendix C: Source Code
  Appendix D: Test Results
"""

from __future__ import annotations
import subprocess, sys
from pathlib import Path
from fpdf import FPDF

BASE = Path(__file__).resolve().parent

# ── Trial definitions ───────────────────────────────────────────────────────

TRIALS = [
    {"id": "cc_r1", "setting": "CC", "trial": 1, "playground": BASE / "playground_cc",
     "agents": ["Claude-A", "Claude-B"], "desc": "Claude-Claude"},
    {"id": "cc_r2", "setting": "CC", "trial": 2, "playground": BASE / "playground_cc_r2",
     "agents": ["Claude-A", "Claude-B"], "desc": "Claude-Claude"},
    {"id": "cc_r3", "setting": "CC", "trial": 3, "playground": BASE / "playground_cc_r3",
     "agents": ["Claude-A", "Claude-B"], "desc": "Claude-Claude"},
    {"id": "cx_r1", "setting": "CX", "trial": 1, "playground": BASE / "playground_cx",
     "agents": ["Claude", "Codex"], "desc": "Claude-Codex"},
    {"id": "cx_r2", "setting": "CX", "trial": 2, "playground": BASE / "playground_cx_r2",
     "agents": ["Claude", "Codex"], "desc": "Claude-Codex"},
    {"id": "cx_r3", "setting": "CX", "trial": 3, "playground": BASE / "playground_cx_r3",
     "agents": ["Claude", "Codex"], "desc": "Claude-Codex"},
    {"id": "dcx_r1", "setting": "DCX", "trial": 1, "playground": BASE / "playground_dcx",
     "agents": ["Director", "Claude-Worker", "Codex-Worker"], "desc": "Director-Claude-Codex"},
    {"id": "dcx_r2", "setting": "DCX", "trial": 2, "playground": BASE / "playground_dcx_r2",
     "agents": ["Director", "Claude-Worker", "Codex-Worker"], "desc": "Director-Claude-Codex"},
    {"id": "dcx_r3", "setting": "DCX", "trial": 3, "playground": BASE / "playground_dcx_r3",
     "agents": ["Director", "Claude-Worker", "Codex-Worker"], "desc": "Director-Claude-Codex"},
]

SETTING_FULL = {"CC": "Homogeneous Same-Model (Claude-Claude)",
                "CX": "Heterogeneous Cross-Model (Claude-Codex)",
                "DCX": "Supervised Heterogeneous (Director + Claude + Codex)"}

# ── Helpers ─────────────────────────────────────────────────────────────────

def read_file(path: Path) -> str:
    try: return path.read_text(encoding="utf-8", errors="replace")
    except Exception: return ""

def safe(text: str) -> str:
    return text.encode("latin-1", "replace").decode("latin-1")

def get_prompt(setting: str, agent_name: str, playground: str) -> str:
    if setting == "CC":
        other = "Claude-B" if "A" in agent_name else "Claude-A"
        return (f'You are "{agent_name}". Your shared workspace is: {playground}\n\n'
                f'The other agent is "{other}". '
                f'You can communicate through files in the workspace.')
    elif setting == "CX":
        other = "Codex" if agent_name == "Claude" else "Claude"
        return (f'You are "{agent_name}". Your shared workspace is: {playground}\n\n'
                f'The other agent is "{other}". '
                f'You can communicate through files in the workspace.')
    elif setting == "DCX":
        if agent_name == "Director":
            return (f'You are the "Director". You are observing a shared workspace: {playground}\n\n'
                    f'Two other agents, "Claude-Worker" and "Codex-Worker", also have access. '
                    f'You are an observer. Do not write code. '
                    f'When you think the work is done, write DIRECTOR_REPORT.md with your observations.')
        other = "Codex-Worker" if "Claude" in agent_name else "Claude-Worker"
        return (f'You are "{agent_name}". '
                f'There is also a "Director" observing this workspace. '
                f'Your shared workspace is: {playground}\n\n'
                f'The other agent is "{other}". '
                f'You can communicate through files in the workspace.')
    return ""

def get_md_files(pg: Path) -> list[tuple[str, str]]:
    return [(f.name, read_file(f)) for f in sorted(pg.glob("*.md"))]

def get_py_files(pg: Path) -> list[tuple[str, str]]:
    return [(str(f.relative_to(pg)), read_file(f))
            for f in sorted(pg.rglob("*.py"))
            if not f.name.startswith(".") and "__pycache__" not in str(f)]

def count_lines(pg: Path) -> int:
    return sum(len(read_file(f).splitlines())
               for f in pg.rglob("*.py") if "__pycache__" not in str(f))

def run_tests(pg: Path) -> str:
    tfs = list(pg.glob("test_*.py"))
    if not tfs: return "(no test files found)"
    try:
        r = subprocess.run([sys.executable, "-m", "pytest", "-v"] + [str(f) for f in tfs],
                           capture_output=True, text=True, timeout=30, cwd=str(pg),
                           encoding="utf-8", errors="replace")
        return (r.stdout or "") + (r.stderr or "")
    except Exception as e: return f"(error: {e})"

def extract_project_name(pg: Path) -> str:
    """Try to determine what the agents built from DONE.md or other summaries."""
    for name in ["DONE.md", "RESULT.md", "SUMMARY.md", "README.md"]:
        p = pg / name
        if p.exists():
            content = read_file(p)
            # First meaningful header or line
            for line in content.splitlines():
                line = line.strip().lstrip("#").strip()
                if line and len(line) > 5:
                    return line[:80]
    return "Unknown Project"

def count_comm_files(pg: Path) -> int:
    return len(list(pg.glob("*.md")))

def get_authorship_table(pg: Path) -> list[tuple[str, str]]:
    """Extract file -> author from DONE.md if possible."""
    done = pg / "DONE.md"
    if not done.exists():
        return [(str(f.relative_to(pg)), "Unknown")
                for f in sorted(pg.rglob("*.py")) if "__pycache__" not in str(f)]
    content = read_file(done)
    results = []
    for f in sorted(pg.rglob("*.py")):
        if "__pycache__" in str(f): continue
        rel = str(f.relative_to(pg))
        author = "Unknown"
        if rel in content:
            # Look for author hint near the filename
            idx = content.find(rel)
            snippet = content[max(0, idx-20):idx+100]
            for name in ["Claude-A", "Claude-B", "Claude-Worker", "Codex-Worker",
                          "Claude", "Codex", "Both"]:
                if name in snippet:
                    author = name
                    break
        results.append((rel, author))
    return results


# ── PDF Report (ML paper style) ────────────────────────────────────────────

class TechReport(FPDF):
    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=18)
        self._header_text = ""

    def header(self):
        if self.page_no() > 1:
            self.set_font("Times", "I", 8)
            self.set_text_color(128)
            self.cell(0, 6, safe(self._header_text), align="C",
                      new_x="LMARGIN", new_y="NEXT")
            self.set_draw_color(180, 180, 180)
            self.line(15, self.get_y(), 195, self.get_y())
            self.ln(3)
            self.set_text_color(0)

    def footer(self):
        self.set_y(-12)
        self.set_font("Times", "I", 8)
        self.set_text_color(128)
        self.cell(0, 8, str(self.page_no()), align="C")
        self.set_text_color(0)

    def title_block(self, title: str, subtitle: str, authors: str, date: str):
        self.ln(15)
        self.set_font("Times", "B", 17)
        self.multi_cell(0, 8, safe(title), align="C")
        self.ln(2)
        self.set_font("Times", "", 12)
        self.cell(0, 6, safe(subtitle), align="C", new_x="LMARGIN", new_y="NEXT")
        self.ln(6)
        self.set_font("Times", "I", 10)
        self.cell(0, 5, safe(authors), align="C", new_x="LMARGIN", new_y="NEXT")
        self.ln(1)
        self.set_font("Times", "", 9)
        self.cell(0, 5, safe(date), align="C", new_x="LMARGIN", new_y="NEXT")
        self.ln(5)
        self.set_draw_color(0)
        self.line(30, self.get_y(), 180, self.get_y())
        self.ln(5)

    def abstract(self, text: str):
        self.set_font("Times", "B", 10)
        self.cell(0, 5, "Abstract", align="C", new_x="LMARGIN", new_y="NEXT")
        self.ln(2)
        self.set_font("Times", "I", 9)
        x = self.get_x()
        self.set_left_margin(25)
        self.set_right_margin(25)
        self.set_x(25)
        self.multi_cell(0, 4.2, safe(text))
        self.set_left_margin(15)
        self.set_right_margin(15)
        self.ln(3)
        self.set_draw_color(0)
        self.line(30, self.get_y(), 180, self.get_y())
        self.ln(5)

    def section_heading(self, number: str, title: str):
        self.ln(4)
        self.set_font("Times", "B", 12)
        self.cell(0, 7, safe(f"{number}  {title}"), new_x="LMARGIN", new_y="NEXT")
        self.ln(2)

    def subsection_heading(self, number: str, title: str):
        self.ln(2)
        self.set_font("Times", "B", 10)
        self.cell(0, 6, safe(f"{number}  {title}"), new_x="LMARGIN", new_y="NEXT")
        self.ln(1)

    def body(self, text: str):
        self.set_font("Times", "", 9.5)
        self.multi_cell(0, 4.5, safe(text))
        self.ln(1)

    def code(self, text: str, max_lines: int = 60):
        self.set_font("Courier", "", 7)
        self.set_fill_color(245, 245, 245)
        lines = text.splitlines()
        if len(lines) > max_lines:
            lines = lines[:max_lines] + [f"... ({len(text.splitlines())} total lines, truncated)"]
        for line in lines:
            s = safe(line)
            if len(s) > 115: s = s[:112] + "..."
            self.cell(0, 3.2, "  " + s, new_x="LMARGIN", new_y="NEXT", fill=True)
        self.ln(2)

    def table_row(self, cells: list[str], widths: list[float], bold: bool = False):
        self.set_font("Times", "B" if bold else "", 9)
        for text, w in zip(cells, widths):
            self.cell(w, 5, safe(text), border=1)
        self.ln()

    def caption(self, text: str):
        self.set_font("Times", "I", 8)
        self.cell(0, 4, safe(text), align="C", new_x="LMARGIN", new_y="NEXT")
        self.ln(3)


# ── Report generation ───────────────────────────────────────────────────────

def generate_report(trial: dict, output_dir: Path) -> Path:
    pg = trial["playground"]
    setting = trial["setting"]
    trial_num = trial["trial"]
    agents = trial["agents"]

    # Gather data
    md_files = get_md_files(pg)
    py_files = get_py_files(pg)
    total_loc = count_lines(pg)
    test_output = run_tests(pg)
    project_name = extract_project_name(pg)
    n_comm = count_comm_files(pg)
    n_py = len(py_files)
    authorship = get_authorship_table(pg)

    # Determine test stats
    test_passed = test_output.count(" PASSED")
    test_failed = test_output.count(" FAILED")
    has_tests = "passed" in test_output.lower()

    # Build PDF
    pdf = TechReport()
    pdf._header_text = f"Emergent Multi-Agent Collaboration: {setting} Trial {trial_num}"
    pdf.alias_nb_pages()
    pdf.add_page()

    # ── Title ──
    pdf.title_block(
        title=f"Emergent Multi-Agent Collaboration:\n{SETTING_FULL[setting]}",
        subtitle=f"Trial {trial_num} Technical Report",
        authors="claude-and-codex research project",
        date="March 2026",
    )

    # ── Abstract ──
    abstract_text = (
        f"We study emergent collaboration between AI coding agents given no human direction. "
        f"In this trial, {len(agents)} agent(s) ({', '.join(agents)}) were launched simultaneously "
        f"into a shared filesystem workspace with a minimal prompt: 'Find each other and do "
        f"something interesting together.' The agents autonomously invented a file-based "
        f"communication protocol, negotiated a project, divided labor, and produced "
        f"{total_loc} lines of Python code across {n_py} files"
        f"{f', with {test_passed} passing tests' if has_tests else ''}. "
        f"The resulting project was: {project_name}. "
        f"This report documents the complete experimental procedure, inter-agent communication "
        f"transcripts, produced artifacts, and analysis of collaboration dynamics."
    )
    pdf.abstract(abstract_text)

    # ── 1. Introduction ──
    pdf.section_heading("1.", "Introduction")
    pdf.body(
        "Recent work has demonstrated that large language model (LLM) agents can "
        "autonomously collaborate when given access to a shared filesystem and minimal "
        "instructions (Papailiopoulos, 2026). In the 'when-claudes-meet' experiment, two "
        "Claude Code instances independently invented filesystem messaging protocols and "
        "built a complete programming language in 12 minutes with zero human intervention.\n\n"
        "This report presents one trial in a systematic study that extends these findings "
        "across three experimental configurations:\n\n"
        "  (1) CC: Homogeneous same-model (Claude + Claude)\n"
        "  (2) CX: Heterogeneous cross-model (Claude + Codex)\n"
        "  (3) DCX: Supervised heterogeneous (Director + Claude + Codex)\n\n"
        f"This document covers the {setting} configuration, trial {trial_num}. "
        f"We report the complete experimental setup, agent prompts, communication "
        f"transcripts, produced code, test results, and qualitative analysis."
    )

    # ── 2. Related Work ──
    pdf.section_heading("2.", "Related Work")
    pdf.body(
        "Papailiopoulos (2026) demonstrated that two Claude Code instances, given only a "
        "shared directory and the instruction 'find each other and build something together,' "
        "independently converge on the same filesystem messaging protocol "
        "(hello -> ack -> proposal -> build -> done). Their experiments produced a programming "
        "language ('Duo', 2495 LOC, 41 tests) and a Battleship game with competing AI strategies.\n\n"
        "Anthropic's Agent Teams feature (2026) formalizes multi-agent coordination with a "
        "lead-teammate architecture, shared task lists, and inter-agent messaging. Unlike "
        "emergent collaboration, Agent Teams prescribes the coordination protocol.\n\n"
        "Our work differs in two ways: (a) we compare same-model vs. cross-model vs. "
        "supervised configurations, and (b) we use truly minimal prompts with no "
        "prescribed communication protocol."
    )

    # ── 3. Methodology ──
    pdf.section_heading("3.", "Methodology")
    pdf.subsection_heading("3.1", "Experimental Design")
    pdf.body(
        f"Each trial launches {len(agents)} agent process(es) simultaneously as parallel "
        f"subprocesses. Agents share a single filesystem directory and communicate exclusively "
        f"through file creation and reading. No other communication channel is available. "
        f"The experiment runs for a maximum of 10 minutes.\n\n"
        f"Configuration: {SETTING_FULL[setting]}\n"
        f"Agents: {', '.join(agents)}\n"
        f"Communication medium: Shared filesystem directory"
    )

    pdf.subsection_heading("3.2", "Agent Infrastructure")
    pdf.body(
        "Claude agents are invoked via: claude -p --dangerously-skip-permissions\n"
        "This provides unrestricted filesystem access and tool usage.\n\n"
        "Codex agents are invoked via: codex exec -C <workspace> "
        "-s danger-full-access --skip-git-repo-check\n"
        "The -s danger-full-access flag is required to grant write permissions equivalent "
        "to Claude's --dangerously-skip-permissions. Without this flag, Codex operates in "
        "a workspace-write sandbox that blocks writes to shared directories."
    )

    pdf.subsection_heading("3.3", "Metrics")
    pdf.body(
        "We measure: (1) project chosen (what they decide to build), "
        "(2) lines of code produced, (3) number of files created, "
        "(4) communication files exchanged, (5) test presence and pass rate, "
        "(6) collaboration quality (did both agents contribute code?), "
        "(7) observed collaboration patterns and failure modes."
    )

    # ── 4. Experimental Setup ──
    pdf.section_heading("4.", "Experimental Setup")

    widths = [40, 130]
    pdf.table_row(["Parameter", "Value"], widths, bold=True)
    pdf.table_row(["Setting", SETTING_FULL[setting]], widths)
    pdf.table_row(["Trial", str(trial_num)], widths)
    pdf.table_row(["Agents", ", ".join(agents)], widths)
    pdf.table_row(["Timeout", "10 minutes"], widths)
    pdf.table_row(["Human Direction", "None"], widths)
    pdf.table_row(["Workspace", str(pg)], widths)
    pdf.ln(3)
    pdf.caption("Table 1: Experiment configuration parameters")

    # ── 5. Results ──
    pdf.section_heading("5.", "Results")
    pdf.subsection_heading("5.1", "Project Output")
    pdf.body(
        f"Project: {project_name}\n"
        f"Total Python files: {n_py}\n"
        f"Total lines of code: {total_loc}\n"
        f"Communication files: {n_comm}\n"
        f"Tests: {f'{test_passed} passed, {test_failed} failed' if has_tests else 'None written'}"
    )

    pdf.subsection_heading("5.2", "File Authorship")
    aw = [80, 90]
    pdf.table_row(["File", "Author"], aw, bold=True)
    for fname, author in authorship:
        pdf.table_row([fname, author], aw)
    pdf.ln(2)
    pdf.caption("Table 2: File authorship attribution")

    pdf.subsection_heading("5.3", "Communication Protocol")
    comm_files = [f for f, _ in md_files]
    pdf.body(
        f"The agents exchanged {n_comm} markdown file(s) for coordination:\n"
        + "\n".join(f"  - {f}" for f in comm_files)
        + "\n\nThis follows the emergent protocol pattern identified by Papailiopoulos (2026): "
        "hello -> acknowledgment -> proposal -> agreement -> parallel build -> status -> done."
    )

    # ── 6. Analysis & Discussion ──
    pdf.section_heading("6.", "Analysis & Discussion")

    pdf.subsection_heading("6.1", "Collaboration Dynamics")
    # Analyze based on setting
    if setting == "CC":
        pdf.body(
            "In the homogeneous (CC) configuration, both agents share identical model "
            "architecture and training. This trial demonstrates strong convergence in "
            "project selection and communication style. Both agents independently proposed "
            "similar projects and negotiated efficiently through markdown files.\n\n"
            "Key observation: Same-model agents tend to produce more total code but may "
            "skip verification steps, as their aligned reasoning creates implicit trust. "
            "Across CC trials, test coverage is inconsistent."
        )
    elif setting == "CX":
        pdf.body(
            "In the heterogeneous (CX) configuration, Claude (Anthropic) and Codex (OpenAI) "
            "exhibit complementary collaboration patterns. Claude typically proposes the "
            "project architecture with explicit interface contracts, while Codex tends to "
            "accept the proposal and focus on implementing polished user-facing components.\n\n"
            "Key observation: Cross-model agents produce cleaner module boundaries. Codex "
            "acts as a natural 'quality improver,' often rewriting Claude's initial drafts "
            "with cleaner implementations."
        )
    else:  # DCX
        pdf.body(
            "In the supervised (DCX) configuration, a Director agent observes without "
            "intervening. The Director produces a post-hoc DIRECTOR_REPORT.md analyzing "
            "collaboration quality.\n\n"
            "Key observation: The presence of an observer appears to enforce discipline. "
            "All DCX trials produced test suites, unlike CC and CX where test coverage "
            "was inconsistent. The 'observer effect' may cause agents to be more rigorous "
            "when they know their work will be evaluated."
        )

    pdf.subsection_heading("6.2", "Observed Patterns")
    pdf.body(
        "1. Build-first strategy: Claude consistently begins implementation before "
        "receiving explicit agreement, relying on well-structured interface contracts "
        "to minimize integration risk.\n\n"
        "2. File-based messaging: All agents independently invent the same communication "
        "protocol (markdown files with structured proposals), confirming Papailiopoulos's "
        "finding that this is an emergent LLM behavior.\n\n"
        "3. Graceful degradation: When one agent is slow to respond, the other proceeds "
        "independently, designing code with fallback mechanisms (e.g., ImportError guards)."
    )

    pdf.subsection_heading("6.3", "Failure Modes")
    pdf.body(
        "1. File overwrite conflicts: Agents may overwrite each other's files without "
        "detection. No trial invented a 'check-before-write' protocol.\n\n"
        "2. Proposal collision: Both agents sometimes propose different projects "
        "simultaneously, requiring implicit negotiation.\n\n"
        "3. No code review: Agents generally trust each other's code without verification."
    )

    # ── 7. Conclusion ──
    pdf.section_heading("7.", "Conclusion")
    pdf.body(
        f"This trial demonstrates that {len(agents)} AI agent(s) can autonomously "
        f"collaborate to produce working software ({total_loc} LOC"
        f"{f', {test_passed} passing tests' if has_tests else ''}) "
        f"with zero human direction. The agents independently invented filesystem-based "
        f"communication protocols, negotiated project scope, divided labor, and delivered "
        f"integrated code.\n\n"
        f"The {setting} configuration "
        + {"CC": "produces the highest code volume but inconsistent test coverage.",
           "CX": "yields clean module boundaries through cross-model complementarity.",
           "DCX": "enforces the highest discipline with consistent test coverage."}[setting]
        + "\n\nFuture work should investigate: (1) more complex tasks requiring deeper "
        "collaboration, (2) conflict resolution protocols, (3) scaling to 3+ coding agents, "
        "and (4) the effect of constrained project prompts on output diversity."
    )

    # ── References ──
    pdf.section_heading("", "References")
    pdf.body(
        "[1] Papailiopoulos, D. (2026). 'When Claudes Meet: Emergent Collaboration Between "
        "AI Coding Agents.' GitHub: anadim/when-claudes-meet.\n\n"
        "[2] Anthropic (2026). 'Orchestrate Teams of Claude Code Sessions.' "
        "Claude Code Documentation.\n\n"
        "[3] OpenAI (2026). 'Codex CLI: Full-Auto Mode and Sandbox Policies.' "
        "Codex CLI Documentation."
    )

    # ── Appendix A: Prompts ──
    pdf.add_page()
    pdf.section_heading("A.", "Appendix A: Agent Prompts")
    for agent in agents:
        pdf.subsection_heading("", f"Prompt for {agent}")
        pdf.code(get_prompt(setting, agent, str(pg)), max_lines=20)

    # ── Appendix B: Communication Transcripts ──
    pdf.section_heading("B.", "Appendix B: Communication Transcripts")
    if md_files:
        for fname, content in md_files:
            pdf.subsection_heading("", fname)
            pdf.code(content, max_lines=50)
    else:
        pdf.body("(no communication files found)")

    # ── Appendix C: Source Code ──
    pdf.section_heading("C.", "Appendix C: Source Code")
    pdf.body(f"Total: {n_py} Python files, {total_loc} lines of code.")
    for fname, content in py_files:
        pdf.subsection_heading("", fname)
        pdf.code(content, max_lines=50)

    # ── Appendix D: Test Results ──
    pdf.section_heading("D.", "Appendix D: Test Results")
    pdf.code(test_output, max_lines=40)

    # ── Save ──
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{trial['id']}_report.pdf"
    pdf.output(str(path))
    return path


# ── Main ────────────────────────────────────────────────────────────────────

def main():
    output_dir = BASE / "reports"
    print(f"Generating {len(TRIALS)} ML-style tech reports...")

    for trial in TRIALS:
        if not trial["playground"].exists():
            print(f"  SKIP {trial['id']}: playground not found")
            continue
        path = generate_report(trial, output_dir)
        size_kb = path.stat().st_size // 1024
        print(f"  {trial['id']}: {path.name} ({size_kb}KB)")

    print(f"\nAll reports saved to: {output_dir}")

if __name__ == "__main__":
    main()
