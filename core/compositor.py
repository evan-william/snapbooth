"""
Assembles individual processed photos into a photobooth strip or grid.
HD quality output — sharp fonts, crisp borders, high resolution rendering.
"""

import logging
import math
from datetime import date
from typing import List, Optional

from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

from config.settings import (
    FrameConfig, LayoutConfig, LAYOUT_MAP, DEFAULT_LAYOUT,
    SLOT_W, SLOT_H,
    STRIP_PADDING, STRIP_HEADER_H, STRIP_FOOTER_H,
)

logger = logging.getLogger(__name__)

_FONT_CACHE = {}

# Render at 2x and downscale for crisp anti-aliased output
HD_SCALE = 2


def _load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    key = (size, bold)
    if key in _FONT_CACHE:
        return _FONT_CACHE[key]
    candidates_bold = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "C:/Windows/Fonts/arialbd.ttf",
    ]
    candidates_reg = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
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
    """Cover-fit crop: fill the slot without distortion. HD quality."""
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
    cropped = resized.crop((left, top, left + width, top + height))
    # Slight sharpness boost after resize to keep photos crisp
    return ImageEnhance.Sharpness(cropped).enhance(1.2)


def _draw_glow_bg(draw: ImageDraw.ImageDraw, frame: FrameConfig,
                  canvas_w: int, canvas_h: int):
    if not frame.glow_color:
        return
    margin = STRIP_PADDING
    gc = frame.glow_color
    draw.rectangle(
        [margin, STRIP_HEADER_H, canvas_w - margin, canvas_h - STRIP_FOOTER_H],
        outline=gc, width=1,
    )


