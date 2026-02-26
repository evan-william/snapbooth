"""
Application-level configuration and constants.
Centralizes all tunable values so they're easy to find and change.
"""

from dataclasses import dataclass, field
from typing import List, Tuple


# --- Photo capture ---
MAX_PHOTOS = 4          # Number of shots in one session
MIN_PHOTOS = 3          # Minimum before strip generation is allowed

# --- Image constraints ---
MAX_UPLOAD_BYTES = 10 * 1024 * 1024     # 10 MB hard cap per captured frame
ALLOWED_MIME_MAGIC = {
    b"\xff\xd8\xff": "image/jpeg",
    b"\x89PNG": "image/png",
}

# --- Output dimensions ---
STRIP_PHOTO_WIDTH  = 400    # px — each photo in the final strip
STRIP_PHOTO_HEIGHT = 300    # px
STRIP_PADDING      = 12     # px between photos and at edges
STRIP_HEADER_H     = 60     # px reserved for branding text at the top

# PDF page size (A4 portrait in points, 1 pt = 1/72 inch)
PDF_PAGE_W = 595
PDF_PAGE_H = 842

# --- Frames ---
@dataclass
class FrameConfig:
    key: str
    label: str
    border_color: Tuple[int, int, int]
    border_width: int
    bg_color: Tuple[int, int, int]
    header_text_color: Tuple[int, int, int]

FRAMES: List[FrameConfig] = [
    FrameConfig("classic",    "Classic",    (255, 255, 255), 6,  (240, 240, 240), (30,  30,  30)),
    FrameConfig("retro",      "Retro",      (210, 160,  80), 8,  (45,  35,  20),  (240, 200, 100)),
    FrameConfig("minimalist", "Minimalist", (20,  20,  20),  3,  (255, 255, 255), (20,  20,  20)),
    FrameConfig("neon",       "Neon",       (0,  255, 180),  6,  (10,  10,  30),  (0,  255, 180)),
    FrameConfig("pastel",     "Pastel",     (255, 180, 200), 6,  (255, 245, 250), (160,  80, 120)),
]

FRAME_MAP = {f.key: f for f in FRAMES}

# --- Filters ---
@dataclass
class FilterConfig:
    key: str
    label: str

FILTERS: List[FilterConfig] = [
    FilterConfig("none",   "Original"),
    FilterConfig("bw",     "Black & White"),
    FilterConfig("sepia",  "Sepia"),
    FilterConfig("retro",  "Retro"),
    FilterConfig("cool",   "Cool Tone"),
    FilterConfig("vivid",  "Vivid"),
]

FILTER_MAP = {f.key: f for f in FILTERS}

# --- Stickers ---
@dataclass
class StickerConfig:
    key: str
    label: str
    emoji: str        # rendered as PIL text overlay (no external files needed)

STICKERS: List[StickerConfig] = [
    StickerConfig("none",        "None",          ""),
    StickerConfig("sunglasses",  "Sunglasses",    "🕶"),
    StickerConfig("crown",       "Crown",         "👑"),
    StickerConfig("cat_ears",    "Cat Ears",      "🐱"),
    StickerConfig("party_hat",   "Party Hat",     "🎉"),
    StickerConfig("star_eyes",   "Star Eyes",     "⭐"),
]

STICKER_MAP = {s.key: s for s in STICKERS}

# --- Session state keys (single source of truth) ---
KEY_STAGE          = "stage"
KEY_FRAME          = "selected_frame"
KEY_PHOTOS         = "captured_photos"
KEY_FILTER         = "selected_filter"
KEY_STICKER        = "selected_sticker"
KEY_PROCESSED      = "processed_photos"
KEY_STRIP_BYTES    = "strip_bytes"
KEY_STRIP_PDF      = "strip_pdf"

STAGE_TEMPLATE  = "template"
STAGE_CAPTURE   = "capture"
STAGE_PREVIEW   = "preview"
STAGE_DOWNLOAD  = "download"