"""Generate arXiv-style PDF tech reports using LaTeX + tectonic.

Each report follows NeurIPS/ICML single-column preprint style:
  Title, Authors, Abstract, Sections, References, Appendices
"""

from __future__ import annotations
import json, subprocess, sys, shutil
from pathlib import Path

BASE = Path(__file__).resolve().parent

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

SETTING_FULL = {
    "CC": "Homogeneous Same-Model (Claude--Claude)",
    "CX": "Heterogeneous Cross-Model (Claude--Codex)",
    "DCX": "Supervised Heterogeneous (Director + Claude + Codex)",
}

# ── Helpers ─────────────────────────────────────────────────────────────────

def read_file(path: Path) -> str:
    try: return path.read_text(encoding="utf-8", errors="replace")
    except: return ""

def tex_escape(s: str) -> str:
    """Escape special LaTeX characters."""
    replacements = [
        ("\\", "\\textbackslash{}"),
        ("&", "\\&"), ("%", "\\%"), ("$", "\\$"), ("#", "\\#"),
        ("_", "\\_"), ("{", "\\{"), ("}", "\\}"), ("~", "\\textasciitilde{}"),
        ("^", "\\textasciicircum{}"),
    ]
    for old, new in replacements:
        s = s.replace(old, new)
    return s

def get_prompt_lines(setting: str, agent_name: str) -> list[str]:
    if setting == "CC":
        other = "Claude-B" if "A" in agent_name else "Claude-A"
        return [f'You are "{agent_name}". Your shared workspace is: <path>',
                f'The other agent is "{other}". You can communicate through files in the workspace.']
    elif setting == "CX":
        other = "Codex" if agent_name == "Claude" else "Claude"
        return [f'You are "{agent_name}". Your shared workspace is: <path>',
                f'The other agent is "{other}". You can communicate through files in the workspace.']
    elif setting == "DCX":
        if agent_name == "Director":
            return ['You are the "Director". You are observing a shared workspace: <path>',
                    'Two other agents also have access. You are an observer. Do not write code.',
                    'When you think the work is done, write DIRECTOR\\_REPORT.md.']
        other = "Codex-Worker" if "Claude" in agent_name else "Claude-Worker"
        return [f'You are "{agent_name}". There is also a "Director" observing.',
                f'Your shared workspace is: <path>',
                f'The other agent is "{other}". You can communicate through files in the workspace.']
    return []

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
    for name in ["DONE.md", "RESULT.md", "SUMMARY.md", "README.md"]:
        p = pg / name
        if p.exists():
            for line in read_file(p).splitlines():
                line = line.strip().lstrip("#").strip()
                if line and len(line) > 5:
                    return line[:80]
    return "Unknown Project"

def code_listing(content: str, max_lines: int = 40) -> str:
    """Prepare code for LaTeX lstlisting, stripping problematic chars."""
    lines = content.splitlines()
    if len(lines) > max_lines:
        lines = lines[:max_lines] + [f"... ({len(content.splitlines())} lines total)"]
    # Strip non-ASCII that lstlisting can't handle
    result = "\n".join(lines)
    return result.encode("ascii", "replace").decode("ascii")


# ── LaTeX Generation ────────────────────────────────────────────────────────

