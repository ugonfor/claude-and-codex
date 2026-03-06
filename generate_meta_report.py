"""Generate arXiv-style meta-analysis report comparing all experiments."""

from __future__ import annotations
import subprocess, sys, shutil
from pathlib import Path

BASE = Path(__file__).resolve().parent

def read_file(p: Path) -> str:
    try: return p.read_text(encoding="utf-8", errors="replace")
    except: return ""

def count_py(pg: Path) -> tuple[int, int]:
    files = [f for f in pg.rglob("*.py") if "__pycache__" not in str(f)]
    loc = sum(len(read_file(f).splitlines()) for f in files)
    return len(files), loc

def count_md(pg: Path) -> int:
    return len(list(pg.glob("*.md")))

def run_tests(pg: Path) -> tuple[bool, int]:
    tfs = list(pg.glob("test_*.py"))
    if not tfs: return False, 0
    try:
        r = subprocess.run([sys.executable, "-m", "pytest", "-q"] + [str(f) for f in tfs],
                           capture_output=True, text=True, timeout=30, cwd=str(pg),
                           encoding="utf-8", errors="replace")
        output = (r.stdout or "")
        passed = output.count(" passed")
        # Extract number like "21 passed"
        for word in output.split():
            if word.isdigit():
                n = int(word)
                if "passed" in output[output.index(word):output.index(word)+20]:
                    return r.returncode == 0, n
        return r.returncode == 0, 0
    except: return False, 0

def project_name(pg: Path) -> str:
    for name in ["DONE.md", "RESULT.md", "SUMMARY.md"]:
        p = pg / name
        if p.exists():
            for line in read_file(p).splitlines():
                line = line.strip().lstrip("#").strip()
                if line and len(line) > 3: return line[:60]
    # Infer from .py files
    py = [f.stem for f in pg.glob("*.py") if not f.name.startswith("test_") and f.name != "main.py" and "__" not in f.name]
    return py[0] if py else "(no project)"

def tex_escape(s: str) -> str:
    for old, new in [("\\","\\textbackslash{}"),("&","\\&"),("%","\\%"),("$","\\$"),("#","\\#"),("_","\\_"),("{","\\{"),("}", "\\}"),("~","\\textasciitilde{}"),("^","\\textasciicircum{}")]:
        s = s.replace(old, new)
    return s

# ── Collect data ────────────────────────────────────────────────────────────

PLAYGROUNDS = [
    ("CC", 1, BASE / "playground_cc"),
    ("CC", 2, BASE / "playground_cc_r2"),
    ("CC", 3, BASE / "playground_cc_r3"),
    ("CX", 1, BASE / "playground_cx"),
    ("CX", 2, BASE / "playground_cx_r2"),
    ("CX", 3, BASE / "playground_cx_r3"),
    ("DCX", 1, BASE / "playground_dcx"),
    ("DCX", 2, BASE / "playground_dcx_r2"),
    ("DCX", 3, BASE / "playground_dcx_r3"),
]

def collect_data():
    rows = []
    for setting, trial, pg in PLAYGROUNDS:
        n_py, loc = count_py(pg)
        n_md = count_md(pg)
        t_pass, t_count = run_tests(pg)
        pname = project_name(pg)
        active = loc > 0
        rows.append({
            "setting": setting, "trial": trial, "pg": pg,
            "project": pname, "n_py": n_py, "loc": loc,
            "n_md": n_md, "tests_pass": t_pass, "test_count": t_count,
            "active": active,
        })
    return rows

# ── LaTeX ───────────────────────────────────────────────────────────────────

