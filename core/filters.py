"""
Image filter pipeline — Pillow + NumPy only (no OpenCV).

Extended with many new aesthetic, cute, and artistic filters.
All filters are HIGH QUALITY with sharp, clean output — no unnecessary blurring.
"""

import logging
from typing import Callable, Dict

import numpy as np
from PIL import Image, ImageEnhance, ImageFilter

logger = logging.getLogger(__name__)


def _to_arr(img: Image.Image) -> np.ndarray:
    return np.array(img, dtype=np.float32)


def _to_pil(arr: np.ndarray) -> Image.Image:
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB")


# ── Original filters ─────────────────────────────────────────────────────────

def _filter_none(img: Image.Image) -> Image.Image:
    return img.copy()


def _filter_bw(img: Image.Image) -> Image.Image:
    return img.convert("L").convert("RGB")


def _filter_sepia(img: Image.Image) -> Image.Image:
    arr = _to_arr(img)
    r, g, b = arr[:,:,0], arr[:,:,1], arr[:,:,2]
    out = np.stack([
        r * 0.393 + g * 0.769 + b * 0.189,
        r * 0.349 + g * 0.686 + b * 0.168,
        r * 0.272 + g * 0.534 + b * 0.131,
    ], axis=2)
    return _to_pil(out)


def _filter_retro(img: Image.Image) -> Image.Image:
    base  = _to_arr(_filter_sepia(img))
    faded = base * 0.80 + 30.0 * 0.20
    h, w  = faded.shape[:2]
    yy, xx = np.ogrid[:h, :w]
    sigma  = max(h, w) * 0.55
    mask   = np.exp(-((xx - w/2)**2 + (yy - h/2)**2) / (2 * sigma**2))
    mask   = (mask / mask.max()).reshape(h, w, 1)
    return _to_pil(faded * mask)


def _filter_cool(img: Image.Image) -> Image.Image:
    arr = _to_arr(img)
    arr[:,:,0] -= 25
    arr[:,:,2] += 30
    return _to_pil(arr)


def _filter_vivid(img: Image.Image) -> Image.Image:
    out = ImageEnhance.Color(img).enhance(1.8)
    return ImageEnhance.Contrast(out).enhance(1.3)


def _filter_soft(img: Image.Image) -> Image.Image:
    blurred = img.filter(ImageFilter.GaussianBlur(radius=0.8))
    out = ImageEnhance.Brightness(blurred).enhance(1.08)
    return ImageEnhance.Color(out).enhance(0.85)


def _filter_warm(img: Image.Image) -> Image.Image:
    arr = _to_arr(img)
    arr[:,:,0] += 20
    arr[:,:,1] += 8
    arr[:,:,2] -= 25
    out = _to_pil(arr)
    return ImageEnhance.Color(out).enhance(1.2)


def _filter_fade(img: Image.Image) -> Image.Image:
    arr  = _to_arr(img)
    arr  = arr * 0.75 + 35
    out  = _to_pil(arr)
    out  = ImageEnhance.Color(out).enhance(0.7)
    return ImageEnhance.Contrast(out).enhance(0.85)


# ── NEW aesthetic filters ─────────────────────────────────────────────────────

def _filter_golden_hour(img: Image.Image) -> Image.Image:
    """Warm golden sunlight — rich oranges and creamy highlights."""
    arr = _to_arr(img)
    arr[:,:,0] = np.clip(arr[:,:,0] * 1.15 + 18, 0, 255)   # red boost
    arr[:,:,1] = np.clip(arr[:,:,1] * 1.05 + 8,  0, 255)   # warm green
    arr[:,:,2] = np.clip(arr[:,:,2] * 0.80 - 10, 0, 255)   # reduce blue
    out = _to_pil(arr)
    out = ImageEnhance.Contrast(out).enhance(1.15)
    return ImageEnhance.Color(out).enhance(1.35)


def _filter_cherry_blossom(img: Image.Image) -> Image.Image:
    """Dreamy pink-toned, soft and romantic."""
    arr = _to_arr(img)
    # Lift shadows + add pink tint
    arr = arr * 0.88 + 25
    arr[:,:,0] = np.clip(arr[:,:,0] + 28, 0, 255)   # pink (red)
    arr[:,:,1] = np.clip(arr[:,:,1] - 5,  0, 255)
    arr[:,:,2] = np.clip(arr[:,:,2] + 12, 0, 255)   # slight lavender
    out = _to_pil(arr)
    out = ImageEnhance.Color(out).enhance(0.75)
    return ImageEnhance.Brightness(out).enhance(1.05)


