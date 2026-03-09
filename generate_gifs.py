"""Generate animated GIFs showing what agents did in each experiment."""

from __future__ import annotations
import subprocess, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

BASE = Path(__file__).resolve().parent

# ── Config ──────────────────────────────────────────────────────────────────

W, H = 1280, 720
BG = (18, 18, 40)         # dark navy
FG = (220, 220, 230)      # light gray
DIM = (120, 120, 140)     # muted
CYAN = (80, 200, 220)     # filenames
PURPLE = (180, 120, 255)  # Claude
GREEN = (80, 220, 130)    # Codex
YELLOW = (240, 200, 80)   # Director
RED = (255, 100, 100)     # errors/passive
WHITE = (255, 255, 255)
ACCENT = (60, 130, 246)   # section bars

AGENT_COLORS = {
    "claude-a": PURPLE, "claude-b": (140, 160, 255),
    "claude": PURPLE, "codex": GREEN,
    "director": YELLOW, "claude-worker": PURPLE, "codex-worker": GREEN,
}

FONT_SIZE = 16
FONT_SMALL = 13
FONT_TITLE = 28
FONT_SUB = 20

try:
    FONT = ImageFont.truetype("cour.ttf", FONT_SIZE)
    FONT_S = ImageFont.truetype("cour.ttf", FONT_SMALL)
    FONT_T = ImageFont.truetype("courbd.ttf", FONT_TITLE)
    FONT_ST = ImageFont.truetype("cour.ttf", FONT_SUB)
except:
    FONT = ImageFont.load_default()
    FONT_S = FONT_T = FONT_ST = FONT

TRIALS = [
    ("cc_r1", "CC", 1, BASE / "playground_cc", ["Claude-A", "Claude-B"]),
    ("cc_r2", "CC", 2, BASE / "playground_cc_r2", ["Claude-A", "Claude-B"]),
    ("cc_r3", "CC", 3, BASE / "playground_cc_r3", ["Claude-A", "Claude-B"]),
    ("cx_r1", "CX", 1, BASE / "playground_cx", ["Claude", "Codex"]),
    ("cx_r2", "CX", 2, BASE / "playground_cx_r2", ["Claude", "Codex"]),
    ("cx_r3", "CX", 3, BASE / "playground_cx_r3", ["Claude", "Codex"]),
    ("dcx_r1", "DCX", 1, BASE / "playground_dcx", ["Director", "Claude-Worker", "Codex-Worker"]),
    ("dcx_r2", "DCX", 2, BASE / "playground_dcx_r2", ["Director", "Claude-Worker", "Codex-Worker"]),
    ("dcx_r3", "DCX", 3, BASE / "playground_dcx_r3", ["Director", "Claude-Worker", "Codex-Worker"]),
]

SETTING_NAMES = {"CC": "Claude + Claude", "CX": "Claude + Codex", "DCX": "Director + Claude + Codex"}

# ── Helpers ─────────────────────────────────────────────────────────────────

def read_file(p: Path) -> str:
    try: return p.read_text(encoding="utf-8", errors="replace")
    except: return ""

def count_loc(pg: Path) -> int:
    return sum(len(read_file(f).splitlines())
               for f in pg.rglob("*.py") if "__pycache__" not in str(f))

def run_tests(pg: Path) -> tuple[bool, int]:
    tfs = list(pg.glob("test_*.py"))
    if not tfs: return False, 0
    try:
        r = subprocess.run([sys.executable, "-m", "pytest", "-q"] + [str(f) for f in tfs],
                           capture_output=True, text=True, timeout=30, cwd=str(pg),
                           encoding="utf-8", errors="replace")
        out = r.stdout or ""
        for part in out.split():
            if part.isdigit() and "passed" in out[out.index(part):out.index(part)+20]:
                return True, int(part)
        return r.returncode == 0, 0
    except: return False, 0

def project_name(pg: Path) -> str:
    for name in ["DONE.md", "RESULT.md", "SUMMARY.md"]:
        p = pg / name
        if p.exists():
            for line in read_file(p).splitlines():
                line = line.strip().lstrip("#").strip()
                if line and len(line) > 3: return line[:50]
    py = [f.stem for f in pg.glob("*.py") if not f.name.startswith("test_") and f.name != "main.py" and "__" not in f.name]
    return py[0].replace("_", " ").title() if py else "No Project"

def infer_author(filename: str, content: str) -> str:
    fname_lower = filename.lower()
    if "claude-a" in fname_lower or "claude_a" in fname_lower: return "claude-a"
    if "claude-b" in fname_lower or "claude_b" in fname_lower: return "claude-b"
    if "codex" in fname_lower: return "codex"
    if "director" in fname_lower: return "director"
    if "hello_codex" in fname_lower: return "claude"
    if "hello_claude" in fname_lower: return "codex"
    content_lower = content.lower()[:500]
    if "claude-a" in content_lower or "i'm claude-a" in content_lower: return "claude-a"
    if "claude-b" in content_lower or "i'm claude-b" in content_lower: return "claude-b"
    if "codex" in content_lower and "i'm codex" in content_lower: return "codex"
    return "claude"

