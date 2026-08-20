# OpenChibiRig

面向正面 Q 版角色立绘的开源自动拆层与基础绑定工具。

项目当前处于需求定义与技术验证阶段。v0.1 先处理规范化分层 PSD 或 PNG 图层目录，验证输入校验、自动网格、基础绑定、实时预览和工程保存链路；单张立绘自动拆层计划在 v0.2 接入。

## 当前文档

- [项目规划](./PROJECT_PLAN_v0.1.md)
- [输入规范](./INPUT_SPEC_v0.1.md)

## 开发环境

项目需要 Python 3.11 或更高版本。建议在独立虚拟环境中安装：

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[dev]'
```

## 首个可运行切片

校验符合 v0.1 规范的目录输入：

```bash
.venv/bin/openchibirig validate path/to/character
```

按 `draw_order` 生成静态 RGBA 预览：

```bash
.venv/bin/openchibirig compose path/to/character --output outputs/preview.png
```

生成运行时无关的基础绑定项目：

```bash
.venv/bin/openchibirig rig path/to/character --output outputs/project.json
```

该命令目前生成参数与动作声明，包括眨眼、口型、视线、呼吸、头部倾斜和头发摆动能力；它还不会执行真正的网格变形。

按参数生成预览图：

```bash
.venv/bin/openchibirig preview path/to/character \
  --set gaze.x=0.5 \
  --set mouth.open=0.8 \
  --set breath=0.4 \
  --set head.tilt=0.2 \
  --output outputs/motion-preview.png
```

该预览使用图层级平移、缩放和旋转验证参数链路。它不是最终的网格变形渲染器，粗糙蒙版产生的接缝需要在人工修层后重新检查。

See-through PSD 导入（可选）：

```bash
pip install -e '.[psd]'
.venv/bin/openchibirig import-psd path/to/see-through-output.psd \
  --output references/private/atori-see-through
.venv/bin/openchibirig validate references/private/atori-see-through
```

该命令只负责将分层 PSD 标准化为 `manifest.json` 和 RGBA PNG 图层，不在本项目内运行 See-through 推理，也不保证直接得到可商用的 Live2D 模型。无法识别的 PSD 图层会保留为 `custom.*` 并显示警告；缺少基础动作角色时会生成隐藏透明占位层，仍需人工检查和修层。

当前实现的标准运行输入是图层目录；ZIP、单图拆层、网格和绑定仍不在本切片范围内。PSD 需要先通过可选的 `import-psd` 适配器转换。

## 设计原则

- 只承诺处理符合规范的正面 Q 版角色；
- 亚托莉是首个测试角色，不是专用架构；
- 核心数据模型与具体角色、商业运行时和导出格式解耦；
- 自动生成基础模型，保留人工检查和修正入口；
- 素材、模型权重和源码许可证分别管理。

## 仓库结构

```text
src/openchibirig/        Python 核心包
tests/                   单元、集成与测试夹具
schemas/                 开放数据格式的 JSON Schema
examples/                可公开分发的输入示例
docs/                    设计与实现记录
```

## 状态

当前仓库已提供输入校验与静态图层合成。拆层、网格和绑定尚未实现。
