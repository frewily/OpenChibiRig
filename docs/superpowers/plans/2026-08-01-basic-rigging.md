# 基础绑定原型实现计划

> **面向 AI 代理的工作者：** 必需子技能：使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 逐任务实现此计划。步骤使用复选框（`- [ ]`）语法来跟踪进度。

**目标：** 从有效分层清单生成运行时无关的 `project.json` 参数与动作模板。

**架构：** `core.project` 定义不可变项目模型，`rigging.template` 根据图层语义生成能力和动作，`project_writer` 负责 JSON 序列化。CLI 只负责加载、生成和写文件。

**技术栈：** Python 3.11、dataclasses、JSON、pytest、ruff。

---

## 文件结构

- 创建：`src/openchibirig/core/project.py`，项目、参数、动作和能力模型。
- 创建：`src/openchibirig/rigging/template.py`，通用基础绑定模板。
- 创建：`src/openchibirig/rigging/project_writer.py`，生成和保存 `project.json`。
- 修改：`src/openchibirig/cli.py`，增加 `rig` 子命令。
- 修改：`src/openchibirig/rigging/__init__.py`、`src/openchibirig/core/__init__.py`，导出公共接口。
- 创建：`tests/unit/test_rigging_template.py`，能力和动作测试。
- 创建：`tests/integration/test_rig_cli.py`，CLI 生成测试。

### 任务 1：领域模型与模板测试

- [ ] 编写有效角色生成 6 个基础参数、动作能力降级和稳定字段顺序测试。
- [ ] 运行 `pytest tests/unit/test_rigging_template.py -q`，确认因模块不存在而失败。
- [ ] 实现不可变 `Project`、`ParameterSpec`、`MotionSpec` 和模板生成器。
- [ ] 再次运行单元测试，确认通过。

### 任务 2：项目写入器

- [ ] 编写 UTF-8 JSON 写入和错误输入拒绝测试。
- [ ] 运行 `pytest tests/unit/test_project_writer.py -q`，确认因模块不存在而失败。
- [ ] 实现 `build_project()` 与 `write_project()`，拒绝含校验错误的输入并保留警告。
- [ ] 再次运行单元测试，确认通过。

### 任务 3：CLI 与文档

- [ ] 编写 `rig <input> --output <project.json>` 的成功和失败退出码测试。
- [ ] 运行 `pytest tests/integration/test_rig_cli.py -q`，确认因命令不存在而失败。
- [ ] 实现 CLI 子命令并更新 README 的使用示例。
- [ ] 运行 `pytest -q`、`ruff check .` 和 `python -m build`。
