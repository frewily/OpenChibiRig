# OpenChibiRig 输入规范（v0.1 草案）

> 文档状态：可评审草案
> 规范版本：v0.1
> 更新日期：2026-08-01
> 适用阶段：Milestone 0 与 Milestone 1

## 1. 目的

本规范定义 OpenChibiRig v0.1 可接受的分层角色输入。目标是让导入、校验、自动绑定和测试使用同一套明确契约，避免核心逻辑依赖某个角色的文件名、外观或身体比例。

v0.1 只接收已经分层的角色素材，不负责从单张立绘自动拆层。单图拆层属于 v0.2，输出仍应转换为本规范后再进入绑定流程。

## 2. 规范用语

本文使用以下约束词：

- **必须：** 不满足时输入无效；
- **应当：** 强烈建议满足，不满足时校验器给出警告；
- **可以：** 可选能力，不影响基础输入是否合法。

所有“左”和“右”均以角色自身方向为准。正面角色的 `left_eye` 通常出现在观看者画面的右侧。

## 3. 支持的输入载体

v0.1 支持：

1. 包含 `manifest.json` 与透明 PNG 图层的目录；
2. 保持相同目录结构的 ZIP 文件；
3. 可解析图层名称和像素内容的分层 PSD / PSB。

目录和 ZIP 是规范基准。PSD / PSB 导入器必须将内容归一化为同一清单模型；遇到不支持的剪贴蒙版、智能对象、图层效果或混合模式时，应报告明确诊断信息，不能静默丢失效果。

## 4. 输入包结构

```text
character/
├── manifest.json
└── layers/
    ├── 010_back_hair.png
    ├── 020_body.png
    ├── 030_clothes.png
    ├── 040_face.png
    ├── 050_left_eye_white.png
    ├── 060_left_iris.png
    ├── 070_left_upper_eyelid.png
    ├── 080_right_eye_white.png
    ├── 090_right_iris.png
    ├── 100_right_upper_eyelid.png
    ├── 110_left_eyebrow.png
    ├── 120_right_eyebrow.png
    ├── 130_mouth.png
    ├── 140_front_hair.png
    ├── 150_left_side_hair.png
    └── 160_right_side_hair.png
```

要求如下：

- 根目录必须包含且只包含 1 个 `manifest.json`；
- 图层文件应放在 `layers/` 下；
- 路径必须使用 `/` 分隔，并相对于输入包根目录；
- ZIP 不得包含绝对路径、`..` 路径段或指向包外部的符号链接；
- 文件名建议使用小写 ASCII、数字、下划线、连字符和扩展名；
- 不得依赖文件系统遍历顺序决定绘制顺序。

## 5. 图像要求

### 5.1 格式与色彩

每个图层必须满足：

- 文件格式为 PNG；
- 像素格式为 RGBA；
- 颜色通道为 8 bit；
- 使用 sRGB 色彩空间；
- 透明区域的 Alpha 值为 0；
- 图像可以无损解码，且不得设置密码或外部资源引用。

首版不接受索引色 PNG、灰度图、16 bit 通道、浮点通道、JPEG 图层或仅通过颜色键表示透明的素材。

### 5.2 画布与坐标系

- 所有 PNG 图层必须与 `canvas.width`、`canvas.height` 完全相同；
- 坐标原点位于画布左上角；
- X 轴向右为正，Y 轴向下为正；
- 像素坐标使用整数，几何计算可以使用浮点数；
- 归一化坐标范围为 `[0.0, 1.0]`；
- 每个图层必须保留其在完整画布中的位置，不得单独裁切后丢失偏移信息。

首版建议画布长边不超过 4096 px。超过该尺寸的输入可以被接受，但校验器应给出性能警告。

### 5.3 图层内容

- 每个声明为可见的图层必须至少包含 1 个 Alpha 大于 0 的像素；
- 图层边缘应保留抗锯齿 Alpha，不应预先合成到纯色背景；
- 需要变形的部件应保留被相邻部件遮挡的合理重叠区域；
- 发丝、眼皮、嘴部和衣摆不应只保留最终可见的狭窄切片；
- 无法补全的遮挡区域应在 `notes` 或质量报告中说明，不能用透明空洞冒充完整素材。

