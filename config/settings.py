"""
Application-level configuration and constants.
"""

from dataclasses import dataclass, field
from typing import List, Tuple, Optional


# --- Image constraints ---
MAX_UPLOAD_BYTES = 10 * 1024 * 1024
ALLOWED_MIME_MAGIC = {
    b"\xff\xd8\xff": "image/jpeg",
    b"\x89PNG":      "image/png",
}

# --- Output dimensions (per photo slot) ---
SLOT_W         = 380   # width of each photo slot
SLOT_H         = 285   # height of each photo slot
STRIP_PADDING  = 12    # padding between/around photos
STRIP_HEADER_H = 68
STRIP_FOOTER_H = 44

# Backwards compat aliases
STRIP_PHOTO_WIDTH  = SLOT_W
STRIP_PHOTO_HEIGHT = SLOT_H

# PDF page size (A4 portrait, points)
PDF_PAGE_W = 595
PDF_PAGE_H = 842


# --- Layouts ----------------------------------------------------------------

@dataclass
class LayoutConfig:
    key:   str
    label: str
    cols:  int
    rows:  int
    emoji: str = "📷"

    @property
    def total(self) -> int:
        return self.cols * self.rows

    @property
    def min_photos(self) -> int:
        return max(1, self.total - 1)


LAYOUTS: List[LayoutConfig] = [
    LayoutConfig("1x3",  "1 × 3  Strip",  1, 3,  "▌"),
    LayoutConfig("1x4",  "1 × 4  Strip",  1, 4,  "▌"),
    LayoutConfig("1x6",  "1 × 6  Strip",  1, 6,  "▌"),
    LayoutConfig("2x2",  "2 × 2  Grid",   2, 2,  "⊞"),
    LayoutConfig("2x3",  "2 × 3  Grid",   2, 3,  "⊞"),
    LayoutConfig("2x4",  "2 × 4  Grid",   2, 4,  "⊞"),
    LayoutConfig("3x2",  "3 × 2  Grid",   3, 2,  "⊟"),
    LayoutConfig("3x3",  "3 × 3  Grid",   3, 3,  "⊟"),
    LayoutConfig("4x2",  "4 × 2  Grid",   4, 2,  "⊟"),
]

LAYOUT_MAP = {l.key: l for l in LAYOUTS}
DEFAULT_LAYOUT = "1x4"


# --- Frames -----------------------------------------------------------------

@dataclass
class FrameConfig:
    key:               str
    label:             str
    border_color:      Tuple[int, int, int]
    border_width:      int
    bg_color:          Tuple[int, int, int]
    header_text_color: Tuple[int, int, int]
    deco_symbols:      List[str]            = field(default_factory=list)
    deco_color:        Tuple[int, int, int] = (200, 200, 200)
    bg_color2:         Optional[Tuple[int, int, int]] = None   # for gradient strips
    glow_color:        Optional[Tuple[int, int, int]] = None   # inner glow tint


