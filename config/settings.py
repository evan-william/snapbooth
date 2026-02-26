"""
Application-level configuration and constants.
"""

from dataclasses import dataclass, field
from typing import List, Tuple


# --- Photo capture ---
MAX_PHOTOS = 4
MIN_PHOTOS = 3

# --- Image constraints ---
MAX_UPLOAD_BYTES = 10 * 1024 * 1024
ALLOWED_MIME_MAGIC = {
    b"\xff\xd8\xff": "image/jpeg",
    b"\x89PNG":      "image/png",
}

# --- Output dimensions ---
STRIP_PHOTO_WIDTH  = 400
STRIP_PHOTO_HEIGHT = 300
STRIP_PADDING      = 14
STRIP_HEADER_H     = 70
STRIP_FOOTER_H     = 50

# PDF page size (A4 portrait, points)
PDF_PAGE_W = 595
PDF_PAGE_H = 842


# --- Frames -----------------------------------------------------------------

@dataclass
class FrameConfig:
    key: str
    label: str
    border_color:      Tuple[int, int, int]
    border_width:      int
    bg_color:          Tuple[int, int, int]
    header_text_color: Tuple[int, int, int]
    deco_symbols: List[str]            = field(default_factory=list)
    deco_color:   Tuple[int, int, int] = (200, 200, 200)
    bg_color2:    Tuple[int, int, int] = None


FRAMES: List[FrameConfig] = [
    FrameConfig(
        key="classic",
        label="Classic",
        border_color=(255, 255, 255),
        border_width=5,
        bg_color=(245, 242, 235),
        header_text_color=(40, 40, 40),
        deco_symbols=[],
    ),
    FrameConfig(
        key="film",
        label="Film",
        border_color=(230, 230, 230),
        border_width=4,
        bg_color=(18, 18, 18),
        header_text_color=(220, 220, 220),
        deco_symbols=["▪", "▪", "▪"],
        deco_color=(80, 80, 80),
    ),
    FrameConfig(
        key="pink_heart",
        label="Pink Heart",
        border_color=(255, 182, 193),
        border_width=6,
        bg_color=(255, 245, 248),
        header_text_color=(210, 100, 130),
        deco_symbols=["♥", "♡", "♥", "♡", "♥"],
        deco_color=(255, 160, 180),
    ),
    FrameConfig(
        key="garden",
        label="Garden",
        border_color=(120, 190, 120),
        border_width=6,
        bg_color=(235, 248, 235),
        header_text_color=(60, 140, 60),
        deco_symbols=["✿", "❀", "✾", "✿", "❀", "✾"],
        deco_color=(100, 180, 100),
    ),
    FrameConfig(
        key="blue_sky",
        label="Blue Sky",
        border_color=(150, 200, 240),
        border_width=6,
        bg_color=(240, 248, 255),
        header_text_color=(60, 120, 200),
        deco_symbols=["♡", "✦", "♡", "✦", "♡"],
        deco_color=(130, 180, 230),
    ),
    FrameConfig(
        key="vintage",
        label="Vintage",
        border_color=(160, 120, 70),
        border_width=7,
        bg_color=(250, 240, 220),
        header_text_color=(100, 70, 30),
        deco_symbols=["✦", "✧", "✦", "✧"],
        deco_color=(190, 150, 90),
    ),
    FrameConfig(
        key="neon",
        label="Neon",
        border_color=(0, 255, 180),
        border_width=5,
        bg_color=(8, 8, 20),
        header_text_color=(0, 255, 180),
        deco_symbols=["✦", "·", "✦", "·", "✦"],
        deco_color=(0, 200, 140),
    ),
    FrameConfig(
        key="lavender",
        label="Lavender",
        border_color=(190, 160, 220),
        border_width=6,
        bg_color=(248, 244, 255),
        header_text_color=(130, 90, 180),
        deco_symbols=["✿", "✦", "♡", "✿", "✦", "♡"],
        deco_color=(180, 140, 210),
    ),
]

FRAME_MAP = {f.key: f for f in FRAMES}


# --- Filters ----------------------------------------------------------------

@dataclass
class FilterConfig:
    key: str
    label: str

FILTERS: List[FilterConfig] = [
    FilterConfig("none",   "Original"),
    FilterConfig("bw",     "B&W"),
    FilterConfig("sepia",  "Sepia"),
    FilterConfig("retro",  "Retro"),
    FilterConfig("cool",   "Cool"),
    FilterConfig("vivid",  "Vivid"),
    FilterConfig("soft",   "Soft"),
]

FILTER_MAP = {f.key: f for f in FILTERS}


# --- Stickers (PIL-only, no mediapipe) -------------------------------------

@dataclass
class StickerConfig:
    key: str
    label: str
    symbols: List[str]
    color:   Tuple[int, int, int]

STICKERS: List[StickerConfig] = [
    StickerConfig("none",     "None",     [],                         (0,   0,   0)),
    StickerConfig("hearts",   "Hearts",   ["♥", "♡", "♥", "♡"],     (255, 100, 130)),
    StickerConfig("stars",    "Stars",    ["✦", "✧", "★", "✦"],     (255, 210,  50)),
    StickerConfig("flowers",  "Flowers",  ["✿", "❀", "✾", "✿"],     (255, 140, 180)),
    StickerConfig("sparkles", "Sparkles", ["✦", "·", "✦", "·"],     (180, 220, 255)),
    StickerConfig("clovers",  "Clovers",  ["✿", "✦", "✿", "✦"],    ( 80, 180,  80)),
]

STICKER_MAP = {s.key: s for s in STICKERS}


# --- Session state keys -----------------------------------------------------

KEY_STAGE       = "stage"
KEY_FRAME       = "selected_frame"
KEY_PHOTOS      = "captured_photos"
KEY_FILTER      = "selected_filter"
KEY_STICKER     = "selected_sticker"
KEY_PROCESSED   = "processed_photos"
KEY_STRIP_BYTES = "strip_bytes"
KEY_STRIP_PDF   = "strip_pdf"

STAGE_TEMPLATE = "template"
STAGE_CAPTURE  = "capture"
STAGE_PREVIEW  = "preview"
STAGE_DOWNLOAD = "download"