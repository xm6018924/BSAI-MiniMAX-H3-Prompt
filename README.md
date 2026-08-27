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
| **BSAI H3 Prompt Template** | 提示词模板：分类选择一键使用 H3 提示词模板，含 GIF 预览 |

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

**✅ 依赖与模型自动安装（无需手动操作）**

本节点自带 `install.py`（ComfyUI 启动时自动执行）与 `requirements.txt`：
- **自动安装** `vosk`（🎤 语音离线中文识别）与 `llama-cpp-python`（⚡ 直通模式本地大模型，后台安装不阻塞启动）；
- **自动下载** Vosk 中文模型 `vosk-model-small-cn-0.22`（约 43MB，多镜像，存放在 `models/`）；
- **运行时兜底**：即使 install.py 未被执行，首次点击 🎤 语音时也会自动补装 vosk 依赖并下载模型；⚡ 直通模式缺失 llama-cpp-python 时自动后台安装并提示稍后重试。

> 直通模式的本地 GGUF 大模型（如 gemma-4-26B）体积大（15GB+），不自动下载。可在首次使用直通模式时按提示设置环境变量 `BSAI_H3_LLM_MODEL` 指向已有 GGUF，或设置 `BSAI_H3_LLM_API_KEY` + `BSAI_H3_LLM_API_BASE` 改用任意 OpenAI 兼容 API（推荐）。

**语音输入（可选，已自动安装）/ Voice input (optional, auto-installed):**

