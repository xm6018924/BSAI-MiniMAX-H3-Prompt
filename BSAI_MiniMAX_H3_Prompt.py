"""
BSAI MiniMax H3 Prompt Optimizer Node

根据 MiniMax H3 模型使用手册，将用户手动输入的提示词优化为符合 H3 规范的完整提示词。
提示词公式：完整提示词 = 参考素材说明 + 核心创意 + 画面过程说明

参考文档：飞书 Wiki - MiniMax H3 模型使用手册
GitHub: https://github.com/xm6018924/BSAI-MiniMAX-H3-Prompt
"""

import os
import gc
import inspect

import folder_paths
import comfy.model_management as mm

try:
    from llama_cpp import Llama
except Exception:
    Llama = None

try:
    from llama_cpp.llama_chat_format import Qwen3VLChatHandler
except Exception:
    Qwen3VLChatHandler = None

try:
    from llama_cpp.llama_chat_format import Qwen35ChatHandler
except Exception:
    Qwen35ChatHandler = None

try:
    from llama_cpp.llama_chat_format import Gemma4ChatHandler
except Exception:
    Gemma4ChatHandler = None


# ============================================================
# 辅助函数
# ============================================================

def _bsai_list_llm_files():
    folder_name = "LLM"
    llm_dir = os.path.join(folder_paths.models_dir, folder_name)
    try:
        if folder_name not in folder_paths.folder_names_and_paths:
            folder_paths.folder_names_and_paths[folder_name] = (
                [llm_dir],
                {".gguf", ".safetensors", ".bin", ".pth", ".pt"},
            )
    except Exception:
        pass
    try:
        return folder_paths.get_filename_list("LLM")
    except Exception:
        return []


def _bsai_call_chat_completion(llm, messages, params):
    kwargs = dict(params or {})
    kwargs["messages"] = messages
    try:
        sig = inspect.signature(llm.create_chat_completion)
        has_var_kw = any(
            p.kind == inspect.Parameter.VAR_KEYWORD
            for p in sig.parameters.values()
        )
    except Exception:
        sig = None
        has_var_kw = True

    if sig is not None and not has_var_kw:
        allowed = sig.parameters
        if (
            "presence_penalty" in kwargs
            and "presence_penalty" not in allowed
            and "present_penalty" in allowed
        ):
            kwargs["present_penalty"] = kwargs.pop("presence_penalty")
        kwargs = {k: v for k, v in kwargs.items() if k in allowed}
    return llm.create_chat_completion(**kwargs)


def _bsai_normalize_seed(seed_value):
    try:
        seed_value = int(seed_value)
    except Exception:
        return None
    if seed_value < 0:
        return None
    return seed_value


def _bsai_reset_llm_state(llm):
    try:
        ctx = getattr(llm, "_ctx", None)
        if ctx is not None and hasattr(ctx, "memory_clear"):
            ctx.memory_clear(True)
    except Exception:
        pass
    try:
        reset = getattr(llm, "reset", None)
        if callable(reset):
            reset()
        elif hasattr(llm, "n_tokens"):
            llm.n_tokens = 0
    except Exception:
        pass


def _bsai_get_free_vram_bytes():
    """获取当前可用显存（字节）。返回 None 表示无法检测。"""
    try:
        import torch
        if torch.cuda.is_available():
            free, _total = torch.cuda.mem_get_info()
            return free
    except Exception:
        pass
    return None