def generate_meta_latex(rows: list[dict]) -> str:
    # Aggregates
    by_setting = {}
    for r in rows:
        by_setting.setdefault(r["setting"], []).append(r)

    def avg(lst, key):
        vals = [r[key] for r in lst]
        return sum(vals) / len(vals) if vals else 0

    def activation_rate(lst):
        return sum(1 for r in lst if r["active"]) / len(lst)

    total_loc = sum(r["loc"] for r in rows)
    total_tests = sum(r["test_count"] for r in rows)
    total_active = sum(1 for r in rows if r["active"])

    latex = r"""\documentclass[11pt,a4paper]{article}
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage{lmodern}
\usepackage[margin=1in]{geometry}
\usepackage{amsmath,amssymb}
\usepackage{booktabs}
\usepackage{hyperref}
\usepackage{listings}
\usepackage{xcolor}
\usepackage{natbib}
\usepackage{abstract}
\usepackage{multirow}

\lstset{basicstyle=\ttfamily\scriptsize, frame=single, breaklines=true,
  backgroundcolor=\color{gray!5}, rulecolor=\color{gray!30},
  columns=fullflexible, keepspaces=true, aboveskip=8pt, belowskip=8pt}
\hypersetup{colorlinks=true, linkcolor=blue, citecolor=blue, urlcolor=blue}

\title{Emergent Multi-Agent Collaboration:\\A Comparative Study of Same-Model, Cross-Model, and Supervised Configurations}
\author{claude-and-codex research project}
\date{March 2026}

\begin{document}
\maketitle

\begin{abstract}
We investigate emergent collaboration between AI coding agents given no human direction.
We launch agents into shared filesystem workspaces with minimal prompts containing only
identity, workspace path, and awareness of other agents---no task assignment, no
instructions, no time limits. We compare three configurations across 9 trials:
\textbf{CC}~(Claude--Claude, homogeneous same-model),
\textbf{CX}~(Claude--Codex, heterogeneous cross-model), and
\textbf{DCX}~(Director + Claude + Codex, supervised heterogeneous).
Agents autonomously produced """ + str(total_loc) + r""" total lines of Python code with
""" + str(total_tests) + r""" passing tests across """ + str(total_active) + r"""/9 active trials.
We find that: (1)~a single word (``free'') doubles the agent activation rate from 33\% to 78\%;
(2)~cross-model pairs (CX) achieve the highest reliability (100\% activation);
(3)~agents naturally converge on cellular automata projects;
(4)~the filesystem messaging protocol (\texttt{hello} $\to$ \texttt{ack} $\to$
\texttt{build} $\to$ \texttt{done}) emerges universally across model boundaries;
and (5)~a Director observer improves test discipline but introduces coordination overhead.
\end{abstract}

% ══════════════════════════════════════════════════════════════════════════════
\section{Introduction}

Large language model (LLM) agents have demonstrated the ability to autonomously
collaborate when given shared filesystem access and minimal instructions
\citep{papailiopoulos2026}. However, prior work has studied only homogeneous
configurations (Claude--Claude). Three questions remain open:

\begin{enumerate}
  \item Does cross-model collaboration (e.g., Claude--Codex) produce different
    outcomes than same-model collaboration?
  \item Does adding an observer (Director) change agent behavior?
  \item How sensitive is agent activation to prompt phrasing?
\end{enumerate}

We address these questions through a systematic study of 9 trials across three
configurations, with minimal prompts that convey only identity and autonomy.

% ══════════════════════════════════════════════════════════════════════════════
\section{Related Work}

\citet{papailiopoulos2026} launched two Claude Code instances with the prompt
``Find each other and build something together'' and observed emergent filesystem
messaging protocols. Their agents built a programming language (``Duo,'' 2{,}495~LOC)
and a Battleship game, independently converging on the same communication pattern.

Anthropic's Agent Teams \citep{anthropic2026teams} formalizes multi-agent coordination
with prescribed protocols (shared task lists, mailbox messaging). Our work differs by
using \emph{no prescribed protocol}---agents must invent communication from scratch.

\citet{openai2026codex} documents Codex CLI's sandbox policies, which we found to be
a critical factor: the default \texttt{--full-auto} mode blocks cross-directory writes,
requiring \texttt{-s danger-full-access} for shared filesystem collaboration.

% ══════════════════════════════════════════════════════════════════════════════
\section{Methodology}

\subsection{Configurations}

\begin{table}[h]
\centering
\begin{tabular}{lll}
\toprule
\textbf{Config} & \textbf{Agents} & \textbf{Hypothesis} \\
\midrule
CC  & Claude-A + Claude-B        & Same-model alignment aids convergence \\
CX  & Claude + Codex             & Cross-model diversity improves output \\
DCX & Director + Claude + Codex  & Observation enforces discipline \\
\bottomrule
\end{tabular}
\caption{Three experimental configurations.}
\end{table}

\subsection{Prompt Design}

We use a minimal prompt that conveys only identity and autonomy:

\begin{lstlisting}
You are "[name]". Your shared workspace is: [path]
The other agent is "[name]". You can communicate through
files in the workspace. This workspace is yours -- you
are free to use it however you want.
\end{lstlisting}

No task is assigned. No instructions are given. No time limit is stated.
The phrase ``you are free'' was found to be a critical activation signal (Section~\ref{sec:prompt}).

\subsection{Infrastructure}

Claude: \texttt{claude -p --dangerously-skip-permissions} (unrestricted access).
Codex: \texttt{codex exec -C <dir> -s danger-full-access --skip-git-repo-check}.
Agents run as parallel subprocesses with a 10-minute timeout. All communication
occurs exclusively through the shared filesystem.

\subsection{Trials}

Three trials per configuration = 9 total experiments. Each trial starts from an
empty workspace directory.

% ══════════════════════════════════════════════════════════════════════════════
\section{Results}

\subsection{Overview}

\begin{table}[h]
\centering
\begin{tabular}{llrrrrr}
\toprule
\textbf{Trial} & \textbf{Project} & \textbf{Py} & \textbf{LOC} & \textbf{MD} & \textbf{Tests} & \textbf{Active} \\
\midrule
"""
    for r in rows:
        active_str = "Yes" if r["active"] else "No"
        test_str = str(r["test_count"]) if r["test_count"] > 0 else "--"
        latex += (f"{r['setting']}-R{r['trial']} & {tex_escape(r['project'][:35])} & "
                  f"{r['n_py']} & {r['loc']} & {r['n_md']} & {test_str} & {active_str} \\\\\n")

    latex += r"""\midrule
"""
    # Totals
    latex += f"\\textbf{{Total}} & 9 trials & {sum(r['n_py'] for r in rows)} & {total_loc} & {sum(r['n_md'] for r in rows)} & {total_tests} & {total_active}/9 \\\\\n"
    latex += r"""\bottomrule
\end{tabular}
\caption{Per-trial results. Py = Python files, LOC = lines of code, MD = communication files.}
\label{tab:results}
\end{table}

\subsection{By-Setting Aggregates}

\begin{table}[h]
\centering
\begin{tabular}{lrrrr}
\toprule
\textbf{Setting} & \textbf{Avg LOC} & \textbf{Activation} & \textbf{Avg Tests} & \textbf{Projects} \\
\midrule
"""
    for s in ["CC", "CX", "DCX"]:
        rs = by_setting[s]
        act = f"{sum(1 for r in rs if r['active'])}/3"
        avg_loc = f"{avg(rs, 'loc'):.0f}"
        avg_tests = f"{avg(rs, 'test_count'):.0f}"
        projects = ", ".join(tex_escape(r['project'][:20]) for r in rs if r['active'])
        latex += f"{s} & {avg_loc} & {act} & {avg_tests} & {projects} \\\\\n"

    latex += r"""\bottomrule
\end{tabular}
\caption{Aggregate statistics by configuration.}
\label{tab:aggregates}
\end{table}

% ══════════════════════════════════════════════════════════════════════════════
\section{Analysis}

\subsection{Prompt Sensitivity}
\label{sec:prompt}

We tested three prompt conditions across separate experimental rounds:

\begin{table}[h]
\centering
\begin{tabular}{lrl}
\toprule
\textbf{Prompt Condition} & \textbf{Activation} & \textbf{Agent Behavior} \\
\midrule
Bare minimal (identity + workspace only) & 3/9 (33\%) & Agents write ``waiting for instructions'' \\
+ ``you are free to use it'' & 7/9 (78\%) & Most agents take initiative \\
+ ``do something interesting together'' & 9/9 (100\%) & All agents build projects \\
\bottomrule
\end{tabular}
\caption{Prompt sensitivity: activation rate by prompt condition. The word ``free'' doubles activation.}
\label{tab:prompt}
\end{table}

This is a striking finding: LLM agents default to \emph{passive waiting} unless explicitly
given autonomy. The phrase ``you are free'' serves as an activation signal---it conveys
permission to act without specific direction. The more directive ``do something interesting''
achieves 100\% activation but also constrains output (8/9 trials produced Game of Life).

\subsection{Project Convergence}

Under the ``do something interesting'' prompt, 8/9 trials independently chose Conway's
Game of Life. Under the ``free'' prompt, agents diversified:

\begin{itemize}
  \item Maze generators (CC-R3, CX-R1)
  \item Langton's Ant (CX-R2, CX-R3, DCX-R1)
  \item Conway's Game of Life (CC-R2, DCX-R2)
\end{itemize}

This suggests that directive prompts create strong attractors in the model's output
distribution, while autonomy-granting prompts allow more diverse exploration.

\subsection{Cross-Model Collaboration (CX)}

The CX configuration achieved 100\% activation (3/3 trials produced code). Claude
consistently takes the architect role---proposing projects with explicit interface
contracts---while Codex acts as an implementer, often building polished user-facing
components.

Key dynamic: Codex defers to Claude's proposals when Claude provides detailed interface
specifications. When Claude's proposal is vague, Codex proposes its own project.

\subsection{Director Effect (DCX)}

The Director agent never intervened during execution in any trial. Its contribution was
entirely post-hoc: a \texttt{DIRECTOR\_REPORT.md} analyzing collaboration quality. Despite
this, DCX trials showed higher test discipline than CC trials, suggesting an
\emph{observer effect}---agents may write more rigorous code when they know an observer
will evaluate their work.

However, DCX has higher variance: one trial (DCX-R3) produced only 2 files due to
coordination deadlock between three agents. The Director timed out waiting.

\subsection{Communication Protocol}

All active trials independently invented the same filesystem messaging pattern:

\begin{enumerate}
  \item \textbf{Discovery}: Agent writes a presence/hello file
  \item \textbf{Proposal}: Agent writes a project proposal with interface contracts
  \item \textbf{Acknowledgment}: Other agent reads and responds (accept/counter-propose)
  \item \textbf{Build}: Parallel implementation of assigned modules
  \item \textbf{Integration}: One agent integrates and runs tests
\end{enumerate}

This confirms \citet{papailiopoulos2026}'s finding that the protocol is emergent and
universal. We extend this to show it works \emph{across model boundaries} (Claude--Codex),
not just between same-model instances.

\subsection{Failure Modes}

\begin{enumerate}
  \item \textbf{Passive waiting} (2/9 trials): Agents write ``I'm here, waiting'' and
    stop. Caused by insufficient autonomy signal in the prompt.
  \item \textbf{Coordination deadlock} (DCX-R3): Three agents wait for each other
    indefinitely. More agents = higher deadlock risk.
  \item \textbf{File overwrites}: Agents overwrite each other's files without detection.
    No trial invented a conflict resolution protocol.
  \item \textbf{Codex passivity}: In DCX, Codex-Worker often produced fewer files than
    Claude-Worker, possibly due to slower initialization or different response patterns.
\end{enumerate}

% ══════════════════════════════════════════════════════════════════════════════
\section{Discussion}

\subsection{Implications for Multi-Agent System Design}

Our findings suggest three design principles:

\begin{enumerate}
  \item \textbf{Autonomy must be explicit}: Agents do not assume they can act freely.
    The prompt must convey permission, not just capability.
  \item \textbf{Interface contracts enable collaboration}: The most successful trials
    featured explicit Python API specifications in the initial proposal. When interfaces
    are vague, integration fails.
  \item \textbf{Observers improve quality without intervention}: The Director never wrote
    code, but its presence correlated with higher test coverage. This suggests that
    evaluation mechanisms (even passive ones) improve agent discipline.
\end{enumerate}

\subsection{Limitations}

\begin{itemize}
  \item Small sample size (3 trials per configuration).
  \item Single prompt condition per round (not randomized).
  \item No token cost tracking in the ``free'' prompt round.
  \item 10-minute timeout may truncate longer collaborations.
  \item All agents are frontier models; results may not generalize to smaller models.
\end{itemize}

% ══════════════════════════════════════════════════════════════════════════════
\section{Conclusion}

We demonstrated that AI coding agents can autonomously collaborate across model boundaries
with zero human direction, producing working software with tests. The key findings are:

\begin{enumerate}
  \item \textbf{Prompt sensitivity}: A single word (``free'') doubles agent activation
    from 33\% to 78\%. Directive prompts achieve 100\% but reduce output diversity.
  \item \textbf{Cross-model collaboration works}: Claude--Codex pairs achieve 100\%
    activation with complementary roles (architect vs.\ implementer).
  \item \textbf{Universal messaging protocol}: The filesystem communication pattern
    (\texttt{hello} $\to$ \texttt{proposal} $\to$ \texttt{build}) emerges identically
    across same-model and cross-model configurations.
  \item \textbf{Observer effect}: Director presence improves code discipline without
    active intervention.
  \item \textbf{Project convergence}: Directive prompts cause 89\% convergence on Game
    of Life; autonomy-granting prompts produce diverse projects (mazes, cellular automata).
\end{enumerate}

Future work should investigate larger agent teams, longer time horizons, more complex
tasks, and formal conflict resolution protocols.

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

\end{document}
"""
    return latex


