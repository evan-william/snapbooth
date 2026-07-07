"""
Sticker overlay — themed, curated layouts inspired by photo booth apps.

Each sticker theme has a LAYOUT: a list of named placement descriptors.
Every placement specifies: anchor position on the photo, which shape to draw,
size, offset, and which color to use.

This means "Hearts" theme has: a big bow top-center, large hearts at corners,
tiny sparkle stars along edges — NOT the same heart shape spammed everywhere.
"""

import math
import logging
from typing import List, Tuple, Optional, Callable

from PIL import Image, ImageDraw, ImageFilter

from config.settings import StickerConfig

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Low-level shape drawers — (draw, cx, cy, size, color, color2)
# ─────────────────────────────────────────────────────────────────────────────

def _heart(draw, cx, cy, sz, col, col2):
    """Smooth heart using two circles + triangle."""
    r = max(4, sz // 2)
    draw.ellipse([cx - r, cy - r, cx,     cy    ], fill=col)
    draw.ellipse([cx,     cy - r, cx + r, cy    ], fill=col)
    draw.polygon([(cx - r, cy), (cx + r, cy), (cx, cy + int(r * 1.25))], fill=col)

def _heart_outline(draw, cx, cy, sz, col, col2):
    """Heart outline / hollow heart."""
    r = max(4, sz // 2)
    draw.ellipse([cx - r, cy - r, cx,     cy    ], outline=col, width=max(1, r//4))
    draw.ellipse([cx,     cy - r, cx + r, cy    ], outline=col, width=max(1, r//4))
    draw.polygon([(cx - r, cy), (cx + r, cy), (cx, cy + int(r * 1.25))], outline=col)

def _star4(draw, cx, cy, sz, col, col2):
    """4-pointed sparkle / star."""
    s = sz
    t = max(1, sz // 6)
    draw.rectangle([cx - s, cy - t, cx + s, cy + t], fill=col)
    draw.rectangle([cx - t, cy - s, cx + t, cy + s], fill=col)
    ds = int(s * 0.55)
    draw.polygon([(cx-ds, cy-ds), (cx, cy-t), (cx+ds, cy-ds), (cx+t, cy),
                  (cx+ds, cy+ds), (cx, cy+t), (cx-ds, cy+ds), (cx-t, cy)], fill=col)

def _star5(draw, cx, cy, sz, col, col2):
    """5-pointed star."""
    outer, inner = sz, sz // 2
    pts = []
    for i in range(10):
        a = math.radians(i * 36 - 90)
        r = outer if i % 2 == 0 else inner
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    draw.polygon(pts, fill=col)

def _star5_outline(draw, cx, cy, sz, col, col2):
    outer, inner = sz, sz // 2
    pts = []
    for i in range(10):
        a = math.radians(i * 36 - 90)
        r = outer if i % 2 == 0 else inner
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    draw.polygon(pts, outline=col, width=max(1, sz // 8))

def _bow(draw, cx, cy, sz, col, col2):
    """Cute ribbon bow."""
    c2 = col2 or col
    s  = sz
    hs = max(3, s * 2 // 3)
    # Left wing
    draw.polygon([(cx - s, cy - hs), (cx - 2, cy - 2), (cx - 2, cy + 2),
                  (cx - s, cy + hs)], fill=col)
    # Right wing
    draw.polygon([(cx + s, cy - hs), (cx + 2, cy - 2), (cx + 2, cy + 2),
                  (cx + s, cy + hs)], fill=c2)
    # Center knot
    kn = max(3, sz // 4)
    draw.ellipse([cx - kn, cy - kn, cx + kn, cy + kn], fill=c2)

def _flower(draw, cx, cy, sz, col, col2):
    """5-petal flower with colored center."""
    c2 = col2 or (255, 255, 255)
    pr = max(3, sz // 3)
    for i in range(5):
        a  = math.radians(i * 72 - 90)
        px = int(cx + (sz - pr) * math.cos(a))
        py = int(cy + (sz - pr) * math.sin(a))
        draw.ellipse([px - pr, py - pr, px + pr, py + pr], fill=col)
    cr = max(2, sz // 4)
    draw.ellipse([cx - cr, cy - cr, cx + cr, cy + cr], fill=c2)

def _circle_filled(draw, cx, cy, sz, col, col2):
    draw.ellipse([cx - sz, cy - sz, cx + sz, cy + sz], fill=col)

def _circle_outline(draw, cx, cy, sz, col, col2):
    draw.ellipse([cx - sz, cy - sz, cx + sz, cy + sz],
                 outline=col, width=max(1, sz // 5))

def _diamond(draw, cx, cy, sz, col, col2):
    c2 = col2 or tuple(min(255, c + 70) for c in col)
    pts = [(cx, cy - sz), (cx + sz, cy), (cx, cy + sz), (cx - sz, cy)]
    draw.polygon(pts, fill=col)
    hi = max(2, sz // 3)
    draw.polygon([(cx, cy - hi), (cx + hi, cy), (cx, cy + hi), (cx - hi, cy)], fill=c2)

def _crown(draw, cx, cy, sz, col, col2):
    c2 = col2 or (255, 255, 255)
    s  = sz
    hs = max(4, s * 2 // 3)
    base = cy + hs // 3
    # Base band
    draw.rectangle([cx - s, base - hs // 4, cx + s, base], fill=col)
    # 3 crown points
    draw.polygon([(cx - s,          base - hs // 4),
                  (cx - s,          cy - hs),
                  (cx - s + s//2,   base - hs // 4)], fill=col)
    draw.polygon([(cx - s // 3,     base - hs // 4),
                  (cx,              cy - hs - sz // 4),
                  (cx + s // 3,     base - hs // 4)], fill=col)
    draw.polygon([(cx + s,          base - hs // 4),
                  (cx + s,          cy - hs),
                  (cx + s - s//2,   base - hs // 4)], fill=col)
    gm = max(2, sz // 5)
    draw.ellipse([cx - gm, cy - gm, cx + gm, cy + gm], fill=c2)

def _snowflake(draw, cx, cy, sz, col, col2):
    """Simple 6-arm snowflake."""
    t = max(1, sz // 7)
    for i in range(6):
        a = math.radians(i * 60)
        ex = int(cx + sz * math.cos(a))
        ey = int(cy + sz * math.sin(a))
        draw.line([cx, cy, ex, ey], fill=col, width=t)
        # Crossbars
        for frac in (0.45, 0.75):
            mx = int(cx + sz * frac * math.cos(a))
            my = int(cy + sz * frac * math.sin(a))
            bar = int(sz * 0.20)
            bx1 = int(mx + bar * math.cos(a + math.pi/2))
            by1 = int(my + bar * math.sin(a + math.pi/2))
            bx2 = int(mx + bar * math.cos(a - math.pi/2))
            by2 = int(my + bar * math.sin(a - math.pi/2))
            draw.line([bx1, by1, bx2, by2], fill=col, width=t)

def _dot_cluster(draw, cx, cy, sz, col, col2):
    """3 small dots in a triangle."""
    r = max(2, sz // 4)
    offsets = [(0, -sz // 2), (-sz // 2, sz // 3), (sz // 2, sz // 3)]
    for ox, oy in offsets:
        draw.ellipse([cx+ox-r, cy+oy-r, cx+ox+r, cy+oy+r], fill=col)

def _paw(draw, cx, cy, sz, col, col2):
    """Cute paw print: big pad + 3 toe beans."""
    pr = max(3, sz // 2)
    draw.ellipse([cx - pr, cy, cx + pr, cy + pr * 2], fill=col)
    toe_r = max(2, sz // 4)
    for ox, oy in [(-sz//2, -sz//3), (0, -sz//2), (sz//2, -sz//3)]:
        draw.ellipse([cx+ox-toe_r, cy+oy-toe_r, cx+ox+toe_r, cy+oy+toe_r], fill=col)

def _ribbon(draw, cx, cy, sz, col, col2):
    """Simple ribbon/badge circle."""
    c2 = col2 or tuple(min(255, c+40) for c in col)
    r  = sz
    draw.ellipse([cx-r, cy-r, cx+r, cy+r], fill=col)
    ir = max(2, r - max(2, r//4))
    draw.ellipse([cx-ir, cy-ir, cx+ir, cy+ir], fill=c2)

def _moon(draw, cx, cy, sz, col, col2):
    """Crescent moon."""
    r = sz
    draw.ellipse([cx-r, cy-r, cx+r, cy+r], fill=col)
    draw.ellipse([cx, cy-r, cx+r+r//3, cy+r], fill=col2 or (20, 20, 40))

def _lightning(draw, cx, cy, sz, col, col2):
    """Lightning bolt."""
    s = sz
    pts = [(cx, cy-s), (cx-s//3, cy), (cx+s//4, cy-s//6),
           (cx, cy+s), (cx+s//3, cy), (cx-s//4, cy+s//6)]
    draw.polygon(pts, fill=col)

def _cloud(draw, cx, cy, sz, col, col2):
    """Puffy cloud sticker."""
    c2 = col2 or (255, 255, 255)
    outline = col
    lobes = [
        (cx - sz, cy, sz * 0.70),
        (cx - sz // 3, cy - sz // 3, sz * 0.82),
        (cx + sz // 2, cy - sz // 8, sz * 0.72),
        (cx + sz, cy + sz // 8, sz * 0.55),
    ]
    for lx, ly, rr in lobes:
        r = int(rr)
        draw.ellipse([lx - r, ly - r, lx + r, ly + r], fill=c2, outline=outline, width=max(1, sz // 10))
    draw.rounded_rectangle([cx - int(sz * 1.45), cy - sz // 5, cx + int(sz * 1.55), cy + int(sz * 0.85)],
                           radius=max(4, sz // 2), fill=c2, outline=outline, width=max(1, sz // 10))

def _pup_head(draw, cx, cy, sz, col, col2):
    """Original cloud-puppy face with floppy ears."""
    face = col2 or (255, 250, 255)
    ear = tuple(max(0, c - 35) for c in col)
    line = col
    r = sz
    draw.ellipse([cx - int(r * 1.05), cy - int(r * 0.78), cx + int(r * 1.05), cy + int(r * 0.92)],
                 fill=face, outline=line, width=max(1, sz // 9))
    draw.ellipse([cx - int(r * 1.65), cy - int(r * 0.50), cx - int(r * 0.72), cy + int(r * 0.90)],
                 fill=face, outline=line, width=max(1, sz // 10))
    draw.ellipse([cx + int(r * 0.72), cy - int(r * 0.50), cx + int(r * 1.65), cy + int(r * 0.90)],
                 fill=face, outline=line, width=max(1, sz // 10))
    draw.ellipse([cx - r // 2, cy - r // 8, cx - r // 3, cy + r // 12], fill=ear)
    draw.ellipse([cx + r // 3, cy - r // 8, cx + r // 2, cy + r // 12], fill=ear)
    draw.arc([cx - r // 5, cy, cx + r // 5, cy + r // 3], 20, 160, fill=ear, width=max(1, sz // 12))
    blush = (255, 170, 200)
    draw.ellipse([cx - int(r * 0.78), cy + r // 5, cx - int(r * 0.42), cy + int(r * 0.45)], fill=blush)
    draw.ellipse([cx + int(r * 0.42), cy + r // 5, cx + int(r * 0.78), cy + int(r * 0.45)], fill=blush)

def _cinnamon_roll(draw, cx, cy, sz, col, col2):
    """Tiny cinnamon-roll pastry with a cute face."""
    dough = col2 or (255, 220, 170)
    line = col
    r = sz
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=dough, outline=line, width=max(1, sz // 8))
    for i in range(3):
        inset = int(r * (0.22 + i * 0.20))
        draw.arc([cx - r + inset, cy - r + inset, cx + r - inset, cy + r - inset],
                 10 + i * 25, 330 - i * 30, fill=line, width=max(1, sz // 10))
    eye = tuple(max(0, c - 65) for c in line)
    draw.ellipse([cx - r // 3, cy + r // 8, cx - r // 5, cy + r // 4], fill=eye)
    draw.ellipse([cx + r // 5, cy + r // 8, cx + r // 3, cy + r // 4], fill=eye)
    draw.arc([cx - r // 5, cy + r // 5, cx + r // 5, cy + r // 2], 20, 160, fill=eye, width=max(1, sz // 14))

def _bunny_head(draw, cx, cy, sz, col, col2):
    """Round bunny face with long ears."""
    face = col2 or (255, 245, 250)
    line = col
    r = sz
    draw.ellipse([cx - int(r * 0.65), cy - int(r * 1.85), cx - int(r * 0.15), cy - int(r * 0.38)],
                 fill=face, outline=line, width=max(1, sz // 11))
    draw.ellipse([cx + int(r * 0.15), cy - int(r * 1.85), cx + int(r * 0.65), cy - int(r * 0.38)],
                 fill=face, outline=line, width=max(1, sz // 11))
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=face, outline=line, width=max(1, sz // 9))
    eye = tuple(max(0, c - 70) for c in line)
    draw.ellipse([cx - r // 3, cy - r // 8, cx - r // 5, cy + r // 10], fill=eye)
    draw.ellipse([cx + r // 5, cy - r // 8, cx + r // 3, cy + r // 10], fill=eye)
    draw.ellipse([cx - r // 12, cy + r // 8, cx + r // 12, cy + r // 4], fill=(255, 150, 180))
    draw.line([cx, cy + r // 4, cx, cy + r // 2], fill=eye, width=max(1, sz // 14))

def _kitty_head(draw, cx, cy, sz, col, col2):
    """Cute kitty face with ears and whiskers."""
    face = col2 or (255, 250, 255)
    line = col
    r = sz
    draw.polygon([(cx - r, cy - r // 3), (cx - int(r * 0.65), cy - int(r * 1.25)), (cx - r // 4, cy - r // 2)],
                 fill=face, outline=line)
    draw.polygon([(cx + r, cy - r // 3), (cx + int(r * 0.65), cy - int(r * 1.25)), (cx + r // 4, cy - r // 2)],
                 fill=face, outline=line)
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=face, outline=line, width=max(1, sz // 9))
    eye = tuple(max(0, c - 80) for c in line)
    draw.ellipse([cx - r // 3, cy - r // 10, cx - r // 5, cy + r // 9], fill=eye)
    draw.ellipse([cx + r // 5, cy - r // 10, cx + r // 3, cy + r // 9], fill=eye)
    draw.polygon([(cx, cy + r // 8), (cx - r // 10, cy + r // 4), (cx + r // 10, cy + r // 4)], fill=(255, 150, 180))
    for side in (-1, 1):
        for off in (-r // 12, r // 12):
            draw.line([cx + side * r // 8, cy + r // 4 + off, cx + side * int(r * 0.75), cy + r // 5 + off],
                      fill=eye, width=max(1, sz // 16))

def _teddy_head(draw, cx, cy, sz, col, col2):
    """Plush teddy bear face."""
    fur = col2 or col
    line = tuple(max(0, c - 55) for c in col)
    r = sz
    draw.ellipse([cx - int(r * 1.15), cy - int(r * 1.20), cx - int(r * 0.45), cy - int(r * 0.50)],
                 fill=fur, outline=line, width=max(1, sz // 10))
    draw.ellipse([cx + int(r * 0.45), cy - int(r * 1.20), cx + int(r * 1.15), cy - int(r * 0.50)],
                 fill=fur, outline=line, width=max(1, sz // 10))
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=fur, outline=line, width=max(1, sz // 9))
    snout = tuple(min(255, c + 45) for c in fur)
    draw.ellipse([cx - r // 2, cy + r // 8, cx + r // 2, cy + int(r * 0.70)], fill=snout)
    draw.ellipse([cx - r // 3, cy - r // 8, cx - r // 5, cy + r // 10], fill=line)
    draw.ellipse([cx + r // 5, cy - r // 8, cx + r // 3, cy + r // 10], fill=line)
    draw.ellipse([cx - r // 10, cy + r // 4, cx + r // 10, cy + r // 2], fill=line)

def _wing_pair(draw, cx, cy, sz, col, col2):
    """Pair of soft angel wings."""
    fill = col2 or (255, 255, 255)
    line = col
    for side in (-1, 1):
        base_x = cx + side * sz // 5
        pts = [
            (base_x, cy),
            (base_x + side * int(sz * 0.95), cy - int(sz * 0.55)),
            (base_x + side * int(sz * 1.25), cy + int(sz * 0.22)),
            (base_x + side * int(sz * 0.45), cy + int(sz * 0.68)),
        ]
        draw.polygon(pts, fill=fill, outline=line)
        draw.arc([base_x + side * int(sz * 0.18), cy - sz // 2,
                  base_x + side * int(sz * 1.15), cy + sz // 2],
                 80 if side > 0 else 100, 245 if side > 0 else 260, fill=line, width=max(1, sz // 12))

def _halo(draw, cx, cy, sz, col, col2):
    """Floating halo."""
    line = col2 or col
    draw.ellipse([cx - sz, cy - sz // 3, cx + sz, cy + sz // 3],
                 outline=line, width=max(2, sz // 5))
    draw.ellipse([cx - int(sz * 0.65), cy - sz // 5, cx + int(sz * 0.65), cy + sz // 5],
                 outline=(255, 255, 255), width=max(1, sz // 10))

def _lollipop(draw, cx, cy, sz, col, col2):
    """Candy lollipop."""
    c2 = col2 or (255, 230, 150)
    draw.line([cx, cy + sz // 2, cx, cy + int(sz * 1.65)], fill=(245, 245, 245), width=max(2, sz // 5))
    draw.ellipse([cx - sz, cy - sz, cx + sz, cy + sz], fill=c2, outline=col, width=max(1, sz // 8))
    draw.arc([cx - int(sz * 0.7), cy - int(sz * 0.7), cx + int(sz * 0.7), cy + int(sz * 0.7)],
             20, 320, fill=col, width=max(1, sz // 7))

def _cake_slice(draw, cx, cy, sz, col, col2):
    """Small cake slice with icing."""
    cake = col2 or (255, 230, 170)
    pts = [(cx - sz, cy - sz // 2), (cx + sz, cy - sz // 4), (cx - sz // 2, cy + sz)]
    draw.polygon(pts, fill=cake, outline=col)
    draw.line([cx - int(sz * 0.75), cy, cx + int(sz * 0.45), cy + sz // 6], fill=col, width=max(1, sz // 8))
    draw.ellipse([cx - sz // 4, cy - sz, cx + sz // 5, cy - sz // 2], fill=(255, 90, 120))

def _speech_love(draw, cx, cy, sz, col, col2):
    """Speech bubble with a heart."""
    fill = col2 or (255, 255, 255)
    draw.rounded_rectangle([cx - int(sz * 1.25), cy - sz, cx + int(sz * 1.25), cy + sz],
                           radius=max(4, sz // 2), fill=fill, outline=col, width=max(1, sz // 9))
    draw.polygon([(cx - sz // 4, cy + sz), (cx - sz // 2, cy + int(sz * 1.35)), (cx + sz // 10, cy + sz)],
                 fill=fill, outline=col)
    _heart(draw, cx, cy - sz // 6, max(4, sz // 3), col, col2)


# ─────────────────────────────────────────────────────────────────────────────
# Anchor → (x_frac, y_frac) mapping
# Fractions of image width/height for anchor point
# ─────────────────────────────────────────────────────────────────────────────
_ANCHORS = {
    "tl":  (0.0,  0.0),   # top-left corner
    "tr":  (1.0,  0.0),   # top-right corner
    "bl":  (0.0,  1.0),   # bottom-left corner
    "br":  (1.0,  1.0),   # bottom-right corner
    "tc":  (0.5,  0.0),   # top-center
    "bc":  (0.5,  1.0),   # bottom-center
    "ml":  (0.0,  0.5),   # mid-left
    "mr":  (1.0,  0.5),   # mid-right
    "tc1": (0.25, 0.0),   # top, 1/4 from left
    "tc3": (0.75, 0.0),   # top, 3/4
    "bc1": (0.25, 1.0),
    "bc3": (0.75, 1.0),
    "ml1": (0.0,  0.25),
    "ml3": (0.0,  0.75),
    "mr1": (1.0,  0.25),
    "mr3": (1.0,  0.75),
}

# Placement = (anchor_key, draw_fn, size_fraction, x_nudge_frac, y_nudge_frac, use_col2)
# x_nudge / y_nudge are additional offsets as fraction of min(w,h)
# Positive nudge pushes inward from edge.
_T = True   # use accent color (col2)
_F = False  # use primary color

# Each theme: list of placements
THEME_LAYOUTS = {

    "cloud_pup": [
        ("tl",  _pup_head,     0.115,  0.13,  0.12,  _T),
        ("br",  _pup_head,     0.105,  0.13,  0.12,  _T),
        ("tr",  _cloud,        0.065,  0.10,  0.08,  _T),
        ("bl",  _cloud,        0.070,  0.10,  0.09,  _T),
        ("tc1", _halo,         0.045,  0.00,  0.05,  _F),
        ("tc3", _star4,        0.040,  0.00,  0.05,  _F),
        ("bc1", _heart_outline,0.040,  0.00,  0.05,  _F),
        ("bc3", _star4,        0.038,  0.00,  0.05,  _F),
        ("ml1", _dot_cluster,  0.030,  0.04,  0.00,  _F),
        ("mr3", _dot_cluster,  0.030,  0.04,  0.00,  _F),
        ("tc",  _wing_pair,    0.045,  0.00,  0.05,  _T),
    ],

    "cinna_cafe": [
        ("tl",  _cinnamon_roll,0.105,  0.12,  0.11,  _T),
        ("br",  _cinnamon_roll,0.100,  0.12,  0.11,  _T),
        ("tr",  _cake_slice,   0.080,  0.10,  0.09,  _T),
        ("bl",  _lollipop,     0.070,  0.10,  0.10,  _T),
        ("tc1", _cloud,        0.050,  0.00,  0.05,  _T),
        ("tc3", _heart,        0.045,  0.00,  0.05,  _F),
        ("bc1", _diamond,      0.038,  0.00,  0.05,  _T),
        ("bc3", _heart_outline,0.040,  0.00,  0.05,  _F),
        ("ml1", _star4,        0.032,  0.04,  0.00,  _T),
        ("mr1", _star4,        0.032,  0.04,  0.00,  _T),
        ("ml3", _dot_cluster,  0.030,  0.04,  0.00,  _F),
        ("mr3", _dot_cluster,  0.030,  0.04,  0.00,  _F),
    ],

    "bunny_diary": [
        ("tl",  _bunny_head,   0.105,  0.12,  0.16,  _T),
        ("tr",  _bow,          0.080,  0.10,  0.08,  _F),
        ("bl",  _speech_love,  0.075,  0.11,  0.10,  _T),
        ("br",  _bunny_head,   0.100,  0.12,  0.16,  _T),
        ("tc1", _heart,        0.048,  0.00,  0.05,  _F),
        ("tc3", _heart_outline,0.044,  0.00,  0.05,  _F),
        ("bc1", _flower,       0.042,  0.00,  0.05,  _T),
        ("bc3", _star4,        0.036,  0.00,  0.05,  _F),
        ("ml1", _dot_cluster,  0.030,  0.04,  0.00,  _F),
        ("mr3", _dot_cluster,  0.030,  0.04,  0.00,  _F),
    ],

    "kitty_beam": [
        ("tl",  _kitty_head,   0.108,  0.12,  0.12,  _T),
        ("br",  _kitty_head,   0.100,  0.12,  0.12,  _T),
        ("tr",  _star5,        0.080,  0.10,  0.08,  _F),
        ("bl",  _bow,          0.080,  0.10,  0.09,  _T),
        ("tc1", _lightning,    0.043,  0.00,  0.05,  _F),
        ("tc3", _heart,        0.045,  0.00,  0.05,  _F),
        ("bc1", _diamond,      0.042,  0.00,  0.05,  _T),
        ("bc3", _star4,        0.038,  0.00,  0.05,  _F),
        ("ml1", _circle_outline,0.030, 0.04,  0.00,  _T),
        ("mr3", _circle_outline,0.030, 0.04,  0.00,  _T),
    ],

    "teddy_plush": [
        ("tl",  _teddy_head,   0.108,  0.12,  0.12,  _T),
        ("br",  _teddy_head,   0.102,  0.12,  0.12,  _T),
        ("tr",  _ribbon,       0.075,  0.10,  0.08,  _T),
        ("bl",  _cinnamon_roll,0.075,  0.10,  0.10,  _T),
        ("tc1", _heart,        0.044,  0.00,  0.05,  _F),
        ("tc3", _cloud,        0.048,  0.00,  0.05,  _T),
        ("bc1", _flower,       0.040,  0.00,  0.05,  _T),
        ("bc3", _heart_outline,0.040,  0.00,  0.05,  _F),
        ("ml1", _dot_cluster,  0.030,  0.04,  0.00,  _F),
        ("mr3", _dot_cluster,  0.030,  0.04,  0.00,  _F),
    ],

    "angel_core": [
        ("tl",  _wing_pair,    0.100,  0.12,  0.10,  _T),
        ("tr",  _halo,         0.080,  0.10,  0.09,  _F),
        ("bl",  _cloud,        0.080,  0.10,  0.10,  _T),
        ("br",  _pup_head,     0.098,  0.12,  0.12,  _T),
        ("tc1", _star4,        0.045,  0.00,  0.05,  _F),
        ("tc3", _heart_outline,0.040,  0.00,  0.05,  _F),
        ("bc1", _diamond,      0.040,  0.00,  0.05,  _T),
        ("bc3", _star4,        0.040,  0.00,  0.05,  _F),
        ("ml",  _dot_cluster,  0.026,  0.04,  0.00,  _F),
        ("mr",  _dot_cluster,  0.026,  0.04,  0.00,  _F),
    ],

    "ribbon_pop": [
        ("tl",  _bow,          0.112,  0.11,  0.08,  _F),
        ("tr",  _bow,          0.100,  0.11,  0.08,  _T),
        ("bl",  _speech_love,  0.078,  0.11,  0.10,  _T),
        ("br",  _heart,        0.088,  0.11,  0.10,  _F),
        ("tc1", _star4,        0.042,  0.00,  0.05,  _T),
        ("tc3", _heart_outline,0.040,  0.00,  0.05,  _F),
        ("bc1", _ribbon,       0.038,  0.00,  0.05,  _T),
        ("bc3", _star5,        0.038,  0.00,  0.05,  _F),
        ("ml1", _dot_cluster,  0.032,  0.04,  0.00,  _F),
        ("mr3", _dot_cluster,  0.032,  0.04,  0.00,  _T),
    ],

    "dessert": [
        ("tl",  _cake_slice,   0.100,  0.11,  0.09,  _T),
        ("tr",  _lollipop,     0.085,  0.11,  0.09,  _T),
        ("bl",  _cinnamon_roll,0.090,  0.11,  0.10,  _T),
        ("br",  _cake_slice,   0.092,  0.11,  0.10,  _T),
        ("tc1", _flower,       0.045,  0.00,  0.05,  _F),
        ("tc3", _heart,        0.043,  0.00,  0.05,  _F),
        ("bc1", _star4,        0.038,  0.00,  0.05,  _T),
        ("bc3", _diamond,      0.040,  0.00,  0.05,  _T),
        ("ml1", _circle_filled,0.026,  0.04,  0.00,  _F),
        ("mr3", _circle_filled,0.026,  0.04,  0.00,  _F),
    ],

    "purikura": [
        ("tl",  _speech_love,  0.082,  0.11,  0.09,  _T),
        ("tr",  _star5,        0.090,  0.10,  0.08,  _F),
        ("bl",  _kitty_head,   0.090,  0.11,  0.11,  _T),
        ("br",  _bunny_head,   0.092,  0.11,  0.15,  _T),
        ("tc1", _heart,        0.050,  0.00,  0.05,  _F),
        ("tc3", _diamond,      0.047,  0.00,  0.05,  _T),
        ("bc1", _lightning,    0.042,  0.00,  0.05,  _F),
        ("bc3", _star4,        0.042,  0.00,  0.05,  _T),
        ("ml1", _circle_outline,0.032, 0.04,  0.00,  _T),
        ("mr1", _dot_cluster,  0.032,  0.04,  0.00,  _F),
        ("ml3", _dot_cluster,  0.032,  0.04,  0.00,  _T),
        ("mr3", _circle_outline,0.032, 0.04,  0.00,  _F),
    ],

    "idol_star": [
        ("tl",  _crown,        0.095,  0.11,  0.10,  _F),
        ("tr",  _star5,        0.102,  0.11,  0.09,  _F),
        ("bl",  _star5_outline,0.085,  0.10,  0.10,  _T),
        ("br",  _wing_pair,    0.090,  0.12,  0.10,  _T),
        ("tc1", _diamond,      0.050,  0.00,  0.05,  _T),
        ("tc3", _star4,        0.046,  0.00,  0.05,  _F),
        ("bc1", _heart,        0.040,  0.00,  0.05,  _F),
        ("bc3", _diamond,      0.044,  0.00,  0.05,  _T),
        ("ml1", _dot_cluster,  0.030,  0.04,  0.00,  _T),
        ("mr3", _dot_cluster,  0.030,  0.04,  0.00,  _T),
    ],

    "hearts": [
        ("tl",  _bow,          0.090,  0.09,  0.07,  _T),
        ("tr",  _heart,        0.085,  0.09,  0.07,  _F),
        ("bl",  _heart,        0.075,  0.09,  0.09,  _F),
        ("br",  _bow,          0.075,  0.09,  0.08,  _T),
        ("tc1", _heart,        0.055,  0.00,  0.06,  _F),
        ("tc3", _heart_outline,0.045,  0.00,  0.05,  _F),
        ("bc1", _heart_outline,0.045,  0.00,  0.05,  _F),
        ("bc3", _heart,        0.050,  0.00,  0.06,  _F),
        ("ml1", _star4,        0.038,  0.05,  0.00,  _T),
        ("mr1", _star4,        0.038,  0.05,  0.00,  _T),
        ("ml3", _dot_cluster,  0.030,  0.04,  0.00,  _F),
        ("mr3", _dot_cluster,  0.030,  0.04,  0.00,  _F),
        ("tc",  _star4,        0.030,  0.00,  0.04,  _T),
        ("bc",  _star4,        0.030,  0.00,  0.04,  _T),
    ],

    "stars": [
        ("tl",  _star5,        0.095,  0.09,  0.08,  _F),
        ("tr",  _star5,        0.085,  0.09,  0.08,  _T),
        ("bl",  _star5_outline,0.080,  0.09,  0.09,  _T),
        ("br",  _star5,        0.090,  0.09,  0.09,  _F),
        ("tc1", _star4,        0.050,  0.00,  0.05,  _F),
        ("tc3", _star4,        0.045,  0.00,  0.05,  _T),
        ("bc1", _star5,        0.045,  0.00,  0.05,  _T),
        ("bc3", _star4,        0.050,  0.00,  0.05,  _F),
        ("ml1", _star5_outline,0.040,  0.05,  0.00,  _F),
        ("mr3", _star5_outline,0.040,  0.05,  0.00,  _F),
        ("ml3", _dot_cluster,  0.030,  0.04,  0.00,  _T),
        ("mr1", _dot_cluster,  0.030,  0.04,  0.00,  _T),
        ("tc",  _diamond,      0.030,  0.00,  0.04,  _T),
        ("bc",  _diamond,      0.030,  0.00,  0.04,  _T),
    ],

    "flowers": [
        ("tl",  _flower,       0.090,  0.09,  0.08,  _F),
        ("tr",  _flower,       0.085,  0.09,  0.08,  _T),
        ("bl",  _flower,       0.080,  0.09,  0.09,  _T),
        ("br",  _flower,       0.085,  0.09,  0.09,  _F),
        ("tc1", _flower,       0.055,  0.00,  0.05,  _F),
        ("tc3", _dot_cluster,  0.038,  0.00,  0.05,  _T),
        ("bc1", _dot_cluster,  0.038,  0.00,  0.05,  _T),
        ("bc3", _flower,       0.050,  0.00,  0.05,  _F),
        ("ml1", _star4,        0.035,  0.05,  0.00,  _T),
        ("mr1", _star4,        0.035,  0.05,  0.00,  _T),
        ("ml3", _flower,       0.042,  0.04,  0.00,  _F),
        ("mr3", _flower,       0.042,  0.04,  0.00,  _T),
        ("tc",  _paw,          0.028,  0.00,  0.04,  _F),
        ("bc",  _paw,          0.028,  0.00,  0.04,  _F),
    ],

    "sparkles": [
        ("tl",  _star4,        0.090,  0.09,  0.08,  _F),
        ("tr",  _diamond,      0.080,  0.09,  0.08,  _T),
        ("bl",  _diamond,      0.080,  0.09,  0.09,  _F),
        ("br",  _star4,        0.085,  0.09,  0.09,  _T),
        ("tc1", _star4,        0.055,  0.00,  0.05,  _T),
        ("tc3", _star4,        0.045,  0.00,  0.05,  _F),
        ("bc1", _star4,        0.045,  0.00,  0.05,  _F),
        ("bc3", _star4,        0.050,  0.00,  0.05,  _T),
        ("ml1", _circle_outline,0.030, 0.04,  0.00,  _F),
        ("mr1", _circle_outline,0.030, 0.04,  0.00,  _F),
        ("ml3", _dot_cluster,  0.032,  0.04,  0.00,  _T),
        ("mr3", _dot_cluster,  0.032,  0.04,  0.00,  _T),
        ("tc",  _diamond,      0.028,  0.00,  0.04,  _F),
        ("bc",  _diamond,      0.028,  0.00,  0.04,  _T),
        ("ml",  _star4,        0.025,  0.04,  0.00,  _T),
        ("mr",  _star4,        0.025,  0.04,  0.00,  _F),
    ],

    "clovers": [
        ("tl",  _flower,       0.090,  0.09,  0.08,  _F),
        ("tr",  _paw,          0.075,  0.09,  0.08,  _T),
        ("bl",  _paw,          0.075,  0.09,  0.09,  _T),
        ("br",  _flower,       0.085,  0.09,  0.09,  _F),
        ("tc1", _star4,        0.045,  0.00,  0.05,  _F),
        ("tc3", _dot_cluster,  0.038,  0.00,  0.05,  _T),
        ("bc1", _dot_cluster,  0.038,  0.00,  0.05,  _T),
        ("bc3", _star4,        0.045,  0.00,  0.05,  _F),
        ("ml1", _flower,       0.040,  0.04,  0.00,  _T),
        ("mr3", _flower,       0.040,  0.04,  0.00,  _F),
        ("ml3", _circle_filled,0.025,  0.04,  0.00,  _F),
        ("mr1", _circle_filled,0.025,  0.04,  0.00,  _F),
    ],

    "butterflies": [
        ("tl",  _bow,          0.090,  0.09,  0.08,  _F),
        ("tr",  _bow,          0.085,  0.09,  0.08,  _T),
        ("bl",  _flower,       0.080,  0.09,  0.09,  _F),
        ("br",  _flower,       0.075,  0.09,  0.09,  _T),
        ("tc1", _star4,        0.045,  0.00,  0.05,  _T),
        ("tc3", _dot_cluster,  0.040,  0.00,  0.05,  _F),
        ("bc1", _dot_cluster,  0.040,  0.00,  0.05,  _T),
        ("bc3", _star4,        0.045,  0.00,  0.05,  _F),
        ("ml1", _heart,        0.038,  0.05,  0.00,  _F),
        ("mr1", _heart,        0.038,  0.05,  0.00,  _T),
        ("ml3", _bow,          0.042,  0.04,  0.00,  _T),
        ("mr3", _bow,          0.042,  0.04,  0.00,  _F),
        ("tc",  _heart,        0.030,  0.00,  0.04,  _F),
        ("bc",  _heart,        0.030,  0.00,  0.04,  _T),
    ],

    "diamonds": [
        ("tl",  _diamond,      0.090,  0.09,  0.08,  _F),
        ("tr",  _crown,        0.085,  0.09,  0.09,  _T),
        ("bl",  _crown,        0.080,  0.09,  0.09,  _F),
        ("br",  _diamond,      0.085,  0.09,  0.08,  _T),
        ("tc1", _diamond,      0.055,  0.00,  0.05,  _T),
        ("tc3", _star4,        0.040,  0.00,  0.05,  _F),
        ("bc1", _star4,        0.040,  0.00,  0.05,  _T),
        ("bc3", _diamond,      0.050,  0.00,  0.05,  _F),
        ("ml1", _circle_outline,0.032, 0.04,  0.00,  _T),
        ("mr3", _circle_outline,0.032, 0.04,  0.00,  _T),
        ("ml3", _dot_cluster,  0.028,  0.04,  0.00,  _F),
        ("mr1", _dot_cluster,  0.028,  0.04,  0.00,  _F),
    ],

    "bows": [
        ("tl",  _bow,          0.100,  0.09,  0.07,  _F),
        ("tr",  _bow,          0.095,  0.09,  0.07,  _T),
        ("bl",  _bow,          0.085,  0.09,  0.09,  _T),
        ("br",  _bow,          0.090,  0.09,  0.09,  _F),
        ("tc1", _heart,        0.050,  0.00,  0.05,  _F),
        ("tc3", _heart,        0.045,  0.00,  0.05,  _T),
        ("bc1", _ribbon,       0.038,  0.00,  0.05,  _T),
        ("bc3", _ribbon,       0.038,  0.00,  0.05,  _F),
        ("ml1", _dot_cluster,  0.032,  0.04,  0.00,  _F),
        ("mr1", _dot_cluster,  0.032,  0.04,  0.00,  _T),
        ("ml3", _star4,        0.028,  0.04,  0.00,  _T),
        ("mr3", _star4,        0.028,  0.04,  0.00,  _F),
        ("tc",  _bow,          0.038,  0.00,  0.04,  _T),
        ("bc",  _heart,        0.030,  0.00,  0.04,  _F),
    ],

    "crowns": [
        ("tl",  _crown,        0.090,  0.09,  0.09,  _F),
        ("tr",  _crown,        0.090,  0.09,  0.09,  _T),
        ("bl",  _star5,        0.080,  0.09,  0.09,  _F),
        ("br",  _star5,        0.080,  0.09,  0.09,  _T),
        ("tc1", _diamond,      0.055,  0.00,  0.05,  _T),
        ("tc3", _star4,        0.045,  0.00,  0.05,  _F),
        ("bc1", _star4,        0.045,  0.00,  0.05,  _T),
        ("bc3", _diamond,      0.050,  0.00,  0.05,  _F),
        ("ml1", _star5_outline,0.038,  0.05,  0.00,  _T),
        ("mr1", _star5_outline,0.038,  0.05,  0.00,  _F),
        ("ml3", _dot_cluster,  0.028,  0.04,  0.00,  _F),
        ("mr3", _dot_cluster,  0.028,  0.04,  0.00,  _T),
        ("tc",  _crown,        0.040,  0.00,  0.04,  _F),
        ("bc",  _star5,        0.032,  0.00,  0.04,  _T),
    ],

    "bubbles": [
        ("tl",  _circle_outline,0.085, 0.09,  0.08,  _F),
        ("tr",  _circle_filled, 0.080, 0.09,  0.08,  _T),
        ("bl",  _circle_filled, 0.075, 0.09,  0.09,  _F),
        ("br",  _circle_outline,0.080, 0.09,  0.09,  _T),
        ("tc1", _circle_outline,0.050, 0.00,  0.05,  _T),
        ("tc3", _circle_filled, 0.040, 0.00,  0.05,  _F),
        ("bc1", _circle_filled, 0.040, 0.00,  0.05,  _T),
        ("bc3", _circle_outline,0.045, 0.00,  0.05,  _F),
        ("ml1", _dot_cluster,   0.035, 0.04,  0.00,  _F),
        ("mr1", _dot_cluster,   0.035, 0.04,  0.00,  _T),
        ("ml3", _circle_outline,0.028, 0.04,  0.00,  _T),
        ("mr3", _circle_outline,0.028, 0.04,  0.00,  _F),
        ("ml",  _circle_filled, 0.020, 0.03,  0.00,  _F),
        ("mr",  _circle_filled, 0.020, 0.03,  0.00,  _T),
    ],

    "confetti": [
        ("tl",  _star5,        0.080,  0.09,  0.08,  _F),
        ("tr",  _bow,          0.080,  0.09,  0.08,  _T),
        ("bl",  _flower,       0.075,  0.09,  0.09,  _T),
        ("br",  _star4,        0.080,  0.09,  0.09,  _F),
        ("tc1", _heart,        0.050,  0.00,  0.05,  _F),
        ("tc3", _diamond,      0.040,  0.00,  0.05,  _T),
        ("bc1", _star5,        0.045,  0.00,  0.05,  _F),
        ("bc3", _flower,       0.045,  0.00,  0.05,  _T),
        ("ml1", _ribbon,       0.035,  0.04,  0.00,  _T),
        ("mr1", _ribbon,       0.035,  0.04,  0.00,  _F),
        ("ml3", _dot_cluster,  0.030,  0.04,  0.00,  _F),
        ("mr3", _dot_cluster,  0.030,  0.04,  0.00,  _T),
        ("tc",  _star4,        0.028,  0.00,  0.04,  _T),
        ("bc",  _heart,        0.028,  0.00,  0.04,  _F),
    ],
}


def _resolve_placement(anchor_key, x_nudge, y_nudge, w, h, base_size):
    """Convert anchor + nudge into absolute (cx, cy) pixel coordinates."""
    xf, yf = _ANCHORS[anchor_key]
    cx = xf * w
    cy = yf * h
    # Nudge pushes away from the nearest edge inward
    nx = x_nudge * base_size
    ny = y_nudge * base_size
    if xf == 0.0: cx += nx
    elif xf == 1.0: cx -= nx
    if yf == 0.0: cy += ny
    elif yf == 1.0: cy -= ny
    return int(cx), int(cy)


def apply_sticker(img: Image.Image, sticker: StickerConfig) -> Image.Image:
    """
    Apply themed sticker layout to a single photo.
    """
    if not sticker or sticker.key == "none":
        return img.copy()

    layout = THEME_LAYOUTS.get(sticker.key)
    if layout is None:
        return img.copy()

    out   = img.copy().convert("RGBA")  # RGBA for anti-alias tricks
    draw  = ImageDraw.Draw(out)
    w, h  = out.size
    base  = min(w, h)

    col   = sticker.color
    col2  = sticker.color2 or tuple(min(255, c + 55) for c in col)

    for (anchor, draw_fn, size_frac, xn, yn, use_col2) in layout:
        sz  = max(4, int(base * size_frac))
        cx, cy = _resolve_placement(anchor, xn, yn, w, h, base)
        c   = col2 if use_col2 else col
        try:
            draw_fn(draw, cx, cy, sz, c, col2 if not use_col2 else col)
        except Exception as exc:
            logger.debug("Sticker %s draw error: %s", sticker.key, exc)

    return out.convert("RGB")