def _bsai_auto_adjust_gpu_layers(model_path, mmproj_path, n_ctx, n_gpu_layers):
    """根据可用显存自动调整 GPU 层数，防止 OOM 导致段错误。

    返回 (adjusted_layers, warning_message) 元组。
    如果原值不是 -1（用户手动指定），则不调整。
    仅当显存确实无法容纳模型时才降级，避免误判。
    """
    if n_gpu_layers != -1:
        return n_gpu_layers, None

    free_vram = _bsai_get_free_vram_bytes()
    if free_vram is None:
        return n_gpu_layers, None

    model_size = os.path.getsize(model_path) if os.path.exists(model_path) else 0
    mmproj_size = os.path.getsize(mmproj_path) if mmproj_path and os.path.exists(mmproj_path) else 0

    # KV 缓存估算：基于模型文件大小和上下文长度
    # 经验公式：每 token KV cache ≈ 模型文件大小 * 1.3e-5（适用于 Q4 量化 GQA 模型）
    # 例如 5.5GB 的 9B Q4_K_M 模型，8192 ctx → ~585MB KV cache
    kv_cache_estimate = int(n_ctx * (model_size + mmproj_size) * 1.3e-5)

    # 安全余量：1GB（CUDA 运行时、ComfyUI 开销等）
    safety_margin = 1 * 1024 ** 3
    total_needed = model_size + mmproj_size + kv_cache_estimate + safety_margin

    free_vram_gb = free_vram / 1024 ** 3
    model_gb = model_size / 1024 ** 3
    mmproj_gb = mmproj_size / 1024 ** 3
    kv_gb = kv_cache_estimate / 1024 ** 3
    print(
        f"[BSAI H3 ModelLoader] VRAM 检测: "
        f"可用={free_vram_gb:.1f}GB, "
        f"模型={model_gb:.1f}GB, mmproj={mmproj_gb:.2f}GB, "
        f"KV缓存≈{kv_gb:.2f}GB, 合计≈{total_needed / 1024**3:.1f}GB"
    )

    if total_needed <= free_vram:
        return n_gpu_layers, None

    # 显存不足，需要部分 offload 到 CPU
    available_for_model = free_vram - safety_margin - mmproj_size - kv_cache_estimate
    if available_for_model <= 0:
        return 0, (
            f"⚠️ 显存严重不足！可用 VRAM={free_vram_gb:.1f}GB，"
            f"模型需要约={total_needed / 1024**3:.1f}GB。\n"
            f"已将 GPU 层数设为 0（纯 CPU 推理），速度会很慢。\n"
            "建议：\n"
            "  1. 使用更小的模型\n"
            "  2. 关闭其他占用显存的工作流节点\n"
            "  3. 增大系统虚拟内存"
        )

    # 估算可加载到 GPU 的层数比例
    ratio = available_for_model / model_size if model_size > 0 else 0
    # 用文件大小估算总层数
    est_layers_per_gb = 64 / (21.8)  # 约 2.94 层/GB
    est_total_layers = max(1, int(model_size / (1024**3) * est_layers_per_gb))
    adjusted_layers = max(1, int(est_total_layers * ratio))

    return adjusted_layers, (
        f"⚠️ 显存不足，无法全部加载到 GPU！\n"
        f"  可用 VRAM: {free_vram_gb:.1f}GB\n"
        f"  模型大小: {model_gb:.1f}GB + mmproj: {mmproj_gb:.2f}GB\n"
        f"  GPU层数从 -1（全部）自动调整为 {adjusted_layers}（部分 offload 到 CPU）\n"
        f"  推理速度会降低，但可避免崩溃。"
    )


# ============================================================
# 模型存储与管理
# ============================================================

