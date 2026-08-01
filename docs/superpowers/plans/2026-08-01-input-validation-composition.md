# 输入校验与静态合成实现计划

> **面向 AI 代理的工作者：** 必需子技能：使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 逐任务实现此计划。步骤使用复选框（`- [ ]`）语法来跟踪进度。

**目标：** 实现目录输入的结构化校验、RGBA 图层静态合成和命令行入口。

**架构：** 清单解析、跨文件校验、图层合成和 CLI 分属独立模块。CLI 只组合公共接口，测试使用动态生成的通用夹具验证完整数据流。

**技术栈：** Python 3.11、Pillow、jsonschema、pytest、ruff、hatchling。

---

## 文件结构

- `src/openchibirig/core/manifest.py`：清单领域对象、Schema 加载和 JSON 解析。
- `src/openchibirig/resources/input-manifest.schema.json`：随 Python 包分发的 Schema。
- `src/openchibirig/validation/diagnostics.py`：诊断项与校验报告。
- `src/openchibirig/validation/input_validator.py`：目录与 PNG 跨文件校验。
- `src/openchibirig/runtime/compositor.py`：稳定排序和 Alpha 合成。
- `src/openchibirig/cli.py`、`src/openchibirig/__main__.py`：命令行入口。
- `tests/conftest.py`：动态角色输入工厂。
- `tests/unit/test_manifest.py`：清单解析测试。
- `tests/unit/test_input_validator.py`：校验规则测试。
- `tests/unit/test_compositor.py`：绘制顺序测试。
- `tests/integration/test_cli.py`：端到端 CLI 测试。

### 任务 1：依赖和清单模型

- [ ] 编写 `tests/unit/test_manifest.py`，断言有效清单产生不可变对象，非法清单抛出 `ManifestError`。
- [ ] 运行 `pytest tests/unit/test_manifest.py -q`，确认因模块不存在而失败。
- [ ] 添加 Pillow、jsonschema 和 CLI 配置，创建打包 Schema 与 `core/manifest.py`。
- [ ] 再次运行测试，确认清单测试通过。

### 任务 2：输入校验器

- [ ] 在 `tests/conftest.py` 创建 8×8 RGBA 通用角色工厂，生成全部 9 个必需角色。
- [ ] 编写缺失角色、非 RGBA、画布不匹配、空图层和有效输入测试。
- [ ] 运行 `pytest tests/unit/test_input_validator.py -q`，确认因校验器不存在而失败。
- [ ] 实现稳定诊断模型与 `validate_input()`，逐条满足失败测试。
- [ ] 再次运行测试，确认校验规则通过。

### 任务 3：静态合成器

- [ ] 编写相同 `draw_order` 使用清单顺序、不同顺序正确覆盖的像素测试。
- [ ] 运行 `pytest tests/unit/test_compositor.py -q`，确认因合成器不存在而失败。
- [ ] 实现 `compose_layers()`，在存在校验错误时拒绝输出。
- [ ] 再次运行测试，确认排序和 Alpha 合成通过。

### 任务 4：CLI 与文档

- [ ] 编写 `validate` 成功/失败退出码及 `compose` 输出文件的集成测试。
- [ ] 运行 `pytest tests/integration/test_cli.py -q`，确认因入口不存在而失败。
- [ ] 实现 `openchibirig validate` 和 `openchibirig compose`，并在 README 添加用法。
- [ ] 再次运行集成测试，确认命令行为稳定。

### 任务 5：仓库整理与发布前验证

- [ ] 将设定图移动到被 Git 忽略的 `references/private/`，将旧规划文档归档但不删除。
- [ ] 运行 `pytest -q`、`ruff check .`、`python -m build` 和通用性扫描。
- [ ] 检查 `git status` 与 `git diff`，确保私有参考图未进入暂存范围。
- [ ] 配置精确的 GitHub 远程地址，只暂存确认文件，创建首次提交并推送授权分支。
