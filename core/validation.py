"""
Input validation for raw image bytes coming from the camera widget.
We check magic bytes (not just extension) to avoid processing unexpected data.
"""

import io
import logging
from typing import Optional

from PIL import Image

from config.settings import MAX_UPLOAD_BYTES, ALLOWED_MIME_MAGIC

logger = logging.getLogger(__name__)


def validate_image_bytes(data: bytes) -> Optional[str]:
    """
    Validate raw image bytes before passing them to any processing pipeline.

    Returns an error message string if invalid, or None if the data is OK.
    Checks:
      - Size cap
      - Magic-byte MIME sniffing (not just extension)
      - Decodability by Pillow
    """
    if not data:
        return "Empty image data received."

    if len(data) > MAX_UPLOAD_BYTES:
        mb = MAX_UPLOAD_BYTES // (1024 * 1024)
        return f"Image exceeds the {mb} MB size limit."

    # Magic-byte check
    matched = False
    for magic, _ in ALLOWED_MIME_MAGIC.items():
        if data[:len(magic)] == magic:
            matched = True
            break

    if not matched:
        return "Unsupported image format (only JPEG and PNG accepted)."

    # Try actually decoding it — catches truncated/corrupted files
    try:
        with Image.open(io.BytesIO(data)) as img:
            img.verify()        # raises on corruption
    except Exception as exc:
        logger.warning("Image verification failed: %s", exc)
        return "Image file appears to be corrupted or incomplete."

    return None


def safe_open_image(data: bytes) -> Optional[Image.Image]:
    """
    Open and return a PIL Image from bytes after passing validation.
    Returns None if validation fails (caller should handle gracefully).
    """
    err = validate_image_bytes(data)
    if err:
        logger.error("safe_open_image rejected input: %s", err)
        return None

    try:
        img = Image.open(io.BytesIO(data))
        img.load()          # force full decode into memory
        return img.convert("RGB")
    except Exception as exc:
        logger.error("Failed to open image: %s", exc)
        return None