class _BSAI_QwenStorage:
    model = None
    settings = None

    @classmethod
    def unload(cls):
        try:
            if cls.model and hasattr(cls.model, "close"):
                cls.model.close()
        except Exception:
            pass
        cls.model = None
        cls.settings = None
        gc.collect()
        mm.soft_empty_cache()

    @classmethod
    def load(cls, config):
        if Llama is None:
            raise RuntimeError("未检测到 llama-cpp-python（llama_cpp）。请先安装该依赖。")

        if cls.model and cls.settings == config:
            return cls.model

        cls.unload()

        model_path = os.path.join(folder_paths.models_dir, "LLM", config["model"])
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"找不到模型文件：{model_path}")

        mmproj = config.get("mmproj", "无")
        mmproj_path = None
        if mmproj and mmproj != "无":
            mmproj_path = os.path.join(folder_paths.models_dir, "LLM", mmproj)
            if not os.path.exists(mmproj_path):
                raise FileNotFoundError(f"找不到 mmproj 文件：{mmproj_path}")

        family = config["family"]
        think = config.get("think", False)
        n_ctx = int(config.get("n_ctx", 8192))
        n_gpu_layers = int(config.get("n_gpu_layers", -1))

        # ── VRAM 预检测：防止 OOM 导致 C++ 层段错误 ──
        n_gpu_layers, vram_warning = _bsai_auto_adjust_gpu_layers(
            model_path, mmproj_path, n_ctx, n_gpu_layers
        )
        if vram_warning:
            print(f"[BSAI H3 ModelLoader] {vram_warning}")

        chat_handler = None
        if mmproj_path:
            if family in ("Qwen3.5-VL", "Qwen3.6-VL"):
                if Qwen35ChatHandler is None:
                    raise RuntimeError(
                        "当前 llama-cpp-python 不支持 Qwen35ChatHandler，请更新 llama-cpp-python。"
                    )
                try:
                    chat_handler = Qwen35ChatHandler(
                        clip_model_path=mmproj_path, enable_thinking=think, verbose=False
                    )
                except Exception:
                    chat_handler = Qwen35ChatHandler(clip_model_path=mmproj_path, verbose=False)
            elif family == "Qwen3-VL":
                if Qwen3VLChatHandler is None:
                    raise RuntimeError(
                        "当前 llama-cpp-python 不支持 Qwen3VLChatHandler，请更新 llama-cpp-python。"
                    )
                try:
                    chat_handler = Qwen3VLChatHandler(
                        clip_model_path=mmproj_path, force_reasoning=think, verbose=False
                    )
                except Exception:
                    chat_handler = Qwen3VLChatHandler(clip_model_path=mmproj_path, verbose=False)
            elif family == "Gemma4":
                if Gemma4ChatHandler is None:
                    raise RuntimeError(
                        "当前 llama-cpp-python 不支持 Gemma4ChatHandler，请更新 llama-cpp-python到0.3.36+。"
                    )
                try:
                    chat_handler = Gemma4ChatHandler(
                        clip_model_path=mmproj_path, enable_thinking=think, verbose=False
                    )
                except Exception:
                    chat_handler = Gemma4ChatHandler(clip_model_path=mmproj_path, verbose=False)

        llama_kwargs = {
            "model_path": model_path,
            "chat_handler": chat_handler,
            "n_ctx": n_ctx,
            "n_gpu_layers": n_gpu_layers,
            "verbose": False,
        }

        # 尝试启用 flash attention 以减少显存使用
        try:
            sig = inspect.signature(Llama.__init__)
            if "flash_attn" in sig.parameters:
                llama_kwargs["flash_attn"] = True
        except Exception:
            pass

        try:
            cls.model = Llama(**llama_kwargs)
            cls.settings = dict(config)
            return cls.model
        except ValueError as e:
            if "Failed to create context with model" in str(e):
                raise RuntimeError(
                    "模型加载失败：Failed to create context with model\n"
                    "可能的原因：\n"
                    "1. 模型文件损坏或格式不兼容\n"
                    "2. llama-cpp-python 版本不支持该模型\n"
                    "3. 显存不足\n"
                    "4. 模型文件路径错误\n"
                    "建议：\n"
                    "- 检查模型文件完整性\n"
                    "- 更新 llama-cpp-python 到最新版本\n"
                    "- 减少 GPU 层数或使用更小的模型\n"
                    "- 确保模型路径正确"
                )
            raise


# ============================================================
# 模型加载节点
# ============================================================

