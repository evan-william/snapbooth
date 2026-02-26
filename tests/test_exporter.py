"""
Tests for core/exporter.py
"""

import io
import pytest
from PIL import Image

from core.exporter import export_jpg, export_pdf


def _sample_strip(size=(424, 900)) -> Image.Image:
    return Image.new("RGB", size, (240, 230, 220))


class TestExportJpg:
    def test_returns_bytes(self):
        result = export_jpg(_sample_strip())
        assert isinstance(result, bytes)

    def test_valid_jpeg(self):
        result = export_jpg(_sample_strip())
        # JPEG magic bytes
        assert result[:3] == b"\xff\xd8\xff"

    def test_decodable(self):
        result = export_jpg(_sample_strip())
        img = Image.open(io.BytesIO(result))
        assert img.width > 0

    def test_higher_quality_larger_file(self):
        strip = _sample_strip()
        low_q  = export_jpg(strip, quality=30)
        high_q = export_jpg(strip, quality=95)
        assert high_q >= low_q    # same image, higher quality → ≥ bytes


class TestExportPdf:
    def test_returns_bytes(self):
        result = export_pdf(_sample_strip())
        assert isinstance(result, bytes)

    def test_pdf_header(self):
        result = export_pdf(_sample_strip())
        assert result.startswith(b"%PDF-")

    def test_non_empty(self):
        result = export_pdf(_sample_strip())
        assert len(result) > 500     # even a minimal PDF has overhead

    def test_small_strip(self):
        small = Image.new("RGB", (50, 100), (255, 255, 255))
        result = export_pdf(small)
        assert result.startswith(b"%PDF-")

    def test_wide_strip(self):
        wide = Image.new("RGB", (2000, 400), (200, 200, 200))
        result = export_pdf(wide)
        assert result.startswith(b"%PDF-")