# 基础绑定原型设计

## 目标

将已通过 v0.1 输入校验的分层角色目录转换为运行时无关的 `project.json`，并生成可供后续预览器消费的基础参数、动作和能力声明。

## 范围

本切片生成数据与模板，不实现网格、纹理变形、物理模拟、摄像头驱动或 GUI。生成器必须对任意符合输入规范的角色工作，不能读取角色名称或使用亚托莉专用分支。

## 数据模型

```text
Manifest
  → Project
     ├── layers（带角色语义与绘制顺序）
     ├── parameters（参数范围与默认值）
     ├── motions（待机/眨眼/口型等动作声明）
     └── capabilities（由可用角色推导的能力）
```

参数使用 `id`、`min`、`max`、`default` 和 `group`；动作使用 `id`、`kind`、`parameter` 和 `enabled`。`enabled=false` 表示输入缺少所需部件，预览器应跳过该动作而不是崩溃。

## 默认能力

- 始终生成 `head.tilt`、`breath` 和 `idle` 声明；
- 左右眼白、虹膜和上眼皮齐全时启用 `blink` 与 `gaze`；
- 存在 `mouth.base` 时启用 `mouth_open`；
- 存在 `hair.front`、`hair.back` 或侧发时启用 `hair_sway`；
- 当前只声明动作，不改变 PNG 像素。

## 错误处理与验证

生成器必须拒绝包含校验错误的输入，并保留校验警告。输出 JSON 使用稳定排序和 UTF-8 编码，便于版本控制。测试覆盖有效输入、能力降级、稳定序列化和错误输入拒绝。
