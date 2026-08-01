from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True, slots=True)
class ParameterSpec:
    id: str
    minimum: float
    maximum: float
    default: float
    group: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "min": self.minimum,
            "max": self.maximum,
            "default": self.default,
            "group": self.group,
        }


@dataclass(frozen=True, slots=True)
class MotionSpec:
    id: str
    kind: str
    parameters: tuple[str, ...]
    enabled: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "kind": self.kind,
            "parameters": list(self.parameters),
            "enabled": self.enabled,
        }


@dataclass(frozen=True, slots=True)
class Project:
    root: Path
    format_version: str
    character_id: str
    display_name: str
    canvas: dict[str, Any]
    layers: tuple[dict[str, Any], ...]
    parameters: tuple[ParameterSpec, ...]
    motions: tuple[MotionSpec, ...]
    capabilities: tuple[str, ...]
    warnings: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "format_version": self.format_version,
            "character_id": self.character_id,
            "display_name": self.display_name,
            "canvas": dict(self.canvas),
            "layers": [dict(layer) for layer in self.layers],
            "parameters": [parameter.to_dict() for parameter in self.parameters],
            "motions": [motion.to_dict() for motion in self.motions],
            "capabilities": list(self.capabilities),
            "warnings": list(self.warnings),
        }
