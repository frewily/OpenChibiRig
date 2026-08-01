from __future__ import annotations

from collections import Counter
from pathlib import Path

from PIL import Image, UnidentifiedImageError

from openchibirig.core.manifest import ManifestError, load_manifest
from openchibirig.validation.diagnostics import Diagnostic, Severity, ValidationReport

REQUIRED_ROLES = frozenset(
    {
        "body.base",
        "face.base",
        "eye.left.white",
        "eye.left.iris",
        "eye.left.lid.upper",
        "eye.right.white",
        "eye.right.iris",
        "eye.right.lid.upper",
        "mouth.base",
    }
)


def _diagnostic(code: str, message: str, location: str | None = None) -> Diagnostic:
    return Diagnostic(code=code, severity=Severity.ERROR, message=message, location=location)


def validate_input(input_root: str | Path) -> ValidationReport:
    root = Path(input_root)
    diagnostics: list[Diagnostic] = []
    try:
        manifest = load_manifest(root)
    except ManifestError as exc:
        return ValidationReport((_diagnostic("MANIFEST_INVALID", str(exc), "manifest.json"),))

    roles = Counter(layer.role for layer in manifest.layers)
    missing = sorted(REQUIRED_ROLES.difference(roles))
    if missing:
        diagnostics.append(
            _diagnostic(
                "ROLE_REQUIRED_MISSING",
                f"缺少必需图层角色：{', '.join(missing)}。",
                "layers",
            )
        )

    ids = Counter(layer.id for layer in manifest.layers)
    for layer_id in sorted(item for item, count in ids.items() if count > 1):
        diagnostics.append(
            _diagnostic("LAYER_ID_DUPLICATE", f"图层 ID 重复：{layer_id}。", "layers")
        )

    for role in sorted(role for role, count in roles.items() if role in REQUIRED_ROLES and count > 1):
        diagnostics.append(
            _diagnostic("ROLE_SINGLETON_DUPLICATE", f"单值图层角色重复：{role}。", "layers")
        )

    order_counts = Counter(layer.draw_order for layer in manifest.layers)
    for order in sorted(value for value, count in order_counts.items() if count > 1):
        diagnostics.append(
            Diagnostic(
                code="DRAW_ORDER_TIE",
                severity=Severity.WARNING,
                message=f"多个图层使用 draw_order={order}，将使用清单顺序稳定排序。",
                location="layers",
            )
        )

    if max(manifest.canvas.width, manifest.canvas.height) > 4096:
        diagnostics.append(
            Diagnostic(
                code="CANVAS_LARGE",
                severity=Severity.WARNING,
                message="画布长边超过 4096 px，可能影响首版性能。",
                location="canvas",
            )
        )

    if manifest.redistribution in {None, "unconfirmed"}:
        diagnostics.append(
            Diagnostic(
                code="LICENSE_UNCONFIRMED",
                severity=Severity.WARNING,
                message="素材再分发授权尚未确认。",
                location="license.redistribution",
            )
        )

    resolved_root = root.resolve()
    for layer in manifest.layers:
        path = root / layer.path
        try:
            resolved_path = path.resolve()
            resolved_path.relative_to(resolved_root)
        except (OSError, ValueError):
            diagnostics.append(_diagnostic("PATH_UNSAFE", "图层路径越过输入目录。", layer.path))
            continue
        if not path.is_file():
            diagnostics.append(
                _diagnostic("LAYER_FILE_MISSING", "声明的图层文件不存在。", layer.path)
            )
            continue
        try:
            with Image.open(path) as image:
                if image.format != "PNG":
                    diagnostics.append(_diagnostic("IMG_NOT_PNG", "图层不是 PNG。", layer.path))
                if image.mode != "RGBA":
                    diagnostics.append(
                        _diagnostic("IMG_NOT_RGBA8", "图层不是 RGBA 8 bit。", layer.path)
                    )
                    continue
                expected_size = (manifest.canvas.width, manifest.canvas.height)
                if image.size != expected_size:
                    diagnostics.append(
                        _diagnostic(
                            "IMG_CANVAS_MISMATCH",
                            f"图层尺寸 {image.size} 与画布 {expected_size} 不一致。",
                            layer.path,
                        )
                    )
                if layer.visible and image.getchannel("A").getbbox() is None:
                    diagnostics.append(
                        _diagnostic("IMG_EMPTY", "可见图层没有非透明像素。", layer.path)
                    )
        except (OSError, UnidentifiedImageError) as exc:
            diagnostics.append(
                _diagnostic("IMG_UNREADABLE", f"无法读取图层：{exc}", layer.path)
            )

    for name, (x, y) in manifest.landmarks.items():
        if not (0 <= x < manifest.canvas.width and 0 <= y < manifest.canvas.height):
            diagnostics.append(
                _diagnostic(
                    "LANDMARK_OUT_OF_BOUNDS",
                    f"关键点 {name} 超出画布。",
                    f"landmarks.{name}",
                )
            )

    return ValidationReport(tuple(diagnostics))
