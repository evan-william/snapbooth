"""
Tests for core/filters.py

These tests verify that each filter:
  - Returns a PIL Image of the same dimensions as the input
  - Does not mutate the original image
  - Handles edge cases without raising
"""

import numpy as np
import pytest
from PIL import Image

from core.filters import apply_filter, generate_thumbnail


# ── Fixtures ─────────────────────────────────────────────────────────────

def _solid_image(color=(128, 64, 200), size=(100, 80)) -> Image.Image:
    img = Image.new("RGB", size, color)
    return img


def _gradient_image(size=(100, 80)) -> Image.Image:
    arr = np.zeros((size[1], size[0], 3), dtype=np.uint8)
    for x in range(size[0]):
        arr[:, x, 0] = int(x * 255 / size[0])
    arr[:, :, 1] = 128
    arr[:, :, 2] = 50
    return Image.fromarray(arr, "RGB")


FILTER_KEYS = ["none", "bw", "sepia", "retro", "cool", "vivid"]


# ── Tests ─────────────────────────────────────────────────────────────────

class TestApplyFilter:
    def test_returns_pil_image(self):
        img = _solid_image()
        for key in FILTER_KEYS:
            result = apply_filter(img, key)
            assert isinstance(result, Image.Image), f"Filter '{key}' did not return PIL Image"

    def test_preserves_dimensions(self):
        img = _gradient_image()
        for key in FILTER_KEYS:
            result = apply_filter(img, key)
            assert result.size == img.size, (
                f"Filter '{key}' changed image size from {img.size} to {result.size}"
            )

    def test_returns_rgb_mode(self):
        img = _solid_image()
        for key in FILTER_KEYS:
            result = apply_filter(img, key)
            assert result.mode == "RGB", f"Filter '{key}' returned mode '{result.mode}'"

    def test_does_not_mutate_original(self):
        img = _solid_image((100, 150, 200))
        original_pixel = img.getpixel((0, 0))
        apply_filter(img, "vivid")
        assert img.getpixel((0, 0)) == original_pixel, "Original image was mutated"

    def test_bw_is_greyscale(self):
        """All pixels in a BW-filtered image should have equal R, G, B values."""
        img = _gradient_image()
        result = apply_filter(img, "bw")
        arr = np.array(result)
        assert np.allclose(arr[:, :, 0], arr[:, :, 1], atol=1), "BW filter R != G"
        assert np.allclose(arr[:, :, 1], arr[:, :, 2], atol=1), "BW filter G != B"

    def test_unknown_key_returns_copy(self):
        img = _solid_image()
        result = apply_filter(img, "nonexistent_filter_xyz")
        assert result.size == img.size
        assert list(result.getdata()) == list(img.getdata())

    @pytest.mark.parametrize("key", FILTER_KEYS)
    def test_single_pixel_image(self, key):
        """Should not raise on a 1×1 image (edge case)."""
        img = Image.new("RGB", (1, 1), (255, 0, 0))
        result = apply_filter(img, key)
        assert result.size == (1, 1)


class TestGenerateThumbnail:
    def test_respects_max_width(self):
        img = Image.new("RGB", (800, 600))
        thumb = generate_thumbnail(img, width=200)
        assert thumb.width == 200

    def test_preserves_aspect_ratio(self):
        img = Image.new("RGB", (400, 200))    # 2:1 ratio
        thumb = generate_thumbnail(img, width=100)
        assert thumb.width == 100
        assert thumb.height == 50

    def test_does_not_upscale_mode(self):
        """Thumbnail is still a valid image even if source is smaller than target width."""
        img = Image.new("RGB", (50, 50))
        thumb = generate_thumbnail(img, width=200)
        assert isinstance(thumb, Image.Image)