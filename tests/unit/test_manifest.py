from __future__ import annotations

import json
from importlib.resources import files
from pathlib import Path

import pytest

from openchibirig.core.manifest import ManifestError, load_manifest


def test_packaged_schema_matches_repository_schema():
    repository_schema = json.loads(
        (Path(__file__).parents[2] / "schemas/input-manifest.schema.json").read_text(
            encoding="utf-8"
        )
    )
    packaged_schema = json.loads(
        files("openchibirig.resources")
        .joinpath("input-manifest.schema.json")
        .read_text(encoding="utf-8")
    )

    assert packaged_schema == repository_schema


def test_load_manifest_returns_immutable_domain_model(character_factory):
    root = character_factory()

    manifest = load_manifest(root)

    assert manifest.character_id == "generic_test_character"
    assert manifest.canvas.width == 8
    assert manifest.layers[0].role == "body.base"
    assert manifest.layers[0].manifest_index == 0


def test_load_manifest_rejects_schema_violation(character_factory):
    root = character_factory()
    path = root / "manifest.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    del data["display_name"]
    path.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(ManifestError, match="display_name"):
        load_manifest(root)
