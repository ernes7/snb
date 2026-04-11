"""Generate upscaled attribute-area crops for each organized roster image.

Reads every PNG under static/graphics/players/<TEAM>/ and writes a zoomed
crop of just the attribute numbers area to .scratch/attr_crops/<TEAM>/.
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SRC_BASE = ROOT / "static" / "graphics" / "players"
DEST_BASE = ROOT / ".scratch" / "attr_crops"

# Crop box in relative coordinates (left, top, right, bottom)
CROP_BOX = (0.15, 0.30, 0.85, 1.00)
SCALE = 3


def crop_image(src: Path, dest: Path) -> None:
    im = Image.open(src)
    w, h = im.size
    l = int(w * CROP_BOX[0])
    t = int(h * CROP_BOX[1])
    r = int(w * CROP_BOX[2])
    b = int(h * CROP_BOX[3])
    region = im.crop((l, t, r, b))
    region = region.resize(
        (region.width * SCALE, region.height * SCALE),
        Image.NEAREST,
    )
    dest.parent.mkdir(parents=True, exist_ok=True)
    region.save(dest)


def main() -> None:
    count = 0
    for team_dir in sorted(SRC_BASE.iterdir()):
        if not team_dir.is_dir():
            continue
        for png in sorted(team_dir.glob("*.png")):
            out = DEST_BASE / team_dir.name / png.name
            crop_image(png, out)
            count += 1
    print(f"Cropped {count} images to {DEST_BASE}")


if __name__ == "__main__":
    main()
