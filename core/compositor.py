"""
Assembles individual processed photos into a photobooth strip or grid.

Supports layouts: 1×N vertical strip, M×N grids.
"""

import logging
import math
from datetime import date
from typing import List, Optional

from PIL import Image, ImageDraw, ImageFont

from config.settings import (
    FrameConfig, LayoutConfig, LAYOUT_MAP, DEFAULT_LAYOUT,
    SLOT_W, SLOT_H,
    STRIP_PADDING, STRIP_HEADER_H, STRIP_FOOTER_H,
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


def _draw_glow_bg(draw: ImageDraw.ImageDraw, frame: FrameConfig,
                  canvas_w: int, canvas_h: int):
    """Paint a subtle glow rectangle in the margins if frame has glow_color."""
    if not frame.glow_color:
        return
    margin = STRIP_PADDING
    # Draw a slightly lighter inner rectangle
    gc = frame.glow_color
    draw.rectangle(
        [margin, STRIP_HEADER_H, canvas_w - margin, canvas_h - STRIP_FOOTER_H],
        outline=gc, width=1,
    )


def _draw_decorations(draw: ImageDraw.ImageDraw, frame: FrameConfig,
                      canvas_w: int, canvas_h: int,
                      photo_boxes: List):
    """
    Scatter deco_symbols in ALL margins: left, right, header, footer,
    and the gaps between photo rows.
    """
    if not frame.deco_symbols:
        return

    symbols  = frame.deco_symbols
    color    = frame.deco_color
    font     = _load_font(13)
    pad      = STRIP_PADDING
    half_pad = max(6, pad // 2)

    x_left  = half_pad
    x_right = canvas_w - half_pad

    y_spots_left  = []
    y_spots_right = []

    # Header zone
    for frac in (0.3, 0.7):
        y = int(STRIP_HEADER_H * frac)
        y_spots_left.append(y)
        y_spots_right.append(y)

    # Beside each photo row
    if photo_boxes:
        for (px, py, pw, ph) in photo_boxes:
            # Only add for the leftmost and rightmost columns
            if px <= pad + 2:           # leftmost column
                for frac in (0.2, 0.5, 0.8):
                    y_spots_left.append(py + int(ph * frac))
            if px + pw >= canvas_w - pad - 2:   # rightmost column
                for frac in (0.2, 0.5, 0.8):
                    y_spots_right.append(py + int(ph * frac))

    # Footer zone
    for frac in (0.3, 0.7):
        y = canvas_h - STRIP_FOOTER_H + int(STRIP_FOOTER_H * frac)
        y_spots_left.append(y)
        y_spots_right.append(y)

    # Draw — alternate symbols
    sym_idx = 0
    for y in y_spots_left:
        sym = symbols[sym_idx % len(symbols)]
        try:
            draw.text((x_left, y), sym, font=font, fill=color, anchor="mm")
        except Exception:
            draw.text((max(0, x_left - 6), max(0, y - 6)), sym, font=font, fill=color)
        sym_idx += 1

    for y in y_spots_right:
        sym = symbols[sym_idx % len(symbols)]
        try:
            draw.text((x_right, y), sym, font=font, fill=color, anchor="mm")
        except Exception:
            draw.text((max(0, x_right - 6), max(0, y - 6)), sym, font=font, fill=color)
        sym_idx += 1

    # Also sprinkle symbols in the gaps between rows (horizontal gaps)
    if photo_boxes and len(photo_boxes) > 1:
        gap_font = _load_font(10)
        # Find unique y positions of gap zones
        rows_y = sorted(set(py for (_, py, _, _) in photo_boxes))
        for ry in rows_y[1:]:
            gap_cy = ry - pad // 2
            for x_frac in (0.25, 0.5, 0.75):
                gx = int(canvas_w * x_frac)
                sym = symbols[sym_idx % len(symbols)]
                try:
                    draw.text((gx, gap_cy), sym, font=gap_font, fill=color, anchor="mm")
                except Exception:
                    draw.text((gx - 4, gap_cy - 4), sym, font=gap_font, fill=color)
                sym_idx += 1


def _slot_size_for_layout(layout: LayoutConfig) -> tuple:
    """
    Compute (slot_w, slot_h) so the strip fits a reasonable page width.
    For multi-column layouts, we shrink slots proportionally.
    """
    base_canvas_w = SLOT_W + STRIP_PADDING * 2
    if layout.cols == 1:
        return SLOT_W, SLOT_H

    # Target total canvas width ~ base_canvas_w * layout.cols (but cap it sensibly)
    max_canvas = 900
    avail_w = min(max_canvas, base_canvas_w * layout.cols)
    # Available width for photos
    photo_area_w = avail_w - STRIP_PADDING * (layout.cols + 1)
    slot_w = max(100, photo_area_w // layout.cols)
    # Keep aspect ratio
    slot_h = int(slot_w * (SLOT_H / SLOT_W))
    return slot_w, slot_h


def compose_strip(photos: List[Image.Image], frame: FrameConfig,
                  layout: Optional[LayoutConfig] = None,
                  placeholder: bool = False) -> Image.Image:
    """
    Compose photos into a photobooth strip or grid.

    Args:
        photos:      PIL Images (already filtered/stickered).
        frame:       FrameConfig controlling look.
        layout:      LayoutConfig (cols × rows). Defaults to 1×4.
        placeholder: Draw coloured rectangles instead of real photos.
    """
    if layout is None:
        layout = LAYOUT_MAP[DEFAULT_LAYOUT]

    if not photos and not placeholder:
        raise ValueError("No photos provided to compose_strip.")

    n_total = layout.total
    cols    = layout.cols
    rows    = layout.rows
    pad     = STRIP_PADDING
    bw      = frame.border_width

    slot_w, slot_h = _slot_size_for_layout(layout)

    canvas_w = cols * slot_w + (cols + 1) * pad
    canvas_h = (
        STRIP_HEADER_H
        + rows * slot_h
        + (rows + 1) * pad
        + STRIP_FOOTER_H
    )

    canvas = Image.new("RGB", (canvas_w, canvas_h), frame.bg_color)
    draw   = ImageDraw.Draw(canvas)

    # ── Optional glow bg ────────────────────────────────────────────────────
    _draw_glow_bg(draw, frame, canvas_w, canvas_h)

    # ── Header ──────────────────────────────────────────────────────────────
    title_font = _load_font(22, bold=True)
    sub_font   = _load_font(10)
    htc        = frame.header_text_color

    title_w = _text_w(draw, "SnapBooth", title_font)
    draw.text(((canvas_w - title_w) / 2, 8), "SnapBooth", font=title_font, fill=htc)

    sub_text = "snapbooth.app"
    sub_w    = _text_w(draw, sub_text, sub_font)
    draw.text(((canvas_w - sub_w) / 2, 38), sub_text, font=sub_font, fill=htc)

    rule_color = tuple(max(0, c - 30) for c in frame.bg_color)
    draw.line(
        [(pad, STRIP_HEADER_H - 4), (canvas_w - pad, STRIP_HEADER_H - 4)],
        fill=rule_color, width=1,
    )

    # ── Photos ──────────────────────────────────────────────────────────────
    placeholder_colors = [
        (200, 185, 175), (185, 200, 185), (175, 185, 205), (205, 195, 175),
        (195, 190, 210), (190, 205, 195), (205, 190, 185), (180, 195, 210),
        (210, 205, 185),
    ]

    photo_boxes = []
    photo_idx   = 0

    for row in range(rows):
        for col in range(cols):
            if photo_idx >= n_total:
                break

            x = pad + col * (slot_w + pad)
            y = STRIP_HEADER_H + pad + row * (slot_h + pad)

            photo_boxes.append((x, y, slot_w, slot_h))

            # Border
            if bw > 0:
                draw.rectangle(
                    [x - bw, y - bw, x + slot_w + bw, y + slot_h + bw],
                    outline=frame.border_color, width=bw,
                )

            if placeholder:
                c = placeholder_colors[photo_idx % len(placeholder_colors)]
                draw.rectangle([x, y, x + slot_w, y + slot_h], fill=c)
            else:
                if photo_idx < len(photos):
                    slot_img = _resize_to_slot(photos[photo_idx], slot_w, slot_h)
                    canvas.paste(slot_img, (x, y))
                else:
                    # Empty slot placeholder
                    draw.rectangle([x, y, x + slot_w, y + slot_h],
                                   fill=tuple(max(0, c - 20) for c in frame.bg_color))

            photo_idx += 1

    # ── Decorations in margins ───────────────────────────────────────────────
    _draw_decorations(draw, frame, canvas_w, canvas_h, photo_boxes)

    # ── Footer ───────────────────────────────────────────────────────────────
    footer_y  = canvas_h - STRIP_FOOTER_H + 10
    date_str  = date.today().strftime("%Y · %m · %d")
    date_font = _load_font(9)
    date_w    = _text_w(draw, date_str, date_font)
    draw.text(((canvas_w - date_w) / 2, footer_y), date_str, font=date_font, fill=htc)

    # Layout label in footer
    layout_str = f"{layout.cols}×{layout.rows}"
    layout_w   = _text_w(draw, layout_str, date_font)
    draw.text((canvas_w - layout_w - pad, footer_y), layout_str,
              font=date_font, fill=htc)

    return canvas


def compose_preview_strip(frame: FrameConfig,
                           layout: Optional[LayoutConfig] = None,
                           scale: float = 0.30) -> Image.Image:
    """
    Generate a small thumbnail preview for template selection.
    """
    if layout is None:
        layout = LAYOUT_MAP[DEFAULT_LAYOUT]
    full  = compose_strip([], frame, layout=layout, placeholder=True)
    new_w = max(60, int(full.width * scale))
    new_h = max(80, int(full.height * scale))
    return full.resize((new_w, new_h), Image.LANCZOS)