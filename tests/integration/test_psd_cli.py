from __future__ import annotations

import sys
import types
from pathlib import Path

from PIL import Image

from openchibirig.cli import main
from openchibirig.runtime.compositor import compose_layers
from openchibirig.validation.input_validator import validate_input


class FakeLayer:
    def __init__(self, name: str, color: tuple[int, int, int, int], bbox: tuple[int, int, int, int]) -> None:
        self.name = name
        self.visible = True
        self._color = color
        self.bbox = bbox

    def is_group(self) -> bool:
        return False

    def composite(self) -> Image.Image:
        return Image.new("RGBA", (self.bbox[2] - self.bbox[0], self.bbox[3] - self.bbox[1]), self._color)


class FakePsd:
    size = (8, 6)

    def descendants(self) -> list[FakeLayer]:
        return [
            FakeLayer("Face", (255, 0, 0, 255), (1, 1, 4, 3)),
            FakeLayer("Mystery Accessory", (0, 0, 255, 255), (4, 2, 6, 4)),
        ]


def install_fake_psd(monkeypatch, tmp_path: Path) -> Path:
    source = tmp_path / "sample.psd"
    source.touch()
    fake_module = types.SimpleNamespace(
        PSDImage=types.SimpleNamespace(open=lambda path: FakePsd()),
    )
    monkeypatch.setitem(sys.modules, "psd_tools", fake_module)
    return source


def test_import_psd_cli_reports_unknown_layer_warning(monkeypatch, tmp_path, capsys) -> None:
    source = install_fake_psd(monkeypatch, tmp_path)
    output = tmp_path / "out"

    code = main(["import-psd", str(source), "--output", str(output)])

    assert code == 0
    assert "WARNING" in capsys.readouterr().out
    assert (output / "manifest.json").is_file()
    assert validate_input(output).is_valid
    assert compose_layers(output).size == (8, 6)


def test_import_psd_cli_rejects_existing_output(monkeypatch, tmp_path, capsys) -> None:
    source = install_fake_psd(monkeypatch, tmp_path)
    output = tmp_path / "out"
    output.mkdir()

    code = main(["import-psd", str(source), "--output", str(output)])

    assert code == 1
    assert "已存在" in capsys.readouterr().err