def _filter_film_grain(img: Image.Image) -> Image.Image:
    """Classic film look — slight grain, faded, slightly desaturated."""
    arr = _to_arr(img)
    # Film fading
    arr = arr * 0.82 + 18
    # Add subtle grain
    grain = np.random.normal(0, 6, arr.shape).astype(np.float32)
    arr = np.clip(arr + grain, 0, 255)
    out = _to_pil(arr)
    out = ImageEnhance.Color(out).enhance(0.80)
    return ImageEnhance.Contrast(out).enhance(0.90)


def _filter_neon_pop(img: Image.Image) -> Image.Image:
    """High-contrast neon cyberpunk look — vivid, punchy colors."""
    arr = _to_arr(img)
    # Boost saturation by spreading channels apart
    mean = arr.mean(axis=2, keepdims=True)
    arr = mean + (arr - mean) * 2.2
    out = _to_pil(arr)
    out = ImageEnhance.Contrast(out).enhance(1.4)
    out = ImageEnhance.Sharpness(out).enhance(1.5)
    return out


def _filter_pastel(img: Image.Image) -> Image.Image:
    """Soft pastel dream — washed out, airy, very aesthetic."""
    arr = _to_arr(img)
    # Lift all values (washout)
    arr = arr * 0.65 + 70
    out = _to_pil(arr)
    out = ImageEnhance.Color(out).enhance(0.6)
    return ImageEnhance.Brightness(out).enhance(1.1)


def _filter_moody(img: Image.Image) -> Image.Image:
    """Moody dark tones — cinematic, brooding shadows."""
    arr = _to_arr(img)
    # Crush blacks, slight teal shadows
    arr[:,:,0] = np.clip(arr[:,:,0] * 0.85 - 5,  0, 255)
    arr[:,:,1] = np.clip(arr[:,:,1] * 0.88 + 3,  0, 255)
    arr[:,:,2] = np.clip(arr[:,:,2] * 0.90 + 8,  0, 255)
    out = _to_pil(arr)
    out = ImageEnhance.Contrast(out).enhance(1.25)
    return ImageEnhance.Color(out).enhance(0.85)


def _filter_y2k(img: Image.Image) -> Image.Image:
    """Y2K vibes — high contrast, oversaturated, slightly blown highlights."""
    arr = _to_arr(img)
    arr[:,:,0] = np.clip(arr[:,:,0] * 1.10 + 10, 0, 255)
    arr[:,:,1] = np.clip(arr[:,:,1] * 1.05,       0, 255)
    arr[:,:,2] = np.clip(arr[:,:,2] * 1.20 + 15, 0, 255)
    out = _to_pil(arr)
    out = ImageEnhance.Color(out).enhance(1.7)
    out = ImageEnhance.Contrast(out).enhance(1.3)
    return ImageEnhance.Sharpness(out).enhance(1.4)


def _filter_matcha(img: Image.Image) -> Image.Image:
    """Soft green earthy matcha tones — trendy aesthetic."""
    arr = _to_arr(img)
    arr[:,:,0] = np.clip(arr[:,:,0] * 0.90 - 5, 0, 255)
    arr[:,:,1] = np.clip(arr[:,:,1] * 1.08 + 12, 0, 255)
    arr[:,:,2] = np.clip(arr[:,:,2] * 0.85 - 8, 0, 255)
    out = _to_pil(arr)
    out = ImageEnhance.Color(out).enhance(0.9)
    return ImageEnhance.Contrast(out).enhance(1.05)


def _filter_lavender_haze(img: Image.Image) -> Image.Image:
    """Purple-blue dreamy haze — ethereal and soft."""
    arr = _to_arr(img)
    arr = arr * 0.85 + 15
    arr[:,:,0] = np.clip(arr[:,:,0] + 10, 0, 255)  # slight warm
    arr[:,:,2] = np.clip(arr[:,:,2] + 22, 0, 255)  # lavender blue
    out = _to_pil(arr)
    out = ImageEnhance.Color(out).enhance(0.70)
    return ImageEnhance.Brightness(out).enhance(1.08)


def _filter_crisp(img: Image.Image) -> Image.Image:
    """Ultra sharp, clean, high detail — like a professional camera."""
    out = ImageEnhance.Sharpness(img).enhance(2.2)
    out = ImageEnhance.Contrast(out).enhance(1.15)
    return ImageEnhance.Color(out).enhance(1.1)


