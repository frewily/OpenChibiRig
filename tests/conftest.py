from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path

import pytest
from PIL import Image

REQUIRED_ROLES = (
    "body.base",
    "face.base",
    "eye.left.white",
    "eye.left.iris",
    "eye.left.lid.upper",
    "eye.right.white",
    "eye.right.iris",
    "eye.right.lid.upper",
    "mouth.base",
)


@pytest.fixture
def character_factory(tmp_path: Path) -> Callable[..., Path]:
    def create(*, size: tuple[int, int] = (8, 8), roles: tuple[str, ...] = REQUIRED_ROLES) -> Path:
        root = tmp_path / "character"
        layers_dir = root / "layers"
        layers_dir.mkdir(parents=True)
        layers = []

        for index, role in enumerate(roles):
            layer_id = role.replace(".", "_")
            relative_path = f"layers/{index:03d}_{layer_id}.png"
            image = Image.new("RGBA", size, (0, 0, 0, 0))
            image.putpixel((index % size[0], index // size[0]), (index + 1, 20, 30, 255))
            image.save(root / relative_path)
            layers.append(
                {
                    "id": layer_id,
                    "role": role,
                    "path": relative_path,
                    "draw_order": index * 10,
                }
            )

        manifest = {
            "spec_version": "0.1",
            "character_id": "generic_test_character",
            "display_name": "Generic Test Character",
            "canvas": {"width": size[0], "height": size[1], "color_space": "srgb"},
            "orientation": {"view": "front", "left_right_basis": "character"},
            "layers": layers,
            "license": {"redistribution": "allowed"},
            "notes": [],
        }
        (root / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        return root

    return create
