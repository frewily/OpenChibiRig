# See-through PSD 导入适配器实现计划

> **面向 AI 代理的工作者：** 必需子技能：使用 `superpowers:subagent-driven-development`（推荐）或 `superpowers:executing-plans` 逐任务实现此计划。步骤使用复选框（`- [ ]`）语法来跟踪进度。

**目标：** 将 See-through 生成的分层 PSD 转换为 OpenChibiRig 可校验、可合成、可预览的标准图层目录。

**架构：** 新增独立的 PSD 导入模块，延迟加载可选的 `psd-tools` 依赖。导入器负责读取 PSD 叶子图层、生成同画布 RGBA PNG、映射标准角色语义和写入 `manifest.json`；CLI 只负责参数解析、错误展示和报告警告。See-through 推理模型不进入本仓库运行时。

**技术栈：** Python 3.11+、Pillow、`psd-tools[composite]`（可选依赖）、现有 `Manifest` schema、pytest、ruff。

---

## 文件结构

- 创建：`src/openchibirig/importers/psd.py`，PSD 读取、图层导出、语义映射和 manifest 写入。
- 修改：`src/openchibirig/importers/__init__.py`，导出导入器公共 API。
- 修改：`src/openchibirig/cli.py`，新增 `import-psd` 子命令。
- 修改：`pyproject.toml`，新增 `psd` 可选依赖组。
- 创建：`tests/unit/test_psd_importer.py`，映射、排序、RGBA 画布和错误行为测试。
- 创建：`tests/integration/test_psd_cli.py`，CLI 成功、警告和失败路径测试。
- 修改：`README.md`，记录可选安装命令、导入用法和 PSD 适配器边界。

### 任务 1：定义可选依赖和导入器错误边界

**文件：**
- 修改：`pyproject.toml` 的 `[project.optional-dependencies]`。
- 创建：`src/openchibirig/importers/psd.py`。
- 修改：`src/openchibirig/importers/__init__.py`。
- 测试：`tests/unit/test_psd_importer.py`。

- [ ] **步骤 1：先写可选依赖和 API 失败测试**

```python
def test_missing_psd_dependency_has_install_hint(monkeypatch, tmp_path):
    monkeypatch.setitem(sys.modules, "psd_tools", None)
    with pytest.raises(PsdImportError, match="psd-tools"):
        import_psd(tmp_path / "input.psd", tmp_path / "output")
```

测试还要断言 `PsdImportError` 是 `ValueError` 的子类，且导入器不在失败时创建输出目录。

- [ ] **步骤 2：运行单测确认失败**

运行：`.venv/bin/pytest tests/unit/test_psd_importer.py -q`

预期：由于 `PsdImportError`、`import_psd` 尚未定义而失败。

- [ ] **步骤 3：实现最小公共边界**

在 `pyproject.toml` 增加：

```toml
psd = ["psd-tools[composite]>=1.10,<2"]
```

在 `psd.py` 定义：

```python
@dataclass(frozen=True, slots=True)
class PsdImportReport:
    output_root: Path
    layer_count: int
    warnings: tuple[str, ...]

class PsdImportError(ValueError):
    """Raised when a PSD cannot be converted to an OpenChibiRig input."""

def import_psd(source: str | Path, output_root: str | Path) -> PsdImportReport:
    raise PsdImportError("PSD 导入器尚未实现")
```

`import_psd` 首先检查输入文件存在、后缀为 `.psd`、输出目录不存在，然后在函数内部执行 `from psd_tools import PSDImage`。依赖缺失时抛出包含 `pip install openchibirig[psd]` 的错误。

- [ ] **步骤 4：运行单测确认边界通过**

运行：`.venv/bin/pytest tests/unit/test_psd_importer.py::test_missing_psd_dependency_has_install_hint -q`

预期：PASS。

- [ ] **步骤 5：提交边界变更**

```bash
git add pyproject.toml src/openchibirig/importers/psd.py src/openchibirig/importers/__init__.py tests/unit/test_psd_importer.py
git commit -m "feat: 增加 PSD 导入器边界"
```

### 任务 2：实现图层名称规范化和语义映射

**文件：**
- 修改：`src/openchibirig/importers/psd.py`。
- 修改：`tests/unit/test_psd_importer.py`。

- [ ] **步骤 1：编写映射测试**

```python
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
def test_map_layer_name(name, expected):
    assert map_layer_name(name).role == expected

def test_unknown_layer_becomes_custom_role():
    result = map_layer_name("Sparkle Ribbon")
    assert result.role == "custom.sparkle_ribbon"
    assert result.warning is not None
```

规范化必须使用 Unicode NFKC、大小写折叠，并把空格、连字符和连续下划线统一为单个 `_`。`left`、`right`、`-1`、`-2` 等侧别提示用于眼睛语义；没有侧别的眼睛图层使用 `eye.base.*`，不得猜测左右。

