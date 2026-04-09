"""Crop roster screenshots to just the player attribute area.

Usage:
    python scripts/crop_attributes.py [source_dir]

Defaults to C:/Users/ernes/Videos/Captures.
Saves cropped copies to a 'cropped/' subfolder — originals are never modified.
"""
from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image

# Crop ratio: attribute area occupies top ~43% of the screen
CROP_RATIO = 0.43
DEFAULT_SOURCE = Path(r"C:\Users\ernes\Videos\Captures")


def crop_all(source: Path) -> int:
    """Crop all PNGs in source dir to top portion. Returns count."""
    out_dir = source / "cropped"
    out_dir.mkdir(exist_ok=True)

    count = 0
    for png in sorted(source.glob("*.png")):
        img = Image.open(png)
        crop_height = int(img.height * CROP_RATIO)
        cropped = img.crop((0, 0, img.width, crop_height))
        cropped.save(out_dir / png.name)
        count += 1

    if count:
        print(f"Cropped {count} images -> {out_dir}")
    else:
        print(f"No PNGs found in {source}")
    return count


if __name__ == "__main__":
    source = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_SOURCE
    if not source.exists():
        print(f"Directory not found: {source}")
        sys.exit(1)
    crop_all(source)
