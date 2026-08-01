# 输入校验与静态合成设计

## 目标

为 OpenChibiRig 建立首个可运行的端到端切片：读取符合 `INPUT_SPEC_v0.1.md` 的目录输入，输出结构化校验结果，并按 `draw_order` 合成为一张 RGBA 预览图。

## 范围

本切片支持目录输入，不处理 ZIP、PSD、单图拆层、网格、绑定、物理或 GUI。现有亚托莉设定图只作为私有设计参考，不作为有效输入，也不进入公开提交。

## 方案选择

采用“小型领域模型 + 独立校验器 + 无状态合成器 + 薄 CLI”方案。相比把全部逻辑写进 CLI，此方案便于测试和后续复用；相比提前建立插件系统，它更符合当前 YAGNI 原则。

## 组件

- `core.manifest`：加载 JSON，使用打包的 JSON Schema 校验结构，并生成不可变清单对象。
- `validation.input_validator`：检查路径安全、必需角色、文件存在、RGBA8、画布一致性、空图层和关键点边界。
- `validation.diagnostics`：提供稳定诊断代码、严重级别和结构化报告。
- `runtime.compositor`：按 `(draw_order, manifest_index)` 稳定排序并使用 Alpha 合成。
- `cli`：提供 `validate` 与 `compose` 两个命令，不承载业务规则。

## 数据流

```text
输入目录
  → manifest.json / JSON Schema
  → Manifest 领域对象
  → InputValidator / ValidationReport
  → Compositor
  → RGBA PNG 预览
```

## 错误处理

清单无法读取或不符合 Schema 时抛出 `ManifestError`。跨文件问题转换为诊断项：存在 `error` 时 CLI 返回退出码 1；只有 `warning` 或 `info` 时返回 0。`compose` 在校验失败时不得产生输出。

## 测试策略

测试动态创建微型 RGBA 图层，不依赖受版权保护的角色素材。单元测试覆盖清单解析、必需角色、图像模式、画布、空图层和稳定排序；集成测试通过 CLI 完成校验与合成，并检查输出像素和退出码。

## 通用性约束

核心源码不得出现 `atori`、`ATRI` 或具体角色名称。角色差异只能通过清单、图层语义和像素几何表达。
