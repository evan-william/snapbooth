"""
Tests for core/compositor.py
"""

import pytest
from PIL import Image

from config.settings import FRAMES, STRIP_PHOTO_WIDTH, STRIP_PHOTO_HEIGHT, STRIP_PADDING, STRIP_HEADER_H
from core.compositor import compose_strip


def _make_photos(n: int = 3, size=(200, 150)) -> list:
    colors = [(220, 50, 50), (50, 180, 50), (50, 50, 220), (200, 180, 30)]
    return [Image.new("RGB", size, colors[i % len(colors)]) for i in range(n)]


class TestComposeStrip:
    def test_returns_pil_image(self):
        frame = FRAMES[0]
        photos = _make_photos(3)
        result = compose_strip(photos, frame)
        assert isinstance(result, Image.Image)

    def test_correct_width(self):
        frame = FRAMES[0]
        photos = _make_photos(3)
        result = compose_strip(photos, frame)
        expected_w = STRIP_PHOTO_WIDTH + STRIP_PADDING * 2
        assert result.width == expected_w

    def test_height_scales_with_photo_count(self):
        frame = FRAMES[0]
        strip_3 = compose_strip(_make_photos(3), frame)
        strip_4 = compose_strip(_make_photos(4), frame)
        assert strip_4.height > strip_3.height

    def test_all_frame_styles(self):
        photos = _make_photos(3)
        for frame in FRAMES:
            result = compose_strip(photos, frame)
            assert isinstance(result, Image.Image)
            assert result.mode == "RGB"

    def test_raises_on_empty_list(self):
        frame = FRAMES[0]
        with pytest.raises((ValueError, Exception)):
            compose_strip([], frame)

    def test_single_photo(self):
        frame = FRAMES[0]
        photos = _make_photos(1)
        result = compose_strip(photos, frame)
        assert isinstance(result, Image.Image)

    def test_result_is_rgb(self):
        result = compose_strip(_make_photos(3), FRAMES[0])
        assert result.mode == "RGB"

    def test_large_photos(self):
        """Compositor should handle large input images without error."""
        photos = [Image.new("RGB", (1920, 1080), (100, 100, 100))] * 3
        result = compose_strip(photos, FRAMES[0])
        assert result.width == STRIP_PHOTO_WIDTH + STRIP_PADDING * 2