class BSAI_H3_ModelLoader:
    """加载本地 GGUF 大语言模型，供 H3 提示词优化节点使用。"""

    @classmethod
    def INPUT_TYPES(s):
        all_files = _bsai_list_llm_files()
        model_list = [
            f
            for f in all_files
            if "mmproj" not in f.lower()
            and os.path.splitext(f)[1].lower() in [".gguf", ".safetensors", ".bin", ".pth", ".pt"]
        ]
        mmproj_list = ["无"] + [
            f
            for f in all_files
            if "mmproj" in f.lower()
            and os.path.splitext(f)[1].lower() in [".gguf", ".safetensors", ".bin"]
        ]

        if not model_list:
            model_list = ["（请把模型放到 models/LLM）"]

        return {
            "required": {
                "模型系列": (
                    ["Qwen3-VL", "Qwen3.5-VL", "Qwen3.6-VL", "Gemma4"],
                    {"default": "Qwen3.6-VL"},
                ),
                "主模型": (
                    model_list,
                    {"tooltip": "主模型文件（建议 .gguf）放到 ComfyUI/models/LLM/"},
                ),
                "视觉投影mmproj": (
                    mmproj_list,
                    {"default": "无", "tooltip": "多模态需要 mmproj；纯文本可选「无」。"},
                ),
                "启用思考": ("BOOLEAN", {"default": False}),
                "上下文长度": (
                    "INT",
                    {"default": 16384, "min": 1024, "max": 327680, "step": 256},
                ),
                "GPU层数": ("INT", {"default": -1, "min": -1, "max": 9999, "step": 1, "tooltip": "-1=全部上GPU。显存不足时自动降低层数防止崩溃。大模型(35B)建议手动设20-25"}),
            }
        }

    RETURN_TYPES = ("BSAI_QWEN_MODEL",)
    RETURN_NAMES = ("qwen模型",)
    FUNCTION = "load"
    CATEGORY = "BSAI"
    DESCRIPTION = "加载本地 GGUF 大语言模型，供 H3 提示词优化节点使用。"

    def load(self, 模型系列, 主模型, 视觉投影mmproj, 启用思考, 上下文长度, GPU层数):
        if 主模型.startswith("（请把模型放到"):
            raise RuntimeError("未找到可用模型文件。请把模型放到 ComfyUI/models/LLM/ 后重启。")

        if 模型系列 in ("Qwen3-VL", "Qwen3.5-VL", "Qwen3.6-VL", "Gemma4"):
            if 视觉投影mmproj == "无":
                raise RuntimeError(
                    f"{模型系列} 是多模态模型，需要选择视觉投影mmproj文件。\n"
                    "请在 '视觉投影mmproj' 选项中选择对应的 mmproj 文件。"
                )

        config = {
            "family": 模型系列,
            "model": 主模型,
            "mmproj": 视觉投影mmproj,
            "think": bool(启用思考),
            "n_ctx": int(上下文长度),
            "n_gpu_layers": int(GPU层数),
        }
        model = _BSAI_QwenStorage.load(config)
        return (model,)


# ============================================================
# H3 提示词优化系统提示词（根据飞书文档整理）
# ============================================================