- [ ] **步骤 2：运行映射测试确认失败**

运行：`.venv/bin/pytest tests/unit/test_psd_importer.py -k 'map_layer_name or unknown_layer' -q`

预期：因映射结果类型和 `map_layer_name` 尚未实现而失败。

- [ ] **步骤 3：实现映射结果和规则表**

定义：

```python
@dataclass(frozen=True, slots=True)
class LayerMapping:
    layer_id: str
    role: str
    warning: str | None = None

def normalize_layer_name(name: str) -> str:
    return re.sub(r"_+", "_", re.sub(r"[^a-z0-9_]+", "_", unicodedata.normalize("NFKC", name).casefold())).strip("_")

def map_layer_name(name: str) -> LayerMapping:
    normalized = normalize_layer_name(name)
    return LayerMapping(layer_id=normalized, role=f"custom.{normalized}", warning=name)
```

规则覆盖 `front hair`、`back hair`、`face`、`eyewhite`、`eyebg`、`iris`、`irides`、`eyelash`、`eyelid`、`mouth`、`topwear`、`clothes`、`body` 和 `skin`。未知名称通过短横线、空格和下划线统一生成安全 slug，角色为 `custom.<slug>`，并记录原始名称警告。

- [ ] **步骤 4：运行映射测试确认通过**

运行：`.venv/bin/pytest tests/unit/test_psd_importer.py -k 'map_layer_name or unknown_layer' -q`

预期：所有映射测试 PASS。

- [ ] **步骤 5：提交映射器**

```bash
git add src/openchibirig/importers/psd.py tests/unit/test_psd_importer.py
git commit -m "feat: 增加 PSD 图层语义映射"
```

### 任务 3：实现 PSD 叶子图层导出和 manifest 生成

**文件：**
- 修改：`src/openchibirig/importers/psd.py`。
- 修改：`tests/unit/test_psd_importer.py`。

- [ ] **步骤 1：编写伪 PSD 测试夹具和失败测试**

在测试中创建 `FakePsd`、`FakeLayer` 和 `FakeBBox`，通过 monkeypatch 注入 `psd_tools.PSDImage.open`，避免提交二进制 PSD。夹具包含 2 个有序叶子图层、1 个组节点和 1 个隐藏图层；每个叶子层的 `composite()` 返回小尺寸 RGBA 图像，`bbox` 提供其在完整画布中的偏移。

测试：

```python
def test_import_writes_full_canvas_rgba_layers(monkeypatch, tmp_path):
    install_fake_psd(monkeypatch, width=8, height=6)
    report = import_psd(tmp_path / "sample.psd", tmp_path / "out")
    assert report.layer_count == 3
    first_layer = next((tmp_path / "out/layers").glob("010_*.png"))
    assert Image.open(first_layer).mode == "RGBA"
```

实际实现测试使用 `glob` 查找输出文件，并断言每张图片尺寸为 `(8, 6)`、manifest 的 `draw_order` 为 `10, 20, 30`，隐藏图层的 `visible` 为 `false`。

- [ ] **步骤 2：运行导出测试确认失败**

运行：`.venv/bin/pytest tests/unit/test_psd_importer.py -k 'full_canvas' -q`

预期：因 PSD 遍历和输出尚未实现而失败。

- [ ] **步骤 3：实现读取、导出和 manifest 写入**

实现以下内部函数：

```python
def _iter_leaf_layers(psd) -> list[object]:
    return [layer for layer in psd.descendants() if not layer.is_group()]

def _full_canvas_rgba(layer, width: int, height: int) -> Image.Image:
    canvas = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    canvas.alpha_composite(layer.composite().convert("RGBA"), dest=layer.bbox[:2])
    return canvas

def _safe_layer_id(name: str, index: int) -> str:
    return f"layer_{index:03d}_{normalize_layer_name(name)}"

def _write_manifest(
    output_root: Path, *, source: Path, width: int, height: int, layers: list[dict]
) -> None:
    manifest = {"spec_version": "0.1", "character_id": output_root.name,
                "display_name": source.stem, "canvas": {"width": width,
                "height": height, "color_space": "srgb"}, "layers": layers,
                "license": {"redistribution": "unconfirmed"}}
    (output_root / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
```

规则：

1. 只导出叶子图层，组节点不重复导出；
2. 按 PSD 的视觉合成顺序转换为底到顶的稳定顺序；
3. 将 `layer.composite()` 转成 RGBA，并按 `layer.bbox` 粘贴到完整画布；
4. 隐藏图层导出全透明 PNG，manifest 设置 `visible: false`；
5. 文件名使用 `NNN_<safe_id>.png`，`draw_order` 使用 `10` 的倍数；
6. 使用 `json.dumps(manifest, ensure_ascii=False, indent=2)` 写入 manifest，并用临时目录完成后原子改名，避免半成品输出；
7. 将映射警告收集进 `PsdImportReport.warnings`，不因未知名称中止。