def _filter_dusk(img: Image.Image) -> Image.Image:
    """Purple-orange sunset dusk tones — magical hour."""
    arr = _to_arr(img)
    arr[:,:,0] = np.clip(arr[:,:,0] * 1.08 + 15, 0, 255)  # orange
    arr[:,:,1] = np.clip(arr[:,:,1] * 0.88,       0, 255)  # reduce green
    arr[:,:,2] = np.clip(arr[:,:,2] * 1.10 + 12, 0, 255)  # purple
    out = _to_pil(arr)
    out = ImageEnhance.Color(out).enhance(1.4)
    return ImageEnhance.Contrast(out).enhance(1.2)


def _filter_tokyo(img: Image.Image) -> Image.Image:
    """Neon night city — teal & magenta split, high contrast."""
    arr = _to_arr(img)
    # Teal shadows, warm highlights
    dark_mask = (arr.mean(axis=2, keepdims=True) < 128).astype(np.float32)
    arr[:,:,0] += (dark_mask[:,:,0] * (-15) + (1-dark_mask[:,:,0]) * 20).astype(np.float32)
    arr[:,:,2] += (dark_mask[:,:,0] * 25  + (1-dark_mask[:,:,0]) * (-10)).astype(np.float32)
    out = _to_pil(arr)
    out = ImageEnhance.Color(out).enhance(1.6)
    return ImageEnhance.Contrast(out).enhance(1.35)


def _filter_cotton_candy(img: Image.Image) -> Image.Image:
    """Super light, airy pink & blue pastel — cute kawaii vibe."""
    arr = _to_arr(img)
    arr = arr * 0.70 + 60
    arr[:,:,0] = np.clip(arr[:,:,0] + 20, 0, 255)  # pink
    arr[:,:,2] = np.clip(arr[:,:,2] + 15, 0, 255)  # blue
    out = _to_pil(arr)
    out = ImageEnhance.Color(out).enhance(0.55)
    return ImageEnhance.Brightness(out).enhance(1.12)


def _filter_polaroid(img: Image.Image) -> Image.Image:
    """Polaroid instant film — slight overexpose, warm shift, soft."""
    arr = _to_arr(img)
    arr = arr * 0.90 + 22
    arr[:,:,0] = np.clip(arr[:,:,0] + 12, 0, 255)
    arr[:,:,1] = np.clip(arr[:,:,1] + 8,  0, 255)
    arr[:,:,2] = np.clip(arr[:,:,2] - 8,  0, 255)
    out = _to_pil(arr)
    out = ImageEnhance.Color(out).enhance(0.88)
    out = ImageEnhance.Brightness(out).enhance(1.06)
    return out


_FILTER_FN: Dict[str, Callable[[Image.Image], Image.Image]] = {
    # Original
    "none":          _filter_none,
    "bw":            _filter_bw,
    "sepia":         _filter_sepia,
    "retro":         _filter_retro,
    "cool":          _filter_cool,
    "vivid":         _filter_vivid,
    "soft":          _filter_soft,
    "warm":          _filter_warm,
    "fade":          _filter_fade,
    # New aesthetic
    "golden_hour":   _filter_golden_hour,
    "cherry":        _filter_cherry_blossom,
    "film":          _filter_film_grain,
    "neon_pop":      _filter_neon_pop,
    "pastel":        _filter_pastel,
    "moody":         _filter_moody,
    "y2k":           _filter_y2k,
    "matcha":        _filter_matcha,
    "lavender":      _filter_lavender_haze,
    "crisp":         _filter_crisp,
    "dusk":          _filter_dusk,
    "tokyo":         _filter_tokyo,
    "cotton_candy":  _filter_cotton_candy,
    "polaroid":      _filter_polaroid,
}


def apply_filter(img: Image.Image, filter_key: str) -> Image.Image:
    fn = _FILTER_FN.get(filter_key)
    if fn is None:
        logger.warning("Unknown filter '%s', returning original.", filter_key)
        return img.copy()
    try:
        return fn(img)
    except Exception as exc:
        logger.error("Filter '%s' error: %s", filter_key, exc)
        return img.copy()


def generate_thumbnail(img: Image.Image, width: int = 200) -> Image.Image:
    ratio = width / img.width
    thumb = img.resize((width, int(img.height * ratio)), Image.LANCZOS)
    # Keep thumbnails sharp
    return ImageEnhance.Sharpness(thumb).enhance(1.3)