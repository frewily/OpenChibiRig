from __future__ import annotations

from pathlib import Path

from PIL import Image

from openchibirig.core.manifest import load_manifest
from openchibirig.validation.input_validator import validate_input


class CompositionError(ValueError):
    """Raised when invalid input cannot be composed."""


def compose_layers(input_root: str | Path) -> Image.Image:
    root = Path(input_root)
    report = validate_input(root)
    if not report.is_valid:
        details = "; ".join(f"{item.code}: {item.message}" for item in report.errors)
        raise CompositionError(details)

    manifest = load_manifest(root)
    canvas = Image.new("RGBA", (manifest.canvas.width, manifest.canvas.height), (0, 0, 0, 0))
    layers = sorted(manifest.layers, key=lambda layer: (layer.draw_order, layer.manifest_index))
    for layer in layers:
        if not layer.visible:
            continue
        with Image.open(root / layer.path) as image:
            canvas = Image.alpha_composite(canvas, image)
    return canvas