## 6. 角色构图要求

v0.1 的自动绑定仅保证处理以下构图：

- Q 版或接近 Q 版的二次元角色；
- 正面或接近正面，脸部偏航角建议不超过约 15°；
- 全身或大部分身体可见；
- 中性站姿；
- 五官清晰可辨；
- 双手不严重遮挡面部；
- 四肢不大面积交叉；
- 头发、脸、身体和衣服边界相对清晰；
- 不包含强烈俯视、仰视或透视缩短。

不满足这些条件不一定导致文件格式无效，但校验器应标记为超出 v0.1 自动绑定的保证范围。

## 7. 图层语义

### 7.1 角色命名

`role` 使用点分层级名称。核心模块根据 `role` 处理语义，不得根据角色名或具体文件名硬编码行为。

基础角色如下：

| `role` | 含义 | 基础输入 | 典型用途 |
|---|---|---:|---|
| `hair.back` | 后发 | 建议 | 头发物理、头部层级 |
| `body.base` | 身体基础 | 必须 | 身体层级与呼吸 |
| `clothes.main` | 主要服装 | 建议 | 呼吸、身体摆动 |
| `face.base` | 脸部底图 | 必须 | 面部变形与五官容器 |
| `eye.left.white` | 左眼眼白 | 必须 | 眼球与眼皮遮罩 |
| `eye.left.iris` | 左眼瞳孔 / 虹膜 | 必须 | 视线移动 |
| `eye.left.lid.upper` | 左上眼皮 | 必须 | 眨眼 |
| `eye.right.white` | 右眼眼白 | 必须 | 眼球与眼皮遮罩 |
| `eye.right.iris` | 右眼瞳孔 / 虹膜 | 必须 | 视线移动 |
| `eye.right.lid.upper` | 右上眼皮 | 必须 | 眨眼 |
| `brow.left` | 左眉 | 建议 | 表情扩展 |
| `brow.right` | 右眉 | 建议 | 表情扩展 |
| `mouth.base` | 基础嘴部 | 必须 | 嘴巴开合 |
| `hair.front` | 前发 | 建议 | 头发物理、脸部遮挡 |
| `hair.side.left` | 左侧发 | 可选 | 独立头发物理 |
| `hair.side.right` | 右侧发 | 可选 | 独立头发物理 |

### 7.2 扩展角色

以下前缀保留给常见扩展：

- `arm.left.*`、`arm.right.*`；
- `leg.left.*`、`leg.right.*`；
- `hand.left.*`、`hand.right.*`；
- `foot.left.*`、`foot.right.*`；
- `mouth.inner`、`mouth.teeth`、`mouth.tongue`；
- `eye.left.highlight`、`eye.right.highlight`；
- `accessory.*`；
- `clothes.skirt.*`、`clothes.ribbon.*`；
- `effect.*`。

未知角色必须使用 `custom.<vendor-or-project>.<name>` 命名。导入器必须保留未知角色，不得擅自删除；自动绑定器可以跳过并发出提示。

### 7.3 唯一性

- 每个图层 `id` 在清单内必须唯一；
- 单值基础角色在同一输入中只能出现 1 次；
- 可重复语义必须使用更具体的后缀，例如 `accessory.hairpin.01`；
- 左右对称部件不得共用同一图层文件。

## 8. 绘制顺序

`draw_order` 是有符号整数，数值越小越先绘制，数值越大越靠近观看者。

- 每个图层必须声明 `draw_order`；
- 不要求连续，但建议以 10 为步长，便于插入图层；
- 相同 `draw_order` 合法，但不建议使用；若出现，导入器以清单顺序作为稳定的次级排序；
- 清单顺序不能替代 `draw_order`；
- 绘制顺序应能在参数默认值下还原原始角色外观。

## 9. 锚点与关键点

### 9.1 图层锚点

`anchor` 是图层局部变换的建议中心，使用完整画布像素坐标 `[x, y]`。

