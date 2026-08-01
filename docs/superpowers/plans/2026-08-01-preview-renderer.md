# 参数化预览渲染实现计划

> **面向 AI 代理的工作者：** 必需子技能：使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 逐任务实现此计划。步骤使用复选框（`- [ ]`）语法来跟踪进度。

**目标：** 用同画布 Alpha 变换生成基础参数预览图。

**架构：** `runtime.preview` 读取有效输入，校验参数范围，对语义图层施加小幅变换后合成 RGBA 输出；CLI 只解析 `name=value` 并写 PNG。

**技术栈：** Python 3.11、Pillow、pytest、ruff。

---

### 任务 1：参数化渲染器

**文件：** `src/openchibirig/runtime/preview.py`、`tests/unit/test_preview_renderer.py`

- [x] 覆盖默认 RGBA 画布、视线/口型变化、未知参数和越界值。
- [x] 实现平移、缩放、旋转和按角色语义选择变换。
- [x] 运行 `.venv/bin/pytest tests/unit/test_preview_renderer.py -q`。

### 任务 2：CLI 与集成验证

**文件：** `src/openchibirig/cli.py`、`tests/integration/test_preview_cli.py`、`README.md`

- [x] 增加 `preview --set name=value --output path`。
- [x] 测试输出 PNG 与错误退出码。
- [x] 运行 `.venv/bin/pytest -q`、`.venv/bin/ruff check .` 和 `.venv/bin/python -m build`。
