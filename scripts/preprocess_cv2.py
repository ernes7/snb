"""Alternative image preprocessor for MVP Baseball 2005 box score screenshots.

Uses a fundamentally different pipeline from game-screenshot-ocr:
- LAB color space + CLAHE (vs direct grayscale)
- INTER_LANCZOS4 upscaling (vs nearest-neighbor)
- Bilateral filtering for edge-preserving denoising
- Unsharp masking before thresholding
- Otsu global threshold (vs adaptive Gaussian)
- Rectangular morphological kernel (vs ellipse)
"""

import argparse
import os
import sys
import cv2
import numpy as np
from pathlib import Path


CROP_BOX = (15, 40, 1190, 548)


def preprocess(input_path: str, output_path: str, scale: int = 4) -> None:
    img = cv2.imread(input_path)
    if img is None:
        print(f"  ERROR: Could not read {input_path}")
        return

    h, w = img.shape[:2]
    print(f"  Original: {w}x{h}")

    if w == 1280 and h == 720:
        x1, y1, x2, y2 = CROP_BOX
        img = img[y1:y2, x1:x2]
        ch, cw = img.shape[:2]
        print(f"  Cropped to data region: {cw}x{ch}")

    # Step 1: CLAHE in LAB color space (enhance local contrast before upscaling)
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    l_chan, a_chan, b_chan = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    l_chan = clahe.apply(l_chan)
    lab = cv2.merge([l_chan, a_chan, b_chan])
    img = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)

    # Step 2: Upscale with Lanczos interpolation (smoother than nearest-neighbor)
    new_w = img.shape[1] * scale
    new_h = img.shape[0] * scale
    img = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_LANCZOS4)

    # Step 3: Bilateral filter (edge-preserving denoising)
    img = cv2.bilateralFilter(img, d=9, sigmaColor=75, sigmaSpace=75)

    # Step 4: Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Step 5: Unsharp mask (sharpen text edges before thresholding)
    blurred = cv2.GaussianBlur(gray, (0, 0), sigmaX=3)
    gray = cv2.addWeighted(gray, 1.5, blurred, -0.5, 0)

    # Step 6: Otsu threshold (automatic global threshold)
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # Step 7: Morphological cleanup with rectangular kernel
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel, iterations=1)
    binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel, iterations=1)

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    cv2.imwrite(output_path, binary)
    print(f"  Saved: {output_path}")


def process_batch(folder: str) -> None:
    folder_path = Path(folder)
    out_dir = folder_path / "enhanced_cv2"
    out_dir.mkdir(exist_ok=True)

    pngs = sorted(folder_path.glob("*.png"))
    if not pngs:
        print(f"No PNG files found in {folder}")
        return

    print(f"Processing {len(pngs)} screenshots from {folder}")
    for png in pngs:
        out_name = png.stem + "_cv2.png"
        preprocess(str(png), str(out_dir / out_name))
    print(f"Done. {len(pngs)} files in {out_dir}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CV2 advanced preprocessor")
    parser.add_argument("--batch", help="Process all PNGs in folder")
    parser.add_argument("--input", help="Single input file")
    parser.add_argument("--output", help="Single output file")
    parser.add_argument("--scale", type=int, default=4, help="Upscale factor")
    args = parser.parse_args()

    if args.batch:
        process_batch(args.batch)
    elif args.input and args.output:
        preprocess(args.input, args.output, args.scale)
    else:
        parser.print_help()