- [ ] **步骤 4：运行导出测试确认通过**

运行：`.venv/bin/pytest tests/unit/test_psd_importer.py -k 'full_canvas' -q`

预期：PASS，并确认输出目录包含 `manifest.json` 和 3 张全画布 RGBA PNG。

- [ ] **步骤 5：运行模块回归测试并提交**

运行：`.venv/bin/pytest tests/unit/test_psd_importer.py tests/unit/test_manifest.py -q`

预期：全部 PASS。

```bash
git add src/openchibirig/importers/psd.py tests/unit/test_psd_importer.py
git commit -m "feat: 导出 PSD 图层和标准 manifest"
```

### 任务 4：接入 CLI 和错误报告

**文件：**
- 修改：`src/openchibirig/cli.py`。
- 修改：`src/openchibirig/importers/__init__.py`。
- 创建：`tests/integration/test_psd_cli.py`。

- [ ] **步骤 1：编写 CLI 失败测试**

```python
def test_import_psd_cli_reports_unknown_layer_warning(fake_psd, tmp_path, capsys):
    code = main(["import-psd", str(fake_psd), "--output", str(tmp_path / "out")])
    assert code == 0
    assert "WARNING" in capsys.readouterr().out

def test_import_psd_cli_rejects_existing_output(fake_psd, tmp_path, capsys):
    output = tmp_path / "out"
    output.mkdir()
    assert main(["import-psd", str(fake_psd), "--output", str(output)]) == 1
    assert "已存在" in capsys.readouterr().err
```

- [ ] **步骤 2：运行 CLI 测试确认失败**

运行：`.venv/bin/pytest tests/integration/test_psd_cli.py -q`

预期：因 CLI 子命令尚未注册而失败。

- [ ] **步骤 3：实现 CLI 子命令**

在 `_parser()` 中注册：

```python
import_psd = commands.add_parser("import-psd", help="将分层 PSD 导入标准图层目录")
import_psd.add_argument("input", type=Path)
import_psd.add_argument("--output", "-o", type=Path, required=True)
```

在 `main()` 中捕获 `PsdImportError`，向 stderr 输出 `导入 PSD 失败：<错误信息>` 并返回 `1`；成功时逐条输出 `WARNING: <警告信息>`，最后输出生成目录并返回 `0`。

- [ ] **步骤 4：运行 CLI 测试确认通过**

运行：`.venv/bin/pytest tests/integration/test_psd_cli.py -q`

预期：所有 CLI 测试 PASS。

- [ ] **步骤 5：提交 CLI 接入**

```bash
git add src/openchibirig/cli.py src/openchibirig/importers/__init__.py tests/integration/test_psd_cli.py
git commit -m "feat: 增加 import-psd 命令"
```

### 任务 5：文档、端到端兼容性和最终验证

**文件：**
- 修改：`README.md`。
- 修改：`tests/integration/test_psd_cli.py`。

- [ ] **步骤 1：增加兼容性测试**

在 CLI 测试中调用 `validate_input(output)`，确认导入结果可被现有校验器接受；再调用 `compose_layers(output)`，确认返回完整画布图像。测试继续使用伪 PSD，不下载 See-through 模型。

- [ ] **步骤 2：运行兼容性测试确认失败**

运行：`.venv/bin/pytest tests/integration/test_psd_cli.py -q`

预期：在 manifest 字段或图层输出不完整时失败，修复实现后转为 PASS。

- [ ] **步骤 3：更新 README**

新增安装与使用说明：

```bash
pip install -e '.[psd]'
openchibirig import-psd see-through-output.psd \
  --output references/private/atori-see-through
openchibirig validate references/private/atori-see-through
```

明确说明：该命令只做 PSD 标准化，不运行 See-through 推理，也不保证自动生成可直接商用的 Live2D 模型。

- [ ] **步骤 4：执行完整验证**

运行：

```bash
.venv/bin/pytest -q
.venv/bin/ruff check .
git diff --check
```

预期：现有测试与新增测试全部通过，ruff 无错误，diff 无空白问题。若本地已安装 `psd-tools`，额外运行：

```bash
.venv/bin/openchibirig import-psd --help
```

- [ ] **步骤 5：提交文档和最终变更**

```bash
git add README.md tests/integration/test_psd_cli.py
git commit -m "docs: 补充 PSD 导入使用说明"
```

## 计划自检

- 规格中的 PSD 读取、RGBA 导出、语义映射、未知图层警告、manifest 生成、CLI、错误处理和测试策略均有对应任务。
- 计划没有把 See-through 推理模型或亚托莉专用逻辑纳入实现范围。
- `PsdImportReport`、`LayerMapping`、`map_layer_name` 和 `import_psd` 的名称在所有任务中保持一致。
- 测试使用伪 PSD，不依赖 GPU、网络或版权不明的角色素材。
