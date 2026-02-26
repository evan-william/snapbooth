"""
Image filter pipeline.

Each filter receives a PIL Image (RGB) and returns a new PIL Image (RGB).
OpenCV is used for operations that benefit from its performance;
PIL handles the rest. No in-place mutation — always returns a fresh image.
"""

import io
import logging
from typing import Callable, Dict

import cv2
import numpy as np
from PIL import Image, ImageEnhance

logger = logging.getLogger(__name__)


# --- Helpers ----------------------------------------------------------------

def _pil_to_bgr(img: Image.Image) -> np.ndarray:
    return cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)


def _bgr_to_pil(arr: np.ndarray) -> Image.Image:
    return Image.fromarray(cv2.cvtColor(arr, cv2.COLOR_BGR2RGB))


# --- Individual filters -----------------------------------------------------

def _filter_none(img: Image.Image) -> Image.Image:
    return img.copy()


def _filter_bw(img: Image.Image) -> Image.Image:
    bgr = _pil_to_bgr(img)
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    gray_bgr = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
    return _bgr_to_pil(gray_bgr)


def _filter_sepia(img: Image.Image) -> Image.Image:
    bgr = _pil_to_bgr(img)
    # Sepia kernel applied per-channel
    kernel = np.array([
        [0.272, 0.534, 0.131],
        [0.349, 0.686, 0.168],
        [0.393, 0.769, 0.189],
    ], dtype=np.float32)
    sepia = cv2.transform(bgr.astype(np.float32), kernel)
    sepia = np.clip(sepia, 0, 255).astype(np.uint8)
    return _bgr_to_pil(sepia)


def _filter_retro(img: Image.Image) -> Image.Image:
    # Sepia base + boosted contrast + slight vignette
    base = _filter_sepia(img)
    bgr = _pil_to_bgr(base)

    # Reduce brightness range (faded look)
    bgr = cv2.addWeighted(bgr, 0.8, np.full_like(bgr, 30), 0.2, 0)

    # Vignette
    rows, cols = bgr.shape[:2]
    sigma = max(rows, cols) * 0.6
    X = cv2.getGaussianKernel(cols, sigma)
    Y = cv2.getGaussianKernel(rows, sigma)
    mask = Y * X.T
    mask = mask / mask.max()
    vignette = (bgr * mask[:, :, np.newaxis]).astype(np.uint8)
    return _bgr_to_pil(vignette)


def _filter_cool(img: Image.Image) -> Image.Image:
    bgr = _pil_to_bgr(img)
    # Shift blue channel up, red channel down
    b, g, r = cv2.split(bgr)
    r = np.clip(r.astype(np.int16) - 25, 0, 255).astype(np.uint8)
    b = np.clip(b.astype(np.int16) + 30, 0, 255).astype(np.uint8)
    return _bgr_to_pil(cv2.merge([b, g, r]))


def _filter_vivid(img: Image.Image) -> Image.Image:
    # Bump saturation and contrast via PIL's ImageEnhance (simpler + reliable)
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