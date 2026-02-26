"""
Assembles individual processed photos into a single photobooth strip image.

Layout (top→bottom):
  [ header with branding text ]
  [ photo 1 ]
  [ gap ]
  [ photo 2 ]
  [ gap ]
  ...
  [ footer padding ]
"""

import logging
from typing import List

from PIL import Image, ImageDraw, ImageFont

from config.settings import (
    FrameConfig,
    STRIP_PHOTO_WIDTH,
    STRIP_PHOTO_HEIGHT,
    STRIP_PADDING,
    STRIP_HEADER_H,
)

logger = logging.getLogger(__name__)


def _load_ui_font(size: int) -> ImageFont.FreeTypeFont:
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


def _resize_to_slot(img: Image.Image, width: int, height: int) -> Image.Image:
    """
    Resize + crop the image to fill the slot exactly (cover behaviour).
    This avoids distorting portraits or landscape captures.
    """
    slot_ratio = width / height
    img_ratio  = img.width / img.height

    if img_ratio > slot_ratio:
        # Image is wider — scale by height, then crop width
        new_h = height
        new_w = int(img.width * (height / img.height))
    else:
        # Image is taller — scale by width, then crop height
        new_w = width
        new_h = int(img.height * (width / img.width))

    resized = img.resize((new_w, new_h), Image.LANCZOS)

    # Centre crop
    left = (new_w - width)  // 2
    top  = (new_h - height) // 2
    return resized.crop((left, top, left + width, top + height))


def compose_strip(photos: List[Image.Image], frame: FrameConfig) -> Image.Image:
    """
    Compose a list of photos into a vertical strip image.

    Args:
        photos: List of PIL Images (already filtered).
        frame:  FrameConfig with colour/width settings.

    Returns:
        A single PIL Image representing the photobooth strip.
    """
    if not photos:
        raise ValueError("No photos provided to compose_strip.")

    n = len(photos)
    pad = STRIP_PADDING
    bw  = frame.border_width

    # Canvas dimensions
    canvas_w = STRIP_PHOTO_WIDTH  + (pad * 2)
    canvas_h = (
        STRIP_HEADER_H
        + n * STRIP_PHOTO_HEIGHT
        + (n - 1) * pad
        + pad * 2
    )

    canvas = Image.new("RGB", (canvas_w, canvas_h), frame.bg_color)
    draw   = ImageDraw.Draw(canvas)

    # --- Header ---
    header_font = _load_ui_font(22)
    sub_font    = _load_ui_font(11)
    header_text = "SnapBooth"
    sub_text    = "snapbooth.app"
    htc = frame.header_text_color

    # Centre header text
    try:
        hw = draw.textlength(header_text, font=header_font)
        sw = draw.textlength(sub_text,    font=sub_font)
    except AttributeError:
        hw = header_font.getlength(header_text)
        sw = sub_font.getlength(sub_text)

    draw.text(((canvas_w - hw) // 2, 10),  header_text, font=header_font, fill=htc)
    draw.text(((canvas_w - sw) // 2, 38),  sub_text,    font=sub_font,    fill=htc)

    # --- Photos ---
    for i, photo in enumerate(photos):
        slot = _resize_to_slot(photo, STRIP_PHOTO_WIDTH, STRIP_PHOTO_HEIGHT)

        x = pad
        y = STRIP_HEADER_H + i * (STRIP_PHOTO_HEIGHT + pad)

        # Border rect
        if bw > 0:
            draw.rectangle(
                [x - bw, y - bw, x + STRIP_PHOTO_WIDTH + bw, y + STRIP_PHOTO_HEIGHT + bw],
                outline=frame.border_color,
                width=bw,
            )

        canvas.paste(slot, (x, y))

    return canvas