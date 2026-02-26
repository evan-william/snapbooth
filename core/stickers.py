"""
Sticker overlay — draws beautiful geometric shapes via PIL.

Improvements over v1:
  - Stickers scattered ALL around the photo border (not just 4 corners)
  - Multiple size classes: large corners, medium edges, small scattered
  - 6 new sticker types: butterflies, diamonds, bows, crowns, bubbles, confetti
  - Deterministic RNG seeded per sticker type → consistent look
"""

import math
import random
import logging
from typing import List, Tuple, Optional

from PIL import Image, ImageDraw

from config.settings import StickerConfig

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Shape drawers — (draw, cx, cy, size, color, color2=None)
# ─────────────────────────────────────────────────────────────────────────────

def _draw_heart(draw, cx, cy, size, color, color2=None):
    r = size // 2
    draw.ellipse([cx - r, cy - r, cx,     cy    ], fill=color)
    draw.ellipse([cx,     cy - r, cx + r, cy    ], fill=color)
    draw.polygon([(cx - r, cy), (cx + r, cy), (cx, cy + int(r * 1.2))], fill=color)


def _draw_star(draw, cx, cy, size, color, color2=None):
    outer, inner = size, size // 2
    pts = []
    for i in range(10):
        a = math.radians(i * 36 - 90)
        r = outer if i % 2 == 0 else inner
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    draw.polygon(pts, fill=color)


def _draw_flower(draw, cx, cy, size, color, color2=None):
    pr = size // 3
    for i in range(5):
        a  = math.radians(i * 72)
        px = int(cx + (size - pr) * math.cos(a))
        py = int(cy + (size - pr) * math.sin(a))
        draw.ellipse([px - pr, py - pr, px + pr, py + pr], fill=color)
    draw.ellipse([cx - pr, cy - pr, cx + pr, cy + pr], fill=color2 or color)


