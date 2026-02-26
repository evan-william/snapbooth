"""
Assembles individual processed photos into a single photobooth strip image.

Layout:
  [ header — branding + frame-specific decorations ]
  [ photo 1 with border ]
  [ gap with side decorations ]
  [ photo 2 with border ]
  ...
  [ footer — date/url ]
"""

import logging
import math
from datetime import date
from typing import List

from PIL import Image, ImageDraw, ImageFont

from config.settings import (
    FrameConfig,
    STRIP_PHOTO_WIDTH,
    STRIP_PHOTO_HEIGHT,
    STRIP_PADDING,
    STRIP_HEADER_H,
    STRIP_FOOTER_H,
)

logger = logging.getLogger(__name__)

_FONT_CACHE = {}


def _load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    key = (size, bold)
    if key in _FONT_CACHE:
        return _FONT_CACHE[key]
    candidates_bold = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "C:/Windows/Fonts/arialbd.ttf",
    ]
    candidates_reg = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "C:/Windows/Fonts/arial.ttf",
    ]
    for path in (candidates_bold if bold else candidates_reg):
        try:
            font = ImageFont.truetype(path, size)
            _FONT_CACHE[key] = font
            return font
        except (IOError, OSError):
            pass
    font = ImageFont.load_default()
    _FONT_CACHE[key] = font
    return font


def _text_w(draw: ImageDraw.ImageDraw, text: str, font) -> float:
    try:
        return draw.textlength(text, font=font)
    except AttributeError:
        return font.getlength(text)


def _resize_to_slot(img: Image.Image, width: int, height: int) -> Image.Image:
    """Cover-fit crop: fill the slot without distortion."""
    slot_ratio = width / height
    img_ratio  = img.width / img.height

    if img_ratio > slot_ratio:
        new_h = height
        new_w = int(img.width * (height / img.height))
    else:
        new_w = width
        new_h = int(img.height * (width / img.width))

    resized = img.resize((new_w, new_h), Image.LANCZOS)
    left = (new_w - width)  // 2
    top  = (new_h - height) // 2
    return resized.crop((left, top, left + width, top + height))


def _draw_decorations(draw: ImageDraw.ImageDraw, frame: FrameConfig,
                      canvas_w: int, canvas_h: int, photo_y_positions: List[int]):
    """
    Scatter the frame's deco_symbols in the left and right margins
    between (and beside) photos.
    """
    if not frame.deco_symbols:
        return

    symbols  = frame.deco_symbols
    color    = frame.deco_color
    font     = _load_font(13, bold=False)
    margin_x = STRIP_PADDING - 2      # centre of left margin
    right_x  = canvas_w - margin_x    # centre of right margin

    # Build a list of y positions — beside each photo at thirds
    y_spots = []
    for py in photo_y_positions:
        y_spots.append(py + STRIP_PHOTO_HEIGHT // 4)
        y_spots.append(py + STRIP_PHOTO_HEIGHT // 2)
        y_spots.append(py + 3 * STRIP_PHOTO_HEIGHT // 4)
    # Also header and footer zones
    y_spots.append(STRIP_HEADER_H // 2)
    y_spots.append(canvas_h - STRIP_FOOTER_H // 2)

    sym_idx = 0
    for y in y_spots:
        sym = symbols[sym_idx % len(symbols)]
        try:
            draw.text((margin_x, y), sym, font=font, fill=color, anchor="mm")
            draw.text((right_x,  y), sym, font=font, fill=color, anchor="mm")
        except Exception:
            draw.text((max(0, margin_x - 6), max(0, y - 6)), sym, font=font, fill=color)
        sym_idx += 1


def compose_strip(photos: List[Image.Image], frame: FrameConfig,
                  placeholder: bool = False) -> Image.Image:
    """
    Compose photos into a vertical photobooth strip.

    Args:
        photos:      PIL Images (already filtered/stickered).
        frame:       FrameConfig controlling look.
        placeholder: If True, draw coloured rectangles instead of real photos
                     (used for frame preview thumbnails).
    """
    if not photos and not placeholder:
        raise ValueError("No photos provided to compose_strip.")

    n   = len(photos) if photos else 3   # preview uses 3 slots
    pad = STRIP_PADDING
    bw  = frame.border_width

    canvas_w = STRIP_PHOTO_WIDTH + pad * 2
    canvas_h = (
        STRIP_HEADER_H
        + n * STRIP_PHOTO_HEIGHT
        + (n - 1) * pad
        + pad
        + STRIP_FOOTER_H
    )

    canvas = Image.new("RGB", (canvas_w, canvas_h), frame.bg_color)
    draw   = ImageDraw.Draw(canvas)

    # ── Header ──────────────────────────────────────────────────────────────
    title_font = _load_font(24, bold=True)
    sub_font   = _load_font(11)
    htc        = frame.header_text_color

    title_w = _text_w(draw, "SnapBooth", title_font)
    draw.text(((canvas_w - title_w) / 2, 10), "SnapBooth",
              font=title_font, fill=htc)

    sub_text = "snapbooth.app"
    sub_w    = _text_w(draw, sub_text, sub_font)
    draw.text(((canvas_w - sub_w) / 2, 42), sub_text,
              font=sub_font, fill=htc)

    # Thin rule under header
    rule_color = tuple(max(0, c - 30) for c in frame.bg_color)
    draw.line([(pad, STRIP_HEADER_H - 4), (canvas_w - pad, STRIP_HEADER_H - 4)],
              fill=rule_color, width=1)

    # ── Photos ──────────────────────────────────────────────────────────────
    photo_ys = []
    placeholder_colors = [
        (200, 185, 175), (185, 200, 185), (175, 185, 205),
        (205, 195, 175),
    ]

    for i in range(n):
        x = pad
        y = STRIP_HEADER_H + i * (STRIP_PHOTO_HEIGHT + pad)
        photo_ys.append(y)

        # Border
        if bw > 0:
            draw.rectangle(
                [x - bw, y - bw,
                 x + STRIP_PHOTO_WIDTH + bw,
                 y + STRIP_PHOTO_HEIGHT + bw],
                outline=frame.border_color,
                width=bw,
            )

        if placeholder:
            c = placeholder_colors[i % len(placeholder_colors)]
            draw.rectangle([x, y, x + STRIP_PHOTO_WIDTH, y + STRIP_PHOTO_HEIGHT], fill=c)
        else:
            slot = _resize_to_slot(photos[i], STRIP_PHOTO_WIDTH, STRIP_PHOTO_HEIGHT)
            canvas.paste(slot, (x, y))

    # ── Decorations in margins ───────────────────────────────────────────────
    _draw_decorations(draw, frame, canvas_w, canvas_h, photo_ys)

    # ── Footer ───────────────────────────────────────────────────────────────
    footer_y   = canvas_h - STRIP_FOOTER_H + 10
    date_str   = date.today().strftime("%Y · %m · %d")
    date_font  = _load_font(10)
    date_w     = _text_w(draw, date_str, date_font)
    draw.text(((canvas_w - date_w) / 2, footer_y), date_str,
              font=date_font, fill=htc)

    return canvas


def compose_preview_strip(frame: FrameConfig, scale: float = 0.35) -> Image.Image:
    """
    Generate a small thumbnail-sized preview of what a frame looks like,
    using placeholder coloured rectangles instead of real photos.
    """
    full = compose_strip([], frame, placeholder=True)
    new_w = int(full.width * scale)
    new_h = int(full.height * scale)
    return full.resize((new_w, new_h), Image.LANCZOS)