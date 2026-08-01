from __future__ import annotations

from openchibirig.cli import main


def test_validate_command_reports_success(character_factory, capsys):
    root = character_factory()

    exit_code = main(["validate", str(root)])

    assert exit_code == 0
    assert "输入有效" in capsys.readouterr().out


def test_compose_command_writes_png(character_factory, tmp_path, capsys):
    root = character_factory()
    output = tmp_path / "preview.png"

    exit_code = main(["compose", str(root), "--output", str(output)])

    assert exit_code == 0
    assert output.is_file()
    assert "已生成" in capsys.readouterr().out