def _draw_sparkle(draw, cx, cy, size, color, color2=None):
    s = size
    t = max(2, size // 5)
    draw.rectangle([cx - s, cy - t, cx + s, cy + t], fill=color)
    draw.rectangle([cx - t, cy - s, cx + t, cy + s], fill=color)
    td = max(1, t // 2)
    ds = int(s * 0.6)
    draw.polygon([(cx-ds-td,cy-ds),(cx-ds+td,cy-ds-td),(cx+ds+td,cy+ds),(cx+ds-td,cy+ds+td)], fill=color)
    draw.polygon([(cx+ds-td,cy-ds),(cx+ds+td,cy-ds+td),(cx-ds+td,cy+ds),(cx-ds-td,cy+ds-td)], fill=color)


def _draw_clover(draw, cx, cy, size, color, color2=None):
    r = size // 2
    for dx, dy in [(0,-r),(r,0),(0,r),(-r,0)]:
        lx, ly = cx+dx-r, cy+dy-r
        draw.ellipse([lx, ly, lx+2*r, ly+2*r], fill=color)


def _draw_butterfly(draw, cx, cy, size, color, color2=None):
    """Two rounded wing pairs."""
    c2 = color2 or color
    s  = size
    hs = max(4, s // 2)
    # Upper wings
    draw.ellipse([cx - s - 2, cy - hs, cx - 2, cy + hs], fill=color)
    draw.ellipse([cx + 2, cy - hs, cx + s + 2, cy + hs], fill=c2)
    # Lower wings (smaller)
    lh = max(3, hs // 2)
    draw.ellipse([cx - s + 4, cy, cx - 4, cy + lh * 2], fill=color)
    draw.ellipse([cx + 4, cy, cx + s - 4, cy + lh * 2], fill=c2)
    # Body
    draw.ellipse([cx - 2, cy - hs // 2, cx + 2, cy + hs // 2 + lh], fill=(60, 40, 60))


def _draw_diamond(draw, cx, cy, size, color, color2=None):
    s = size
    pts = [(cx, cy - s), (cx + s, cy), (cx, cy + s), (cx - s, cy)]
    draw.polygon(pts, fill=color)
    # Inner highlight
    hi = max(2, s // 3)
    hi_pts = [(cx, cy - hi), (cx + hi, cy), (cx, cy + hi), (cx - hi, cy)]
    draw.polygon(hi_pts, fill=color2 or tuple(min(255, c + 60) for c in color))


def _draw_bow(draw, cx, cy, size, color, color2=None):
    """Simple bow tie / ribbon bow shape."""
    s  = size
    hs = max(3, s // 2)
    # Left wing
    draw.polygon([(cx - s, cy - hs), (cx, cy), (cx - s, cy + hs)], fill=color)
    # Right wing
    draw.polygon([(cx + s, cy - hs), (cx, cy), (cx + s, cy + hs)], fill=color2 or color)
    # Knot
    kn = max(2, s // 5)
    draw.ellipse([cx - kn, cy - kn, cx + kn, cy + kn], fill=color2 or color)


def _draw_crown(draw, cx, cy, size, color, color2=None):
    s  = size
    hs = max(4, s // 2)
    base_y = cy + hs // 2
    # Crown base band
    draw.rectangle([cx - s, base_y - hs // 3, cx + s, base_y], fill=color)
    # 3 points
    draw.polygon([(cx - s, base_y - hs // 3), (cx - s, cy - hs), (cx - s + hs // 2, base_y - hs // 3)], fill=color)
    draw.polygon([(cx - hs // 4, base_y - hs // 3), (cx, cy - hs - hs // 3), (cx + hs // 4, base_y - hs // 3)], fill=color)
    draw.polygon([(cx + s, base_y - hs // 3), (cx + s, cy - hs), (cx + s - hs // 2, base_y - hs // 3)], fill=color)
    # Gems
    gm = max(2, s // 6)
    draw.ellipse([cx - gm, cy - gm, cx + gm, cy + gm], fill=color2 or (255,255,255))


def _draw_bubble(draw, cx, cy, size, color, color2=None):
    """Outlined circle with highlight — like a soap bubble."""
    r  = size
    c2 = color2 or tuple(min(255, c + 80) for c in color)
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=color, width=max(1, r // 5))
    # Small highlight
    hr = max(2, r // 4)
    draw.ellipse([cx - r + hr, cy - r + hr, cx - r + hr * 3, cy - r + hr * 3], fill=c2)


def _draw_confetti(draw, cx, cy, size, color, color2=None):
    """A little rectangle rotated at a random-ish angle."""
    c2 = color2 or (min(255, color[1] + 80), color[2], min(255, color[0] + 50))
    s  = size
    # Draw a simple small rotated rectangle via polygon
    w, h = s, max(2, s // 2)
    # Use fixed 45° tilt based on position (deterministic look)
    angle = math.radians(45 * ((cx + cy) % 4))
    cos_a, sin_a = math.cos(angle), math.sin(angle)
    corners = [(-w, -h), (w, -h), (w, h), (-w, h)]
    rotated = [(cx + x * cos_a - y * sin_a, cy + x * sin_a + y * cos_a) for x, y in corners]
    draw.polygon(rotated, fill=color)
    # Second tiny piece nearby
    dx, dy = int(s * 1.5), 0
    rotated2 = [(cx + dx + x * cos_a - y * sin_a, cy + dy + x * sin_a + y * cos_a) for x, y in corners]
    draw.polygon(rotated2, fill=c2)


# Map key → draw function
_STICKER_SHAPES = {
    "hearts":      _draw_heart,
    "stars":       _draw_star,
    "flowers":     _draw_flower,
    "sparkles":    _draw_sparkle,
    "clovers":     _draw_clover,
    "butterflies": _draw_butterfly,
    "diamonds":    _draw_diamond,
    "bows":        _draw_bow,
    "crowns":      _draw_crown,
    "bubbles":     _draw_bubble,
    "confetti":    _draw_confetti,
}


def _build_placement_grid(w: int, h: int, base_size: int) -> List[Tuple[int, int, float]]:
    """
    Return a list of (cx, cy, size_scale) tuples for sticker placement.

    Strategy:
      • 4 large corners
      • 4 medium edge midpoints
      • Dense scatter along top & bottom edge bands
      • Dense scatter along left & right edge bands
      • A few in header / footer areas
    """
    rng = random.Random(42)   # fixed seed — looks the same every render
    edge_band = int(base_size * 2.2)
    placements: List[Tuple[int, int, float]] = []

    # ── Corners (large) ─────────────────────────────────────────────────────
    margin = int(base_size * 1.4)
    for cx, cy in [(margin, margin), (w - margin, margin),
                   (margin, h - margin), (w - margin, h - margin)]:
        placements.append((cx, cy, 1.0))

    # ── Edge midpoints (medium) ──────────────────────────────────────────────
    for cx, cy in [(w // 2, margin), (w // 2, h - margin),
                   (margin, h // 2), (w - margin, h // 2)]:
        placements.append((cx, cy, 0.65))

    # ── Scattered along top & bottom bands ──────────────────────────────────
    n_top_bot = max(4, w // (base_size * 4))
    step      = w // (n_top_bot + 1)
    for i in range(1, n_top_bot + 1):
        x  = i * step
        ty = rng.randint(int(base_size * 0.5), edge_band)
        by = rng.randint(h - edge_band, h - int(base_size * 0.5))
        sc = rng.uniform(0.35, 0.55)
        placements.append((x, ty,  sc))
        placements.append((x, by,  sc))

    # ── Scattered along left & right bands ───────────────────────────────────
    n_sides = max(3, h // (base_size * 5))
    step_h  = (h - STRIP_HEADER_H_approx(h)) // (n_sides + 1)  # skip header zone
    for i in range(1, n_sides + 1):
        y  = int(h * 0.15) + i * step_h
        lx = rng.randint(int(base_size * 0.3), edge_band)
        rx = rng.randint(w - edge_band, w - int(base_size * 0.3))
        sc = rng.uniform(0.30, 0.50)
        placements.append((lx, y, sc))
        placements.append((rx, y, sc))

    return placements


def STRIP_HEADER_H_approx(canvas_h: int) -> int:
    """Rough guess at header height so we don't overwrite it."""
    return max(40, canvas_h // 8)


def apply_sticker(img: Image.Image, sticker: StickerConfig) -> Image.Image:
    """
    Draw sticker shapes scattered around the entire photo border.
    """
    if not sticker or sticker.key == "none":
        return img.copy()

    draw_fn = _STICKER_SHAPES.get(sticker.key)
    if draw_fn is None:
        return img.copy()

    out   = img.copy().convert("RGB")
    draw  = ImageDraw.Draw(out)
    w, h  = out.size

    base_size = max(8, min(w, h) // 13)
    color     = sticker.color
    color2    = sticker.color2

    placements = _build_placement_grid(w, h, base_size)

    for (cx, cy, scale) in placements:
        sz = max(4, int(base_size * scale))
        try:
            draw_fn(draw, cx, cy, sz, color, color2)
        except Exception as exc:
            logger.debug("Sticker draw error: %s", exc)

    return out