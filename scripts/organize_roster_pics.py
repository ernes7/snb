"""Move cropped roster screenshots into team folders, named by player.

Reads .scratch/roster_ids.md for the identification map, then moves each
image from C:/Users/ernes/Videos/Captures/cropped/ to
static/graphics/players/<TEAM>/<player_filename>.png.

Idempotent: if the destination exists, skips. If the source is gone
(already moved), skips quietly.
"""
from __future__ import annotations

import re
import shutil
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRATCH = PROJECT_ROOT / ".scratch" / "roster_ids.md"
SOURCE_DIR = Path(r"C:\Users\ernes\Videos\Captures\cropped")
DEST_BASE = PROJECT_ROOT / "static" / "graphics" / "players"

LINE_RE = re.compile(
    r"^(?P<ts>\d{1,2}_\d{2}_\d{2} [AP]M)\s*\|\s*"
    r"(?P<team>[A-Z]{3})\s*\|\s*"
    r"(?P<name>[^|]+?)\s*\|"
)


def slugify(name: str) -> str:
    """Convert a DB player name to a safe filename base.

    "R. Lunar"         -> "R_Lunar"
    "A. Sanchez LTU"   -> "A_Sanchez_LTU"
    "L. La O"          -> "L_La_O"
    "C. Barrabi Jr."   -> "C_Barrabi_Jr"
    "L. Gourriel Jr"   -> "L_Gourriel_Jr"
    """
    cleaned = name.replace(".", "").strip()
    return re.sub(r"\s+", "_", cleaned)


def source_path(timestamp: str) -> Path:
    return SOURCE_DIR / f"MVP Cuba 2011 4_10_2026 {timestamp}.png"


def main() -> None:
    if not SCRATCH.exists():
        raise SystemExit(f"Scratch file missing: {SCRATCH}")

    moved = 0
    skipped = 0
    missing = 0
    collisions: list[str] = []

    for raw in SCRATCH.read_text(encoding="utf-8").splitlines():
        m = LINE_RE.match(raw)
        if not m:
            continue
        ts = m.group("ts")
        team = m.group("team")
        name = m.group("name").strip()

        src = source_path(ts)
        dest_dir = DEST_BASE / team
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / f"{slugify(name)}.png"

        if dest.exists():
            collisions.append(f"{team}/{dest.name}  ({ts} | {name})")
            skipped += 1
            continue
        if not src.exists():
            missing += 1
            continue

        shutil.move(str(src), str(dest))
        moved += 1

    print(f"Moved:    {moved}")
    print(f"Skipped:  {skipped} (destination already exists)")
    print(f"Missing:  {missing} (source not found — possibly already moved)")
    if collisions:
        print("\nCollisions — two images mapped to the same destination name:")
        for c in collisions:
            print(f"  {c}")


if __name__ == "__main__":
    main()
