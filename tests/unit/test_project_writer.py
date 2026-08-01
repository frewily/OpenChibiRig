from __future__ import annotations

import json

import pytest

from openchibirig.rigging.project_writer import RiggingError, write_project


def test_write_project_emits_utf8_stable_json(character_factory, tmp_path):
    output = tmp_path / "project.json"

    project = write_project(character_factory(), output)
    data = json.loads(output.read_text(encoding="utf-8"))

    assert data["format_version"] == "0.1"
    assert data["display_name"] == "Generic Test Character"
    assert data["parameters"][0]["id"] == "head.tilt"
    assert project.character_id == data["character_id"]


def test_write_project_rejects_invalid_input(character_factory, tmp_path):
    output = tmp_path / "project.json"

    with pytest.raises(RiggingError, match="ROLE_REQUIRED_MISSING"):
        write_project(character_factory(roles=("body.base",)), output)

    assert not output.exists()