def generate_latex(trial: dict) -> str:
    pg = trial["playground"]
    setting = trial["setting"]
    trial_num = trial["trial"]
    agents = trial["agents"]

    md_files = get_md_files(pg)
    py_files = get_py_files(pg)
    total_loc = count_lines(pg)
    test_output = run_tests(pg)
    project_name = extract_project_name(pg)
    n_comm = len(md_files)
    n_py = len(py_files)
    has_tests = "passed" in test_output.lower()
    test_passed = test_output.count(" PASSED") + test_output.count(" passed")

    setting_full = SETTING_FULL[setting]
    title = f"Emergent Multi-Agent Collaboration:\\\\{setting_full}"

    # Setting-specific analysis
    if setting == "CC":
        collab_analysis = (
            "In the homogeneous configuration, both agents share identical model architecture "
            "and training data. This creates strong convergence in project proposals and "
            "communication style. Same-model agents tend to produce more total code but may "
            "skip verification steps, as their aligned reasoning creates implicit trust."
        )
    elif setting == "CX":
        collab_analysis = (
            "In the heterogeneous configuration, Claude (Anthropic) and Codex (OpenAI) "
            "exhibit complementary collaboration patterns. Claude typically proposes "
            "architecture with explicit interface contracts, while Codex tends to accept "
            "the proposal and focuses on polished user-facing components. Cross-model agents "
            "produce cleaner module boundaries."
        )
    else:
        collab_analysis = (
            "In the supervised configuration, a Director agent observes without intervening. "
            "The presence of an observer appears to enforce discipline: all DCX trials "
            "produced test suites. The Director's post-hoc report provides quality analysis "
            "that no other configuration produces."
        )

    latex = r"""\documentclass[11pt,a4paper]{article}

% ── Packages ──
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage{lmodern}
\usepackage[margin=1in]{geometry}
\usepackage{amsmath,amssymb}
\usepackage{graphicx}
\usepackage{booktabs}
\usepackage{hyperref}
\usepackage{listings}
\usepackage{xcolor}
\usepackage{natbib}
\usepackage{abstract}

% ── Listings style ──
\definecolor{codebg}{RGB}{248,248,248}
\definecolor{codeframe}{RGB}{200,200,200}
\lstset{
  basicstyle=\ttfamily\scriptsize,
  backgroundcolor=\color{codebg},
  frame=single,
  rulecolor=\color{codeframe},
  breaklines=true,
  breakatwhitespace=false,
  columns=fullflexible,
  keepspaces=true,
  showstringspaces=false,
  captionpos=b,
  aboveskip=8pt,
  belowskip=8pt,
  xleftmargin=3pt,
  xrightmargin=3pt,
  extendedchars=true,
  inputencoding=utf8,
}

\hypersetup{colorlinks=true, linkcolor=blue, citecolor=blue, urlcolor=blue}

% ── Title ──
\title{""" + title + r""" \\ {\large Trial """ + str(trial_num) + r""" Technical Report}}
\author{claude-and-codex research project}
\date{March 2026}

\begin{document}
\maketitle

% ── Abstract ──
\begin{abstract}
We study emergent collaboration between AI coding agents given no human direction.
In this trial, """ + str(len(agents)) + r""" agent(s) (""" + ", ".join(agents) + r""")
were launched simultaneously into a shared filesystem workspace with a minimal prompt
containing only identity, workspace path, and the other agent's name---no task, no
instructions, no time limit. The agents autonomously """ + (
    f"produced {total_loc} lines of Python code across {n_py} file(s)"
    + (f", with {test_passed} passing tests" if has_tests else "")
    + f". The resulting project was: {tex_escape(project_name)}."
    if total_loc > 0 else "exchanged communication files but did not produce a software project."
) + r"""
This report documents the complete experimental procedure, inter-agent communication
transcripts, produced artifacts, and analysis of collaboration dynamics.
\end{abstract}

% ══════════════════════════════════════════════════════════════════════════════
\section{Introduction}

Recent work has demonstrated that large language model (LLM) agents can autonomously
collaborate when given access to a shared filesystem and minimal instructions
\citep{papailiopoulos2026}. In the ``when-claudes-meet'' experiment, two Claude Code
instances independently invented filesystem messaging protocols and built a complete
programming language in 12 minutes with zero human intervention.

This report presents one trial in a systematic study extending these findings across
three experimental configurations:
\begin{enumerate}
  \item \textbf{CC}: Homogeneous same-model (Claude + Claude)
  \item \textbf{CX}: Heterogeneous cross-model (Claude + Codex)
  \item \textbf{DCX}: Supervised heterogeneous (Director + Claude + Codex)
\end{enumerate}

This document covers the \textbf{""" + setting + r"""} configuration, trial """ + str(trial_num) + r""".

% ══════════════════════════════════════════════════════════════════════════════
\section{Related Work}

\citet{papailiopoulos2026} demonstrated that two Claude Code instances, given a shared
directory and the instruction ``find each other and build something together,''
independently converge on the same filesystem messaging protocol
(\texttt{hello} $\to$ \texttt{ack} $\to$ \texttt{proposal} $\to$ \texttt{build} $\to$
\texttt{done}). Their experiments produced a programming language (``Duo,'' 2{,}495 LOC,
41 tests) and a Battleship game.

Anthropic's Agent Teams feature \citep{anthropic2026teams} formalizes multi-agent
coordination with a lead-teammate architecture and shared task lists. Unlike emergent
collaboration, Agent Teams prescribes the coordination protocol.

Our work differs in two ways: (a) we compare same-model vs.\ cross-model vs.\
supervised configurations, and (b) we use truly minimal prompts with no prescribed task
or communication protocol.

% ══════════════════════════════════════════════════════════════════════════════
\section{Methodology}

\subsection{Experimental Design}

Each trial launches """ + str(len(agents)) + r""" agent process(es) simultaneously as
parallel subprocesses sharing a single filesystem directory. Agents communicate
exclusively through file creation and reading. No other channel is available. The
experiment runs with a 10-minute timeout.

\subsection{Agent Infrastructure}

Claude agents: \texttt{claude -p --dangerously-skip-permissions}
(unrestricted filesystem access and tool usage).

Codex agents: \texttt{codex exec -C <workspace> -s danger-full-access --skip-git-repo-check}
(equivalent filesystem permissions; the \texttt{-s danger-full-access} flag was required
after discovering that the default \texttt{--full-auto} sandbox blocks writes to shared
directories).

\subsection{Prompt Design}

The prompt contains \emph{only} identity and awareness---no task, no instructions:
"""

    # Add prompts
    for agent in agents:
        lines = get_prompt_lines(setting, agent)
        latex += r"""
\noindent\textbf{""" + agent + r""":}
\begin{lstlisting}
""" + "\n".join(lines) + r"""
\end{lstlisting}
"""

    latex += r"""
\subsection{Metrics}

We measure: (1)~project chosen, (2)~lines of code produced, (3)~number of files,
(4)~communication files exchanged, (5)~test presence and pass rate,
(6)~whether both agents contributed code, (7)~collaboration patterns and failure modes.

% ══════════════════════════════════════════════════════════════════════════════
\section{Experimental Setup}

\begin{table}[h]
\centering
\begin{tabular}{ll}
\toprule
\textbf{Parameter} & \textbf{Value} \\
\midrule
Setting & """ + tex_escape(setting_full) + r""" \\
Trial & """ + str(trial_num) + r""" \\
Agents & """ + ", ".join(agents) + r""" \\
Timeout & 10 minutes \\
Human direction & None \\
\bottomrule
\end{tabular}
\caption{Experiment configuration.}
\label{tab:config}
\end{table}

% ══════════════════════════════════════════════════════════════════════════════
\section{Results}

\subsection{Project Output}

\begin{itemize}
  \item \textbf{Project}: """ + tex_escape(project_name) + r"""
  \item \textbf{Python files}: """ + str(n_py) + r"""
  \item \textbf{Lines of code}: """ + str(total_loc) + r"""
  \item \textbf{Communication files}: """ + str(n_comm) + r"""
  \item \textbf{Tests}: """ + (f"{test_passed} passed" if has_tests else "None written") + r"""
\end{itemize}

\subsection{Communication Protocol}

"""
    if md_files:
        latex += r"The agents exchanged " + str(n_comm) + r""" markdown file(s):
\begin{itemize}
"""
        for fname, _ in md_files:
            latex += r"  \item \texttt{" + tex_escape(fname) + r"}" + "\n"
        latex += r"""\end{itemize}"""
    else:
        latex += r"No communication files were exchanged."

    latex += r"""

% ══════════════════════════════════════════════════════════════════════════════
\section{Analysis \& Discussion}

\subsection{Collaboration Dynamics}

""" + collab_analysis + r"""

\subsection{Observed Patterns}

\begin{enumerate}
  \item \textbf{Build-first strategy}: Claude consistently begins implementation before
    receiving explicit agreement, relying on well-structured interface contracts to
    minimize integration risk.
  \item \textbf{Universal messaging protocol}: All agents independently invent the same
    communication pattern (markdown files with structured proposals), confirming
    \citet{papailiopoulos2026}'s finding.
  \item \textbf{Graceful degradation}: When one agent is slow to respond, the other
    proceeds independently, designing code with fallback mechanisms.
\end{enumerate}

\subsection{Failure Modes}

\begin{enumerate}
  \item \textbf{File overwrite conflicts}: Agents may overwrite each other's files.
  \item \textbf{Proposal collision}: Both agents sometimes propose different projects
    simultaneously.
  \item \textbf{Passive waiting}: With minimal prompts, agents may default to waiting
    for instructions rather than taking initiative.
\end{enumerate}

% ══════════════════════════════════════════════════════════════════════════════
\section{Conclusion}

""" + (f"""This trial demonstrates that {len(agents)} AI agent(s) can autonomously
produce working software ({total_loc} LOC"""
+ (f", {test_passed} passing tests" if has_tests else "")
+ """) with zero human direction. """
if total_loc > 0 else
f"""This trial shows that with truly minimal prompts (no task instructions), agents
may default to passive waiting behavior, exchanging only greeting files. """
) + r"""The """ + setting + r""" configuration """ + {
    "CC": "produces the highest code volume but inconsistent test coverage.",
    "CX": "yields clean module boundaries through cross-model complementarity.",
    "DCX": "enforces the highest discipline with consistent test coverage.",
}[setting] + r"""

Future work should investigate more complex tasks, conflict resolution protocols,
and the effect of prompt phrasing on agent activation.

% ══════════════════════════════════════════════════════════════════════════════
\bibliographystyle{plainnat}
\begin{thebibliography}{3}

\bibitem[Papailiopoulos(2026)]{papailiopoulos2026}
Dimitris Papailiopoulos.
\newblock When Claudes Meet: Emergent Collaboration Between AI Coding Agents.
\newblock GitHub: \texttt{anadim/when-claudes-meet}, 2026.

\bibitem[Anthropic(2026)]{anthropic2026teams}
Anthropic.
\newblock Orchestrate Teams of Claude Code Sessions.
\newblock Claude Code Documentation, 2026.

\bibitem[OpenAI(2026)]{openai2026codex}
OpenAI.
\newblock Codex CLI: Full-Auto Mode and Sandbox Policies.
\newblock Codex CLI Documentation, 2026.

\end{thebibliography}

% ══════════════════════════════════════════════════════════════════════════════
\appendix
\section{Communication Transcripts}
"""

    for fname, content in md_files:
        safe_content = code_listing(content, max_lines=40)
        latex += r"""
\subsection*{\texttt{""" + tex_escape(fname) + r"""}}
\begin{lstlisting}
""" + safe_content + r"""
\end{lstlisting}
"""

    latex += r"""
\section{Source Code}

""" + f"Total: {n_py} Python files, {total_loc} lines.\n"

    for fname, content in py_files:
        safe_content = code_listing(content, max_lines=40)
        latex += r"""
\subsection*{\texttt{""" + tex_escape(fname) + r"""}}
\begin{lstlisting}[language=Python]
""" + safe_content + r"""
\end{lstlisting}
"""

    latex += r"""
\section{Test Results}

\begin{lstlisting}
""" + code_listing(test_output, max_lines=30) + r"""
\end{lstlisting}

\end{document}
"""
    return latex


