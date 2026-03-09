"""Generate story-driven animated GIFs for each experiment trial.

Each GIF tells the narrative: who spoke, what they proposed,
what they built, and the outcome — not code dumps.
"""

from __future__ import annotations
import subprocess, sys, textwrap
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

BASE = Path(__file__).resolve().parent

# ── Visual Config ───────────────────────────────────────────────────────────

W, H = 1920, 1080
BG = (15, 15, 30)
FG = (210, 210, 220)
DIM = (110, 110, 130)
CYAN = (80, 210, 230)
PURPLE = (170, 120, 255)
BLUE_LIGHT = (130, 160, 255)
GREEN = (80, 220, 130)
YELLOW = (240, 200, 80)
RED = (255, 90, 90)
WHITE = (255, 255, 255)
ACCENT = (60, 130, 246)
BOX_BG = (25, 25, 50)
BOX_BORDER = (50, 50, 80)

AGENT_COLORS = {
    "Claude-A": PURPLE, "Claude-B": BLUE_LIGHT,
    "Claude": PURPLE, "Codex": GREEN,
    "Director": YELLOW, "Claude-Worker": PURPLE, "Codex-Worker": GREEN,
}

try:
    F_TITLE = ImageFont.truetype("courbd.ttf", 40)
    F_SUB = ImageFont.truetype("cour.ttf", 26)
    F_BODY = ImageFont.truetype("cour.ttf", 22)
    F_SMALL = ImageFont.truetype("cour.ttf", 18)
    F_CODE = ImageFont.truetype("cour.ttf", 16)
    F_BIG = ImageFont.truetype("courbd.ttf", 52)
except:
    F_TITLE = F_SUB = F_BODY = F_SMALL = F_CODE = F_BIG = ImageFont.load_default()

SETTING_NAMES = {"CC": "Claude + Claude", "CX": "Claude + Codex", "DCX": "Director + Claude + Codex"}

# ── Data Helpers ────────────────────────────────────────────────────────────

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
            if part.isdigit() and "passed" in out:
                return True, int(part)
        return r.returncode == 0, 0
    except: return False, 0

def extract_story(pg: Path, setting: str, agents: list[str]) -> dict:
    """Extract the narrative elements from a trial."""
    md_files = sorted(pg.glob("*.md"))
    py_files = [f for f in sorted(pg.rglob("*.py"))
                if "__pycache__" not in str(f) and not f.name.startswith("test_")]
    test_files = [f for f in sorted(pg.glob("test_*.py"))]
    loc = count_loc(pg)
    t_pass, t_count = run_tests(pg)

    # Read first .md for the proposal
    proposals = []
    for md in md_files:
        content = read_file(md)
        proposals.append((md.name, content))

    # Determine project name
    project = "No Project"
    for md in md_files:
        for line in read_file(md).splitlines():
            stripped = line.strip().lstrip("#").strip()
            if "proposal:" in stripped.lower() or "let's build" in stripped.lower():
                project = stripped.split(":")[-1].strip() if ":" in stripped else stripped
                project = project[:50]
                break
        if project != "No Project":
            break
    if project == "No Project":
        for f in py_files:
            project = f.stem.replace("_", " ").title()
            break

    # Extract key quotes from communication
    key_quotes = []
    for md_name, content in proposals:
        lines = content.splitlines()
        for line in lines[:20]:
            stripped = line.strip().lstrip("#").strip()
            if stripped and len(stripped) > 10 and not stripped.startswith("```") and not stripped.startswith("-"):
                key_quotes.append(stripped[:90])
                if len(key_quotes) >= 3:
                    break

    # List built files with descriptions
    built_files = []
    for f in py_files:
        lines = read_file(f).splitlines()
        desc = ""
        for line in lines[:5]:
            if '"""' in line or "'''" in line:
                desc = line.strip().strip('"').strip("'").strip()[:60]
                break
        built_files.append((f.name, len(lines), desc))
    for f in test_files:
        lines = read_file(f).splitlines()
        built_files.append((f.name, len(lines), f"{t_count} tests"))

    return {
        "project": project,
        "loc": loc,
        "n_files": len(py_files) + len(test_files) + len(md_files),
        "t_count": t_count,
        "t_pass": t_pass,
        "proposals": proposals,
        "key_quotes": key_quotes,
        "built_files": built_files,
        "active": loc > 0,
        "md_names": [md.name for md in md_files],
    }


