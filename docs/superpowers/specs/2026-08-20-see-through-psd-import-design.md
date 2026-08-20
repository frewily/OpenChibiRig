# See-through PSD 导入适配器设计

## 目标

为 OpenChibiRig 增加一个可选的 PSD 导入适配器，将 See-through 生成的分层 PSD 转换为 OpenChibiRig 的标准输入目录：`manifest.json` 加 RGBA PNG 图层。该适配器只负责格式转换和语义映射，不在 OpenChibiRig 内部运行 See-through 的重型推理模型。

## 背景与范围

See-through 可以从单张动漫立绘生成带透明补全区域和绘制顺序的分层 PSD。OpenChibiRig 当前的校验器、静态合成器和预览器则要求 `manifest.json` 与同画布 RGBA PNG 图层目录。两者之间缺少稳定的格式边界。

本切片包含：

- 读取标准 PSD 文件；
- 提取可见和不可见图层的像素、名称、顺序与画布尺寸；
- 将图层导出为同尺寸 RGBA PNG；
- 按图层名称映射 OpenChibiRig 标准角色语义；
- 为无法识别的图层生成 `custom.*` 角色并提供警告；
- 生成可被现有 `validate`、`compose` 和 `preview` 使用的 `manifest.json`；
- 通过 CLI 提供导入命令。

本切片不包含：

- See-through 模型推理、权重下载或 CUDA 运行时；
- Live2D 网格、参数绑定或物理生成；
- 自动修复导入结果中的艺术性接缝；
- 将任何亚托莉专用规则写入核心代码。

## 方案

新增 `openchibirig import-psd` 命令。适配器使用可选的 `psd-tools` 依赖读取 PSD；核心安装不强制安装重型 See-through 依赖。导入器接收输入 PSD 和不存在的输出目录，成功时创建完整目录，若输出目录已存在则拒绝执行，避免覆盖人工修层结果。

```text
See-through PSD
        │
        ▼
PSD 导入器
        │  读取图层名称、顺序、可见性、RGBA 像素
        ▼
语义映射器
        │  已知名称 → 标准 role；未知名称 → custom.* + warning
        ▼
manifest.json + layers/*.png
        │
        ▼
现有 validate / compose / preview
```

## 输出约定

```text
output/
├── manifest.json
└── layers/
    ├── 010_front_hair.png
    ├── 020_face.png
    ├── 030_eye_left_white.png
    └── ...
```

- PSD 画布尺寸写入 `manifest.canvas`；
- 输出 PNG 始终为 RGBA，并保留完整画布尺寸，不按图层边界裁剪；
- `draw_order` 按 PSD 从底到顶的合成顺序生成，使用稳定的 10 为步长；
- 文件名使用序号、规范化图层 ID 和 `.png` 后缀；
- `character_id` 由输出目录名称生成，`display_name` 使用 PSD 文件名；
- `license.redistribution` 默认写为 `unconfirmed`，不推断用户素材版权。

## 语义映射

映射器采用大小写不敏感的规范化匹配，并保留原始图层名称用于诊断。第一版覆盖 See-through 常见命名：

| 图层名称关键词 | 标准角色 |
|---|---|
| `front hair`、`hair front`、`hairf` | `hair.front` |
| `back hair`、`hair back`、`hairb` | `hair.back` |
| `face`、`head` | `face.base` |
| `eyewhite`、`eye white`、`eyebg` | `eye.<side>.white` 或 `eye.base.white` |
| `iris`、`irides` | `eye.<side>.iris` 或 `eye.base.iris` |
| `eyelash`、`eyelid` | `eye.<side>.lid.upper` 或 `eye.base.lid` |
| `mouth` | `mouth.base` |
| `topwear`、`clothes`、`服装` | `clothes.main` |
| `body`、`skin` | `body.base` |

无法识别的名称使用 `custom.<slug>`，并在 CLI 输出中列出警告。适配器不得因未知图层而丢弃像素。

## 错误处理

导入失败时不创建半成品输出目录，并返回非零退出码。以下情况必须报告清晰错误：

- 输入文件不存在或不是 `.psd`；
- PSD 无法解析；
- PSD 没有有效画布；
- 输出目录已存在；
- 图层像素无法转换为 RGBA。

未知图层名称不是错误，而是警告。导入完成后，适配器可以调用现有输入校验器做最终检查；校验失败时保留输出目录，便于用户查看诊断。

## 测试策略

- 使用测试夹具生成最小 PSD，避免提交版权不明的角色素材；
- 单元测试覆盖名称规范化、标准语义映射、未知图层警告和稳定排序；
- 集成测试覆盖 PSD 导入 CLI、输出目录结构、RGBA 图像尺寸和现有 `validate` 兼容性；
- 回归测试确认现有 24 项测试继续通过；
- 不在测试中下载 See-through 模型或执行 GPU 推理。

## 后续边界

导入适配器完成后，可以用 See-through 在线演示生成亚托莉 PSD，再在本地转换并检查预览质量。只有在 PSD 到标准目录的边界稳定后，才评估人工蒙版编辑器和真实网格绑定的实现。