def _draw_decorations(draw: ImageDraw.ImageDraw, frame: FrameConfig,
                      canvas_w: int, canvas_h: int,
                      photo_boxes: List):
    if not frame.deco_symbols:
        return

    symbols  = frame.deco_symbols
    color    = frame.deco_color
    font     = _load_font(15)
    pad      = STRIP_PADDING
    half_pad = max(8, pad // 2)

    x_left  = half_pad
    x_right = canvas_w - half_pad

    y_spots_left  = []
    y_spots_right = []

    for frac in (0.3, 0.7):
        y = int(STRIP_HEADER_H * frac)
        y_spots_left.append(y)
        y_spots_right.append(y)

    if photo_boxes:
        for (px, py, pw, ph) in photo_boxes:
            if px <= pad + 2:
                for frac in (0.2, 0.5, 0.8):
                    y_spots_left.append(py + int(ph * frac))
            if px + pw >= canvas_w - pad - 2:
                for frac in (0.2, 0.5, 0.8):
                    y_spots_right.append(py + int(ph * frac))

    for frac in (0.3, 0.7):
        y = canvas_h - STRIP_FOOTER_H + int(STRIP_FOOTER_H * frac)
        y_spots_left.append(y)
        y_spots_right.append(y)

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

    if photo_boxes and len(photo_boxes) > 1:
        gap_font = _load_font(11)
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
    base_canvas_w = SLOT_W + STRIP_PADDING * 2
    if layout.cols == 1:
        return SLOT_W, SLOT_H

    max_canvas = 1100
    avail_w = min(max_canvas, base_canvas_w * layout.cols)
    photo_area_w = avail_w - STRIP_PADDING * (layout.cols + 1)
    slot_w = max(120, photo_area_w // layout.cols)
    slot_h = int(slot_w * (SLOT_H / SLOT_W))
    return slot_w, slot_h


def compose_strip(photos: List[Image.Image], frame: FrameConfig,
                  layout: Optional[LayoutConfig] = None,
                  placeholder: bool = False) -> Image.Image:
    """
    Compose photos into a HD photobooth strip or grid.
    Renders at 2x resolution internally and downscales for maximum sharpness.
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

    # ── Render at 2x for HD crispness ────────────────────────────────────
    S = HD_SCALE
    hi_w = canvas_w * S
    hi_h = canvas_h * S
    hi_pad = pad * S
    hi_bw  = bw * S
    hi_slot_w = slot_w * S
    hi_slot_h = slot_h * S
    hi_header = STRIP_HEADER_H * S
    hi_footer = STRIP_FOOTER_H * S

    canvas = Image.new("RGB", (hi_w, hi_h), frame.bg_color)
    draw   = ImageDraw.Draw(canvas)

    # Optional glow
    if frame.glow_color:
        gc = frame.glow_color
        draw.rectangle(
            [hi_pad, hi_header, hi_w - hi_pad, hi_h - hi_footer],
            outline=gc, width=2,
        )

    # ── Header ──────────────────────────────────────────────────────────
    title_font = _load_font(44, bold=True)   # 22 * 2
    sub_font   = _load_font(20)              # 10 * 2
    htc        = frame.header_text_color

    title_w = _text_w(draw, "SnapBooth", title_font)
    draw.text(((hi_w - title_w) / 2, 16), "SnapBooth", font=title_font, fill=htc)

    sub_text = "snapbooth.app"
    sub_w    = _text_w(draw, sub_text, sub_font)
    draw.text(((hi_w - sub_w) / 2, 76), sub_text, font=sub_font, fill=htc)

    rule_color = tuple(max(0, c - 30) for c in frame.bg_color)
    draw.line(
        [(hi_pad, hi_header - 8), (hi_w - hi_pad, hi_header - 8)],
        fill=rule_color, width=2,
    )

    # ── Photos ──────────────────────────────────────────────────────────
    placeholder_colors = [
        (200, 185, 175), (185, 200, 185), (175, 185, 205), (205, 195, 175),
        (195, 190, 210), (190, 205, 195), (205, 190, 185), (180, 195, 210),
        (210, 205, 185),
    ]

    photo_boxes_logical = []  # for decoration (in logical coords)
    photo_idx = 0

    for row in range(rows):
        for col in range(cols):
            if photo_idx >= n_total:
                break

            # Logical coords
            lx = pad + col * (slot_w + pad)
            ly = STRIP_HEADER_H + pad + row * (slot_h + pad)
            photo_boxes_logical.append((lx, ly, slot_w, slot_h))

            # Hi-res coords
            x = hi_pad + col * (hi_slot_w + hi_pad)
            y = hi_header + hi_pad + row * (hi_slot_h + hi_pad)

            # Border (rounded feel via thick outline)
            if hi_bw > 0:
                draw.rectangle(
                    [x - hi_bw, y - hi_bw, x + hi_slot_w + hi_bw, y + hi_slot_h + hi_bw],
                    outline=frame.border_color, width=hi_bw,
                )

            if placeholder:
                c = placeholder_colors[photo_idx % len(placeholder_colors)]
                draw.rectangle([x, y, x + hi_slot_w, y + hi_slot_h], fill=c)
            else:
                if photo_idx < len(photos):
                    slot_img = _resize_to_slot(photos[photo_idx], hi_slot_w, hi_slot_h)
                    canvas.paste(slot_img, (x, y))
                else:
                    draw.rectangle([x, y, x + hi_slot_w, y + hi_slot_h],
                                   fill=tuple(max(0, c - 20) for c in frame.bg_color))

            photo_idx += 1

    # ── Decorations (in hi-res coords) ───────────────────────────────────
    deco_font      = _load_font(26)
    deco_gap_font  = _load_font(22)
    if frame.deco_symbols:
        symbols = frame.deco_symbols
        color   = frame.deco_color

        x_left  = hi_pad
        x_right = hi_w - hi_pad

        y_spots_left  = []
        y_spots_right = []

        for frac in (0.3, 0.7):
            y = int(hi_header * frac)
            y_spots_left.append(y)
            y_spots_right.append(y)

        hi_photo_boxes = [
            (hi_pad + col * (hi_slot_w + hi_pad),
             hi_header + hi_pad + row * (hi_slot_h + hi_pad),
             hi_slot_w, hi_slot_h)
            for row in range(rows) for col in range(cols)
        ]

        for (hpx, hpy, hpw, hph) in hi_photo_boxes:
            if hpx <= hi_pad + 2:
                for frac in (0.2, 0.5, 0.8):
                    y_spots_left.append(hpy + int(hph * frac))
            if hpx + hpw >= hi_w - hi_pad - 2:
                for frac in (0.2, 0.5, 0.8):
                    y_spots_right.append(hpy + int(hph * frac))

        for frac in (0.3, 0.7):
            y = hi_h - hi_footer + int(hi_footer * frac)
            y_spots_left.append(y)
            y_spots_right.append(y)

        sym_idx = 0
        for y in y_spots_left:
            sym = symbols[sym_idx % len(symbols)]
            try:
                draw.text((x_left, y), sym, font=deco_font, fill=color, anchor="mm")
            except Exception:
                draw.text((max(0, x_left - 10), max(0, y - 10)), sym, font=deco_font, fill=color)
            sym_idx += 1

        for y in y_spots_right:
            sym = symbols[sym_idx % len(symbols)]
            try:
                draw.text((x_right, y), sym, font=deco_font, fill=color, anchor="mm")
            except Exception:
                draw.text((max(0, x_right - 10), max(0, y - 10)), sym, font=deco_font, fill=color)
            sym_idx += 1

        if len(hi_photo_boxes) > 1:
            rows_y = sorted(set(py for (_, py, _, _) in hi_photo_boxes))
            for ry in rows_y[1:]:
                gap_cy = ry - hi_pad // 2
                for x_frac in (0.25, 0.5, 0.75):
                    gx = int(hi_w * x_frac)
                    sym = symbols[sym_idx % len(symbols)]
                    try:
                        draw.text((gx, gap_cy), sym, font=deco_gap_font, fill=color, anchor="mm")
                    except Exception:
                        draw.text((gx - 6, gap_cy - 6), sym, font=deco_gap_font, fill=color)
                    sym_idx += 1

    # ── Footer with copyright ─────────────────────────────────────────────
    footer_y   = hi_h - hi_footer + 18
    date_str   = date.today().strftime("%Y · %m · %d")
    date_font  = _load_font(18)
    copy_font  = _load_font(16, bold=True)

    date_w = _text_w(draw, date_str, date_font)
    draw.text(((hi_w - date_w) / 2, footer_y), date_str, font=date_font, fill=htc)

    # Copyright line
    copy_str = "© Evan William"
    copy_w   = _text_w(draw, copy_str, copy_font)
    copy_color = tuple(min(255, c + 30) for c in htc)
    draw.text(((hi_w - copy_w) / 2, footer_y + 22), copy_str, font=copy_font, fill=copy_color)

    # Layout label (right side)
    layout_str = f"{layout.cols}×{layout.rows}"
    layout_w   = _text_w(draw, layout_str, date_font)
    draw.text((hi_w - layout_w - hi_pad, footer_y), layout_str,
              font=date_font, fill=htc)

    # ── Downscale to final size for crisp AA ─────────────────────────────
    final = canvas.resize((canvas_w, canvas_h), Image.LANCZOS)
    # One last sharpness pass to keep edges crisp
    return ImageEnhance.Sharpness(final).enhance(1.15)


def compose_preview_strip(frame: FrameConfig,
                           layout: Optional[LayoutConfig] = None,
                           scale: float = 0.30) -> Image.Image:
    """
    Generate a thumbnail preview for template selection — rendered HD then scaled.
    """
    if layout is None:
        layout = LAYOUT_MAP[DEFAULT_LAYOUT]
    full  = compose_strip([], frame, layout=layout, placeholder=True)
    new_w = max(60, int(full.width * scale))
    new_h = max(80, int(full.height * scale))
    thumb = full.resize((new_w, new_h), Image.LANCZOS)
    return ImageEnhance.Sharpness(thumb).enhance(1.2)