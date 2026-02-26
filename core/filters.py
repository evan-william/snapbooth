"""
Image filter pipeline.

Uses only Pillow + NumPy — no OpenCV dependency — so it works across all
Python versions including 3.13+. No in-place mutation; always returns a
fresh image.
"""

import logging
from typing import Callable, Dict

import numpy as np
from PIL import Image, ImageEnhance, ImageFilter

logger = logging.getLogger(__name__)


# --- Helpers ----------------------------------------------------------------

def _to_arr(img: Image.Image) -> np.ndarray:
    return np.array(img, dtype=np.float32)


def _to_pil(arr: np.ndarray) -> Image.Image:
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB")


# --- Individual filters -----------------------------------------------------

def _filter_none(img: Image.Image) -> Image.Image:
    return img.copy()


def _filter_bw(img: Image.Image) -> Image.Image:
    # Luminosity-weighted greyscale, then back to RGB
    gray = img.convert("L")
    return gray.convert("RGB")


def _filter_sepia(img: Image.Image) -> Image.Image:
    arr = _to_arr(img)
    r = arr[:, :, 0]
    g = arr[:, :, 1]
    b = arr[:, :, 2]
    # Standard sepia matrix (input in RGB order)
    out = np.stack([
        r * 0.393 + g * 0.769 + b * 0.189,
        r * 0.349 + g * 0.686 + b * 0.168,
        r * 0.272 + g * 0.534 + b * 0.131,
    ], axis=2)
    return _to_pil(out)


def _filter_retro(img: Image.Image) -> Image.Image:
    # Sepia base → fade (blend with mid-grey) → vignette
    base = _to_arr(_filter_sepia(img))

    # Fade: blend 80% sepia + 20% flat grey (30)
    faded = base * 0.80 + 30.0 * 0.20

    # Vignette via a gaussian mask
    h, w = faded.shape[:2]
    yy, xx = np.ogrid[:h, :w]
    cy, cx = h / 2.0, w / 2.0
    sigma  = max(h, w) * 0.55
    mask   = np.exp(-((xx - cx) ** 2 + (yy - cy) ** 2) / (2 * sigma ** 2))
    mask   = (mask / mask.max()).reshape(h, w, 1)

    return _to_pil(faded * mask)


def _filter_cool(img: Image.Image) -> Image.Image:
    arr = _to_arr(img)
    arr[:, :, 0] -= 25   # red down
    arr[:, :, 2] += 30   # blue up
    return _to_pil(arr)


def _filter_vivid(img: Image.Image) -> Image.Image:
    out = ImageEnhance.Color(img).enhance(1.8)
    out = ImageEnhance.Contrast(out).enhance(1.3)
    return out


# --- Registry ---------------------------------------------------------------

_FILTER_FN: Dict[str, Callable[[Image.Image], Image.Image]] = {
    "none":   _filter_none,
    "bw":     _filter_bw,
    "sepia":  _filter_sepia,
    "retro":  _filter_retro,
    "cool":   _filter_cool,
    "vivid":  _filter_vivid,
}


def apply_filter(img: Image.Image, filter_key: str) -> Image.Image:
    """
    Apply a named filter to a PIL Image.
    Falls back to the original image if the key is unknown or an error occurs.
    """
    fn = _FILTER_FN.get(filter_key)
    if fn is None:
        logger.warning("Unknown filter key '%s', returning original.", filter_key)
        return img.copy()

    try:
        return fn(img)
    except Exception as exc:
        logger.error("Filter '%s' raised an error: %s", filter_key, exc)
        return img.copy()


def generate_thumbnail(img: Image.Image, width: int = 200) -> Image.Image:
    """Return a proportionally-scaled thumbnail, max `width` pixels wide."""
    ratio = width / img.width
    new_h = int(img.height * ratio)
    return img.resize((width, new_h), Image.LANCZOS)