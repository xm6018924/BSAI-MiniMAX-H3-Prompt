# BSAI MiniMax H3 Prompt - ComfyUI 自定义节点

根据 [MiniMax H3 模型使用手册](https://vrfi1sk8a0.feishu.cn/wiki/FIWjwgL33ipnkekzk30crmKUnIh)，将用户手动输入的提示词自动优化为符合 H3 规范的完整结构化提示词。

## 核心功能

按照 H3 提示词三段公式自动优化：

```
完整提示词 = 参考素材说明 + 核心创意 + 画面过程说明
```

### 节点列表

| 节点名称 | 功能 |
|-|-|
| **BSAI MiniMAX H3 Prompt** | 核心节点：接收用户提示词，输出优化后的 H3 提示词 |
| **BSAI H3 Model Loader** | 加载本地 GGUF 大语言模型（基于 llama-cpp-python） |
| **BSAI H3 Unload Model** | 卸载模型释放显存 |

### 提示词优化覆盖的维度

- **参考素材说明**：13 种素材用途（人物参考、物体参考、场景参考、关键帧、音色参考、故事版、风格参考、构图参考、音频复用、音频部分复用、动作参考、运镜参考、视频编辑）
- **核心创意**：主体、地点、事件、题材/风格、特殊运镜、时长、宽高比
- **画面过程说明**：按时间轴/shot 分段，景别+内容+运镜+动作+台词+音效，想要/不想要
- **三类生成模式**：纯文字生成视频、上传图片生成视频、上传多模态素材融合
- **常见坑位避免**：6 条易错点自动检测与修正

## 安装

### 方式一：手动安装（推荐）

1. 将本仓库克隆或下载到 ComfyUI 的 `custom_nodes` 目录：

```bash
cd ComfyUI/custom_nodes
git clone https://github.com/xm6018924/BSAI-MiniMAX-H3-Prompt.git
```

或手动下载 ZIP 解压到 `ComfyUI/custom_nodes/BSAI-MiniMAX-H3-Prompt/`

2. 安装依赖：

```bash
pip install llama-cpp-python
```

> 如需 GPU 加速，请参考 [llama-cpp-python 安装指南](https://github.com/abetlen/llama-cpp-python#installation-with-hardware-acceleration)

3. 重启 ComfyUI

### 方式二：通过 ComfyUI Manager

在 ComfyUI Manager 中搜索 `BSAI MiniMax H3` 即可安装。

## 使用方法

### 1. 准备模型

下载 GGUF 格式的大语言模型文件（推荐 Qwen3 系列），放到：

```
ComfyUI/models/LLM/
```

如需多模态（视觉理解），还需下载对应的 mmproj 文件放到同一目录。

### 2. 工作流连接

```
BSAI H3 Model Loader ──qwen模型──> BSAI MiniMAX H3 Prompt ──提示词输出──> 视频生成节点
```

### 3. 参数说明

#### BSAI MiniMAX H3 Prompt 节点

| 参数 | 类型 | 说明 |
|-|-|-|
| qwen模型 | 输入 | 连接 BSAI H3 Model Loader 的输出 |
| 用户提示词 | 文本 | 用户手动输入的原始创意描述 |
| 生成模式 | 下拉 | 纯文字生成视频 / 上传图片生成视频 / 上传多模态素材融合 |
| 视频时长 | 整数 | 4-15 秒（H3 支持） |
| 宽高比 | 下拉 | 21:9 / 16:9 / 4:3 / 1:1 / 3:4 / 9:16 |
| 不需要背景音乐 | 布尔 | 勾选后自动添加「非叙事性音乐：N/A」 |
| 补充要求 | 文本 | 可选的额外风格偏好 |
| 最大生成token | 整数 | 默认 4096，自动限制不超过上下文长度 |
| 温度 | 浮点 | LLM 采样温度（0.0-2.0） |
| top_p | 浮点 | 核采样概率（0.0-1.0） |
| seed | 整数 | 随机种子 |
| 图片1~5 | 可选输入 | 最多支持5张参考图片，发送给视觉模型分析后融入提示词 |

#### BSAI H3 Model Loader 节点

| 参数 | 类型 | 说明 |
|-|-|-|
| 模型系列 | 下拉 | Qwen3-VL / Qwen3.5-VL / Qwen3.6-VL / Gemma4 |
| 主模型 | 下拉 | 从 models/LLM/ 目录中选择的模型文件 |
| 视觉投影mmproj | 下拉 | 多模态需要；纯文本可选「无」 |
| 上下文长度 | 整数 | 建议 16384 以上 |
| GPU层数 | 整数 | -1=全部上GPU；显存不足时自动降低层数防止崩溃 |

### 稳定性机制

本节点内置多重防护，确保在各种显存条件下稳定运行：

- **VRAM 自动检测**：加载模型前检测可用显存，不足时自动降低 GPU 层数并提示
- **Flash Attention**：自动检测并启用，减少显存占用
- **max_tokens 安全限制**：根据上下文长度和提示词长度自动限制生成 token 数，防止溢出
- **参数精简**：仅传递核心参数（max_tokens/temperature/top_p/seed），避免 C++ 层段错误

### 4. 使用示例

在「用户提示词」中输入简单描述：

```
一个穿汉服的女子在樱花庭院里舞剑
```

优化后输出：

```
【核心创意】
一位穿汉服的年轻女子在樱花纷飞的庭院里舞剑，古典国风，电影质感，10秒，16:9横版。

【画面过程描述】
0-3 秒：全景，女子从画面左侧缓步走入樱花庭院，背景虚化，没有对白，只有脚步声。
3-8 秒：切镜到女子的中景，她拔出长剑，缓缓起势，樱花瓣从树上飘落。镜头推进。
8-10 秒：切镜到特写，剑光一闪，慢动作，樱花被剑气激得四散。
```

## 支持的模型

推荐使用以下 GGUF 模型（需放到 `ComfyUI/models/LLM/`）：

- **Qwen3.6-VL**（推荐）— 多模态，需配 mmproj
- **Qwen3.5-VL** — 多模态，需配 mmproj
- **Qwen3-VL** — 多模态，需配 mmproj
- **Gemma4** — 多模态，需配 mmproj，需 llama-cpp-python 0.3.36+

## 技术细节

### 系统提示词结构

节点内置的系统提示词严格遵循 H3 使用手册，包含：

1. **提示词整体公式**：三段结构定义
2. **四要素详解**：参考素材说明（13 种用途）、核心创意（6 要素）、画面过程说明（想要/不想要/写作原则）
3. **镜头拆分建议**：shot 对齐、跨 shot 台词、画内外说话人
4. **三类生成模式**：纯文字、图生视频、多模态融合
5. **常见坑位避免**：6 条易错点
6. **输出要求**：8 条格式约束

### H3 模型参数参考

| 参数 | H3 规格 |
|-|-|
| 输出时长 | 4-15 秒 |
| 输出宽高比 | 21:9 / 16:9 / 4:3 / 1:1 / 3:4 / 9:16 |
| 分辨率 | 768p / 1440p |
| 输出帧率 | 24 FPS |
| 输出声音 | 原生双声道 |
| 提示词字数上限 | 7000 字符 |
| 语言支持 | 多语言（TTS 精准覆盖 11 种） |

## 许可证

MIT License

## 致谢

- 提示词规范来源：[MiniMax H3 模型使用手册](https://vrfi1sk8a0.feishu.cn/wiki/FIWjwgL33ipnkekzk30crmKUnIh)
- 模型推理：[llama-cpp-python](https://github.com/abetlen/llama-cpp-python)
- 平台：[ComfyUI](https://github.com/comfyanonymous/ComfyUI)
