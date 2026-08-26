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

#### 三级分类体系 / Three-Level Category System (176 templates / 9 categories)

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

#### 使用方法 / Usage

1. 在 ComfyUI 中添加 `BSAI H3 Prompt Template` 节点
2. 节点上方显示可视化模板浏览器：
   - **一级分类**下拉框：选择生成模式（图生视频 / 文生视频 / 首尾帧生成 / 多模态融合 / 生长 / 延时 / 表情 / 武打 / 电影运镜）
   - **二级分类**下拉框：选择模板子类（线稿类 / 角色参考类 / 产品展示类 等）
   - **模板列表**：点击任意模板即可选择
3. 右侧显示 **WebP 预览动画**（400×400 动图，遵循 ComfyUI 官方 workflow templates 规格）和模板信息（生成模式 / 时长 / 是否需要图片）
4. `prompt_output` 输出端口直接输出完整的 H3 三字段提示词
5. 可将输出连接到视频生成节点，或先连接到 `BSAI MiniMAX H3 Prompt` 节点进一步优化
6. `external_prompt` 可选输入端口可连接其他节点文本，用于修改或补充模板提示词

**EN:**
1. Add the `BSAI H3 Prompt Template` node in ComfyUI.
2. A visual template browser appears above the node:
   - **Category** dropdown: choose a generation mode (I2VA / T2VA / FL2VA / Ref2VA / Growth / Time-Lapse / Expression / Combat / Cinematic)
   - **Subcategory** dropdown: choose a template subclass
   - **Template list**: click any template to select it
3. The right panel shows a **WebP preview animation** (400×400, per ComfyUI official workflow-templates spec) and template info (generation mode / duration / needs-image).
4. The `prompt_output` port directly outputs the full H3 three-field prompt.
5. Connect the output to a video generator, or chain it into the `BSAI MiniMAX H3 Prompt` node for further optimization.
6. The optional `external_prompt` input port accepts text from other nodes to modify or supplement the template prompt.

> **模板通用化 / Generic templates:** 全部 144 个模板均经过审计与通用化重写，不包含具体场景或人物形象细节（发型、服装、鞋帽、性别等）。图生视频 / 首尾帧模板只引用输入图像（`<Picture 1>` / `<Picture 2>`）并描述动作、运镜、氛围，不会覆盖输入图像的人物或场景特征。All 144 templates have been audited and genericized — no specific scene or character-appearance details. I2VA/FL2VA templates only reference the input images and describe action/camera/atmosphere, so they never overwrite the input image features.

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
