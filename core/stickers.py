"""
Sticker overlay — draws geometric shapes directly via PIL.

No font/unicode dependency. Uses PIL's polygon/ellipse drawing so it works
on every platform regardless of installed fonts.
"""

import math
import logging
from typing import List, Tuple

from PIL import Image, ImageDraw

from config.settings import StickerConfig

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Shape drawers — each takes (draw, cx, cy, size, color)
# ---------------------------------------------------------------------------

def _draw_heart(draw: ImageDraw.ImageDraw, cx: int, cy: int,
                size: int, color: Tuple):
    """Approximate heart from two circles + a triangle."""
    r = size // 2
    # Left circle
    draw.ellipse([cx - r, cy - r, cx, cy], fill=color)
    # Right circle
    draw.ellipse([cx, cy - r, cx + r, cy], fill=color)
    # Bottom triangle
    draw.polygon([(cx - r, cy), (cx + r, cy), (cx, cy + int(r * 1.2))], fill=color)


def _draw_star(draw: ImageDraw.ImageDraw, cx: int, cy: int,
               size: int, color: Tuple):
    """5-pointed star polygon."""
    outer = size
    inner = size // 2
    points = []
    for i in range(10):
        angle = math.radians(i * 36 - 90)
        r = outer if i % 2 == 0 else inner
        points.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
    draw.polygon(points, fill=color)


def _draw_flower(draw: ImageDraw.ImageDraw, cx: int, cy: int,
                 size: int, color: Tuple):
    """5 petal circles around a centre."""
    petal_r = size // 3
    for i in range(5):
        angle = math.radians(i * 72)
        px = int(cx + (size - petal_r) * math.cos(angle))
        py = int(cy + (size - petal_r) * math.sin(angle))
        draw.ellipse([px - petal_r, py - petal_r, px + petal_r, py + petal_r],
                     fill=color)
    # Centre
    draw.ellipse([cx - petal_r, cy - petal_r, cx + petal_r, cy + petal_r],
                 fill=color)


def _draw_sparkle(draw: ImageDraw.ImageDraw, cx: int, cy: int,
                  size: int, color: Tuple):
    """4-pointed sparkle (thin cross + diagonal cross)."""
    s = size
    t = max(2, size // 5)  # thickness
    # Horizontal
    draw.rectangle([cx - s, cy - t, cx + s, cy + t], fill=color)
    # Vertical
    draw.rectangle([cx - t, cy - s, cx + t, cy + s], fill=color)
    # Diagonals (thinner)
    td = max(1, t // 2)
    ds = int(s * 0.6)
    points_d1 = [(cx - ds - td, cy - ds), (cx - ds + td, cy - ds - td),
                 (cx + ds + td, cy + ds), (cx + ds - td, cy + ds + td)]
    draw.polygon(points_d1, fill=color)
    points_d2 = [(cx + ds - td, cy - ds), (cx + ds + td, cy - ds + td),
                 (cx - ds + td, cy + ds), (cx - ds - td, cy + ds - td)]
    draw.polygon(points_d2, fill=color)


def _draw_clover(draw: ImageDraw.ImageDraw, cx: int, cy: int,
                 size: int, color: Tuple):
    """4-leaf clover: 4 circles in cardinal directions."""
    r = size // 2
    offsets = [(0, -r), (r, 0), (0, r), (-r, 0)]
    for dx, dy in offsets:
        lx, ly = cx + dx - r, cy + dy - r
        draw.ellipse([lx, ly, lx + 2*r, ly + 2*r], fill=color)


# Sticker key → (shape_fn, per-photo count, scatter positions as fractions of w/h)
_STICKER_SHAPES = {
    "hearts":   _draw_heart,
    "stars":    _draw_star,
    "flowers":  _draw_flower,
    "sparkles": _draw_sparkle,
    "clovers":  _draw_clover,
}

# Where to place sticker instances on the photo (as fraction: (x_frac, y_frac))
_POSITIONS = [
    (0.08, 0.10),   # top-left
    (0.92, 0.10),   # top-right
    (0.08, 0.88),   # bottom-left
    (0.92, 0.88),   # bottom-right
    (0.50, 0.07),   # top-centre
    (0.50, 0.92),   # bottom-centre
]


def apply_sticker(img: Image.Image, sticker: StickerConfig) -> Image.Image:
    """
    Draw sticker shapes at fixed corner/edge positions on the photo.
    Always returns a copy in RGB mode.
    """
    if not sticker or sticker.key == "none":
        return img.copy()

    draw_fn = _STICKER_SHAPES.get(sticker.key)
    if draw_fn is None:
        return img.copy()

    out  = img.copy().convert("RGB")
    draw = ImageDraw.Draw(out)
    w, h = out.size

    size  = max(10, min(w, h) // 12)
    color = sticker.color

    # Draw at first 4 (or 6 for dense stickers) positions
    n_positions = min(len(_POSITIONS), 6)
    for i in range(n_positions):
        xf, yf = _POSITIONS[i]
        cx = int(xf * w)
        cy = int(yf * h)
        try:
            draw_fn(draw, cx, cy, size, color)
        except Exception as exc:
            logger.debug("Sticker draw error at pos %d: %s", i, exc)

    return out