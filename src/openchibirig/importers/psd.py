from __future__ import annotations

import json
import os
import re
import shutil
import tempfile
import unicodedata
from dataclasses import dataclass
from pathlib import Path

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


class PsdImportError(ValueError):
    """Raised when a PSD cannot be converted to an OpenChibiRig input."""


@dataclass(frozen=True, slots=True)
class PsdImportReport:
    output_root: Path
    layer_count: int
    warnings: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class LayerMapping:
    layer_id: str
    role: str
    warning: str | None = None


def normalize_layer_name(name: str) -> str:
    normalized = unicodedata.normalize("NFKC", name).casefold()
    normalized = re.sub(r"[^a-z0-9]+", "_", normalized)
    return re.sub(r"_+", "_", normalized).strip("_") or "layer"


def _side(name: str) -> str | None:
    if re.search(r"(?:^|_)(?:left|l|1)(?:_|$)", name):
        return "left"
    if re.search(r"(?:^|_)(?:right|r|2)(?:_|$)", name):
        return "right"
    return None


def map_layer_name(name: str) -> LayerMapping:
    normalized = normalize_layer_name(name)
    side = _side(normalized)

    if "front_hair" in normalized or normalized in {"hairf", "hair_front"}:
        return LayerMapping(normalized, "hair.front")
    if "back_hair" in normalized or normalized in {"hairb", "hair_back"}:
        return LayerMapping(normalized, "hair.back")
    if normalized in {"face", "head"} or normalized.endswith("_face"):
        return LayerMapping(normalized, "face.base")
    if "eyewhite" in normalized or "eye_white" in normalized or "eyebg" in normalized:
        role = f"eye.{side}.white" if side else "eye.base.white"
        return LayerMapping(normalized, role)
    if "iris" in normalized or "irides" in normalized:
        role = f"eye.{side}.iris" if side else "eye.base.iris"
        return LayerMapping(normalized, role)
    if "eyelash" in normalized or "eyelid" in normalized or "lid" in normalized:
        role = f"eye.{side}.lid.upper" if side else "eye.base.lid"
        return LayerMapping(normalized, role)
    if normalized == "mouth" or normalized.endswith("_mouth"):
        return LayerMapping(normalized, "mouth.base")
    if any(token in normalized for token in ("topwear", "clothes", "cloth", "outfit")):
        return LayerMapping(normalized, "clothes.main")
    if normalized in {"body", "skin"} or normalized.endswith("_body"):
        return LayerMapping(normalized, "body.base")

    return LayerMapping(
        normalized,
        f"custom.{normalized}",
        warning=f"无法识别 PSD 图层名称：{name}，已保留为 custom.{normalized}。",
    )


def _iter_leaf_layers(psd: object) -> list[object]:
    descendants = getattr(psd, "descendants", None)
    if descendants is None:
        raise PsdImportError("PSD 对象不支持图层遍历。")
    layers = [layer for layer in descendants() if not layer.is_group()]
    if not layers:
        raise PsdImportError("PSD 没有可导出的叶子图层。")
    return layers


def _full_canvas_rgba(layer: object, width: int, height: int) -> Image.Image:
    canvas = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    if not getattr(layer, "visible", True):
        return canvas
    try:
        rendered = layer.composite().convert("RGBA")
        left, top, right, bottom = layer.bbox
    except (AttributeError, TypeError, ValueError, OSError) as exc:
        raise PsdImportError(f"无法读取 PSD 图层像素：{exc}") from exc
    expected_size = (max(0, right - left), max(0, bottom - top))
    if rendered.size != expected_size:
        rendered = rendered.resize(expected_size, Image.Resampling.BICUBIC)
    canvas.paste(rendered, (left, top), rendered)
    return canvas


def _safe_layer_id(mapping: LayerMapping, index: int) -> str:
    slug = re.sub(r"[^a-z0-9_-]+", "_", mapping.layer_id).strip("_") or "layer"
    return f"layer_{index:03d}_{slug}"[:64]


def _safe_character_id(name: str) -> str:
    slug = normalize_layer_name(name)
    return slug[:64]


