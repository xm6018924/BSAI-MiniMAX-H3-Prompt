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
| **BSAI MiniMAX H3 Prompt** | 核心节点：使用本地模型，接收用户提示词，输出优化后的 H3 提示词 |
| **BSAI H3 Model Loader** | 加载本地 GGUF 大语言模型（基于 llama-cpp-python） |
| **BSAI H3 Unload Model** | 卸载模型释放显存 |
| **BSAI H3 Remote API** | 远程 API 调用：通过 OpenAI/DashScope 兼容接口优化提示词，无需本地模型 |

### 两种使用模式

| 模式 | 节点组合 | 显存占用 | 适用场景 |
|-|-|-|-|
| **本地模型模式** | Model Loader + H3 Prompt + Unload Model | 高（需加载 GGUF 模型） | 离线环境、隐私敏感、无 API 额度 |
| **远程 API 模式** | H3 Remote API（独立使用） | 零（不加载本地模型） | 节省显存给视频生成、使用更强云端模型 |

### 提示词优化覆盖的维度

- **参考素材说明**：13 种素材用途（人物参考、物体参考、场景参考、关键帧、音色参考、故事版、风格参考、构图参考、音频复用、音频部分复用、动作参考、运镜参考、视频编辑）
- **核心创意**：主体、地点、事件、题材/风格、特殊运镜、时长、导演风格、摄影风格、电影类型、切镜类型、配乐风格
- **画面过程说明**：按时间轴/shot 分段，景别+内容+运镜+动作+台词+音效，想要/不想要
- **五类生成模式**：纯文字生成视频(T2VA)、图片生成视频(I2VA)、首尾帧生成(FL2VA)、尾帧生成(L2VA)、多模态素材融合(Ref2VA)，系统推荐根据输入自动判断
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
# 本地模型模式（必需）
pip install llama-cpp-python

# 远程 API 模式（必需）
pip install requests
```

> 如需 GPU 加速，请参考 [llama-cpp-python 安装指南](https://github.com/abetlen/llama-cpp-python#installation-with-hardware-acceleration)

3. 重启 ComfyUI

### 方式二：通过 ComfyUI Manager

在 ComfyUI Manager 中搜索 `BSAI MiniMax H3` 即可安装。

## 使用方法

### 模式一：本地模型

#### 1. 准备模型

下载 GGUF 格式的大语言模型文件（推荐 Qwen3 系列），放到：

```
ComfyUI/models/LLM/
```

如需多模态（视觉理解），还需下载对应的 mmproj 文件放到同一目录。

#### 2. 工作流连接

```
BSAI H3 Model Loader ──qwen_model──> BSAI MiniMAX H3 Prompt ──prompt_output──> 视频生成节点
                                         |
                                   (可选) image_1~10
                                         |
                                   (可选) video_1~4
                                         |
                                   (可选) audio_1~3
```

### 模式二：远程 API

无需加载本地模型，直接调用云端 LLM API 进行提示词优化，将显存全部留给视频生成。

#### 1. 工作流连接

```
BSAI H3 Remote API ──prompt_output──> 视频生成节点
      |
 (可选) image_1~10
      |
 (可选) video_1~4
      |
 (可选) audio_1~3
```

> 该节点为独立节点，不需要连接 Model Loader，不占用任何显存。

#### 2. 配置 API

在节点参数中填写：

| 参数 | 说明 |
|-|-|
| **api_base_url** | API 基础地址（不含 `/chat/completions` 后缀） |
| **api_key** | 你的 API 密钥 |
| **model_name** | 调用的模型名称 |

#### 3. 支持的 API 服务商

| 服务商 | api_base_url | 推荐模型 | 多模态 |
|-|-|-|-|
| **DashScope（阿里云）** | `https://dashscope.aliyuncs.com/compatible-mode/v1` | qwen-plus, qwen-max, qwen-vl-plus | qwen-vl-plus |
| **OpenAI** | `https://api.openai.com/v1` | gpt-4o, gpt-4o-mini, gpt-4-turbo | gpt-4o, gpt-4o-mini |
| **Ollama（本地）** | `http://localhost:11434/v1` | qwen2.5:14b, llama3:8b 等 | 视模型而定 |
| **LM Studio** | `http://localhost:1234/v1` | 已加载的模型 | 视模型而定 |
| **vLLM** | `http://localhost:8000/v1` | 部署的模型 | 视模型而定 |
| **SiliconFlow** | `https://api.siliconflow.cn/v1` | Qwen/Qwen2.5-72B 等 | 视模型而定 |

