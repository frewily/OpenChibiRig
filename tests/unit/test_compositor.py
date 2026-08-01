from __future__ import annotations

import json

from PIL import Image

from openchibirig.runtime.compositor import compose_layers


def test_compositor_uses_draw_order(character_factory):
    root = character_factory()
    body = Image.open(root / "layers/000_body_base.png")
    body.putpixel((7, 7), (255, 0, 0, 255))
    body.save(root / "layers/000_body_base.png")
    face = Image.open(root / "layers/001_face_base.png")
    face.putpixel((7, 7), (0, 255, 0, 255))
    face.save(root / "layers/001_face_base.png")

    result = compose_layers(root)

    assert result.getpixel((7, 7)) == (0, 255, 0, 255)


def test_equal_draw_order_uses_manifest_order(character_factory):
    root = character_factory()
    manifest_path = root / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["layers"][0]["draw_order"] = 10
    manifest["layers"][1]["draw_order"] = 10
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    for path, color in (
        (root / "layers/000_body_base.png", (255, 0, 0, 255)),
        (root / "layers/001_face_base.png", (0, 255, 0, 255)),
    ):
        image = Image.open(path)
        image.putpixel((7, 7), color)
        image.save(path)

    result = compose_layers(root)

    assert result.getpixel((7, 7)) == (0, 255, 0, 255)