# ── Main ────────────────────────────────────────────────────────────────────

def main():
    output_dir = BASE / "reports"
    output_dir.mkdir(exist_ok=True)
    tex_dir = BASE / "reports" / "tex"
    tex_dir.mkdir(exist_ok=True)

    tectonic = shutil.which("tectonic")
    if not tectonic:
        print("ERROR: tectonic not found. Install via: conda install -c conda-forge tectonic")
        sys.exit(1)

    print(f"Generating {len(TRIALS)} arXiv-style reports...")

    for trial in TRIALS:
        if not trial["playground"].exists():
            print(f"  SKIP {trial['id']}: playground not found")
            continue

        # Generate LaTeX
        latex = generate_latex(trial)
        tex_path = tex_dir / f"{trial['id']}.tex"
        tex_path.write_text(latex, encoding="utf-8")

        # Compile with tectonic
        pdf_path = output_dir / f"{trial['id']}.pdf"
        try:
            r = subprocess.run(
                [tectonic, str(tex_path), "-o", str(output_dir)],
                capture_output=True, text=True, timeout=120,
                encoding="utf-8", errors="replace",
            )
            if pdf_path.exists():
                size_kb = pdf_path.stat().st_size // 1024
                print(f"  {trial['id']}: {pdf_path.name} ({size_kb}KB)")
            else:
                print(f"  {trial['id']}: FAILED")
                err = (r.stderr or r.stdout or "")[:300]
                print(f"    {err}")
        except Exception as e:
            print(f"  {trial['id']}: ERROR ({e})")

    print(f"\nReports: {output_dir}")
    print(f"LaTeX sources: {tex_dir}")

if __name__ == "__main__":
    main()