> 任何兼容 OpenAI Chat Completions API 格式的服务均可使用。

#### 4. 远程 API 使用示例

以 DashScope qwen-plus 为例：

1. 在 [阿里云 DashScope](https://dashscope.console.aliyun.com/) 获取 API Key
2. 节点参数设置：
   - `api_base_url`: `https://dashscope.aliyuncs.com/compatible-mode/v1`
   - `api_key`: `sk-xxxxxxxxxxxx`
   - `model_name`: `qwen-plus`
3. 在 `user_prompt` 输入提示词，点击生成

使用多模态模型分析图片：

1. 选择支持视觉的模型（如 `qwen-vl-plus` 或 `gpt-4o`）
2. 将 LoadImage 节点输出连接到 `image_1`~`image_10` 端口
3. 输入提示词，模型会同时分析图片和文本

## 参数参考

### BSAI MiniMAX H3 Prompt Node（本地模型）

| Parameter | Type | Description |
|-|-|-|
| qwen_model | Input | Connect to BSAI H3 Model Loader output |
| user_prompt | Text | User's original creative prompt description |
| generation_mode | Dropdown | System Recommended: auto-detects T2VA/I2VA/FL2VA/L2VA/Ref2VA based on connected inputs / 生成模式 |
| video_duration | Int | 0=System Recommended auto-detect; H3 supports 4-15 seconds / 视频时长 |
| output_language | Dropdown | Output description language (default: Chinese). Options: Chinese, English, Japanese, Korean, French, German, Spanish, Russian, Bilingual CN+EN / 输出语言 |
| no_bgm | Bool | If checked, sets non_diegetic_music to N/A (sound effects still generated) |
| extra_requirements | Text | Optional extra style preferences |
| director_style | Dropdown | Director style (default: Official SKILL). Official SKILL: pure H3 SKILL output, no presets; System Recommended: auto-detect; 37+ directors: Hitchcock, Wong Kar-wai, Kubrick, Kurosawa, Nolan, Tarantino, Spielberg, etc. |
| cinematography_style | Dropdown | Cinematography/lighting style (default: Official SKILL). Official SKILL: pure H3 SKILL output, no presets; System Recommended: auto-detect; 20+ cinematographers: Deakins, Lubezki, Storaro, Doyle, Hoyte van Hoytema, etc. |
| film_genre | Dropdown | Film genre/type (default: Official SKILL). Official SKILL: pure H3 SKILL output, no presets; System Recommended: auto-detect; 50+ genres: Realism, Film Noir, Sci-Fi, Wuxia, Ghibli Animation, etc. |
| cut_style | Dropdown | Number of segments/cuts (default: Official SKILL). Official SKILL: pure H3 SKILL output, no presets; 1-15 segments for 15s max video. |
| score_style | Dropdown | Film score/composer style (default: Official SKILL). Official SKILL: pure H3 SKILL output, no presets; System Recommended: auto-detect; 40+ composers: John Williams, Hans Zimmer, Morricone, Hisaishi, Sakamoto, etc. |
| max_tokens | Int | Default 4096, auto-limited to context length |
| temperature | Float | LLM sampling temperature (0.0-2.0) |
| top_p | Float | Nucleus sampling probability (0.0-1.0) |
| top_k | Int | Top-K sampling (0=disabled) |
| repeat_penalty | Float | Repetition penalty (0.5-2.0) |
| frequency_penalty | Float | Frequency penalty (0.0-2.0) |
| presence_penalty | Float | Presence penalty (0.0-2.0) |
| seed | Int | Random seed (0=random) |
| image_1~10 | Optional | Up to 10 reference images sent to vision model for analysis |
| video_1~4 | Optional | Up to 4 reference videos (key frames automatically extracted) |
| audio_1~3 | Optional | Up to 3 reference audio clips (metadata extracted as text reference) |

> **注意**：`top_k`、`repeat_penalty`、`frequency_penalty`、`presence_penalty` 参数仅在 UI 中显示，实际推理时仅传递 `max_tokens`、`temperature`、`top_p`、`seed` 核心参数，以避免 Qwen-VL 模型的 C++ 层段错误。

### BSAI H3 Remote API Node（远程 API）

| Parameter | Type | Default | Description |
|-|-|-|-|
| user_prompt | Text | "" | User's original creative prompt description |
| api_base_url | Text | `https://dashscope.aliyuncs.com/compatible-mode/v1` | OpenAI-compatible API base URL |
| api_key | Text | "" | API key for authentication |
| model_name | Text | `qwen-plus` | Model name (e.g. gpt-4o, qwen-plus, qwen-max, qwen-vl-plus) |
| generation_mode | Dropdown | System Recommended | System Recommended: auto-detects T2VA/I2VA/FL2VA/L2VA/Ref2VA based on connected inputs |
| video_duration | Int | 0 | 0=System Recommended auto-detect; H3 supports 4-15 seconds |
| output_language | Dropdown | Chinese (中文) | Output language: Chinese, English, Japanese, Korean, French, German, Spanish, Russian, Bilingual CN+EN |
| no_bgm | Bool | False | If checked, sets non_diegetic_music to N/A (sound effects still generated) |
| extra_requirements | Text | "" | Optional extra style preferences |
| director_style | Dropdown | Official SKILL (官方SKILL模式) | Official SKILL: pure H3 SKILL output, no presets; System Recommended: auto-detect; Hitchcock, Wong Kar-wai, Kubrick, Kurosawa, Nolan, etc. |
| cinematography_style | Dropdown | Official SKILL (官方SKILL模式) | Official SKILL: pure H3 SKILL output, no presets; System Recommended: auto-detect; Deakins, Lubezki, Storaro, Doyle, etc. |
| film_genre | Dropdown | Official SKILL (官方SKILL模式) | Official SKILL: pure H3 SKILL output, no presets; System Recommended: auto-detect; Realism, Film Noir, Sci-Fi, Wuxia, Ghibli, etc. |
| cut_style | Dropdown | Official SKILL (官方SKILL模式) | Official SKILL: pure H3 SKILL output, no presets; 1 (one shot) to 15 segments |
| score_style | Dropdown | Official SKILL (官方SKILL模式) | Official SKILL: pure H3 SKILL output, no presets; System Recommended: auto-detect; John Williams, Hans Zimmer, Morricone, Hisaishi, etc. |
| max_tokens | Int | 4096 | Max generation tokens |
| temperature | Float | 0.7 | LLM sampling temperature (0.0-2.0) |
| top_p | Float | 0.9 | Nucleus sampling probability (0.0-1.0) |
| seed | Int | 0 | Random seed (0=random, >0=fixed) |
| image_1~10 | Optional | - | Up to 10 reference images (requires multimodal model) |
| video_1~4 | Optional | - | Up to 4 reference videos (key frames automatically extracted) |
| audio_1~3 | Optional | - | Up to 3 reference audio clips (metadata extracted as text reference) |

### BSAI H3 Model Loader Node

| Parameter | Type | Description |
|-|-|-|
| model_family | Dropdown | Qwen3-VL / Qwen3.5-VL / Qwen3.6-VL / Gemma4 |
| model_file | Dropdown | Model file from models/LLM/ directory |
| mmproj | Dropdown | Multimodal mmproj file; 'None' for text-only |
| enable_thinking | Bool | Enable thinking/reasoning mode |
| context_length | Int | Recommend 16384+ |
| gpu_layers | Int | -1=all on GPU; auto-reduces if VRAM insufficient |

## 稳定性机制

本地模型模式内置多重保护机制，确保在不同显存条件下稳定运行：

- **VRAM 自动检测**：加载前检测可用显存，不足时自动降低 GPU 层数
- **Flash Attention**：自动检测并启用，减少显存占用
- **max_tokens 安全限制**：根据上下文长度和提示词大小自动限制生成 token 数
- **最小参数传递**：仅传递核心参数（max_tokens/temperature/top_p/seed），避免 C++ 层段错误
- **模型有效性检测**：推理前检测模型是否已卸载，自动从缓存设置重载
- **推理失败自动恢复**：推理出错时自动重载模型并重试一次

远程 API 模式无需上述机制，由云端服务保障稳定性，内置：
- **超时保护**：120 秒请求超时，避免工作流卡死
- **错误处理**：连接错误、HTTP 错误、JSON 解析错误均有清晰提示
- **多模态支持**：自动检测图片输入，使用 OpenAI 多模态 content 格式

## 提示词输出格式

系统提示词已对齐 [H3 官方 Prompt Writing Guide](https://github.com/MiniMax-AI/MiniMax-H3/tree/main/skills/h3-prompt-writing)，输出严格遵循官方三字段结构：

| 字段 | 说明 |
|-|-|
| `integrated_multimodal_description` | 画面描述：视觉风格、镜头、主体、动作、台词、叙事性声音 |
| `overall_soundscape` | 环境音效（必填）：场景氛围声、人物动作声、物体运动声、背景音效（1-4句）。**禁止静音**，即使安静场景也需包含细微环境声 |
| `non_diegetic_music` | 背景音乐：仅观众可听的音乐描述。仅在用户明确勾选 no_bgm 时填 N/A，否则根据场景氛围生成合适的背景音乐 |

### 官方格式特性

- **时间段分段**：`integrated_multimodal_description` 必须按时间段分段。英文用 `[0-3s]`、`[3-8s]`，中文用 `【0-3秒】`、`【3-8秒】`
- **运镜规范**：Motion Type + Amplitude + Speed（如 `Push In with small amplitude at slow speed`）
- **台词格式**：`(S1) says: <d>[Chinese] 你来了，剑等你好久了。</d>` — 台词保留原始语言
- **画面文字**：可见文字用英文双引号包裹，如 `"营业中"`
- **图片对齐指令**：I2VA/FL2VA/L2VA 模式在首行输出帧对齐指令
- **跨分段台词**：使用 `<scenetrans>` 标记连接点
- **强制音效**：`overall_soundscape` 必须覆盖四类音效（场景氛围声、背景音效、人物动作声、物体运动声），任何场景都不允许静音。即使用户勾选 no_bgm 仅关闭背景音乐，环境音效仍必须输出

### 多语言输出

通过 `output_language` 参数控制输出描述语言（默认中文），可选英文、日文、韩文、法语、德语、西班牙语、俄语，或中英双语输出。台词、歌词和画面文字始终保留原始语言，符合 H3 官方规范。

默认中文输出示例：

```
integrated_multimodal_description: 【0-3秒】实拍，电影感，全景镜头... 【3-8秒】切镜到中景... 【8-12秒】切镜到特写...
overall_soundscape: 樱花庭院中微风轻拂...
non_diegetic_music: 古风配乐...
```

中英双语输出示例（选择 Bilingual CN+EN 时）：

```
---中文版本---

integrated_multimodal_description: 【0-3秒】实拍，电影感，全景镜头... 【3-8秒】切镜到中景... 【8-12秒】切镜到特写...
overall_soundscape: 樱花庭院中微风轻拂...
non_diegetic_music: 古风配乐...

---English Version---

integrated_multimodal_description: [0-3s] Live-action, cinematic, a wide shot... [3-8s] The camera cuts to a medium shot... [8-12s] Cut to a close-up...
overall_soundscape: A gentle breeze rustles through the cherry blossom courtyard...
non_diegetic_music: Traditional Chinese instrumental music...
```

## 使用示例

### 示例 1：纯文字生成视频（T2VA）

在 `user_prompt` 输入：

```
一个穿汉服的女子在樱花庭院里舞剑
```

优化后输出（节选英文版本）：

```
---English Version---

integrated_multimodal_description: [0-5s] Live-action, cinematic, a medium-wide shot frames a young woman in a flowing Hanfu dress standing amid blooming cherry blossoms. The camera pushes in with small amplitude at slow speed as she draws a slender sword. The woman with a calm, clear voice (S1) says: <d>[Chinese] 你来了，剑等你好久了。</d> [5-10s] The camera cuts to a close-up as she begins her sword dance. Petals scatter with each movement, backlit by warm afternoon light.
overall_soundscape: A gentle breeze rustles the cherry blossom branches while petals drift to the ground. The sword swishes through the air with each stroke, and soft footsteps tap against the stone path.
non_diegetic_music: Traditional Chinese guzheng and bamboo flute at a slow tempo, building slightly in intensity during the sword dance before fading.
```

### 示例 2：图片生成视频（I2VA）

1. 将 LoadImage 节点输出连接到 `image_1`
2. `generation_mode` 选择 `Image to Video`
3. 输入提示词：

```
让这个角色从持剑起势到舞剑完毕，自然衔接
```

模型会自动分析图片并生成首帧对齐指令和完整提示词。

### 示例 3：远程 API + 多模态

1. 使用 `BSAI H3 Remote API` 节点
2. `model_name` 设为 `gpt-4o` 或 `qwen-vl-plus`（多模态模型）
3. 连接图片到 `image_1`~`image_10`
4. `generation_mode` 选择 `Multimodal Fusion`
5. 输入提示词，云端模型会同时分析图片和文本

## 支持的模型

### 本地模型（GGUF 格式）

推荐使用以下 GGUF 模型（需放到 `ComfyUI/models/LLM/`）：

- **Qwen3.6-VL**（推荐）— 多模态，需配 mmproj
- **Qwen3.5-VL** — 多模态，需配 mmproj
- **Qwen3-VL** — 多模态，需配 mmproj
- **Gemma4** — 多模态，需配 mmproj，需 llama-cpp-python 0.3.36+

### 远程 API 模型

| 服务商 | 文本模型 | 多模态模型 |
|-|-|-|
| DashScope | qwen-plus, qwen-max, qwen-turbo | qwen-vl-plus, qwen-vl-max |
| OpenAI | gpt-4o, gpt-4o-mini, gpt-4-turbo | gpt-4o, gpt-4o-mini |
| SiliconFlow | Qwen/Qwen2.5-72B 等 | 视模型而定 |

## 技术细节

### 系统提示词结构

节点内置的系统提示词严格遵循 H3 使用手册，包含：

1. **提示词整体公式**：三段结构定义
2. **四要素详解**：参考素材说明（13 种用途）、核心创意（6 要素）、画面过程说明（想要/不想要/写作原则）
3. **镜头拆分建议**：shot 对齐、跨 shot 台词、画内外说话人
4. **五类生成模式**：纯文字(T2VA)、图生视频(I2VA)、首尾帧(FL2VA)、尾帧(L2VA)、多模态融合(Ref2VA)，系统推荐自动判断
5. **常见坑位避免**：6 条易错点
6. **输出要求**：8 条格式约束

### 图片处理

- 支持 ComfyUI IMAGE 张量输入（自动转换为 base64 JPEG）
- 自动缩放至最大 1024px，压缩为 JPEG quality 85
- 多模态模型使用 OpenAI 兼容的 `image_url` content 格式
- 最多支持 10 张图片同时分析

### 视频处理

- 视频输入作为 IMAGE 张量批次接收（ComfyUI 视频格式）
- 自动提取关键帧（均匀采样，每个视频最多 4 帧）
- 关键帧转换为 base64 JPEG 并标注序号
- 最多支持 4 个视频同时分析

### 音频处理

- 音频输入为 ComfyUI AUDIO 类型（含 waveform 和 sample_rate）
- 自动提取声道数、时长、采样率等元数据
- 生成文本描述供 LLM 参考（语音/音乐/音效参考）
- 同时生成 base64 WAV 编码供远程 API 使用
- 最多支持 3 个音频同时分析

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
- 本地模型推理：[llama-cpp-python](https://github.com/abetlen/llama-cpp-python)
- 远程 API 协议：[OpenAI API](https://platform.openai.com/docs/api-reference)
- 平台：[ComfyUI](https://github.com/comfyanonymous/ComfyUI)