- 锚点可以省略；
- 省略时，系统可以根据非透明像素包围盒和图层语义推断；
- 手工提供的锚点必须位于画布范围内；
- 头发锚点通常位于发根，眼球锚点通常位于瞳孔中心。

### 9.2 角色级关键点

`landmarks` 使用稳定名称映射到 `[x, y]`。v0.1 可以提供：

- `eye.left.center`；
- `eye.right.center`；
- `mouth.center`；
- `head.top`；
- `chin.center`；
- `shoulder.left`；
- `shoulder.right`；
- `hip.center`。

关键点可以由输入提供，也可以后续推断。提供时必须位于画布范围内，并遵守角色自身左右方向约定。

## 10. `manifest.json`

### 10.1 顶层字段

| 字段 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| `spec_version` | string | 是 | 固定为 `0.1` |
| `character_id` | string | 是 | 输入包内稳定、与显示名解耦的标识符 |
| `display_name` | string | 是 | 用户界面显示名称 |
| `canvas` | object | 是 | 画布尺寸与色彩空间 |
| `orientation` | object | 是 | 视角和左右方向约定 |
| `layers` | array | 是 | 非空图层列表 |
| `landmarks` | object | 否 | 角色级关键点 |
| `license` | object | 否 | 素材来源和再分发状态 |
| `notes` | array | 否 | 对遮挡、缺失或特殊处理的说明 |

### 10.2 完整示例

```json
{
  "$schema": "schemas/input-manifest.schema.json",
  "spec_version": "0.1",
  "character_id": "sample_chibi_001",
  "display_name": "Sample Chibi",
  "canvas": {
    "width": 2048,
    "height": 2048,
    "color_space": "srgb"
  },
  "orientation": {
    "view": "front",
    "left_right_basis": "character"
  },
  "layers": [
    {
      "id": "back_hair",
      "role": "hair.back",
      "path": "layers/010_back_hair.png",
      "draw_order": 10,
      "anchor": [1024, 520]
    },
    {
      "id": "body",
      "role": "body.base",
      "path": "layers/020_body.png",
      "draw_order": 20,
      "anchor": [1024, 1320]
    },
    {
      "id": "face",
      "role": "face.base",
      "path": "layers/040_face.png",
      "draw_order": 40,
      "anchor": [1024, 620]
    }
  ],
  "landmarks": {
    "eye.left.center": [1100, 650],
    "eye.right.center": [948, 650],
    "mouth.center": [1024, 785]
  },
  "license": {
    "redistribution": "allowed",
    "source": "https://example.invalid/sample-license"
  },
  "notes": []
}
```

机器可读约束见 [schemas/input-manifest.schema.json](./schemas/input-manifest.schema.json)。Schema 负责结构和基本类型校验，图像尺寸、Alpha、角色集合与路径安全等跨文件规则由输入校验器负责。

## 11. PSD / PSB 映射

PSD / PSB 导入遵循以下规则：

- 可见像素必须按文档画布尺寸导出为完整画布 PNG；
- 图层组用于组织，不自动成为可绘制图层；
- 图层名称可以使用 `NNN_role_name`，也可以通过同目录清单覆盖；
- 默认使用 Photoshop 自下而上的图层顺序生成递增 `draw_order`；
- 隐藏图层默认不导入，除非清单显式声明；
- 调整图层、智能对象、矢量蒙版、剪贴蒙版和特殊混合模式需要栅格化或报告不支持；
- 栅格化结果必须与 Photoshop 中的默认合成结果进行视觉比对。

## 12. 校验结果

校验器输出 3 个级别：

- `error`：输入无效，不能进入自动绑定；
- `warning`：输入可以继续，但可能降低质量或超出保证范围；
- `info`：归一化、推断或兼容性提示。

每条诊断必须包含稳定代码、严重级别、可读消息和相关文件或字段路径。例如：

```json
{
  "code": "IMG_CANVAS_MISMATCH",
  "severity": "error",
  "message": "图层尺寸为 1024×2048，与清单画布 2048×2048 不一致。",
  "location": "layers/070_left_upper_eyelid.png"
}
```

首批稳定诊断代码建议包括：

