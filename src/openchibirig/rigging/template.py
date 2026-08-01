from __future__ import annotations

from pathlib import Path

from openchibirig.core.manifest import Manifest, load_manifest
from openchibirig.core.project import MotionSpec, ParameterSpec, Project
from openchibirig.rigging.errors import RiggingError
from openchibirig.validation.diagnostics import Severity
from openchibirig.validation.input_validator import validate_input

_EYE_ROLES = frozenset(
    {
        "eye.left.white",
        "eye.left.iris",
        "eye.left.lid.upper",
        "eye.right.white",
        "eye.right.iris",
        "eye.right.lid.upper",
    }
)


def _parameters() -> tuple[ParameterSpec, ...]:
    return (
        ParameterSpec("head.tilt", -1.0, 1.0, 0.0, "head"),
        ParameterSpec("breath", 0.0, 1.0, 0.0, "body"),
        ParameterSpec("gaze.x", -1.0, 1.0, 0.0, "eyes"),
        ParameterSpec("gaze.y", -1.0, 1.0, 0.0, "eyes"),
        ParameterSpec("blink.left", 0.0, 1.0, 0.0, "eyes"),
        ParameterSpec("blink.right", 0.0, 1.0, 0.0, "eyes"),
        ParameterSpec("mouth.open", 0.0, 1.0, 0.0, "mouth"),
    )


def _motions(roles: set[str]) -> tuple[MotionSpec, ...]:
    eyes_complete = _EYE_ROLES.issubset(roles)
    return (
        MotionSpec("idle", "loop", ("breath", "head.tilt"), True),
        MotionSpec("blink", "event", ("blink.left", "blink.right"), eyes_complete),
        MotionSpec(
            "gaze",
            "continuous",
            ("gaze.x", "gaze.y"),
            {"eye.left.white", "eye.left.iris", "eye.right.white", "eye.right.iris"}.issubset(
                roles
            ),
        ),
        MotionSpec("mouth_open", "continuous", ("mouth.open",), "mouth.base" in roles),
        MotionSpec(
            "hair_sway",
            "physics",
            ("head.tilt",),
            any(role.startswith("hair.") for role in roles),
        ),
    )


def _layers(manifest: Manifest) -> tuple[dict[str, object], ...]:
    ordered = sorted(manifest.layers, key=lambda layer: (layer.draw_order, layer.manifest_index))
    return tuple(
        {
            "id": layer.id,
            "role": layer.role,
            "path": layer.path,
            "draw_order": layer.draw_order,
            "visible": layer.visible,
        }
        for layer in ordered
    )


def build_project(input_root: str | Path) -> Project:
    root = Path(input_root)
    report = validate_input(root)
    if not report.is_valid:
        details = "; ".join(f"{item.code}: {item.message}" for item in report.errors)
        raise RiggingError(details)

    manifest = load_manifest(root)
    roles = {layer.role for layer in manifest.layers}
    motions = _motions(roles)
    capabilities = tuple(sorted(motion.id for motion in motions if motion.enabled and motion.id != "idle"))
    warnings = tuple(
        item.message for item in report.diagnostics if item.severity is Severity.WARNING
    )
    return Project(
        root=root,
        format_version="0.1",
        character_id=manifest.character_id,
        display_name=manifest.display_name,
        canvas={
            "width": manifest.canvas.width,
            "height": manifest.canvas.height,
            "color_space": manifest.canvas.color_space,
        },
        layers=_layers(manifest),
        parameters=_parameters(),
        motions=motions,
        capabilities=capabilities,
        warnings=warnings,
    )
