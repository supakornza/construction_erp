"""Image preprocessing for weight-ticket OCR.

Pipeline (in order):
  1. EXIF auto-rotate (mobile photos)
  2. Resize so max side <= 2000 px (Tesseract throughput)
  3. Convert to grayscale
  4. Adaptive threshold (handles colored paper: yellow MIT vs white ITD)

No deskew yet — sample tickets show <5deg tilt and Tesseract handles that
well. Add Hough-line deskew if accuracy drops on real intake.
"""
from __future__ import annotations

from pathlib import Path
from PIL import Image, ImageOps, ImageFilter

MAX_SIDE = 2000


def load(path: str | Path) -> Image.Image:
    img = Image.open(path)
    img = ImageOps.exif_transpose(img)  # respect orientation tag
    return img


def resize(img: Image.Image, max_side: int = MAX_SIDE) -> Image.Image:
    w, h = img.size
    m = max(w, h)
    if m <= max_side:
        return img
    scale = max_side / m
    return img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)


def to_grayscale(img: Image.Image) -> Image.Image:
    return img.convert('L')


def adaptive_threshold(img_gray: Image.Image, block: int = 31, c: int = 10) -> Image.Image:
    """Simple adaptive threshold via local mean (Pillow-only, no OpenCV).

    block must be odd. c is subtracted from local mean.
    """
    if block % 2 == 0:
        block += 1
    # local mean via box blur
    mean = img_gray.filter(ImageFilter.BoxBlur(block // 2))
    # binarize: pixel > (mean - c) -> white, else black
    out = Image.new('L', img_gray.size)
    out_data = bytearray(img_gray.size[0] * img_gray.size[1])
    px = img_gray.load()
    mp = mean.load()
    W, H = img_gray.size
    for y in range(H):
        row_off = y * W
        for x in range(W):
            out_data[row_off + x] = 255 if px[x, y] > mp[x, y] - c else 0
    out.frombytes(bytes(out_data))
    return out


def prepare(path: str | Path, threshold: bool = False) -> Image.Image:
    img = load(path)
    img = resize(img)
    img = to_grayscale(img)
    if threshold:
        img = adaptive_threshold(img)
    return img
