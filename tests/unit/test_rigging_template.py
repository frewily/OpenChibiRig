from __future__ import annotations

from openchibirig.rigging.template import build_project


def test_template_generates_stable_parameters_and_motions(character_factory):
    project = build_project(
        character_factory(
            roles=(
                "body.base",
                "face.base",
                "eye.left.white",
                "eye.left.iris",
                "eye.left.lid.upper",
                "eye.right.white",
                "eye.right.iris",
                "eye.right.lid.upper",
                "mouth.base",
                "hair.back",
            )
        )
    )

    assert project.format_version == "0.1"
    assert [item.id for item in project.parameters] == [
        "head.tilt",
        "breath",
        "gaze.x",
        "gaze.y",
        "blink.left",
        "blink.right",
        "mouth.open",
    ]
    assert [item.id for item in project.motions] == [
        "idle",
        "blink",
        "gaze",
        "mouth_open",
        "hair_sway",
    ]
    assert all(item.enabled for item in project.motions)
    assert project.capabilities == (
        "blink",
        "gaze",
        "hair_sway",
        "mouth_open",
    )


def test_template_disables_optional_motion_when_parts_are_missing(character_factory):
    project = build_project(
        character_factory(
            roles=(
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
        )
    )

    enabled = {item.id: item.enabled for item in project.motions}

    assert enabled == {
        "idle": True,
        "blink": True,
        "gaze": True,
        "mouth_open": True,
        "hair_sway": False,
    }
    assert project.capabilities == ("blink", "gaze", "mouth_open")
