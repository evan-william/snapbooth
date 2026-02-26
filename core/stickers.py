"""
Sticker overlay pipeline.

Uses MediaPipe Face Detection to locate face bounding boxes, then renders
emoji-based stickers via Pillow's ImageDraw + a bundled font.

The module is intentionally defensive: if MediaPipe isn't available or
detection fails, it returns the original image unmodified rather than crashing.
"""

import logging
from typing import List, Tuple, Optional

import numpy as np
from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger(__name__)

# Lazy-load mediapipe so that import errors don't break the entire app
_mp_face_detection = None
_mp_drawing = None


def _get_face_detector():
    global _mp_face_detection
    if _mp_face_detection is not None:
        return _mp_face_detection
    try:
        import mediapipe as mp
        _mp_face_detection = mp.solutions.face_detection
    except ImportError:
        logger.warning("MediaPipe not available; sticker face-tracking disabled.")
        _mp_face_detection = False
    return _mp_face_detection


def detect_faces(img: Image.Image) -> List[Tuple[int, int, int, int]]:
    """
    Return a list of (x, y, w, h) face bounding boxes in pixel coordinates.
    Returns an empty list if detection fails or MediaPipe is unavailable.
    """
    mp_fd = _get_face_detector()
    if not mp_fd:
        return []

    arr = np.array(img.convert("RGB"))
    boxes = []
    try:
        with mp_fd.FaceDetection(model_selection=0, min_detection_confidence=0.5) as detector:
            results = detector.process(arr)
            if not results.detections:
                return []
            h, w = arr.shape[:2]
            for det in results.detections:
                bbox = det.location_data.relative_bounding_box
                x = max(0, int(bbox.xmin * w))
                y = max(0, int(bbox.ymin * h))
                bw = min(int(bbox.width * w), w - x)
                bh = min(int(bbox.height * h), h - y)
                if bw > 0 and bh > 0:
                    boxes.append((x, y, bw, bh))
    except Exception as exc:
        logger.error("Face detection error: %s", exc)

    return boxes


# Sticker emoji mapped to a simple position offset (fraction of face height)
_STICKER_CONFIG = {
    "sunglasses": dict(emoji="🕶",  y_offset=0.25,  scale=1.1),
    "crown":      dict(emoji="👑",  y_offset=-0.6,  scale=1.0),
    "cat_ears":   dict(emoji="🐱",  y_offset=-0.55, scale=1.0),
    "party_hat":  dict(emoji="🎉",  y_offset=-0.55, scale=0.9),
    "star_eyes":  dict(emoji="⭐",  y_offset=0.20,  scale=1.2),
}


def _load_font(size: int) -> ImageFont.FreeTypeFont:
    """Try to load a system font capable of rendering emoji."""
    candidates = [
        "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf",
        "/System/Library/Fonts/Apple Color Emoji.ttc",
        "C:/Windows/Fonts/seguiemj.ttf",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except (IOError, OSError):
            pass
    return ImageFont.load_default()


def apply_sticker(img: Image.Image, sticker_key: str) -> Image.Image:
    """
    Detect faces in `img` and draw the requested sticker above/over each face.
    Returns the original image if sticker_key is 'none', no faces are found,
    or any error occurs.
    """
    if sticker_key == "none" or sticker_key not in _STICKER_CONFIG:
        return img.copy()

    faces = detect_faces(img)
    if not faces:
        return img.copy()

    cfg = _STICKER_CONFIG[sticker_key]
    out = img.copy().convert("RGBA")
    draw = ImageDraw.Draw(out)

    for (fx, fy, fw, fh) in faces:
        font_size = max(20, int(fw * cfg["scale"]))
        font = _load_font(font_size)

        # Position: horizontally centred on the face
        x = fx + fw // 2 - font_size // 2
        y = int(fy + fh * cfg["y_offset"])

        try:
            draw.text((x, y), cfg["emoji"], font=font, embedded_color=True)
        except TypeError:
            # Older Pillow versions don't support embedded_color
            draw.text((x, y), cfg["emoji"], font=font)

    return out.convert("RGB")