"""
Sticker overlay — PIL-only, no MediaPipe, no face detection.

Stickers are decorative symbols drawn at the four corners (and optionally
midpoints) of each photo. This is reliable on every platform/Python version.
"""

import logging
import random
from typing import List, Tuple

from PIL import Image, ImageDraw, ImageFont

from config.settings import StickerConfig

logger = logging.getLogger(__name__)

# Corner positions as (x_anchor, y_anchor, text_anchor)
# text_anchor: "lt"=left-top, "rt"=right-top, "lb"=left-bottom, "rb"=right-bottom
_CORNER_OFFSETS = [
    ("lt", 8,  8),   # top-left
    ("rt", -8, 8),   # top-right
    ("lb", 8,  -8),  # bottom-left
    ("rb", -8, -8),  # bottom-right
]

# Extra midpoint positions for stickers with more symbols
_EDGE_OFFSETS = [
    ("mt", 0,   6),   # top-mid
    ("mb", 0,  -6),   # bottom-mid
]


def _load_font(size: int) -> ImageFont.FreeTypeFont:
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "C:/Windows/Fonts/arialbd.ttf",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except (IOError, OSError):
            pass
    return ImageFont.load_default()


def apply_sticker(img: Image.Image, sticker: StickerConfig) -> Image.Image:
    """
    Draw decorative sticker symbols at the corners of the photo.
    Returns a copy of the image; never mutates in place.
    Returns original copy if sticker is 'none' or has no symbols.
    """
    if not sticker or not sticker.symbols:
        return img.copy()

    out  = img.copy().convert("RGBA")
    draw = ImageDraw.Draw(out)

    w, h    = out.size
    symbols = sticker.symbols
    color   = sticker.color + (230,)   # slight transparency

    positions = _CORNER_OFFSETS[:]
    if len(symbols) > 4:
        positions += _EDGE_OFFSETS

    font_size = max(16, min(w, h) // 14)
    font      = _load_font(font_size)

    for i, (anchor, dx, dy) in enumerate(positions[:len(symbols)]):
        sym = symbols[i % len(symbols)]

        # Resolve pixel coordinate from anchor
        if anchor.startswith("r") or anchor == "mt":
            # right or mid-top needs special x handling
            pass

        x = (dx if dx >= 0 else w + dx)
        y = (dy if dy >= 0 else h + dy)

        # Map anchor to PIL text_anchor string
        pil_anchor = {
            "lt": "lt", "rt": "rt",
            "lb": "lb", "rb": "rb",
            "mt": "mt", "mb": "mb",
        }.get(anchor, "lt")

        # Mid-top/bottom need centred x
        if anchor in ("mt", "mb"):
            x = w // 2

        try:
            draw.text((x, y), sym, font=font, fill=color, anchor=pil_anchor)
        except Exception:
            # Fallback: no anchor parameter (older Pillow)
            draw.text((max(0, x - font_size // 2), max(0, y - font_size // 2)),
                      sym, font=font, fill=color[:3])

    return out.convert("RGB")