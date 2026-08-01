from __future__ import annotations

import pytest
from PIL import ImageChops

from openchibirig.runtime.preview import PreviewError, render_preview


def test_render_preview_returns_rgba_canvas(character_factory):
    image = render_preview(character_factory())

    assert image.mode == "RGBA"
    assert image.size == (8, 8)


def test_gaze_value_changes_rendered_image(character_factory):
    root = character_factory()
    neutral = render_preview(root)
    gaze = render_preview(root, {"gaze.x": 1.0})

    assert ImageChops.difference(neutral, gaze).getbbox() is not None


def test_mouth_value_changes_rendered_image(character_factory):
    root = character_factory()
    neutral = render_preview(root)
    mouth_open = render_preview(root, {"mouth.open": 1.0})

    assert ImageChops.difference(neutral, mouth_open).getbbox() is not None


def test_preview_rejects_unknown_or_out_of_range_values(character_factory):
    root = character_factory()

    with pytest.raises(PreviewError, match="未知参数"):
        render_preview(root, {"not_a_parameter": 1.0})
    with pytest.raises(PreviewError, match="超出范围"):
        render_preview(root, {"gaze.x": 2.0})
