from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from PIL import Image

from openchibirig.core.manifest import Layer, load_manifest
from openchibirig.rigging.template import build_project
from openchibirig.validation.input_validator import validate_input


class PreviewError(ValueError):
    """Raised when preview parameters or source input are invalid."""


def _affine(image: Image.Image, coefficients: tuple[float, ...]) -> Image.Image:
    return image.transform(
        image.size,
        Image.Transform.AFFINE,
        coefficients,
        resample=Image.Resampling.BICUBIC,
    )


def _translate(image: Image.Image, dx: float, dy: float) -> Image.Image:
    return _affine(image, (1.0, 0.0, -dx, 0.0, 1.0, -dy))


def _scale_y(image: Image.Image, factor: float, center_y: float) -> Image.Image:
    inverse = 1.0 / factor
    return _affine(image, (1.0, 0.0, 0.0, 0.0, inverse, center_y - center_y * inverse))


def _rotate(image: Image.Image, degrees: float) -> Image.Image:
    return image.rotate(
        degrees,
        resample=Image.Resampling.BICUBIC,
        expand=False,
        center=(image.width / 2.0, image.height / 2.0),
    )


def _value(values: Mapping[str, float], parameter: str, minimum: float, maximum: float) -> float:
    value = float(values.get(parameter, 0.0))
    if not minimum <= value <= maximum:
        raise PreviewError(f"参数 {parameter} 超出范围 [{minimum}, {maximum}]。")
    return value


def _transform_layer(
    image: Image.Image,
    layer: Layer,
    values: Mapping[str, float],
    canvas_height: int,
) -> Image.Image:
    role = layer.role
    if role.startswith("eye.") and role.endswith(".iris"):
        image = _translate(
            image,
            _value(values, "gaze.x", -1.0, 1.0) * 12.0,
            _value(values, "gaze.y", -1.0, 1.0) * 8.0,
        )

    if role.startswith("eye.left"):
        blink = _value(values, "blink.left", 0.0, 1.0)
        if role.endswith((".white", ".iris")):
            image = _scale_y(image, max(0.2, 1.0 - 0.75 * blink), canvas_height * 0.30)
        elif role.endswith(".lid.upper"):
            image = _translate(image, 0.0, blink * 18.0)
    elif role.startswith("eye.right"):
        blink = _value(values, "blink.right", 0.0, 1.0)
        if role.endswith((".white", ".iris")):
            image = _scale_y(image, max(0.2, 1.0 - 0.75 * blink), canvas_height * 0.30)
        elif role.endswith(".lid.upper"):
            image = _translate(image, 0.0, blink * 18.0)

    if role == "mouth.base":
        image = _scale_y(image, 1.0 + 0.8 * _value(values, "mouth.open", 0.0, 1.0), canvas_height * 0.37)

    if role.startswith(("face.", "eye.", "mouth.", "hair.")):
        image = _rotate(image, _value(values, "head.tilt", -1.0, 1.0) * 4.0)

    if role.startswith(("body.", "clothes.")):
        image = _scale_y(image, 1.0 + 0.03 * _value(values, "breath", 0.0, 1.0), canvas_height * 0.62)

    return image


def render_preview(input_root: str | Path, values: Mapping[str, float] | None = None) -> Image.Image:
    root = Path(input_root)
    report = validate_input(root)
    if not report.is_valid:
        details = "; ".join(f"{item.code}: {item.message}" for item in report.errors)
        raise PreviewError(details)

    project = build_project(root)
    values = dict(values or {})
    known = {parameter.id for parameter in project.parameters}
    unknown = sorted(set(values).difference(known))
    if unknown:
        raise PreviewError(f"未知参数：{', '.join(unknown)}。")

    manifest = load_manifest(root)
    canvas = Image.new("RGBA", (manifest.canvas.width, manifest.canvas.height), (0, 0, 0, 0))
    ordered_layers = sorted(manifest.layers, key=lambda layer: (layer.draw_order, layer.manifest_index))
    for layer in ordered_layers:
        if not layer.visible:
            continue
        with Image.open(root / layer.path) as source:
            transformed = _transform_layer(source.convert("RGBA"), layer, values, manifest.canvas.height)
        canvas = Image.alpha_composite(canvas, transformed)
    return canvas
