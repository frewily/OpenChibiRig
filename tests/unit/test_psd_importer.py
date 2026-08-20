from __future__ import annotations

import sys
import types
from dataclasses import dataclass
from pathlib import Path

import pytest
from PIL import Image

from openchibirig.importers.psd import PsdImportError, import_psd, map_layer_name


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("Front Hair", "hair.front"),
        ("hairb", "hair.back"),
        ("Face", "face.base"),
        ("mouth", "mouth.base"),
        ("topwear", "clothes.main"),
        ("skin", "body.base"),
        ("left iris", "eye.left.iris"),
    ],
)
def test_map_layer_name(name: str, expected: str) -> None:
    assert map_layer_name(name).role == expected


def test_unknown_layer_becomes_custom_role() -> None:
    result = map_layer_name("Sparkle Ribbon")
    assert result.role == "custom.sparkle_ribbon"
    assert result.warning is not None


def test_missing_psd_dependency_has_install_hint(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    source = tmp_path / "input.psd"
    source.touch()
    monkeypatch.setitem(sys.modules, "psd_tools", None)
    with pytest.raises(PsdImportError, match="psd-tools"):
        import_psd(source, tmp_path / "output")
    assert not (tmp_path / "output").exists()


@dataclass
class FakeLayer:
    name: str
    pixels: Image.Image
    bbox: tuple[int, int, int, int]
    visible: bool = True
    group: bool = False

    def is_group(self) -> bool:
        return self.group

    def composite(self) -> Image.Image:
        return self.pixels


class FakePsd:
    size = (8, 6)

    def __init__(self, layers: list[FakeLayer]) -> None:
        self._layers = layers

    def descendants(self) -> list[FakeLayer]:
        return self._layers


def install_fake_psd(monkeypatch: pytest.MonkeyPatch, *, width: int = 8, height: int = 6) -> None:
    red = Image.new("RGBA", (3, 2), (255, 0, 0, 255))
    blue = Image.new("RGBA", (2, 2), (0, 0, 255, 255))
    layers = [
        FakeLayer("Face", red, (1, 1, 4, 3)),
        FakeLayer("Sparkle Ribbon", blue, (4, 2, 6, 4)),
        FakeLayer("Hidden Detail", blue, (0, 0, 2, 2), visible=False),
    ]
    fake_module = types.SimpleNamespace(
        PSDImage=types.SimpleNamespace(open=lambda path: FakePsd(layers)),
    )
    monkeypatch.setitem(sys.modules, "psd_tools", fake_module)
    FakePsd.size = (width, height)


def test_import_writes_full_canvas_rgba_layers(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    source = tmp_path / "sample.psd"
    source.touch()
    install_fake_psd(monkeypatch)

    report = import_psd(source, tmp_path / "out")

    assert report.layer_count >= 3
    first_layer = next((tmp_path / "out/layers").glob("010_*.png"))
    with Image.open(first_layer) as image:
        assert image.mode == "RGBA"
        assert image.size == (8, 6)

    manifest_text = (tmp_path / "out/manifest.json").read_text(encoding="utf-8")
    assert '"draw_order": 10' in manifest_text
    assert '"visible": false' in manifest_text
    assert any("Sparkle Ribbon" in warning for warning in report.warnings)