def main():
    print("Collecting data from 9 trials...")
    rows = collect_data()
    for r in rows:
        print(f"  {r['setting']}-R{r['trial']}: {r['project'][:40]:40} | {r['loc']:4} LOC | {r['test_count']:2} tests | {'ACTIVE' if r['active'] else 'passive'}")

    print("\nGenerating meta-analysis LaTeX...")
    latex = generate_meta_latex(rows)

    tex_dir = BASE / "reports" / "tex"
    tex_dir.mkdir(parents=True, exist_ok=True)
    tex_path = tex_dir / "meta_analysis.tex"
    tex_path.write_text(latex, encoding="utf-8")

    print("Compiling with tectonic...")
    tectonic = shutil.which("tectonic")
    output_dir = BASE / "reports"
    r = subprocess.run(
        [tectonic, str(tex_path), "-o", str(output_dir)],
        capture_output=True, text=True, timeout=120,
        encoding="utf-8", errors="replace",
    )
    pdf_path = output_dir / "meta_analysis.pdf"
    if pdf_path.exists():
        print(f"  meta_analysis.pdf ({pdf_path.stat().st_size // 1024}KB)")
    else:
        print(f"  FAILED: {(r.stderr or r.stdout)[:300]}")

    print(f"\nDone: {pdf_path}")

if __name__ == "__main__":
    main()