```bash
# 若自动安装失败，可手动执行：
pip install vosk
python scripts/download_vosk_model.py    # 下载 vosk-model-small-cn-0.22（约 43MB）
```

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
| weighted_keywords | Text | H3 weighted prompt embeddings (PR #15697). Format: `keyword:weight` (e.g. `美女:1.5, 小提琴:1.2`). Use `((keyword))` for layered weights. Empty = no weights / H3加权提示词嵌入 |
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
| weighted_keywords | Text | "" | H3 weighted prompt embeddings (PR #15697). Format: `keyword:weight` (e.g. `美女:1.5, 小提琴:1.2`). Use `((keyword))` for layered weights. Empty = no weights |
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
| model_family | Dropdown | Qwen3-VL / Qwen3.5-VL / Qwen3.6-VL / Qwen3.8-VL / Gemma4 |
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

### 示例 4：加权提示词嵌入（H3 PR #15697）

H3 分词器现已支持 prompt embeddings（加权提示词嵌入），可在 `integrated_multimodal_description` 中对关键词施加权重控制。

**使用方法：**

在 `weighted_keywords` 参数中输入关键词和权重，格式为 `关键词:权重值`，多个用逗号分隔：

```
美女:1.5, 拉着小提琴:1.2, 唱着歌:0.8
```

LLM 会在输出提示词中对这些关键词自动添加 H3 加权语法：

```
integrated_multimodal_description: [Shot 1] [0-3s] (美女:1.5)在欧洲小镇的街道上，(拉着小提琴:1.2)，(唱着歌:0.8)...
```

**支持的权重语法：**

| 语法 | 效果 | 示例 |
|-|-|-|
| `(关键词:1.5)` | 增强权重1.5倍 | `(美女:1.5)` |
| `(关键词:0.5)` | 降低权重至0.5倍 | `(背景:0.5)` |
| `((关键词))` | 逐层增加权重（每层≈1.1倍） | `((美女))` |

> 留空 `weighted_keywords` 参数则不添加任何权重语法，输出与之前版本完全一致。

### 示例 5：BSAI 提示词模板（一键选择） / Example 5: BSAI Prompt Template (One-Click Selection)

**BSAI H3 Prompt Template** 节点提供分类化的 H3 提示词模板，一键选择即可输出完整的三字段结构化提示词，无需 LLM 优化。

**EN:** The **BSAI H3 Prompt Template** node provides categorized H3 prompt templates. One click outputs a complete three-field structured prompt without needing LLM optimization.

#### 三级分类体系 / Three-Level Category System (246 templates / 11 categories)

| 一级分类 / Category | 二级分类 / Subcategories | 模板示例 / Examples |
|-|-|-|
| **图生视频 (I2VA)** | 线稿类 / 角色参考类 / 产品展示类 / 场景参考类 / 风格迁移类 | 黑白线稿转彩色真人跳舞、肖像照转说话视频、产品360度旋转展示 |
| **文生视频 (T2VA)** | 电影场景类 / 舞蹈编排类 / 自然风光类 / 奇幻创意类 / 城市生活类 | 赛博朋克雨夜街道、芭蕾独舞舞台、太空行走 |
| **首尾帧 (FL2VA)** | 过渡变换类 / 变形效果类 | 日转夜延时过渡、面孔渐变变形 |
| **多模态融合 (Ref2VA)** | 品牌广告类 / 短剧叙事类 / 音乐节拍类 / 角色合成类 | 时尚品牌广告片、竖屏短剧对话、动漫OP节拍同步 |
| **生长类 (Growth)** | 植物生长类 / 动物生长类 / 人物生长类 / 物体生长类 | 种子破土开花、破茧成蝶、婴儿到成人、城市扩张生长 |
| **延时摄影类 (Time-Lapse)** | 建筑延时类 / 产品组装延时类 / 交通类延时 / 自然景观延时类 | 摩天楼拔地而起、智能手表组装、高速车流光轨、星轨流转 |
| **人物表情模板 (Expression)** | 基础表情类 / 微表情类 / 情绪过渡类 / 社交面具类 / 崩溃边缘类 | 微笑、忍住不哭、笑转哭、被揭穿后微笑、沉默太久 |
| **武打打斗模板 (Combat)** | 拳脚对打类 / 冷兵器对战类 / 快慢镜头类 / 打斗运镜类 / 多人群战类 / 特殊招式类 / 触发词战斗类 / 多图成战类 | 散打对咏春、双刀对长枪、子弹时间闪避、双雄决战 |
| **电影运镜模板 (Cinematic)** | 基础运动类 / 跟随与环绕类 / 变焦与焦距类 / 角度与视角类 / 大范围与特殊运镜类 | 推镜、甩镜、360度环绕、推拉变焦、子弹时间、无人机穿越 |
| **电影调色 (Color Grading)** | 经典胶片模拟 / 大片商业风格 / 氛围色调 / 黑白摄影 / 摄影工艺 | 柯达2383、青橙好莱坞大片、黄金时刻、黑色电影、拍立得 |
| **风格转绘 (Style Transfer)** | 手绘绘画 / 传统艺术 / 动漫插画 / 数字与3D / 摄影工艺 | 水墨画、吉卜力、赛博朋克、浮世绘、皮克斯3D |

#### 使用方法 / Usage

1. 在 ComfyUI 中添加 `BSAI H3 Prompt Template` 节点
2. 节点上方显示可视化模板浏览器：
   - **一级分类**下拉框：选择生成模式（图生视频 / 文生视频 / 首尾帧生成 / 多模态融合 / 生长 / 延时 / 表情 / 武打 / 电影运镜 / 电影调色 / 风格转绘）
   - **二级分类**下拉框：选择模板子类（线稿类 / 角色参考类 / 产品展示类 等）
   - **模板列表**：点击任意模板即可加入已选叠加栈
3. **多选叠加（Multi-Stack）**：默认<b>单选</b>（点击模板即选中并立即预览）。开启列表上方的"多选叠加 / Multi-Stack"开关后可叠加选择多个模板（最多 5 个），如先选"贴身缠斗 | Close Grappling"再选"环绕镜头 | Orbit (Arc Shot)"，画面效果更丰富；第 1 个为基础模板（场景/动作），其余为叠加模板（如运镜）。已选条支持单个移除与一键清除，关闭开关后仅保留基础模板。
4. 右侧显示 **WebP 预览动画**（400×400 动图，遵循 ComfyUI 官方 workflow templates 规格）和模板信息（生成模式 / 时长 / 是否需要图片）
5. `prompt_output` 输出端口直接输出**合并后的单一 H3 三字段提示词**（基础场景/动作 + 叠加运镜指令，音效合并，音乐优先级补全）
6. 可将输出连接到视频生成节点，或先连接到 `BSAI MiniMAX H3 Prompt` 节点进一步优化
7. `external_prompt` 可选输入端口可连接其他节点文本，输入后将**覆盖模板中的动作**（如"抬腿"替换行走动作，而非追加到末尾）
8. **🎤 语音输入**：点击搜索框旁的"🎤 语音 / Voice"按钮，允许麦克风权限后点击"开始录音"说话，再点"停止并转写"。录音由本地离线 Vosk 中文模型识别，可填入 `external_prompt`（覆盖动作）或 `user_customization`（补充修改）。安装：`pip install vosk` + `python scripts/download_vosk_model.py`

**EN:**
1. Add the `BSAI H3 Prompt Template` node in ComfyUI.
2. A visual template browser appears above the node:
   - **Category** dropdown: choose a generation mode (I2VA / T2VA / FL2VA / Ref2VA / Growth / Time-Lapse / Expression / Combat / Cinematic / Color Grading / Style Transfer)
   - **Subcategory** dropdown: choose a template subclass
   - **Template list**: click any template to add it to the selection stack
3. **Multi-select stacking**: stack up to 5 templates, e.g. pick "Close Grappling" first, then "Orbit (Arc Shot)" for a richer result. The 1st template is the base (scene/action); the rest are overlays (e.g. camera moves). The chips bar supports per-item removal and one-click clear.
4. The right panel shows a **WebP preview animation** (400×400, per ComfyUI official workflow-templates spec) and template info (generation mode / duration / needs-image).
5. The `prompt_output` port outputs the **merged single H3 three-field prompt** (base scene/action + overlay camera directives, soundscape merged, music priority-filled).
6. Connect the output to a video generator, or chain it into the `BSAI MiniMAX H3 Prompt` node for further optimization.
7. The optional `external_prompt` input port accepts text from other nodes; when provided it **OVERRIDES the template's action** (e.g. "抬腿" replaces the walking motion) instead of merely appending.
8. **🎤 语音输入 / Voice input**: click the **🎤 语音 / Voice** button next to the search box, allow the mic, speak, then "Stop & Transcribe". The recording is transcribed locally (offline Vosk) and can be filled into `external_prompt` (action override) or `user_customization`. Install: `pip install vosk` + `python scripts/download_vosk_model.py`.

> **模板通用化 / Generic templates:** 全部 246 个模板均经过审计与通用化重写，不包含具体场景或人物形象细节（发型、服装、鞋帽、性别等）。图生视频 / 首尾帧模板只引用输入图像（`<Picture 1>` / `<Picture 2>`）并描述动作、运镜、氛围，不会覆盖输入图像的人物或场景特征。All 246 templates have been audited and genericized — no specific scene or character-appearance details. I2VA/FL2VA templates only reference the input images and describe action/camera/atmosphere, so they never overwrite the input image features.

#### 预览动画 / Previews

25 个模板配有预览动画（动图 WebP，400×400，遵循 ComfyUI 官方 workflow templates 预览规格）。文件位于 `web/previews/` 目录，可自行添加更多预览。25 templates ship with animated WebP previews (400×400, matching the ComfyUI official workflow-templates preview spec) in `web/previews/`; add more by copying files there and setting the `preview` field in the JSON.

#### 自定义模板

在 `templates/prompt_templates.json` 中可添加自定义模板，格式如下：

```json
{
  "id": "my_template",
  "name": "模板名称",
  "name_en": "Template Name (EN)",
  "description": "模板描述",
  "preview": "my_preview.webp",
  "generation_mode": "Image to Video (图生视频)",
  "duration": 6,
  "needs_image": true,
  "needs_video": false,
  "needs_audio": false,
  "tags": ["标签1", "标签2"],
  "prompt": "integrated_multimodal_description: ...\n\noverall_soundscape: ...\n\nnon_diegetic_music: ..."
}
```

> 修改后需同步复制到 `web/templates_data.json`，或在 `web/` 目录放置同名文件。

## 支持的模型

### 本地模型（GGUF 格式）

推荐使用以下 GGUF 模型（需放到 `ComfyUI/models/LLM/`）：

- **Qwen3.8-VL**（推荐）— 多模态，需配 mmproj
- **Qwen3.6-VL** — 多模态，需配 mmproj
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

## 更新日志 / Changelog

### v1.11.8 — 融合失败不再"伪装成功"（显式报错+未改动检测）/ Merge failures surfaced explicitly

**中文说明：**

- **修复「确认修改后对比无任何变化」**：此前融合失败会被静默当成成功（返回原模板却报 ok:true），前端无从得知。现后端**严格区分成功/失败**：失败时返回 `ok:false` + 具体原因（如显存不足/模型未加载），前端显示明确错误；即使后端误报成功，前端也会检测「融合结果==源模板」并提示"未检测到任何修改"及建议（停止生成后再试 / 配置 `BSAI_H3_LLM_API_KEY` 用云端模型零显存）。
- **务必重启 ComfyUI** 使新后端生效（本版同时改了后端与前端）。
- 实测（sulphur 模型）：「让图1人物自然走进场景2」成功返回 `changed=True`，`Match-cut transition` 被改写为 walk-through。

**English:**

- **Fix "Apply shows no change"**: a failed merge used to be silently reported as success (original prompt returned with `ok:true`), so the frontend had no way to know. Now the backend **strictly distinguishes success/failure** — failures return `ok:false` + reason (e.g. VRAM OOM / model not loaded), and the frontend shows the error clearly; even if the backend reports ok, the frontend detects "merged == source" and warns "not changed" with suggestions (stop generation first, or set `BSAI_H3_LLM_API_KEY` for zero-VRAM cloud merging).
- **Restart ComfyUI** is required (backend + frontend changed in this release).
- Verified (sulphur): "let the person naturally walk into Scene 2" returns `changed=True`, `Match-cut transition` → walk-through.

### v1.11.7 — 新增「源模板 vs 修改后」对比窗口 / Source-vs-Merged diff view added

**中文说明：**

- 输出提示词预览新增「**📊 源/修改后 对比 Diff**」按钮：展开左右分栏对比窗口——左「源模板提示词」、右「修改后提示词」，并做**行级差异高亮**（🟥红=源中被删除，🟩绿=修改后新增）。
- 点击「确认修改 / Apply」融合完成后，对比窗口**自动展开**，一眼看出补充修改到底改动了哪些行（如转场描述、音效行是否真正被改写）。
- 仅需刷新浏览器（Ctrl+F5），无需重启 ComfyUI。

**English:**

- The Output Preview now has a "**📊 源/修改后 对比 Diff**" button: it expands a two-column comparison — Source Template (left) vs Merged Result (right) — with **line-level diff highlighting** (red = removed from source, green = added in merged).
- After clicking "确认修改 / Apply", the diff panel **auto-expands** so you can instantly see exactly which lines the customization changed.
- Browser refresh (Ctrl+F5) only — no ComfyUI restart needed.

### v1.11.6 — 新增「确认修改 / Apply」按钮（手动触发融合）/ "Apply Customization" button added

**中文说明：**

- 补充修改输入框后新增「**确认修改 / Apply**」按钮：点击后立即通过本地大模型把补充修改**真正融合进模板**，并在「输出提示词预览」中直接查看最终结果。
- 输入时不再自动触发融合（避免打字过程反复启动 30s 大模型），改为即时「追加预览 + 提示点按钮」。按下按钮才融合；同一模板+同一修改缓存命中后**秒出**。
- 仅需刷新浏览器（Ctrl+F5）即可生效，无需重启 ComfyUI。

**English:**

- Added an "**确认修改 / Apply**" button after the Customization field: click to LIVE-MERGE the customization into the template via the local LLM and see the final prompt in the Output Preview immediately.
- Typing no longer auto-triggers the slow merge (prevents repeated LLM starts); an instant append preview with a hint is shown instead. Only the button triggers the merge; the same template+edit is instant once cached.
- Refresh the browser (Ctrl+F5) only — no ComfyUI restart needed.

### v1.11.5 — 补充修改真实融入模板（修复推理模型吞掉输出）/ Customization merge fixed (reasoning-model output bug)

**中文说明：**

- **修复「补充修改没有真正融入」**：此前融合用的大模型（如 Qwen3.5-9B 推理模型）输出被「思考过程」占满，真正的改写提示词根本没生成，导致看起来只是末尾追加。现改用**提示词增强专用模型 `sulphur_prompt_enhancer`**（8GB，直接输出不思考），配合「禁止思考、直接输出最终提示词」的指令与更健壮的输出清理/校验，融合结果干净、字段完整。
- **实测验证**：将「请让图1的人物自然地从场景1走进场景2，而不是从场景1硬切到场景2」融入「角色多场景演绎」模板后，`[Shot 2]` 的 `Match-cut transition` 被真正改写为 `Natural walk-through transition: ...walks ... into the setting from <Picture 3>`，`overall_soundscape` 同步更新为 walk-through——修改确实写进模板内部，不再追加。
- **更快**：首次约 30-40 秒（含模型加载），之后同一模板+同一修改**秒出**（缓存 + 模型常驻）。
- 引擎支持多模型常驻：直通生成仍用默认模型（gemma-4-26B），融合自动优先用 sulphur；也可设置 `BSAI_H3_LLM_MODEL` 或 `BSAI_H3_LLM_API_KEY` 指定。

**English:**

- **Fix "customization not truly merged"**: the previous merge LLM (e.g. the Qwen3.5-9B reasoning model) spent its whole output on "thinking", so the rewritten prompt was never produced — it looked like a plain append. Now the merge uses the **prompt-enhancer model `sulphur_prompt_enhancer`** (8GB, direct output, no reasoning), with a "no thinking, output the final prompt immediately" instruction plus robust output cleaning/validation, so the merged result is clean and complete.
- **Verified**: merging "let the person in Picture 1 naturally walk from Scene 1 into Scene 2 instead of a hard cut" into the Character multi-scene template rewrites `[Shot 2]`'s `Match-cut transition` to `Natural walk-through transition: ...walks ... into the setting from <Picture 3>`, and `overall_soundscape` is updated to walk-through too — the change is written inside the prompt, not appended.
- **Faster**: first run ~30-40s (incl. model load); afterwards the same template+edit returns **instantly** (cache + resident model).
- Multiple models can stay resident: Direct Mode still uses the default model (gemma-4-26B), merging auto-prefers sulphur; set `BSAI_H3_LLM_MODEL` or `BSAI_H3_LLM_API_KEY` to override.

### v1.11.4 — 补充修改真实融入模板 / Customization truly merged into the template

**中文说明：**

- **补充修改从「末尾追加」升级为「真实融入」**：模板提示词 + 补充修改会交给本地大模型（与直通模式同引擎）**重写**，把修改要求**真正写进提示词内部**——例如「两个不同场景的转场不要硬切，让图1人物自然地从场景1走进场景2」会把模板里的 `Match-cut transition`（硬切）直接改成自然行走转场，而不是在末尾加一句话。
- **前端实时预览**：在「补充修改」框输入文字后，输出提示词预览会实时调用本地大模型，展示融合后的完整三段式（含 subject_definitions 等块），当场可见修改效果。
- **全覆盖**：对任意模板、多选叠加、直通模式、自定义文本都生效。
- **降级兜底**：本地大模型不可用时（未装 llama-cpp-python / 未放置 GGUF / 未设置 API），自动退回末尾追加，不影响使用。
- 引擎优先级：`BSAI_H3_LLM_API_KEY`（OpenAI 兼容 API）→ 本地 GGUF（`BSAI_H3_LLM_MODEL` 或自动检测）。

**English:**

- **Customization upgraded from "append at the end" to "truly merged"**: the template prompt + customization are REWRITTEN by the local LLM (same engine as Direct Mode), so the modification is written INSIDE the prompt — e.g. "no hard cut between the two scenes, let the subject walk naturally from scene 1 into scene 2" will replace the template's `Match-cut transition` with a natural walk-through, instead of appending a sentence.
- **Live preview**: typing in the customization box live-merges via the local LLM and shows the rewritten full prompt (including subject_definitions etc.) in the output preview.
- **Applies everywhere**: any template, multi-stack, Direct mode, custom text.
- **Fallback**: when no LLM is available (llama-cpp-python missing / no GGUF / no API), it falls back to appending at the end.
- Engine priority: `BSAI_H3_LLM_API_KEY` (OpenAI-compatible API) → local GGUF (`BSAI_H3_LLM_MODEL` or auto-detect).

### v1.11.3 — 修复补充修改不生效 + 输出预览 / Fix "Set as customization" + Output preview

**中文说明：**

- **修复 🎤 语音「填入补充修改 / Set as customization」不起作用**：原实现只写入了隐藏 widget 的值，未同步界面补充修改框的显示，且节点上没有展示合并后的最终提示词，导致看不到效果、误以为未生效。
- **现在**：点击「填入补充修改」后，文字会立即显示在节点上的「补充修改 / Customization」框内，并在「输出提示词预览 / Output Preview」实时渲染「选中模板合并 + 补充修改追加」后的完整提示词，效果一目了然；手动修改补充修改框时预览同步刷新；模板选择/清除/多选叠加也会同步刷新预览。
- **补充修改对所有模板生效（已验证）**：后端在直通模式、自定义模式、任意模板/多选叠加输出末尾统一追加 `--- User Customization / 用户自定义 ---` 块，覆盖全部模板。

**English:**

- **Fix 🎤 voice "Set as customization" not taking effect**: previously only the hidden widget value was written; the on-node customization textarea was not updated and the merged final prompt was not shown, so the change appeared to do nothing.
- **Now**: clicking "Set as customization" instantly shows the text in the node's customization box and renders the full merged prompt (selected templates + customization appended) in the "Output Preview" box; manual edits to the box also refresh the preview; template select/clear/multi-stack refresh it too.
- **Customization applies to ALL templates (verified)**: the backend appends a `--- User Customization / 用户自定义 ---` block to every output path — Direct mode, custom text, and any template / multi-stack merge.

### v1.11.2 — 依赖与模型自动安装 / Auto-install dependencies & models

**中文说明：**

- **新增 `install.py`**：ComfyUI 启动时自动执行——自动安装 `vosk`（语音离线识别）与 `llama-cpp-python`（直通模式本地大模型，后台安装不阻塞启动）；自动下载 Vosk 中文模型 `vosk-model-small-cn-0.22`（约 43MB，多镜像）。任何电脑下载本插件后开箱即用。
- **requirements.txt 补充 `vosk`**：ComfyUI-Manager 等自动安装依赖时也会带上。
- **运行时兜底**：即使 install.py 未执行，首次点击 🎤 语音按钮会自动补装 vosk 并下载模型；⚡ 直通模式缺失 llama-cpp-python 时自动后台安装并提示稍后重试。
- 直通模式本地 GGUF 大模型（15GB+）不自动下载，建议设置 `BSAI_H3_LLM_API_KEY` 使用 OpenAI 兼容 API，或放置/指定 GGUF。

**English:**

- **New `install.py`**: auto-executed on ComfyUI startup — installs `vosk` (offline ASR) and `llama-cpp-python` (Direct-Mode local LLM, installed in background so startup is never blocked); auto-downloads the Vosk Chinese model `vosk-model-small-cn-0.22` (~43 MB, multi-mirror). Fresh installs on any machine now work out of the box.
- **`requirements.txt` now includes `vosk`** so ComfyUI-Manager-style installers pick it up too.
- **Runtime fallback**: even if `install.py` did not run, the first 🎤 voice click auto-installs vosk and downloads the model; Direct Mode auto-installs llama-cpp-python in the background and asks to retry.
- The Direct-Mode local GGUF LLM (15GB+) is NOT auto-downloaded; prefer setting `BSAI_H3_LLM_API_KEY` for an OpenAI-compatible API, or place/point to a GGUF.

### v1.11.1 — 语音直通流程优化 + 输出提示词预览 / Direct-Mode confirm dialog + Output Preview

**中文说明：**

- **转写后 3 秒等待 + 询问框**：直通模式下语音停止转写后，先停留 **3 秒**——
  - **只要用户手动修改了文字（任何时候）→ 询问框都不会出现**；即使询问框已弹出也会被立即关闭，用户直接使用录音界面本就存在的「⚡ 生成 H3 提示词」与「✅ 确定并输出」按钮（点「确定并输出」= 直通输出文字，点「生成 H3」再「确定并输出」= H3 三段式输出）；
  - 3 秒内**未手动修改**文字 → 3 秒后弹出「如何输出？」询问框：✏️ 修改文字 ／ ⚡ 不修改直通输出文本（不生成 H3）／ ⚡ H3 生成提示词 ／ ✕ 取消。
  - 「直通输出文本」**不经过 H3 生成**，直接把语音转文字原文输出给下游节点、窗口自动关闭；「H3 生成提示词」由本地大模型按 **H3 SKILL 三段式标准**扩写后再输出给下游；
- **输出提示词预览**：节点「补充修改」下方新增只读「**输出提示词预览 / Output Preview**」窗口，直通/语音输出的完整提示词在语音窗口关闭后仍在此显示；工作流重载时自动恢复。

**English:**

- **3s grace period + confirm dialog**: in Direct Mode, once transcription finishes, there is a **3-second grace period** —
  - **editing the text at any time suppresses the dialog** — even if the dialog is already open, it is closed immediately; use the always-present buttons in the recording dialog —「✅ 确定并输出 / Confirm &amp; Output」outputs the text as-is (raw), and「⚡ 生成 H3 提示词 / Generate H3」first expands it into a full H3 prompt;
  - if you do **not** edit the text within 3s → after 3s the「如何输出？/ How to output?」dialog appears: ✏️ Edit text ／ ⚡ Output raw text (no H3 generation) ／ ⚡ Generate H3 ／ ✕ Cancel.
  -「⚡ Output raw text」sends the raw transcribed text downstream **without H3 generation** and auto-closes;「⚡ Generate H3」expands it into a full H3 three-field prompt per the H3 SKILL, then outputs downstream.
- **Output Preview**: a new read-only「**输出提示词预览 / Output Preview**」box below the Customization area shows the full prompt sent to downstream; it persists after the voice dialog closes and is restored on workflow load.

### v1.11.0 — 新增电影调色 + 风格转绘模板 / Add Cinematic Color Grading + Style Transfer templates

**中文说明：**

- **新增「电影调色」板块**（30 个模板 / 5 子类）：经典胶片模拟（Kodak 2383/2393、富士 3513、Vision3、LOG、35mm 颗粒）、大片商业风格（青橙好莱坞、夏日大片、商业明亮、漂白跳过、低饱和剧情、柔和低饱和）、氛围色调（黄金时刻、冷蓝夜景、暗黑惊悚、梦幻柔和、深褐怀旧、恐怖绿）、黑白摄影（高反差黑白、柔和黑白、黑色电影、红外、银盐、黑白胶片）、摄影工艺（拍立得、长曝光、双重曝光、移轴、达盖尔银版、复古摄影）。
- **新增「风格转绘」板块**（40 个模板 / 5 子类）：手绘绘画（水彩、古典油画、印象派、水墨、素描、点彩、水粉、厚涂）、传统艺术（浮世绘、工笔、木刻版画、剪纸、彩色玻璃、新艺术、立体主义、波普）、动漫插画（日漫、90年代动漫、吉卜力、新海诚、国漫、美漫、童书插画、概念艺术）、数字与3D（皮克斯3D、低多边形、像素、赛博朋克、蒸汽波、扁平、粘土定格、折纸）、摄影工艺（双重曝光、长曝光、移轴、拍立得、红外、黑白、超现实、极简）。
- **通用化 + H3 SKILL**：全部模板严格遵守 MiniMax H3 三字段结构（`integrated_multimodal_description` / `overall_soundscape` / `non_diegetic_music`），含分镜时间轴与【ACTION】覆盖标记；只改变色调或画风，绝不描述具体人物/场景细节，不改变输入图像主体特征——适用于图生视频。
- **双语命名**：所有新模板名称中英双语对照。
- 总模板数：176 → 246；总分类：9 → 11。

**English:**

- **New "Cinematic Color Grading" category** (30 templates / 5 subcategories): Film Stock Emulation (Kodak 2383/2393, Fuji 3513, Vision3, LOG, 35mm grain), Blockbuster Looks (Teal & Orange, Summer Blockbuster, Bright Commercial, Bleach Bypass, Moody Desaturated, Soft Muted), Mood Tones (Golden Hour, Cool Blue Night, Dark Thriller, Dreamy Pastel, Sepia, Horror Green), Monochrome (High Contrast B&W, Soft Gray, Film Noir, Infrared, Silver Gelatin, B&W Film), Photo Craft (Polaroid, Long Exposure, Double Exposure, Tilt-Shift, Daguerreotype, Vintage).
- **New "Style Transfer" category** (40 templates / 5 subcategories): Painting & Drawing (Watercolor, Oil, Impressionism, Ink Wash, Sketch, Pointillism, Gouache, Impasto), Traditional Art (Ukiyo-e, Gongbi, Woodcut, Paper Cut, Stained Glass, Art Nouveau, Cubism, Pop Art), Anime & Illustration (Anime, 90s Anime, Ghibli, Shinkai, Manhua, Comic, Children's Book, Concept Art), Digital & 3D (Pixar 3D, Low Poly, Pixel, Cyberpunk, Vaporwave, Flat, Claymation, Origami), Photo Craft (Double Exposure, Long Exposure, Tilt-Shift, Polaroid, Infrared, B&W, Surrealism, Minimalism).
- **Generic + H3 SKILL**: all templates strictly follow the MiniMax H3 three-field structure, with time-coded shots and 【ACTION】 override markers; only the color grade or art style changes — never describe specific character/scene details, never alter the input image's subject features (I2VA-ready).
- **Bilingual names** for all new templates.
- Total templates: 176 → 246; categories: 9 → 11.

### v1.10.0 — 直通模式（语音/文字 → 完整 H3 提示词）/ Direct Mode (Voice/Text → Full H3 Prompt)

**中文说明：**

- **新增 ⚡ 直通模式**：语音对话框中勾选"⚡ 直通模式 / Direct Mode"并点击"⚡ 生成 H3 提示词 / Generate H3"，框内文字（语音转写或手动输入）将由 **本地 llama.cpp GGUF 大模型** 按 **H3 官方提示词 SKILL** 扩写为完整的 `integrated_multimodal_description` / `overall_soundscape` / `non_diegetic_music` 三字段提示词（含分镜时间轴、运镜、音效、音乐；中文输入自动译为英文）。
- **直接输出**：点击"✅ 确定并输出 / Confirm &amp; Output"后，节点新增的 `direct_prompt` 输入生效，`prompt_output` **直接输出该提示词给下游节点，绕过所有模板**（名称显示"直通模式 | Direct Mode"）。
- **全自动流程（直通模式）**：录音时 **3 秒无声音**自动停止并转写；转写完成后**停留 3 秒**——3 秒内直接修改了文字则**不再弹询问框**，直接用录音界面原有的「⚡ 生成 H3 提示词」/「✅ 确定并输出」按钮输出；3 秒内未手动修改则 3 秒后弹出「如何输出？」询问框（✏️ 修改文字 / ⚡ 直通输出文本 / ⚡ H3 生成提示词 / ✕ 取消）。「直通输出文本」直接输出语音原文（不生成 H3）给下游并自动关闭；「H3 生成提示词」由本地大模型按 H3 三段式标准扩写后输出。输出后可在节点下方「**输出提示词预览 / Output Preview**」只读窗口中查看发送给下游的完整提示词（窗口关闭后仍保留）。
- **本地模型自动检测**：默认加载 `ComfyUI/models/LLM/Gemma4-GGUF/gemma-4-26B-A4B-it-heretic-ara.Q4_K_M.gguf`（输出干净、质量高）。可通过环境变量覆盖：`BSAI_H3_LLM_MODEL`（任意 GGUF 路径，如 9B 的 `Qwen3.5-9B-...-Q8_0.gguf`）、`BSAI_H3_LLM_GPU_LAYERS`（默认 -1=全部 GPU，可调小省显存）、`BSAI_H3_LLM_API_KEY` + `BSAI_H3_LLM_API_BASE`（改用 OpenAI 兼容远程 API）。
- **懒加载**：首次调用才加载模型（约 1 分钟），之后常驻；重启 ComfyUI 释放显存。
- 依赖：`pip install llama-cpp-python`（本机已装，GPU 加速）。

**English:**

- **New ⚡ Direct Mode**: in the voice dialog tick "⚡ 直通模式 / Direct Mode" and click "⚡ 生成 H3 提示词 / Generate H3" — the box text (voice transcription or manual input) is expanded by a **local llama.cpp GGUF LLM** per the **official H3 prompt SKILL** into a full three-field prompt (`integrated_multimodal_description` / `overall_soundscape` / `non_diegetic_music`), including time-coded shot breakdown, camera moves, soundscape and music; Chinese input is translated to English.
- **Direct output**: after "✅ 确定并输出 / Confirm &amp; Output", the new `direct_prompt` input takes effect and `prompt_output` **emits the text directly to downstream nodes, bypassing all templates** (name shows "直通模式 | Direct Mode").
- **Fully automatic flow (Direct Mode)**: while recording, **3 seconds of mic silence** auto-stops and transcribes; after transcription there is a **3-second grace period** — if you **edit the text** within 3s, **no dialog appears**; use the always-present「⚡ 生成 H3 提示词 / Generate H3」and「✅ 确定并输出 / Confirm &amp; Output」buttons directly (Confirm = raw output, Generate H3 then Confirm = H3 output). If you do not edit within 3s, the full「如何输出？/ How to output?」dialog appears (✏️ Edit text / ⚡ Output raw text / ⚡ Generate H3 / ✕ Cancel).「⚡ Output raw text」sends the raw transcribed text downstream **without H3 generation** and auto-closes;「⚡ Generate H3」expands it into a full H3 three-field prompt first. The full prompt sent downstream stays visible in the node's read-only「**输出提示词预览 / Output Preview**」box even after the dialog closes.
- **Auto-detected local model**: defaults to `ComfyUI/models/LLM/Gemma4-GGUF/gemma-4-26B-A4B-it-heretic-ara.Q4_K_M.gguf` (clean, high-quality output). Overridable via env: `BSAI_H3_LLM_MODEL` (any GGUF path), `BSAI_H3_LLM_GPU_LAYERS` (default -1 = all GPU), `BSAI_H3_LLM_API_KEY` + `BSAI_H3_LLM_API_BASE` (OpenAI-compatible remote API).
- **Lazy load**: the model loads on first use (~1 min), then stays resident; restart ComfyUI to free VRAM.
- Deps: `pip install llama-cpp-python` (installed on this machine, GPU-accelerated).

### v1.9.0 — 语音输入（本地离线 ASR）/ Voice Input (Local Offline ASR)

**中文说明：**

- **新增 🎤 语音输入**：模板浏览器搜索框旁新增"🎤 语音 / Voice"按钮。点击后弹出录音对话框，允许麦克风权限后"开始录音"，说完点"停止并转写"。
- **本地离线识别**：录音在浏览器编码为 16kHz 单声道 WAV，经 `/bsai_h3/asr` 接口由 **Vosk 中文模型**（vosk-model-small-cn-0.22）本地转写——无需联网、无需 API Key，数据不出本地。
- **结果回填**：可编辑的识别文本可一键填入 `external_prompt`（覆盖模板动作）或 `user_customization`（补充修改）。
- **模型管理**：模型约 43MB，已加入 `.gitignore`；运行 `python scripts/download_vosk_model.py` 自动下载（含多镜像回退）。依赖：`pip install vosk`。

**English:**

- **New 🎤 voice input**: a "🎤 语音 / Voice" button next to the search box opens a recording dialog (allow mic → Start → speak → Stop & Transcribe).
- **Local offline ASR**: the recording is encoded to 16kHz mono WAV in the browser and transcribed locally by a **Vosk Chinese model** (vosk-model-small-cn-0.22) via the `/bsai_h3/asr` endpoint — no cloud, no API key, data stays local.
- **Result fill-back**: the editable text can be filled into `external_prompt` (action override) or `user_customization` with one click.
- **Model management**: the ~43MB model is git-ignored; run `python scripts/download_vosk_model.py` to fetch it (multi-mirror fallback). Dependency: `pip install vosk`.

---

### v1.8.0 — 外部提示词覆盖模板动作 / External Prompt Action Override

**中文说明：**

- **外部提示词改为"动作覆盖"**：`external_prompt` 输入后不再简单追加到末尾，而是**覆盖模板中的动作描述**。例如"全身照转动作视频 | Full-body photo to action video"输入"抬腿"后，模板内的自然行走/运动描述被直接替换为抬腿动作。
- **字面替换（标记模板）**：含 `【ACTION】...【/ACTION】` 标记的模板（当前为图生视频动作类 6 个：线稿跳舞/线稿行走/线稿动画/肖像说话/全身照转动作/角色定转）会对动作文本进行字面替换。
- **通用指令覆盖（其余所有模板）**：无标记的模板会在 `integrated_multimodal_description` 内注入强"Action Override / 动作覆盖"指令，同样让外部提示词生效。
- **保持 H3 规范**：替换/覆盖时始终保留构图、运镜、环境、光照、时间与主体特征；并在 `overall_soundscape` 中附加"音效适配新动作"提示。`user_customization` 仍在末尾自由追加。
- **示例**：`external_prompt = 抬腿` + 全身照转动作 → 输出中行走描述消失，替换为"The subject performs the action "抬腿"..."。

**English:**

- **External prompt is now an action override**: `external_prompt` no longer just appends — it **overrides the template's action**. E.g. for "Full-body photo to action video", inputting "抬腿" directly replaces the built-in walking/motion description with leg-lifting.
- **Literal replacement (marked templates)**: templates containing `【ACTION】...【/ACTION】` markers (currently 6 I2VA action templates: line-art dance / line-art walking / line-art anime / portrait speaking / full-body action / character turnaround) get their action text literally replaced.
- **Generic directive override (all other templates)**: templates without markers receive a strong "Action Override / 动作覆盖" directive injected into `integrated_multimodal_description`.
- **H3 compliance kept**: framing, camera, environment, lighting, timing and subject identity are always preserved; `overall_soundscape` gains an "adapt to the new action" note. `user_customization` still appends freely at the end.
- **Example**: `external_prompt = 抬腿` + Full-body action template → the walking clause disappears, replaced by "The subject performs the action "抬腿" exactly as instructed."

---

### v1.7.0 — 模板多选叠加 / Template Multi-Select Stacking

**中文说明：**

- **模板浏览器支持多选叠加（最多 5 个）**：新增"多选叠加 / Multi-Stack"开关，**默认单选**（点击模板即选中并立即预览）。开启开关后点击模板加入已选叠加栈，第 1 个为基础模板（场景/动作），其余为叠加模板（如运镜、表情）。顶部已选条支持单个移除与一键清除，列表项高亮显示已选状态；关闭开关后仅保留基础模板。
- **合并输出单一 H3 提示词**：`template_select` 以 `|||` 携带多个模板标签；节点按 H3 SKILL 三字段结构智能合并——基础场景/动作 + 叠加模板指令块追加（`# Overlay 叠加模板: XXX`），音效合并，音乐优先级补全（基础无音乐则取叠加模板音乐）。
- **示例**：先选"贴身缠斗 | Close Grappling"再选"环绕镜头 | Orbit (Arc Shot)"，输出为"近身缠斗动作 + 环绕运镜"的单一规范 H3 提示词。
- **输出端口同步**：`template_name` 返回合并名称（A + B），`generation_mode` 标记"多模板叠加 Multi-Stack"，`description` 附叠加列表，`preview_file`/`duration` 取基础模板。

**English:**

- **Multi-select stacking in the template browser (up to 5)**: a **Multi-Stack switch** controls the mode. It is **OFF (single-select) by default** — clicking a template selects it and previews it immediately. Turn the switch ON to stack templates; the 1st is the base (scene/action), the rest are overlays (e.g. camera moves, expressions). The chips bar supports per-item removal and one-click clear; list items are highlighted when selected. Turning the switch OFF keeps only the base template.
- **Merged single H3 prompt**: `template_select` carries multiple labels joined by `|||`; the node merges them per the H3 SKILL three-field structure — base scene/action + overlay directive blocks appended (`# Overlay: XXX`), soundscape merged, music priority-filled (base's N/A music falls back to overlay's).
- **Example**: pick "Close Grappling" first, then "Orbit (Arc Shot)" → one coherent H3 prompt of close-combat action + orbit camera move.
- **Output ports updated**: `template_name` returns the merged name (A + B), `generation_mode` flags "Multi-Stack", `description` lists the overlays, `preview_file`/`duration` come from the base template.

---

### v1.6.0 — 电影运镜模板 + 预览统一为 WebP / Cinematic Camera Movement + WebP Previews

**中文说明：**

- **新增电影运镜模板分类**：全网搜索整理 32 个电影运镜模板（5 个子类：基础运动 / 跟随环绕 / 变焦焦距 / 角度视角 / 大范围特殊），涵盖推拉摇移升降甩、跟随、侧跟、环绕、360度环绕、斯坦尼康、手持、推拉变焦（希区柯克）、变焦推近/拉远、跟焦、低/高角度、顶拍、荷兰角、旋转、主观视角、过肩、航拍、无人机穿越、摇臂、穿越、穿越机、子弹时间等。全部遵循 MiniMax H3 提示词 SKILL 三字段格式，全部名称与参数设置中英双语对照。
- **运镜模板通用化**：所有运镜模板只描述摄影机运动（方向 / 速度 / 时间节拍 / 构图景别），严格引用输入图片 `<Picture 1>` 且保持其场景与人物特征完全不变，绝不覆盖输入画面内容。
- **预览文件统一为 WebP**：将全部 25 个模板预览从 GIF 转换为动图 WebP，尺寸统一为 **400×400**，与 ComfyUI 官方 workflow templates 的模板预览格式与大小保持一致；JSON `preview` 字段同步更新为 `.webp`。
- **模板总数**：144 → **176**（9 大分类）。

**English:**

- **New Cinematic Camera Movement category**: 32 camera-movement templates researched and organized into 5 subcategories (Basic / Follow & Orbit / Zoom & Focus / Angle & POV / Aerial & Special) covering push in, pull out, pan, tilt, truck, pedestal, whip pan, tracking, side tracking, orbit, 360° orbit, steadicam, handheld, dolly zoom (Vertigo), zoom in/out, rack focus, low/high angle, top-down, dutch angle, roll, POV, over-the-shoulder, aerial, drone fly-through, crane, dolly through, FPV, and bullet time. All follow the MiniMax H3 prompt SKILL three-field structure, all names and parameters are bilingual (中文 | English).
- **Generic camera templates**: each template describes only the camera motion (direction / speed / time beats / framing) and strictly references `<Picture 1>` while keeping its scene and character features completely unchanged — never overriding the input image.
- **Previews unified to WebP**: all 25 template previews converted from GIF to animated WebP at **400×400**, matching the ComfyUI official workflow-templates preview format and size; JSON `preview` fields updated to `.webp`.
- **Total templates**: 144 → **176** (9 categories).

---

### v1.5.0 — 模板通用化 + 预览GIF + 双语使用说明 / Generic Templates + Preview GIFs + Bilingual Docs

**中文说明：**

- **全 144 模板通用化审计**：逐条检查全部模板，删除所有具体场景描述与人物形象细节（发型、服装、鞋帽、性别等）。图生视频（I2VA）/ 首尾帧（FL2VA）模板改为只引用输入图像（`<Picture 1>` / `<Picture 2>`）并描述动作、运镜、转场与氛围，不再覆盖输入图像的人物或场景特征；文生视频（T2VA）模板保留主题场景、去除人物形象细节与内置具体台词。
- **预览 GIF 上传**：将 `H3 Prompt/提示词模板预览/预览GIF` 目录内 25 个 GIF 一一对应上传至节点 `previews/` 与 `web/previews/`，并同步设置 JSON 的 `preview` 字段。
- **外部提示词端口**：新增可选 `external_prompt` STRING 输入端口（forceInput），可连接其他节点文本修改或补充模板提示词。
- **中英双语使用说明**：更新 `BSAI_H3_PromptTemplate_Doc.html`（新增"最新升级说明"章节、external_prompt 参数说明）与 `README.md`（示例5 改为中英双语、完整 8 大分类 144 模板）。
- **8 大分类 144 模板**：图生视频 / 文生视频 / 首尾帧 / 多模态融合 / 生长类 / 延时摄影 / 人物表情（46）/ 武打打斗（30），模板名称全部中英双语对照。

**English:**

- **All 144 templates genericized**: Every template audited; all specific scene descriptions and character-appearance details (hairstyle, clothing, shoes/hats, gender) removed. I2VA/FL2VA templates now only reference the input images (`<Picture 1>` / `<Picture 2>`) and describe action, camera, transitions, and atmosphere — never overwriting the input image's character or scene features. T2VA templates keep the theme scene but drop character-appearance details and built-in dialogue.
- **Preview GIFs uploaded**: 25 GIFs from the preview folder copied one-to-one into the node's `previews/` and `web/previews/`, with the JSON `preview` field set accordingly.
- **External prompt port**: New optional `external_prompt` STRING input (forceInput) to modify or supplement the template prompt from other nodes.
- **Bilingual docs**: Updated `BSAI_H3_PromptTemplate_Doc.html` (new "Latest Upgrade" section, external_prompt parameter) and `README.md` (bilingual Example 5, full 8-category / 144-template overview).
- **8 categories / 144 templates**: I2VA / T2VA / FL2VA / Ref2VA / Growth / Time-Lapse / Expression (46) / Combat (30), all with bilingual CN/EN names.

---

### v1.4.0 — BSAI 提示词模板 / Prompt Template Browser

**中文说明：**

新增 **BSAI H3 Prompt Template** 节点，提供分类化的 H3 提示词模板一键选择功能。根据 MiniMax H3 官方提示词 SKILL 及模型使用说明，全网收集整理各类 H3 提示词，分门别类做成可一键直接使用的模板。

新增功能：
- **三级分类体系**：一级分类（图生视频/文生视频/首尾帧/多模态融合/生长类/延时摄影/人物表情/武打打斗）→ 二级分类（线稿类/角色参考类/产品展示类/场景参考类/风格迁移类/电影场景类/舞蹈编排类/自然风光类/奇幻创意类/城市生活类/过渡变换类/变形效果类/品牌广告类/短剧叙事类/音乐节拍类/角色合成类/植物/动物/人物/物体生长类/建筑/产品组装/交通/自然景观延时类/基础/微表情/情绪过渡/社交面具/崩溃边缘类/拳脚/冷兵器/快慢镜头/打斗运镜/多人群战/特殊招式/触发词/多图成战类）→ 具体模板（**144 个**精选模板，名称中英双语对照）
- **GIF 预览**：25 个模板配有预览动画，选择模板后右侧显示循环缩略动画示意
- **可视化模板浏览器**：前端扩展提供级联下拉选择和模板列表，直观易用
- **三字段结构化输出**：所有模板均遵循 H3 官方三字段格式（integrated_multimodal_description / overall_soundscape / non_diegetic_music）
- **外部提示词端口**：`external_prompt` 可选输入端口，可连接其他节点文本修改或补充模板提示词
- **模板通用化**：所有模板不含具体场景/人物形象细节，I2VA/FL2VA 仅引用输入图像，避免覆盖输入特征
- **自定义模板**：支持在 `templates/prompt_templates.json` 中添加自定义模板
- **六个输出端口**：prompt_output（提示词）、template_name（模板名）、generation_mode（生成模式）、description（描述）、video_duration（时长）、preview_file（预览文件）

**English:**

Added **BSAI H3 Prompt Template** node for one-click categorized H3 prompt template selection. Based on MiniMax H3 official SKILL and model documentation, with prompts collected and categorized from various sources.

New features:
- **Three-level category system**: Category (I2VA/T2VA/FL2VA/Ref2VA/Growth/Time-Lapse/Expression/Combat) → Subcategory → Template (**144** curated templates with bilingual CN/EN names)
- **GIF preview**: 25 templates ship with preview animations shown in a loop when selected
- **Visual template browser**: Frontend extension with cascading dropdowns and template list
- **Three-field structured output**: All templates follow H3 official format (integrated_multimodal_description / overall_soundscape / non_diegetic_music)
- **External prompt port**: optional `external_prompt` input for modifying or supplementing the template prompt from other nodes
- **Generic templates**: no specific scene/character-appearance details; I2VA/FL2VA reference input images only, avoiding feature override
- **Custom templates**: Add custom templates in `templates/prompt_templates.json`
- **Six output ports**: prompt_output, template_name, generation_mode, description, video_duration, preview_file

---

### v1.3.0 — MTP/NextN 层自动剥离 / Auto MTP Layer Stripping

**中文说明：**

修复 Qwen3.5/3.6/3.8 GGUF 模型加载失败的问题。部分 GGUF 文件包含 MTP（多令牌预测）层元数据（`nextn_predict_layers`），但实际张量缺失（trunk-only GGUF）。由于 llama-cpp-python 0.3.36 未包含 llama.cpp [PR #25024](https://github.com/ggml-org/llama.cpp/pull/25024) 的修复，导致加载时报错 `missing tensor 'blk.64.ssm_conv1d.weight'`。

新增功能：
- **MTP 自动检测**：加载前检测 GGUF 元数据中的 `nextn_predict_layers` 字段
- **MTP 自动剥离**：生成去 MTP 版本的 `-noMTP.gguf` 文件，重计算张量偏移并调整 `block_count`
- **动态块索引计算**：从 `block_count` 元数据动态计算 MTP 块索引，而非硬编码 `blk.64`
- **异常回退**：加载失败时自动尝试 MTP 剥离并重试

首次加载时会自动生成 `-noMTP.gguf` 文件（约 3 分钟），之后直接使用缓存文件。该功能从 [BSAI_ComfyUI_Nodes](https://github.com/xm6018924/BSAI_ComfyUI_Nodes) 移植并改进。

**English:**

Fixed Qwen3.5/3.6/3.8 GGUF model loading failure. Some GGUF files contain MTP (Multi-Token Prediction) layer metadata (`nextn_predict_layers`) but the actual tensors are absent (trunk-only GGUF). Since llama-cpp-python 0.3.36 does not include the fix from llama.cpp [PR #25024](https://github.com/ggml-org/llama.cpp/pull/25024), loading fails with `missing tensor 'blk.64.ssm_conv1d.weight'`.

New features:
- **MTP auto-detection**: Checks GGUF metadata for `nextn_predict_layers` field before loading
- **MTP auto-stripping**: Generates a de-MTP'd `-noMTP.gguf` file with recalculated tensor offsets and adjusted `block_count`
- **Dynamic block index**: Computes MTP block index from `block_count` metadata instead of hardcoding `blk.64`
- **Exception fallback**: Automatically attempts MTP stripping and retry on load failure

The first load auto-generates the `-noMTP.gguf` file (~3 minutes); subsequent loads use the cached file. Ported and improved from [BSAI_ComfyUI_Nodes](https://github.com/xm6018924/BSAI_ComfyUI_Nodes).

---

### v1.2.0 — H3 加权提示词嵌入 / Weighted Prompt Embeddings (PR #15697)

**中文说明：**

新增 H3 加权提示词嵌入支持。通过 `weighted_keywords` 参数对提示词中的关键词施加权重控制，支持三种语法格式：`(关键词:1.5)` 增强权重、`(关键词:0.5)` 降低权重、`((关键词))` 逐层增加权重。

**English:**

Added H3 weighted prompt embeddings support. The `weighted_keywords` parameter applies weight control to keywords in the prompt, supporting three syntax formats: `(keyword:1.5)` to enhance, `(keyword:0.5)` to reduce, `((keyword))` for layered weight increase.

---

### v1.1.0 — Qwen3.8-VL 支持 / Qwen3.8-VL Support

**中文说明：**

新增 Qwen3.8-VL 模型系列支持并设为默认。Qwen3.8-VL 是阿里通义千问 2026 年 8 月发布的 27B 稠密视觉语言模型，基于 Qwen3.5 架构，使用相同的 ChatML 格式和 `enable_thinking` API。

**English:**

Added Qwen3.8-VL model family support and set as default. Qwen3.8-VL is a 27B dense vision-language model released by Alibaba in August 2026, based on the Qwen3.5 architecture with the same ChatML format and `enable_thinking` API.

---

### v1.0.0 — 初始版本 / Initial Release

**中文说明：**

根据 MiniMax H3 模型使用手册，实现提示词自动优化节点。支持本地模型和远程 API 两种模式，覆盖 13 种参考素材、五类生成模式、37+ 导演风格、20+ 摄影风格、50+ 电影类型、40+ 配乐风格。

**English:**

Initial release implementing automatic prompt optimization based on the MiniMax H3 model manual. Supports both local model and remote API modes, covering 13 reference material types, 5 generation modes, 37+ director styles, 20+ cinematography styles, 50+ film genres, and 40+ score styles.

## 许可证

MIT License

## 致谢

- 提示词规范来源：[MiniMax H3 模型使用手册](https://vrfi1sk8a0.feishu.cn/wiki/FIWjwgL33ipnkekzk30crmKUnIh)
- 本地模型推理：[llama-cpp-python](https://github.com/abetlen/llama-cpp-python)
- 远程 API 协议：[OpenAI API](https://platform.openai.com/docs/api-reference)
- 平台：[ComfyUI](https://github.com/comfyanonymous/ComfyUI)