_H3_SYSTEM_PROMPT = """你是 MiniMax H3 视频模型的提示词优化专家。你的任务是根据用户输入的简单提示词，按照 MiniMax H3 的规范优化为完整的、结构化的视频生成提示词。

## 一、提示词整体公式

完整提示词 = 参考素材说明 + 核心创意 + 画面过程说明

三个部分用【参考素材说明】【核心创意】【画面过程描述】作为段落标题分隔。

## 二、四个要素详解

### 1. 参考素材说明
告诉 H3 你上传的每个素材是干什么用的：
- 写清素材编号：按上传顺序，如 @图片1、@音频2、@视频3
- 写清每个素材的用途：
  - 人物参考（锁定脸/形象）
  - 物体参考（锁定物体）
  - 场景参考（锁定场景）
  - 关键帧（首帧/尾帧，需明确指出）
  - 音色参考（锁定音色）
  - 故事版（根据故事版分镜生成镜头内容）
  - 风格参考（根据图片风格生成类似风格内容）
  - 构图参考（根据图片中物体构图生成对应构图）
  - 音频复用（生成视频的音频直接复用参考音频素材）
  - 音频部分复用（生成视频某声音轨道/某时间段部分复用参考音频素材）
  - 动作参考（锁定动作）
  - 运镜参考（锁定运镜）
  - 视频编辑（对视频某内容进行增删改）
- 没有上传素材时整段跳过，不写【参考素材说明】部分
- 如果素材中有想要保持的特征，建议明确写出来
- 音频复刻中如对歌词/对白内容保持有高要求，强烈建议补充具体歌词文本

示例：
@图片1 提供了主角的形象参考（锁脸），@视频2 提供了动作参考。

### 2. 核心创意
用一句话锁定全片信息，必须包含以下要素：
- 主体：谁/什么（人/物/动物/其他）
- 地点：在哪里
- 事件：在做什么
- 题材/风格：什么调性（写实/动画/电影感/广告片/纪录片/赛博朋克/霓虹灯美学/涂鸦风等）
- 特殊运镜：是否需要特殊镜头（航拍/一镜到底/慢动作等）
  - 默认会切镜（普通切镜 cut / 叠化切镜 fade / 随节奏卡点切镜 / 快切）
  - 运镜风格写清即可；注意环绕运镜建议用 truck left+pan right 或 truck right+pan left，而非直接说"环绕运镜"
- 时长和宽高比信息
- 如果任何元素与引用素材有关联，用 @图片1/@音频1/@视频1 等方式强调

示例：
一位穿汉服的年轻女子（@图片1）在樱花纷飞的庭院里舞剑，古典国风，电影质感，一镜到底，10秒，16:9横版。

### 3. 画面过程说明
按时间轴或故事线分段写，每个分镜/时间段包含两部分：

#### 想要（画面里要出现什么）
- 画面景别 + 内容 + 运镜 + 动作 + 台词 + 音效
- 以切镜 shot 作为时间戳的分段
- 每个 shot 内部写好：景别、具体内容、shot 内部运镜、人物台词、音效
- 台词长短尽量和镜头长短对齐（很多口型问题来自于此）
- 如果一句台词跨 shot，用"接着上个 shot 继续说"这样的描述
- 如果希望视频中出现具体文字、Logo、标题、标语等，一定要把文字原文写出来
  例如：画面中出现英文："H3"。或：手机屏幕上显示标题："AI Video Creation"，按钮文字为："Start Now"。

#### 不想要（视频里不要出现什么）
- 不想要背景音乐时，需明确写明：
  非叙事性音乐：N/A
  或使用英文格式："non_diegetic_music": N/A
  不要额外添加背景音乐。

#### 写作原则
- 尽量少写比喻句，多写看得见的画面
- 使用具体、直接、可视化的描述，少写需要"意会"的句子
- 如有台词，必须明确具体内容
  例如：一位穿汉服的年轻女子说："你来了，剑等你好久了。"

示例：
0-3 秒：全景，女子（@图片1）从画面左侧缓步走入樱花庭院（@图片2），背景虚化，没有对白，只有脚步声。
3-8 秒：切镜到女子（@图片1）的中景，她拔出长剑（@图片3），缓缓起势，樱花瓣从树上飘落。镜头推进。
8-12 秒：切镜到特写，剑光一闪，慢动作，樱花被剑气激得四散。
非叙事性音乐：N/A

## 三、镜头拆分建议
- H3 有基础的分镜能力，对切镜点遵从较强
- 台词长短和画面变化内容需要合乎每个 shot 的长短逻辑，避免一个 3s shot 说很大一段话
- H3 能响应跨 shot（J-cut、L-cut）的台词，只要明确写出一句台词跨了哪些 shot
- 画面内说话人需写清是哪个角色；画面外说话人写清是画外说话人
- 切镜时可明确写出切镜到什么景别、具体主体是之前的哪个角色，有助于跨镜头一致性

## 四、三类生成模式

### 1. 纯文字生成视频
- 不依赖任何参考素材，直接根据文字提示词建立主体、场景、动作
- 文字描述要更具体（主体外观、场景细节、动作描述都要写清）
- 多用「大全景交代空间 + 中景承载动作 + 特写强调细节」的分层写法
- 示例：写实自然纪录片风格，电影级真实光影。清晨的薄雾中，在广阔的湿地芦苇荡里，一只优雅的白鹤单腿站立在浅水中，缓慢转头看向镜头。柔和的逆光，雾气在光束里飘动。

### 2. 上传图片生成视频（图生视频）
- 只上传 1 张图：说清楚是首帧（视频开头画面）还是尾帧（视频结尾画面）
- 上传 2 张图（首+尾帧）：H3 不会自动加切镜，只补两帧之间的动作、光影、声音
- 示例：@图片1 是首帧参考图：女子持剑站在樱花树下。让她从持剑起势到舞剑完毕，自然衔接，不要切镜。

### 3. 上传多模态素材融合（多模态参考）
- 可同时上传：人物图 + 动作视频 + 场景图 + 音乐
- 每个素材都要写清它的角色：
  @图片1 → 人物参考（锁脸）
  @视频1 → 动作参考（锁动作）
  @音频1 → 节奏/情绪参考
- 示例：@图片1 是人物参考（锁这位女子的脸），@视频1 是动作参考（用里面的舞剑动作），@音频1 是情绪参考（古风配乐）。让这位女子在樱花庭院里按视频里的动作舞剑。

## 五、容易踩的坑（必须避免）
| 常见问题 | 怎么改 |
|-|-|
| 只写一段话没分段 | 按 3 段公式拆开写 |
| 素材上传了但没说用途 | 补一句「@图片1 是 XX 参考」 |
| 想用音乐但说「不要 BGM」 | 这两个矛盾，要么删一个，要么分场景写 |
| 想一镜到底但写了很多分镜 | 全文保持一段情节描述，删掉【镜头 N】结构 |
| 想要主角脸一致但没传图 | 一定要上传人物参考图，并标注「人物参考」 |
| 提示词太短（H3 没素材可参考时） | 至少写出主体外观 + 场景细节 + 动作 + 风格 |

## 六、输出要求
1. 严格按照【参考素材说明】+【核心创意】+【画面过程描述】三段结构输出
2. 如果是纯文字生成视频模式且无素材，则省略【参考素材说明】部分
3. 画面过程描述要按时间轴分段，使用 shot 或时间段作为分段标记
4. 如无特殊要求，不要在最后添加"非叙事性音乐：N/A"（除非用户明确表示不需要背景音乐）
5. 直接输出优化后的提示词，不要添加任何解释性文字、前言或后记
6. 提示词总字数不超过 7000 字符
7. 保持用户原始创意意图，不要擅自改变用户描述的核心内容
8. 输出语言与用户输入语言保持一致"""