# ── Frame Builders ──────────────────────────────────────────────────────────

def new_frame() -> tuple[Image.Image, ImageDraw.ImageDraw]:
    img = Image.new("RGB", (W, H), BG)
    return img, ImageDraw.Draw(img)

def bar(draw, y, color=ACCENT, x1=80, x2=None):
    draw.rectangle([x1, y, x2 or W - 80, y + 2], fill=color)

def frame_title(setting: str, trial: int, agents: list[str]) -> Image.Image:
    img, draw = new_frame()
    cy = H // 2 - 120
    draw.text((W // 2, cy), f"{setting} Trial {trial}", fill=WHITE, font=F_BIG, anchor="mt")
    draw.text((W // 2, cy + 65), SETTING_NAMES.get(setting, ""), fill=DIM, font=F_SUB, anchor="mt")
    bar(draw, cy + 100)
    y = cy + 130
    for agent in agents:
        color = AGENT_COLORS.get(agent, FG)
        draw.text((W // 2, y), agent, fill=color, font=F_BODY, anchor="mt")
        y += 32
    # Bottom
    draw.text((W // 2, H - 60), "Emergent Collaboration Experiment", fill=DIM, font=F_SMALL, anchor="mt")
    return img

def frame_prompt(setting: str, trial: int) -> Image.Image:
    img, draw = new_frame()
    draw.text((W // 2, 60), f"{setting} Trial {trial}", fill=DIM, font=F_SUB, anchor="mt")
    bar(draw, 95)
    draw.text((W // 2, 130), "The Prompt", fill=WHITE, font=F_TITLE, anchor="mt")
    draw.text((W // 2, 180), "Given to each agent — no task, no instructions:", fill=DIM, font=F_SMALL, anchor="mt")
    # Prompt box
    box_y = 230
    draw.rounded_rectangle([120, box_y, W - 120, box_y + 200], radius=12, fill=BOX_BG, outline=BOX_BORDER)
    lines = [
        'You are "[name]".',
        'Your shared workspace is: [path]',
        '',
        'The other agent is "[name]".',
        'You can communicate through files in the workspace.',
        'This workspace is yours -- you are free to use it',
        'however you want.',
    ]
    for i, line in enumerate(lines):
        draw.text((160, box_y + 20 + i * 24), line, fill=CYAN, font=F_BODY)
    # Emphasis
    draw.text((W // 2, box_y + 250), '"you are free"', fill=YELLOW, font=F_SUB, anchor="mt")
    draw.text((W // 2, box_y + 290), "This single phrase is the activation signal.", fill=DIM, font=F_SMALL, anchor="mt")
    return img

def frame_communication(setting: str, trial: int, proposals: list[tuple[str, str]],
                        agents: list[str]) -> Image.Image:
    img, draw = new_frame()
    draw.text((W // 2, 60), f"{setting} Trial {trial}", fill=DIM, font=F_SUB, anchor="mt")
    bar(draw, 95)
    draw.text((W // 2, 130), "Communication", fill=WHITE, font=F_TITLE, anchor="mt")

    y = 200
    for md_name, content in proposals[:3]:
        # Determine speaker from filename
        speaker = "Agent"
        color = FG
        name_lower = md_name.lower()
        for agent in agents:
            if agent.lower().replace("-", "").replace(" ", "") in name_lower.replace("-", "").replace("_", ""):
                speaker = agent
                color = AGENT_COLORS.get(agent, FG)
                break
        if "hello" in name_lower:
            for agent in agents:
                if agent.lower() not in name_lower.lower():
                    speaker = agent  # hello_codex means Claude wrote it
                    color = AGENT_COLORS.get(agent, FG)
                    break

        # Speaker bubble
        draw.text((100, y), f"{speaker}:", fill=color, font=F_BODY)
        draw.text((100 + len(speaker) * 14 + 20, y), md_name, fill=DIM, font=F_SMALL)
        y += 30

        # Quote box with first meaningful lines
        lines = content.splitlines()
        shown = []
        for line in lines:
            stripped = line.strip().lstrip("#").strip()
            if stripped and not stripped.startswith("```") and not stripped.startswith("---"):
                shown.append(stripped[:85])
            if len(shown) >= 4:
                break

        box_h = len(shown) * 24 + 20
        draw.rounded_rectangle([120, y, W - 120, y + box_h], radius=8, fill=BOX_BG, outline=color + (80,) if len(color) == 3 else BOX_BORDER)
        for i, line in enumerate(shown):
            draw.text((145, y + 10 + i * 24), line, fill=FG, font=F_SMALL)
        y += box_h + 25

        if y > H - 100:
            break

    return img

def frame_what_they_built(setting: str, trial: int, story: dict) -> Image.Image:
    img, draw = new_frame()
    draw.text((W // 2, 60), f"{setting} Trial {trial}", fill=DIM, font=F_SUB, anchor="mt")
    bar(draw, 95)
    draw.text((W // 2, 130), "What They Built", fill=WHITE, font=F_TITLE, anchor="mt")
    draw.text((W // 2, 180), story["project"], fill=CYAN, font=F_SUB, anchor="mt")

    y = 240
    # File cards
    for fname, lines, desc in story["built_files"]:
        color = GREEN if "test" in fname else PURPLE
        draw.rounded_rectangle([120, y, W - 120, y + 50], radius=6, fill=BOX_BG, outline=BOX_BORDER)
        draw.text((145, y + 8), fname, fill=color, font=F_BODY)
        draw.text((500, y + 12), f"{lines} lines", fill=DIM, font=F_SMALL)
        if desc:
            draw.text((650, y + 12), desc, fill=DIM, font=F_SMALL)
        y += 60
        if y > H - 150:
            break

    # Stats bar
    y = H - 120
    bar(draw, y)
    stats = f"{story['loc']} lines of code    |    {len(story['built_files'])} files"
    draw.text((W // 2, y + 20), stats, fill=WHITE, font=F_BODY, anchor="mt")
    if story["t_count"] > 0:
        draw.text((W // 2, y + 55), f"{story['t_count']} tests passing", fill=GREEN, font=F_BODY, anchor="mt")
    return img

def frame_outcome(setting: str, trial: int, story: dict) -> Image.Image:
    img, draw = new_frame()
    draw.text((W // 2, 60), f"{setting} Trial {trial}", fill=DIM, font=F_SUB, anchor="mt")
    bar(draw, 95)

    if not story["active"]:
        draw.text((W // 2, H // 2 - 80), "Agents Waited", fill=RED, font=F_BIG, anchor="mt")
        draw.text((W // 2, H // 2), "No project was built.", fill=DIM, font=F_SUB, anchor="mt")
        draw.text((W // 2, H // 2 + 50), "The agents wrote hello files but took no initiative.",
                   fill=DIM, font=F_SMALL, anchor="mt")
        draw.text((W // 2, H // 2 + 90), "This is a prompt sensitivity finding:",
                   fill=DIM, font=F_SMALL, anchor="mt")
        draw.text((W // 2, H // 2 + 120), '"free" alone is not always enough to activate.',
                   fill=YELLOW, font=F_BODY, anchor="mt")
        return img

    draw.text((W // 2, 150), "Outcome", fill=WHITE, font=F_TITLE, anchor="mt")

    y = 230
    # Project name big
    draw.text((W // 2, y), story["project"], fill=CYAN, font=F_SUB, anchor="mt")
    y += 60

    # Key metrics in big numbers
    metrics = [
        (str(story["loc"]), "lines of code", PURPLE),
        (str(len(story["built_files"])), "files created", BLUE_LIGHT),
        (str(story["t_count"]), "tests passing" if story["t_count"] > 0 else "tests", GREEN if story["t_count"] > 0 else RED),
    ]
    x_positions = [W // 4, W // 2, 3 * W // 4]
    for (num, label, color), x in zip(metrics, x_positions):
        draw.text((x, y), num, fill=color, font=F_BIG, anchor="mt")
        draw.text((x, y + 60), label, fill=DIM, font=F_SMALL, anchor="mt")

    y += 130
    bar(draw, y)
    y += 25

    # Collaboration summary
    setting_summary = {
        "CC": "Two Claude instances collaborated autonomously.",
        "CX": "Claude and Codex worked across model boundaries.",
        "DCX": "Claude and Codex built while Director observed.",
    }
    draw.text((W // 2, y), setting_summary.get(setting, ""), fill=FG, font=F_BODY, anchor="mt")

    return img

def frame_passive(setting: str, trial: int) -> Image.Image:
    """Special frame for trials where agents didn't build anything."""
    img, draw = new_frame()
    draw.text((W // 2, H // 2 - 120), f"{setting} Trial {trial}", fill=DIM, font=F_SUB, anchor="mt")
    bar(draw, H // 2 - 75)
    draw.text((W // 2, H // 2 - 40), "Agents Waited", fill=RED, font=F_BIG, anchor="mt")
    draw.text((W // 2, H // 2 + 40), "Both agents wrote greeting files", fill=DIM, font=F_BODY, anchor="mt")
    draw.text((W // 2, H // 2 + 75), "but waited for instructions that never came.", fill=DIM, font=F_BODY, anchor="mt")
    draw.text((W // 2, H // 2 + 140), "Finding: Without explicit activation,", fill=YELLOW, font=F_BODY, anchor="mt")
    draw.text((W // 2, H // 2 + 175), "LLM agents default to passive behavior.", fill=YELLOW, font=F_BODY, anchor="mt")
    return img


# ── GIF Assembly ────────────────────────────────────────────────────────────

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

def generate_gif(trial_id, setting, trial, pg, agents, output_dir):
    story = extract_story(pg, setting, agents)
    frames = []
    durations = []

    # 1. Title (3s)
    frames.append(frame_title(setting, trial, agents))
    durations.append(3000)

    # 2. Prompt (3s)
    frames.append(frame_prompt(setting, trial))
    durations.append(3000)

    if story["active"]:
        # 3. Communication (4s)
        if story["proposals"]:
            frames.append(frame_communication(setting, trial, story["proposals"], agents))
            durations.append(4000)

        # 4. What they built (4s)
        if story["built_files"]:
            frames.append(frame_what_they_built(setting, trial, story))
            durations.append(4000)

        # 5. Outcome (4s)
        frames.append(frame_outcome(setting, trial, story))
        durations.append(4000)
    else:
        # Passive trial
        frames.append(frame_passive(setting, trial))
        durations.append(5000)

    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{trial_id}.gif"
    frames[0].save(str(path), save_all=True, append_images=frames[1:],
                   duration=durations, loop=0, optimize=False)
    return path


def main():
    output_dir = BASE / "gifs"
    print(f"Generating {len(TRIALS)} story GIFs (1920x1080)...")

    for trial_id, setting, trial, pg, agents in TRIALS:
        if not pg.exists():
            print(f"  SKIP {trial_id}")
            continue
        path = generate_gif(trial_id, setting, trial, pg, agents, output_dir)
        size_kb = path.stat().st_size // 1024
        story = extract_story(pg, setting, agents)
        tag = story["project"] if story["active"] else "PASSIVE"
        print(f"  {trial_id}: {size_kb:4}KB | {tag}")

    print(f"\nAll GIFs: {output_dir}")

if __name__ == "__main__":
    main()
