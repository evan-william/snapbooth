"""
Tests for core/validation.py

Security-focused: ensures only valid, safe image data passes through.
"""

import io
import pytest
from PIL import Image

from core.validation import validate_image_bytes, safe_open_image
from config.settings import MAX_UPLOAD_BYTES


def _make_jpeg_bytes(size=(10, 10), color=(100, 100, 100)) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", size, color).save(buf, format="JPEG")
    return buf.getvalue()


def _make_png_bytes(size=(10, 10)) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", size, (200, 200, 200)).save(buf, format="PNG")
    return buf.getvalue()


class TestValidateImageBytes:
    def test_valid_jpeg_passes(self):
        assert validate_image_bytes(_make_jpeg_bytes()) is None

    def test_valid_png_passes(self):
        assert validate_image_bytes(_make_png_bytes()) is None

    def test_empty_bytes_fails(self):
        err = validate_image_bytes(b"")
        assert err is not None
        assert len(err) > 0

    def test_oversized_fails(self):
        big = b"\xff\xd8\xff" + b"\x00" * (MAX_UPLOAD_BYTES + 1)
        err = validate_image_bytes(big)
        assert err is not None
        assert "limit" in err.lower() or "mb" in err.lower()

    def test_wrong_magic_bytes_fails(self):
        # PDF header
        err = validate_image_bytes(b"%PDF-1.4 fake content here ...")
        assert err is not None

    def test_corrupted_jpeg_fails(self):
        # Valid magic, garbage body
        bad = b"\xff\xd8\xff" + b"\xde\xad\xbe\xef" * 50
        err = validate_image_bytes(bad)
        assert err is not None

    def test_text_file_fails(self):
        err = validate_image_bytes(b"Hello, this is a text file, not an image.")
        assert err is not None

    def test_returns_none_for_valid(self):
        assert validate_image_bytes(_make_jpeg_bytes()) is None


class TestSafeOpenImage:
    def test_valid_jpeg_returns_image(self):
        result = safe_open_image(_make_jpeg_bytes())
        assert result is not None
        assert isinstance(result, Image.Image)

    def test_valid_png_returns_image(self):
        result = safe_open_image(_make_png_bytes())
        assert result is not None

    def test_returns_rgb_mode(self):
        result = safe_open_image(_make_jpeg_bytes())
        assert result.mode == "RGB"

    def test_invalid_returns_none(self):
        result = safe_open_image(b"not an image")
        assert result is None

    def test_empty_returns_none(self):
        result = safe_open_image(b"")
        assert result is None