# ============================================================
# H3 提示词优化节点
# ============================================================

class BSAI_MiniMAX_H3_Prompt:
    """MiniMax H3 提示词优化节点

    根据飞书文档《MiniMax H3 模型使用手册》的规范，
    将用户手动输入的提示词优化为符合 H3 三段公式（参考素材说明 + 核心创意 + 画面过程说明）的完整提示词。
    """

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "qwen模型": ("BSAI_QWEN_MODEL",),
                "用户提示词": (
                    "STRING",
                    {
                        "default": "",
                        "multiline": True,
                        "tooltip": "用户手动输入的原始提示词，节点会根据 H3 规范自动优化",
                    },
                ),
                "生成模式": (
                    ["纯文字生成视频", "上传图片生成视频", "上传多模态素材融合"],
                    {"default": "纯文字生成视频", "tooltip": "选择视频生成模式，影响提示词优化方向"},
                ),
                "视频时长": (
                    "INT",
                    {"default": 10, "min": 4, "max": 15, "step": 1, "tooltip": "H3 支持 4-15 秒输出"},
                ),
                "宽高比": (
                    ["21:9", "16:9", "4:3", "1:1", "3:4", "9:16"],
                    {"default": "16:9", "tooltip": "输出视频宽高比"},
                ),
                "不需要背景音乐": (
                    "BOOLEAN",
                    {"default": False, "tooltip": "勾选后会在提示词末尾添加「非叙事性音乐：N/A」"},
                ),
                "补充要求": (
                    "STRING",
                    {
                        "default": "",
                        "multiline": True,
                        "tooltip": "可选：额外的优化要求或风格偏好（如特定运镜、色调、节奏等）",
                    },
                ),
                "最大生成token": ("INT", {"default": 4096, "min": 256, "max": 65536, "step": 1, "tooltip": "会自动限制为不超过上下文长度"}),
                "温度": ("FLOAT", {"default": 0.7, "min": 0.0, "max": 2.0, "step": 0.01}),
                "top_p": ("FLOAT", {"default": 0.9, "min": 0.0, "max": 1.0, "step": 0.01}),
                "top_k": ("INT", {"default": 20, "min": 0, "max": 200, "step": 1}),
                "重复惩罚": ("FLOAT", {"default": 1.0, "min": 0.5, "max": 2.0, "step": 0.01}),
                "频率惩罚": ("FLOAT", {"default": 0.0, "min": 0.0, "max": 2.0, "step": 0.01}),
                "存在惩罚": ("FLOAT", {"default": 0.0, "min": 0.0, "max": 2.0, "step": 0.01}),
                "seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff, "step": 1}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("提示词输出",)
    FUNCTION = "optimize_prompt"
    CATEGORY = "BSAI"
    DESCRIPTION = """
根据 MiniMax H3 模型使用手册，将用户手动输入的提示词优化为符合 H3 规范的完整提示词。
提示词公式：完整提示词 = 参考素材说明 + 核心创意 + 画面过程说明。
需要配合 BSAI H3 Model Loader 节点使用。
"""

    def optimize_prompt(
        self,
        qwen模型,
        用户提示词,
        生成模式,
        视频时长,
        宽高比,
        不需要背景音乐,
        补充要求,
        最大生成token,
        温度,
        top_p,
        top_k,
        重复惩罚,
        频率惩罚,
        存在惩罚,
        seed,
    ):
        llm = qwen模型

        if not hasattr(llm, "create_chat_completion"):
            raise TypeError(
                f"无效的模型输入：期望 Llama 模型对象，但收到 {type(llm).__name__} 类型。"
                "请检查工作流连接，确保 'qwen模型' 输入连接到 BSAI_H3_ModelLoader 的输出。"
            )

        user_prompt = (用户提示词 or "").strip()
        if not user_prompt:
            raise ValueError("用户提示词不能为空。请输入需要优化的提示词。")

        mode_hints = {
            "纯文字生成视频": "当前为纯文字生成视频模式（无参考素材），请确保提示词中包含详细的主体外观、场景细节、动作描述和风格说明。不需要写【参考素材说明】部分。",
            "上传图片生成视频": "当前为图生视频模式，用户会上传图片。请在提示词中注明 @图片1 是首帧还是尾帧参考。如果用户提到两张图，请说明是首帧+尾帧。",
            "上传多模态素材融合": "当前为多模态参考模式，用户可能上传人物图、动作视频、场景图、音乐等多种素材。请为每个素材写清编号和用途（如 @图片1 → 人物参考、@视频1 → 动作参考等）。",
        }

        user_message_parts = [
            f"【生成模式】{生成模式}",
            f"【视频时长】{视频时长}秒（H3 支持 4-15 秒）",
            f"【宽高比】{宽高比}",
            f"【背景音乐】{'不需要背景音乐，请在提示词末尾添加 非叙事性音乐：N/A' if 不需要背景音乐 else '无特殊要求（可包含背景音乐）'}",
        ]

        if 补充要求 and 补充要求.strip():
            user_message_parts.append(f"【补充要求】{补充要求.strip()}")

        user_message_parts.append(f"【模式提示】{mode_hints.get(生成模式, '')}")
        user_message_parts.append(f"【用户原始提示词】\n{user_prompt}")
        user_message_parts.append(
            "\n请根据以上信息，按照 H3 提示词规范优化为完整的结构化提示词。直接输出优化后的提示词，不要添加任何解释。"
        )

        user_message = "\n".join(user_message_parts)

        messages = [
            {"role": "system", "content": _H3_SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ]

        try:
            max_tokens_val = int(最大生成token)
        except (TypeError, ValueError):
            raise TypeError(
                f"最大生成token 必须是整数类型，但收到 {type(最大生成token).__name__} 类型。"
            )

        normalized_seed = _bsai_normalize_seed(seed)

        # ── max_tokens 安全限制：防止超过上下文长度导致段错误 ──
        # llama-cpp-python 中 n_ctx 是方法而非属性，需要调用获取值
        try:
            n_ctx_raw = getattr(llm, "n_ctx", 4096)
            n_ctx = int(n_ctx_raw()) if callable(n_ctx_raw) else int(n_ctx_raw)
        except Exception:
            n_ctx = 4096
        prompt_text = _H3_SYSTEM_PROMPT + user_message
        est_prompt_tokens = int(len(prompt_text) * 1.2)
        safe_max_tokens = min(max_tokens_val, n_ctx - est_prompt_tokens - 256)
        if safe_max_tokens < 512:
            safe_max_tokens = min(max_tokens_val, max(256, n_ctx // 4))
            print(
                f"[BSAI H3] 警告：提示词较长（约{est_prompt_tokens} tokens），"
                f"上下文长度仅{n_ctx}，max_tokens 已限制为 {safe_max_tokens}。"
                f"建议在 ModelLoader 中增大「上下文长度」到 16384+。"
            )
        elif safe_max_tokens < max_tokens_val:
            print(
                f"[BSAI H3] max_tokens 从 {max_tokens_val} 限制为 {safe_max_tokens}"
                f"（上下文长度 {n_ctx} - 提示词约 {est_prompt_tokens} tokens - 安全余量 256）"
            )

        # 只保留最核心的参数，避免可选参数在 C++ 层触发段错误。
        # Qwen-VL 模型的 chat_handler 对部分参数（如 presence_penalty、
        # frequency_penalty、top_k、repeat_penalty）的兼容性较差，可能导致 segfault。
        params = {
            "max_tokens": safe_max_tokens,
            "temperature": float(温度),
            "top_p": float(top_p),
            "stream": False,
        }
        if normalized_seed is not None:
            params["seed"] = normalized_seed

        # 不调用 _bsai_reset_llm_state(llm)：
        # llm.reset() / ctx.memory_clear() 在部分 llama-cpp-python 版本
        # 和 Qwen-VL 模型组合下会导致段错误（segfault），直接使 Python
        # 进程崩溃。create_chat_completion 本身会处理上下文，无需手动重置。

        try:
            out = _bsai_call_chat_completion(llm, messages=messages, params=params)
        except RuntimeError as e:
            if "Context Shift is explicitly disabled" in str(e):
                current_n_ctx = getattr(llm, "n_ctx", "未知")
                raise RuntimeError(
                    "Context Shift 被 C++ 后端禁用（M-RoPE 模型不支持上下文滑动窗口）。\n"
                    f"当前 n_ctx = {current_n_ctx}，无法容纳完整对话。\n"
                    "请在 BSAI_H3_ModelLoader 节点中增大「上下文长度」：\n"
                    "  - 纯文本建议 16384\n"
                    "  - 含图片/视频建议 32768 或更高\n"
                    f"原始错误：{e}"
                ) from e
            raise

        try:
            text = out["choices"][0]["message"]["content"]
        except Exception:
            text = str(out)

        return (text.lstrip().removeprefix(": ").strip(),)


# ============================================================
# 模型卸载节点
# ============================================================

class BSAI_H3_UnloadModel:
    """卸载已加载的 LLM 模型，释放显存。"""

    @classmethod
    def INPUT_TYPES(s):
        return {"required": {"任意输入": ("*",)}}

    RETURN_TYPES = ("*",)
    RETURN_NAMES = ("任意输出",)
    FUNCTION = "run"
    CATEGORY = "BSAI"
    DESCRIPTION = "卸载已加载的 LLM 模型，释放显存。"

    def run(self, 任意输入):
        _BSAI_QwenStorage.unload()
        return (任意输入,)


NODE_CLASS_MAPPINGS = {
    "BSAI_MiniMAX H3 prompt": BSAI_MiniMAX_H3_Prompt,
    "BSAI_H3_ModelLoader": BSAI_H3_ModelLoader,
    "BSAI_H3_UnloadModel": BSAI_H3_UnloadModel,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "BSAI_MiniMAX H3 prompt": "BSAI MiniMAX H3 Prompt",
    "BSAI_H3_ModelLoader": "BSAI H3 Model Loader",
    "BSAI_H3_UnloadModel": "BSAI H3 Unload Model",
}