FRAMES: List[FrameConfig] = [
    # ── Originals ────────────────────────────────────────────────────────────
    FrameConfig(
        "classic", "Classic",
        border_color=(255, 255, 255), border_width=5,
        bg_color=(245, 242, 235), header_text_color=(40, 40, 40),
    ),
    FrameConfig(
        "film", "Film Strip",
        border_color=(230, 230, 230), border_width=4,
        bg_color=(18, 18, 18), header_text_color=(220, 220, 220),
        deco_symbols=["▪", "▪", "▪"], deco_color=(80, 80, 80),
    ),
    FrameConfig(
        "pink_heart", "Pink Heart",
        border_color=(255, 182, 193), border_width=6,
        bg_color=(255, 245, 248), header_text_color=(210, 100, 130),
        deco_symbols=["♥", "♡", "♥", "♡"], deco_color=(255, 160, 180),
    ),
    FrameConfig(
        "garden", "Garden",
        border_color=(120, 190, 120), border_width=6,
        bg_color=(235, 248, 235), header_text_color=(60, 140, 60),
        deco_symbols=["✿", "❀", "✾", "✿", "❀"], deco_color=(100, 180, 100),
    ),
    FrameConfig(
        "blue_sky", "Blue Sky",
        border_color=(150, 200, 240), border_width=6,
        bg_color=(240, 248, 255), header_text_color=(60, 120, 200),
        deco_symbols=["♡", "✦", "♡", "✦"], deco_color=(130, 180, 230),
    ),
    FrameConfig(
        "vintage", "Vintage",
        border_color=(160, 120, 70), border_width=7,
        bg_color=(250, 240, 220), header_text_color=(100, 70, 30),
        deco_symbols=["✦", "✧", "✦", "✧"], deco_color=(190, 150, 90),
    ),
    FrameConfig(
        "neon", "Neon Glow",
        border_color=(0, 255, 180), border_width=5,
        bg_color=(8, 8, 20), header_text_color=(0, 255, 180),
        deco_symbols=["✦", "·", "✦", "·"], deco_color=(0, 200, 140),
        glow_color=(0, 80, 60),
    ),
    FrameConfig(
        "lavender", "Lavender",
        border_color=(190, 160, 220), border_width=6,
        bg_color=(248, 244, 255), header_text_color=(130, 90, 180),
        deco_symbols=["✿", "✦", "♡", "✿", "✦", "♡"], deco_color=(180, 140, 210),
    ),
    # ── New frames ───────────────────────────────────────────────────────────
    FrameConfig(
        "midnight", "Midnight",
        border_color=(80, 100, 200), border_width=6,
        bg_color=(6, 6, 22), header_text_color=(140, 160, 255),
        deco_symbols=["★", "·", "✦", "·", "★"], deco_color=(80, 100, 200),
        glow_color=(20, 20, 70),
    ),
    FrameConfig(
        "cherry_blossom", "Cherry Blossom",
        border_color=(255, 130, 160), border_width=6,
        bg_color=(255, 238, 244), header_text_color=(200, 60, 110),
        deco_symbols=["✿", "♡", "✾", "♡", "✿", "✾"], deco_color=(255, 150, 180),
    ),
    FrameConfig(
        "gold_foil", "Gold Foil",
        border_color=(215, 175, 55), border_width=8,
        bg_color=(252, 248, 230), header_text_color=(130, 90, 10),
        deco_symbols=["◈", "✦", "◈", "✧", "◈"], deco_color=(215, 175, 55),
    ),
    FrameConfig(
        "ocean", "Ocean Wave",
        border_color=(40, 160, 220), border_width=6,
        bg_color=(230, 248, 255), header_text_color=(20, 100, 170),
        deco_symbols=["∿", "·", "∿", "·", "∿"], deco_color=(80, 180, 230),
    ),
    FrameConfig(
        "galaxy", "Galaxy",
        border_color=(160, 60, 230), border_width=6,
        bg_color=(4, 4, 18), header_text_color=(200, 140, 255),
        deco_symbols=["★", "·", "✦", "◦", "★", "·"], deco_color=(160, 80, 240),
        glow_color=(40, 10, 70),
    ),
    FrameConfig(
        "rose_gold", "Rose Gold",
        border_color=(195, 135, 125), border_width=7,
        bg_color=(255, 246, 244), header_text_color=(155, 85, 75),
        deco_symbols=["♡", "✦", "♡", "✧", "♡"], deco_color=(210, 150, 140),
    ),
    FrameConfig(
        "pastel_dream", "Pastel Dream",
        border_color=(200, 175, 235), border_width=5,
        bg_color=(250, 247, 255), header_text_color=(150, 110, 200),
        deco_symbols=["✦", "♡", "✿", "★", "✦", "♡"], deco_color=(200, 175, 235),
    ),
    FrameConfig(
        "autumn", "Autumn",
        border_color=(185, 90, 30), border_width=7,
        bg_color=(255, 246, 232), header_text_color=(140, 60, 10),
        deco_symbols=["✦", "❧", "✦", "✿"], deco_color=(200, 110, 40),
    ),
    FrameConfig(
        "mint_fresh", "Mint Fresh",
        border_color=(80, 205, 170), border_width=5,
        bg_color=(232, 255, 250), header_text_color=(30, 150, 120),
        deco_symbols=["✿", "·", "✦", "·", "✿"], deco_color=(80, 200, 165),
    ),
    FrameConfig(
        "black_gold", "Black & Gold",
        border_color=(210, 170, 45), border_width=8,
        bg_color=(10, 10, 10), header_text_color=(210, 170, 45),
        deco_symbols=["◈", "✦", "◈", "✦"], deco_color=(180, 140, 30),
        glow_color=(50, 40, 0),
    ),
    FrameConfig(
        "sakura", "Sakura",
        border_color=(245, 160, 185), border_width=5,
        bg_color=(255, 242, 248), header_text_color=(200, 80, 130),
        deco_symbols=["✿", "✿", "✾", "✿", "✿", "✾", "✿"], deco_color=(255, 180, 205),
    ),
    FrameConfig(
        "electric", "Electric Blue",
        border_color=(0, 180, 255), border_width=6,
        bg_color=(4, 12, 28), header_text_color=(0, 200, 255),
        deco_symbols=["✦", "·", "✦", "·"], deco_color=(0, 160, 240),
        glow_color=(0, 30, 60),
    ),
    FrameConfig(
        "warm_sunset", "Warm Sunset",
        border_color=(255, 120, 60), border_width=7,
        bg_color=(255, 245, 235), header_text_color=(180, 60, 20),
        deco_symbols=["✦", "·", "★", "·", "✦"], deco_color=(255, 140, 80),
    ),
    FrameConfig(
        "ice", "Ice Crystal",
        border_color=(200, 230, 255), border_width=6,
        bg_color=(240, 248, 255), header_text_color=(80, 140, 200),
        deco_symbols=["❄", "·", "❄", "·", "❄"], deco_color=(160, 210, 245),
    ),
    FrameConfig(
        "purple_rain", "Purple Rain",
        border_color=(150, 60, 200), border_width=6,
        bg_color=(248, 240, 255), header_text_color=(120, 40, 180),
        deco_symbols=["✦", "♡", "★", "♡", "✦"], deco_color=(180, 100, 230),
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
    FilterConfig("warm",   "Warm"),
    FilterConfig("fade",   "Fade"),
]

FILTER_MAP = {f.key: f for f in FILTERS}


# --- Stickers ---------------------------------------------------------------

@dataclass
class StickerConfig:
    key:    str
    label:  str
    color:  Tuple[int, int, int]
    color2: Optional[Tuple[int, int, int]] = None   # accent color

STICKERS: List[StickerConfig] = [
    StickerConfig("none",       "None",         (0,   0,   0)),
    StickerConfig("hearts",     "Hearts",        (255,  90, 120)),
    StickerConfig("stars",      "Stars",         (255, 205,  50)),
    StickerConfig("flowers",    "Flowers",       (255, 130, 180)),
    StickerConfig("sparkles",   "Sparkles",      (160, 210, 255)),
    StickerConfig("clovers",    "Clovers",       ( 70, 190,  90)),
    StickerConfig("butterflies","Butterflies",   (200, 100, 240),  (240, 160, 255)),
    StickerConfig("diamonds",   "Diamonds",      ( 80, 200, 220),  (180, 240, 255)),
    StickerConfig("bows",       "Bows",          (255, 140, 160),  (255, 200, 210)),
    StickerConfig("crowns",     "Crowns",        (220, 170,  40),  (255, 220, 100)),
    StickerConfig("bubbles",    "Bubbles",       (140, 190, 255),  (210, 235, 255)),
    StickerConfig("confetti",   "Confetti",      (255, 100, 100),  (100, 200, 100)),
]

STICKER_MAP = {s.key: s for s in STICKERS}


# --- Session state keys -----------------------------------------------------

KEY_STAGE       = "stage"
KEY_FRAME       = "selected_frame"
KEY_LAYOUT      = "selected_layout"
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

# Legacy aliases (so existing code that imports MAX_PHOTOS still works)
MAX_PHOTOS = LAYOUT_MAP[DEFAULT_LAYOUT].total
MIN_PHOTOS = LAYOUT_MAP[DEFAULT_LAYOUT].min_photos