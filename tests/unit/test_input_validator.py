from __future__ import annotations

import json

from PIL import Image

from openchibirig.validation.input_validator import validate_input


def diagnostic_codes(report):
    return {item.code for item in report.diagnostics}


def test_valid_character_has_no_errors(character_factory):
    report = validate_input(character_factory())

    assert report.is_valid
    assert report.errors == ()


def test_missing_required_role_is_reported(character_factory):
    root = character_factory(roles=("body.base",))

    report = validate_input(root)

    assert not report.is_valid
    assert "ROLE_REQUIRED_MISSING" in diagnostic_codes(report)


def test_non_rgba_layer_is_reported(character_factory):
    root = character_factory()
    Image.new("RGB", (8, 8), "white").save(root / "layers/000_body_base.png")

    report = validate_input(root)

    assert "IMG_NOT_RGBA8" in diagnostic_codes(report)


def test_canvas_mismatch_is_reported(character_factory):
    root = character_factory()
    Image.new("RGBA", (4, 4), "white").save(root / "layers/000_body_base.png")

    report = validate_input(root)

    assert "IMG_CANVAS_MISMATCH" in diagnostic_codes(report)


def test_empty_visible_layer_is_reported(character_factory):
    root = character_factory()
    Image.new("RGBA", (8, 8), (0, 0, 0, 0)).save(root / "layers/000_body_base.png")

    report = validate_input(root)

    assert "IMG_EMPTY" in diagnostic_codes(report)


def test_manifest_error_becomes_diagnostic(character_factory):
    root = character_factory()
    path = root / "manifest.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    data["canvas"]["width"] = 0
    path.write_text(json.dumps(data), encoding="utf-8")

    report = validate_input(root)

    assert diagnostic_codes(report) == {"MANIFEST_INVALID"}