def _write_manifest(
    output_root: Path,
    *,
    source: Path,
    width: int,
    height: int,
    layers: list[dict[str, object]],
) -> None:
    manifest = {
        "spec_version": "0.1",
        "character_id": _safe_character_id(output_root.name),
        "display_name": source.stem,
        "canvas": {"width": width, "height": height, "color_space": "srgb"},
        "orientation": {"view": "front", "left_right_basis": "character"},
        "layers": layers,
        "license": {"redistribution": "unconfirmed", "source": source.name},
        "notes": ["由 See-through PSD 导入；请人工检查补全区域和图层语义。"],
    }
    (output_root / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def _load_psd(source: Path) -> object:
    try:
        from psd_tools import PSDImage
    except ModuleNotFoundError as exc:
        raise PsdImportError(
            "缺少 psd-tools 依赖，请运行：pip install openchibirig[psd]。"
        ) from exc
    try:
        return PSDImage.open(source)
    except (OSError, ValueError, RuntimeError) as exc:
        raise PsdImportError(f"无法解析 PSD：{exc}") from exc


def import_psd(source: str | Path, output_root: str | Path) -> PsdImportReport:
    source_path = Path(source)
    output_path = Path(output_root)
    if not source_path.is_file():
        raise PsdImportError(f"输入 PSD 不存在：{source_path}")
    if source_path.suffix.casefold() != ".psd":
        raise PsdImportError(f"输入文件必须是 .psd：{source_path}")
    if output_path.exists():
        raise PsdImportError(f"输出目录已存在，为避免覆盖而停止：{output_path}")

    psd = _load_psd(source_path)
    try:
        width, height = tuple(psd.size)
    except (AttributeError, TypeError, ValueError) as exc:
        raise PsdImportError("PSD 没有有效画布尺寸。") from exc
    if not isinstance(width, int) or not isinstance(height, int) or width < 1 or height < 1:
        raise PsdImportError("PSD 没有有效画布尺寸。")

    layers = _iter_leaf_layers(psd)
    parent = output_path.parent
    parent.mkdir(parents=True, exist_ok=True)
    temp_path = Path(tempfile.mkdtemp(prefix=f".{output_path.name}.", dir=parent))
    warnings: list[str] = []
    manifest_layers: list[dict[str, object]] = []
    roles: set[str] = set()
    try:
        layer_dir = temp_path / "layers"
        layer_dir.mkdir()
        for index, layer in enumerate(layers, start=1):
            name = str(getattr(layer, "name", f"layer_{index}"))
            mapping = map_layer_name(name)
            if mapping.warning:
                warnings.append(mapping.warning)
            image = _full_canvas_rgba(layer, width, height)
            filename = f"{index * 10:03d}_{_safe_layer_id(mapping, index)}.png"
            image.save(layer_dir / filename, format="PNG")
            visible = bool(getattr(layer, "visible", True))
            manifest_layers.append(
                {
                    "id": _safe_layer_id(mapping, index),
                    "role": mapping.role,
                    "path": f"layers/{filename}",
                    "draw_order": index * 10,
                    "visible": visible,
                }
            )
            roles.add(mapping.role)

        for index, role in enumerate(REQUIRED_ROLES, start=len(manifest_layers) + 1):
            if role in roles:
                continue
            placeholder_id = f"placeholder_{role.replace('.', '_')}"[:64]
            filename = f"{index * 10:03d}_{placeholder_id}.png"
            Image.new("RGBA", (width, height), (0, 0, 0, 0)).save(
                layer_dir / filename, format="PNG"
            )
            manifest_layers.append(
                {
                    "id": placeholder_id,
                    "role": role,
                    "path": f"layers/{filename}",
                    "draw_order": index * 10,
                    "visible": False,
                }
            )
            warnings.append(f"缺少角色 {role}，已生成隐藏透明占位层。")

        _write_manifest(
            temp_path,
            source=source_path,
            width=width,
            height=height,
            layers=manifest_layers,
        )
        os.replace(temp_path, output_path)
    except Exception:
        shutil.rmtree(temp_path, ignore_errors=True)
        raise
    return PsdImportReport(output_path, len(manifest_layers), tuple(warnings))
