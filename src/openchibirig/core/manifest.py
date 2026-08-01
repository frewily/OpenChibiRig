from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path
from types import MappingProxyType
from typing import Any

from jsonschema import Draft202012Validator


class ManifestError(ValueError):
    """Raised when an input manifest cannot be parsed or validated."""


@dataclass(frozen=True, slots=True)
class Canvas:
    width: int
    height: int
    color_space: str


@dataclass(frozen=True, slots=True)
class Layer:
    id: str
    role: str
    path: str
    draw_order: int
    manifest_index: int
    anchor: tuple[float, float] | None = None
    visible: bool = True


@dataclass(frozen=True, slots=True)
class Manifest:
    root: Path
    spec_version: str
    character_id: str
    display_name: str
    canvas: Canvas
    layers: tuple[Layer, ...]
    landmarks: Mapping[str, tuple[float, float]]
    redistribution: str | None


def _schema() -> dict[str, Any]:
    resource = files("openchibirig.resources").joinpath("input-manifest.schema.json")
    return json.loads(resource.read_text(encoding="utf-8"))


def _format_error(error: Any) -> str:
    location = ".".join(str(part) for part in error.absolute_path)
    return f"{location}: {error.message}" if location else error.message


def load_manifest(input_root: str | Path) -> Manifest:
    root = Path(input_root)
    path = root / "manifest.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ManifestError(f"无法读取 {path}: {exc}") from exc

    errors = sorted(
        Draft202012Validator(_schema()).iter_errors(data),
        key=lambda item: tuple(str(part) for part in item.absolute_path),
    )
    if errors:
        raise ManifestError("; ".join(_format_error(error) for error in errors))

    layers = tuple(
        Layer(
            id=item["id"],
            role=item["role"],
            path=item["path"],
            draw_order=item["draw_order"],
            manifest_index=index,
            anchor=tuple(item["anchor"]) if "anchor" in item else None,
            visible=item.get("visible", True),
        )
        for index, item in enumerate(data["layers"])
    )
    landmarks = MappingProxyType(
        {name: tuple(point) for name, point in data.get("landmarks", {}).items()}
    )
    license_data = data.get("license", {})
    return Manifest(
        root=root,
        spec_version=data["spec_version"],
        character_id=data["character_id"],
        display_name=data["display_name"],
        canvas=Canvas(**data["canvas"]),
        layers=layers,
        landmarks=landmarks,
        redistribution=license_data.get("redistribution"),
    )
