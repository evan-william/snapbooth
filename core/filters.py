"""
Image filter pipeline — Pillow + NumPy only (no OpenCV).
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
    # Slight blur + brightness boost + desaturate a touch
    blurred = img.filter(ImageFilter.GaussianBlur(radius=0.8))
    out = ImageEnhance.Brightness(blurred).enhance(1.08)
    return ImageEnhance.Color(out).enhance(0.85)


_FILTER_FN: Dict[str, Callable[[Image.Image], Image.Image]] = {
    "none":   _filter_none,
    "bw":     _filter_bw,
    "sepia":  _filter_sepia,
    "retro":  _filter_retro,
    "cool":   _filter_cool,
    "vivid":  _filter_vivid,
    "soft":   _filter_soft,
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
    return img.resize((width, int(img.height * ratio)), Image.LANCZOS)