from __future__ import annotations

import json

from openchibirig.cli import main


def test_rig_command_writes_project_json(character_factory, tmp_path, capsys):
    output = tmp_path / "project.json"

    exit_code = main(["rig", str(character_factory()), "--output", str(output)])

    assert exit_code == 0
    assert json.loads(output.read_text(encoding="utf-8"))["format_version"] == "0.1"
    assert "已生成项目" in capsys.readouterr().out


def test_rig_command_rejects_invalid_input(character_factory, tmp_path, capsys):
    output = tmp_path / "project.json"

    exit_code = main(
        ["rig", str(character_factory(roles=("body.base",))), "--output", str(output)]
    )

    assert exit_code == 1
    assert not output.exists()
    assert "生成绑定项目失败" in capsys.readouterr().err
