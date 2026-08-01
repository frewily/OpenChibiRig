from __future__ import annotations

from PIL import Image

from openchibirig.cli import main


def test_preview_command_writes_parameterized_png(character_factory, tmp_path, capsys):
    output = tmp_path / "preview.png"

    exit_code = main(
        [
            "preview",
            str(character_factory()),
            "--set",
            "gaze.x=0.5",
            "--set",
            "mouth.open=0.8",
            "--output",
            str(output),
        ]
    )

    assert exit_code == 0
    assert Image.open(output).mode == "RGBA"
    assert "已生成预览" in capsys.readouterr().out