| 代码 | 级别 | 含义 |
|---|---|---|
| `MANIFEST_INVALID` | error | 清单不符合 Schema |
| `PATH_UNSAFE` | error | 路径越界、绝对路径或不安全链接 |
| `LAYER_FILE_MISSING` | error | 声明的图层文件不存在 |
| `LAYER_ID_DUPLICATE` | error | 图层 ID 重复 |
| `ROLE_REQUIRED_MISSING` | error | 基础角色缺失 |
| `ROLE_SINGLETON_DUPLICATE` | error | 单值角色重复 |
| `IMG_NOT_RGBA8` | error | 图像不是 RGBA 8 bit |
| `IMG_CANVAS_MISMATCH` | error | 图像尺寸与画布不一致 |
| `IMG_EMPTY` | error | 可见图层没有非透明像素 |
| `DRAW_ORDER_TIE` | warning | 多个图层绘制顺序相同 |
| `CANVAS_LARGE` | warning | 画布超过首版建议尺寸 |
| `ROLE_UNKNOWN` | warning | 自动绑定器不认识该角色 |
| `LANDMARK_OUT_OF_BOUNDS` | error | 关键点超出画布 |
| `LICENSE_UNCONFIRMED` | warning | 素材再分发授权未确认 |

## 13. 能力降级

输入合法不代表所有动作都能生成。校验器应同时报告能力矩阵：

- 缺少左右眼白或瞳孔：不能生成可靠的眼球移动；
- 缺少任一上眼皮：不能生成标准眨眼；
- 嘴部只有单一扁平图层：只能生成基础缩放或网格开合；
- 缺少独立头发图层：不能生成头发物理；
- 缺少衣摆或丝带图层：跳过对应物理；
- 缺少关键点：允许自动推断，但应降低置信度并提示检查。

能力降级必须以结构化结果返回，不能因为某个可选动作不可用而让整个导入失败。

## 14. 素材与许可证

- 测试素材必须记录作者、来源和使用范围；
- `redistribution` 使用 `allowed`、`prohibited` 或 `unconfirmed`；
- `prohibited` 或 `unconfirmed` 的原始素材不得提交到公开仓库；
- 模型训练许可与示例素材再分发许可必须分开记录；
- 亚托莉测试素材未确认再分发授权前，只能保存在本地且不得进入公开历史。

## 15. 通用性要求

为防止架构写死为亚托莉专用，所有实现必须遵守：

- 核心包不出现角色名称判断；
- 角色差异只通过清单、图层语义、关键点、轮廓和模板参数表达；
- 自动绑定规则使用 `role` 与几何特征，不使用固定文件名；
- 测试至少包含 1 个亚托莉夹具和 1 个可公开分发的通用夹具；
- Milestone 1 验收至少覆盖 3 个不同 Q 版角色；
- 任何为单个角色增加的例外，都必须先抽象成可配置且可测试的通用规则。

## 16. v0.1 验收清单

输入规范可进入冻结状态前，必须确认：

- [ ] 目录与 ZIP 对同一输入产生相同的归一化清单；
- [ ] JSON Schema 能拒绝缺少必填字段和非法路径格式的清单；
- [ ] 校验器检查 PNG 格式、画布、Alpha 和空图层；
- [ ] 左右方向使用角色自身方向，并有自动化测试；
- [ ] 绘制顺序能稳定还原原始角色；
- [ ] 缺少可选部件时返回能力降级，而不是异常终止；
- [ ] PSD 导入不会静默忽略不支持的特性；
- [ ] 亚托莉和通用角色使用同一导入与校验代码路径；
- [ ] 所有测试素材都有明确许可证状态。

## 17. 后续版本

不在 v0.1 规范内的能力包括：

- 单张 PNG / JPEG 自动拆层；
- 多套服装和表情切换；
- 复杂嘴型集合；
- 大角度头部旋转；
- 自定义混合模式与非破坏性 PSD 效果；
- Cubism 专用工程输入或输出。

这些能力需要新版本字段或独立扩展规范，不得通过破坏 v0.1 兼容性的方式加入。