def get_files_ordered(pg: Path) -> list[tuple[str, str, str]]:
    """Return (filename, content, author) ordered: .md first, then .py, then tests."""
    files = []
    for f in sorted(pg.rglob("*")):
        if f.is_file() and "__pycache__" not in str(f) and not f.name.startswith("."):
            rel = str(f.relative_to(pg))
            content = read_file(f)
            author = infer_author(rel, content)
            files.append((rel, content, author))
    # Sort: .md first, then non-test .py, then test .py
    def sort_key(item):
        name = item[0]
        if name.endswith(".md"): return (0, name)
        if name.startswith("test_"): return (2, name)
        if name.endswith(".py"): return (1, name)
        return (3, name)
    files.sort(key=sort_key)
    return files

# ── Frame Rendering ─────────────────────────────────────────────────────────

def new_frame() -> Image.Image:
    return Image.new("RGB", (W, H), BG)

def draw_bar(draw: ImageDraw.ImageDraw, y: int, color=ACCENT):
    draw.rectangle([40, y, W - 40, y + 2], fill=color)

def draw_header(draw: ImageDraw.ImageDraw, setting: str, trial: int, y: int = 30) -> int:
    title = f"{setting} Trial {trial}"
    subtitle = SETTING_NAMES.get(setting, setting)
    draw.text((W // 2, y), title, fill=WHITE, font=FONT_T, anchor="mt")
    draw.text((W // 2, y + 38), subtitle, fill=DIM, font=FONT_ST, anchor="mt")
    draw_bar(draw, y + 65)
    return y + 78

def draw_footer(draw: ImageDraw.ImageDraw, loc: int, n_files: int, n_tests: int):
    y = H - 40
    draw_bar(draw, y - 8, DIM)
    stats = f"Files: {n_files}   |   LOC: {loc}   |   Tests: {n_tests}"
    draw.text((W // 2, y + 5), stats, fill=DIM, font=FONT_S, anchor="mt")

def make_title_frame(setting: str, trial: int, agents: list[str],
                     loc: int, n_files: int, n_tests: int, project: str) -> Image.Image:
    img = new_frame()
    draw = ImageDraw.Draw(img)
    y = draw_header(draw, setting, trial, y=60)
    y += 40
    draw.text((W // 2, y), f'Project: {project}', fill=CYAN, font=FONT_ST, anchor="mt")
    y += 50
    draw.text((W // 2, y), "Agents:", fill=DIM, font=FONT, anchor="mt")
    y += 30
    for agent in agents:
        color = AGENT_COLORS.get(agent.lower().replace(" ", "-"), FG)
        draw.text((W // 2, y), agent, fill=color, font=FONT, anchor="mt")
        y += 24
    y += 30
    stats_lines = [
        f"{n_files} files created",
        f"{loc} lines of Python",
        f"{n_tests} tests passing" if n_tests > 0 else "No tests written",
    ]
    for line in stats_lines:
        color = GREEN if "passing" in line else (RED if "No tests" in line else FG)
        draw.text((W // 2, y), line, fill=color, font=FONT, anchor="mt")
        y += 26
    return img

def make_prompt_frame(setting: str, trial: int, agents: list[str]) -> Image.Image:
    img = new_frame()
    draw = ImageDraw.Draw(img)
    y = draw_header(draw, setting, trial)
    y += 10
    draw.text((60, y), "Prompt given to each agent:", fill=DIM, font=FONT)
    y += 30
    # Draw prompt box
    draw.rectangle([50, y, W - 50, y + 120], outline=DIM, width=1)
    prompt_lines = [
        'You are "[name]". Your shared workspace is: [path]',
        '',
        'The other agent is "[name]". You can communicate',
        'through files in the workspace. This workspace is',
        'yours -- you are free to use it however you want.',
    ]
    for line in prompt_lines:
        draw.text((65, y + 8), line, fill=CYAN, font=FONT_S)
        y += 18
    return img

def make_file_frame(setting: str, trial: int, filename: str, content: str,
                    author: str, file_idx: int, total_files: int,
                    loc: int, n_files: int, n_tests: int) -> Image.Image:
    img = new_frame()
    draw = ImageDraw.Draw(img)
    y = draw_header(draw, setting, trial)

    # File counter
    draw.text((W - 60, y + 5), f"{file_idx}/{total_files}", fill=DIM, font=FONT_S, anchor="rt")

    # Author + filename
    author_color = AGENT_COLORS.get(author, FG)
    y += 8
    draw.text((60, y), f"[{author}]", fill=author_color, font=FONT)
    author_w = draw.textlength(f"[{author}]  ", font=FONT)
    draw.text((60 + author_w, y), filename, fill=CYAN, font=FONT)
    y += 30

    # Content box
    box_top = y
    box_bottom = H - 55
    draw.rectangle([50, box_top, W - 50, box_bottom], outline=(50, 50, 70), width=1)

    # Render content lines
    lines = content.splitlines()
    max_lines = (box_bottom - box_top - 16) // 17
    for i, line in enumerate(lines[:max_lines]):
        if len(line) > 85:
            line = line[:82] + "..."
        # Syntax-like coloring
        color = FG
        stripped = line.strip()
        if stripped.startswith("#") or stripped.startswith("//"):
            color = DIM
        elif stripped.startswith("def ") or stripped.startswith("class "):
            color = YELLOW
        elif stripped.startswith("import ") or stripped.startswith("from "):
            color = (100, 160, 220)
        elif stripped.startswith("assert "):
            color = GREEN
        draw.text((65, box_top + 8 + i * 17), line, fill=color, font=FONT_S)

    if len(lines) > max_lines:
        draw.text((65, box_bottom - 20),
                   f"... ({len(lines)} lines total)", fill=DIM, font=FONT_S)

    draw_footer(draw, loc, n_files, n_tests)
    return img

def make_summary_frame(setting: str, trial: int, files: list[tuple[str, str, str]],
                       loc: int, n_tests: int, project: str, active: bool) -> Image.Image:
    img = new_frame()
    draw = ImageDraw.Draw(img)
    y = draw_header(draw, setting, trial)
    y += 15

    if not active:
        draw.text((W // 2, y + 60), "Agents waited", fill=RED, font=FONT_T, anchor="mt")
        draw.text((W // 2, y + 100), "No project was built in this trial.", fill=DIM, font=FONT, anchor="mt")
        draw.text((W // 2, y + 140), "The minimal prompt did not activate autonomous behavior.",
                   fill=DIM, font=FONT_S, anchor="mt")
        return img

    draw.text((W // 2, y), f"Completed: {project}", fill=GREEN, font=FONT_ST, anchor="mt")
    y += 40

    # File list
    draw.text((60, y), "Files created:", fill=DIM, font=FONT)
    y += 26
    for fname, _, author in files:
        color = AGENT_COLORS.get(author, FG)
        draw.text((80, y), f"  {fname}", fill=color, font=FONT_S)
        y += 19
        if y > H - 120: break

    y = H - 110
    draw_bar(draw, y)
    y += 12
    draw.text((W // 2, y), f"{len(files)} files  |  {loc} LOC  |  {n_tests} tests",
              fill=WHITE, font=FONT, anchor="mt")
    y += 30
    status = "All tests passing" if n_tests > 0 else "No tests written"
    color = GREEN if n_tests > 0 else YELLOW
    draw.text((W // 2, y), status, fill=color, font=FONT, anchor="mt")
    return img


# ── GIF Assembly ────────────────────────────────────────────────────────────

def generate_gif(trial_id: str, setting: str, trial: int,
                 pg: Path, agents: list[str], output_dir: Path) -> Path | None:
    files = get_files_ordered(pg)
    loc = count_loc(pg)
    _, n_tests = run_tests(pg)
    project = project_name(pg)
    n_files = len(files)
    active = loc > 0

    frames: list[Image.Image] = []
    durations: list[int] = []  # milliseconds

    # Frame 1: Title
    frames.append(make_title_frame(setting, trial, agents, loc, n_files, n_tests, project))
    durations.append(3000)

    # Frame 2: Prompt
    frames.append(make_prompt_frame(setting, trial, agents))
    durations.append(2500)

    # Frames 3-N: Each file
    for i, (fname, content, author) in enumerate(files, 1):
        frames.append(make_file_frame(
            setting, trial, fname, content, author,
            i, n_files, loc, n_files, n_tests))
        durations.append(3500)

    # Final: Summary
    frames.append(make_summary_frame(setting, trial, files, loc, n_tests, project, active))
    durations.append(4000)

    # Save GIF
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{trial_id}.gif"
    frames[0].save(
        str(path), save_all=True, append_images=frames[1:],
        duration=durations, loop=0, optimize=False,
    )
    return path


# ── Main ────────────────────────────────────────────────────────────────────

def main():
    output_dir = BASE / "gifs"
    print(f"Generating {len(TRIALS)} experiment GIFs...")

    for trial_id, setting, trial, pg, agents in TRIALS:
        if not pg.exists():
            print(f"  SKIP {trial_id}")
            continue
        path = generate_gif(trial_id, setting, trial, pg, agents, output_dir)
        if path:
            size_kb = path.stat().st_size // 1024
            n_frames = len(get_files_ordered(pg)) + 3  # title + prompt + files + summary
            print(f"  {trial_id}: {path.name} ({size_kb}KB, {n_frames} frames)")

    print(f"\nAll GIFs saved to: {output_dir}")

if __name__ == "__main__":
    main()
