"""
BSAI MiniMax H3 Prompt Optimizer Node

根据 MiniMax H3 模型使用手册，将用户手动输入的提示词优化为符合 H3 规范的完整提示词。
提示词公式：完整提示词 = 参考素材说明 + 核心创意 + 画面过程说明

参考文档：飞书 Wiki - MiniMax H3 模型使用手册
GitHub: https://github.com/xm6018924/BSAI-MiniMAX-H3-Prompt
"""

import os
import io
import gc
import base64
import inspect

import folder_paths
import comfy.model_management as mm

try:
    import torch
except Exception:
    torch = None

try:
    from PIL import Image as PILImage
except Exception:
    PILImage = None

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


def _bsai_image_tensor_to_data_uri(image_input):
    """将 ComfyUI IMAGE 张量转换为 base64 JPEG data URI。

    ComfyUI IMAGE 格式: torch.Tensor, shape=[B, H, W, C], dtype=float32, 值域[0,1]
    返回 list[str]，每个元素是一张图的 data URI。
    """
    if image_input is None or PILImage is None or torch is None:
        return []

    images = image_input
    # 单张图可能无 batch 维度，统一添加
    if images.ndim == 3:
        images = images.unsqueeze(0)

    data_uris = []
    for i in range(images.shape[0]):
        img_tensor = images[i]
        # [H, W, C] float32 [0,1] → numpy uint8 [0,255]
        img_np = (img_tensor.cpu().numpy() * 255.0).clip(0, 255).astype("uint8")
        pil_img = PILImage.fromarray(img_np)
        buf = io.BytesIO()
        # 限制最大边长，减少 token 消耗
        max_side = 1024
        if max(pil_img.size) > max_side:
            ratio = max_side / max(pil_img.size)
            pil_img = pil_img.resize(
                (int(pil_img.size[0] * ratio), int(pil_img.size[1] * ratio)),
                PILImage.LANCZOS,
            )
        pil_img.save(buf, format="JPEG", quality=85)
        b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
        data_uris.append(f"data:image/jpeg;base64,{b64}")
    return data_uris


def _bsai_build_multimodal_content(text, image_data_uris, image_label):
    """构建多模态 user message content（OpenAI 兼容格式）。

    text: 纯文本部分
    image_data_uris: list[str] data URI
    image_label: 每张图的标注前缀，如 "图片1"
    返回 list[dict]，每个 dict 是 {"type": "text"/"image_url", ...}
    """
    content = []
    if text:
        content.append({"type": "text", "text": text})
    for idx, uri in enumerate(image_data_uris):
        content.append(
            {
                "type": "image_url",
                "image_url": {"url": uri},
            }
        )
        # 在图片后追加标注文本，帮助模型理解图片编号
        label = f"{image_label}{idx + 1}" if image_label else f"图片{idx + 1}"
        content.append(
            {"type": "text", "text": f"（以上是 {label}）"}
        )
    return content


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


def _bsai_is_model_valid(llm):
    """Check if a Llama model object is still valid (not closed/unloaded).

    After unload(), the model's internal _ctx is set to None, causing
    KeyError: None or segfault when accessed. This function detects that.
    """
    if llm is None:
        return False
    try:
        # n_ctx() will fail if the model has been closed
        n_ctx_raw = getattr(llm, "n_ctx", None)
        if n_ctx_raw is None:
            return False
        if callable(n_ctx_raw):
            _ = n_ctx_raw()
        return True
    except Exception:
        return False


# ============================================================
# Model Storage & Management
# ============================================================

class _BSAI_QwenStorage:
    model = None
    settings = None  # Retained after unload() for auto-reload

    @classmethod
    def unload(cls):
        try:
            if cls.model and hasattr(cls.model, "close"):
                cls.model.close()
        except Exception:
            pass
        cls.model = None
        # Keep settings for auto-reload on next load() call
        gc.collect()
        mm.soft_empty_cache()

    @classmethod
    def load(cls, config):
        if Llama is None:
            raise RuntimeError("llama-cpp-python (llama_cpp) not detected. Please install this dependency.")

        # Check if cached model is still valid and matches config
        if cls.model is not None and cls.settings == config:
            if _bsai_is_model_valid(cls.model):
                return cls.model
            # Model was closed externally (e.g. by UnloadModel), reload
            cls.model = None

        # If settings differ, do a full unload first
        if cls.model is not None:
            cls.unload()

        model_path = os.path.join(folder_paths.models_dir, "LLM", config["model"])
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model file not found: {model_path}")

        mmproj = config.get("mmproj", "None")
        mmproj_path = None
        if mmproj and mmproj not in ("None", "无", ""):
            mmproj_path = os.path.join(folder_paths.models_dir, "LLM", mmproj)
            if not os.path.exists(mmproj_path):
                raise FileNotFoundError(f"mmproj file not found: {mmproj_path}")

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
    """Load a local GGUF LLM model for H3 prompt optimization."""

    @classmethod
    def INPUT_TYPES(s):
        all_files = _bsai_list_llm_files()
        model_list = [
            f
            for f in all_files
            if "mmproj" not in f.lower()
            and os.path.splitext(f)[1].lower() in [".gguf", ".safetensors", ".bin", ".pth", ".pt"]
        ]
        mmproj_list = ["None"] + [
            f
            for f in all_files
            if "mmproj" in f.lower()
            and os.path.splitext(f)[1].lower() in [".gguf", ".safetensors", ".bin"]
        ]

        if not model_list:
            model_list = ["(Place models in models/LLM)"]

        return {
            "required": {
                "model_family": (
                    ["Qwen3-VL", "Qwen3.5-VL", "Qwen3.6-VL", "Gemma4"],
                    {"default": "Qwen3.6-VL", "tooltip": "Model family / 模型系列"},
                ),
                "model_file": (
                    model_list,
                    {"tooltip": "Main model file (.gguf recommended) in ComfyUI/models/LLM/ / 主模型文件"},
                ),
                "mmproj": (
                    mmproj_list,
                    {"default": "None", "tooltip": "Multimodal mmproj file; 'None' for text-only / 视觉投影文件"},
                ),
                "enable_thinking": ("BOOLEAN", {"default": False, "tooltip": "Enable thinking/reasoning mode / 启用思考模式"}),
                "context_length": (
                    "INT",
                    {"default": 16384, "min": 1024, "max": 327680, "step": 256, "tooltip": "Context length, recommend 16384+ / 上下文长度，建议16384以上"},
                ),
                "gpu_layers": ("INT", {"default": -1, "min": -1, "max": 9999, "step": 1, "tooltip": "-1=all on GPU. Auto-reduces if VRAM insufficient / GPU层数，-1为全部上GPU"}),
            }
        }

    RETURN_TYPES = ("BSAI_QWEN_MODEL",)
    RETURN_NAMES = ("qwen_model",)
    FUNCTION = "load"
    CATEGORY = "BSAI"
    DESCRIPTION = "Load a local GGUF LLM model for H3 prompt optimization."

    def load(self, model_family, model_file, mmproj, enable_thinking, context_length, gpu_layers):
        if model_file.startswith("(Place models"):
            raise RuntimeError("No model files found. Place models in ComfyUI/models/LLM/ and restart.")

        if model_family in ("Qwen3-VL", "Qwen3.5-VL", "Qwen3.6-VL", "Gemma4"):
            if mmproj == "None":
                raise RuntimeError(
                    f"{model_family} is a multimodal model that requires an mmproj file.\n"
                    "Please select the corresponding mmproj file in the 'mmproj' option."
                )

        config = {
            "family": model_family,
            "model": model_file,
            "mmproj": mmproj,
            "think": bool(enable_thinking),
            "n_ctx": int(context_length),
            "n_gpu_layers": int(gpu_layers),
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
    """MiniMax H3 Prompt Optimizer Node

    Optimizes user prompts into H3-compliant structured prompts following
    the H3 formula: Reference Description + Core Creative + Scene Process.
    """

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "qwen_model": ("BSAI_QWEN_MODEL",),
                "user_prompt": (
                    "STRING",
                    {
                        "default": "",
                        "multiline": True,
                        "tooltip": "User's original prompt to be optimized / 用户原始提示词",
                    },
                ),
                "generation_mode": (
                    ["Text to Video", "Image to Video", "Multimodal Fusion"],
                    {"default": "Text to Video", "tooltip": "Video generation mode / 生成模式"},
                ),
                "video_duration": (
                    "INT",
                    {"default": 10, "min": 4, "max": 15, "step": 1, "tooltip": "H3 supports 4-15 seconds / 视频时长"},
                ),
                "aspect_ratio": (
                    ["21:9", "16:9", "4:3", "1:1", "3:4", "9:16"],
                    {"default": "16:9", "tooltip": "Output video aspect ratio / 宽高比"},
                ),
                "no_bgm": (
                    "BOOLEAN",
                    {"default": False, "tooltip": "If checked, adds 'non_diegetic_music: N/A' / 不需要背景音乐"},
                ),
                "extra_requirements": (
                    "STRING",
                    {
                        "default": "",
                        "multiline": True,
                        "tooltip": "Optional: extra style preferences / 补充要求",
                    },
                ),
                "max_tokens": ("INT", {"default": 4096, "min": 256, "max": 65536, "step": 1, "tooltip": "Auto-limited to context length / 最大生成token"}),
                "temperature": ("FLOAT", {"default": 0.7, "min": 0.0, "max": 2.0, "step": 0.01, "tooltip": "LLM sampling temperature / 温度"}),
                "top_p": ("FLOAT", {"default": 0.9, "min": 0.0, "max": 1.0, "step": 0.01}),
                "top_k": ("INT", {"default": 20, "min": 0, "max": 200, "step": 1}),
                "repeat_penalty": ("FLOAT", {"default": 1.0, "min": 0.5, "max": 2.0, "step": 0.01}),
                "frequency_penalty": ("FLOAT", {"default": 0.0, "min": 0.0, "max": 2.0, "step": 0.01}),
                "presence_penalty": ("FLOAT", {"default": 0.0, "min": 0.0, "max": 2.0, "step": 0.01}),
                "seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff, "step": 1}),
            },
            "optional": {
                "image_1": ("IMAGE", {"tooltip": "Optional: reference image 1 / 参考图片1"}),
                "image_2": ("IMAGE", {"tooltip": "Optional: reference image 2 / 参考图片2"}),
                "image_3": ("IMAGE", {"tooltip": "Optional: reference image 3 / 参考图片3"}),
                "image_4": ("IMAGE", {"tooltip": "Optional: reference image 4 / 参考图片4"}),
                "image_5": ("IMAGE", {"tooltip": "Optional: reference image 5 / 参考图片5"}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("prompt_output",)
    FUNCTION = "optimize_prompt"
    CATEGORY = "BSAI"
    DESCRIPTION = """
Optimize user prompts into H3-compliant structured prompts.
H3 formula: Reference Description + Core Creative + Scene Process.
Requires BSAI H3 Model Loader node.
"""

    def optimize_prompt(
        self,
        qwen_model,
        user_prompt,
        generation_mode,
        video_duration,
        aspect_ratio,
        no_bgm,
        extra_requirements,
        max_tokens,
        temperature,
        top_p,
        top_k,
        repeat_penalty,
        frequency_penalty,
        presence_penalty,
        seed,
        image_1=None,
        image_2=None,
        image_3=None,
        image_4=None,
        image_5=None,
    ):
        llm = qwen_model

        # ── Auto-recovery: if model was unloaded (e.g. by BSAI_H3_UnloadModel
        # in a previous run), ComfyUI's cache may still hold the closed model
        # object. Detect this and reload automatically. ──
        if not _bsai_is_model_valid(llm):
            if _BSAI_QwenStorage.settings is not None:
                print("[BSAI H3] Model was unloaded, auto-reloading from cached settings...")
                llm = _BSAI_QwenStorage.load(_BSAI_QwenStorage.settings)
            else:
                raise RuntimeError(
                    "Model is invalid (closed/unloaded) and no cached settings "
                    "available for auto-reload. Please re-run BSAI_H3_ModelLoader."
                )

        if not hasattr(llm, "create_chat_completion"):
            raise TypeError(
                f"Invalid model input: expected Llama model object, got {type(llm).__name__}."
                "Check workflow connections: 'qwen_model' input should connect to BSAI_H3_ModelLoader output."
            )

        prompt_text_input = (user_prompt or "").strip()
        if not prompt_text_input:
            raise ValueError("user_prompt cannot be empty. Please enter a prompt to optimize.")

        mode_hints = {
            "Text to Video": "Current mode: Text to Video (no reference materials). Ensure the prompt contains detailed subject appearance, scene details, action descriptions, and style. Skip the [Reference Description] section.",
            "Image to Video": "Current mode: Image to Video. The user will upload images. Please indicate in the prompt whether @image_1 is a first frame or last frame reference. If two images are provided, specify first frame + last frame.",
            "Multimodal Fusion": "Current mode: Multimodal Fusion. The user may upload character images, action videos, scene images, music, etc. Write clear labels and usage for each material (e.g., @image_1 → character reference, @video_1 → action reference, etc.).",
        }

        user_message_parts = [
            f"[Generation Mode] {generation_mode}",
            f"[Video Duration] {video_duration}s (H3 supports 4-15s)",
            f"[Aspect Ratio] {aspect_ratio}",
            f"[Background Music] {'No background music needed. Add non_diegetic_music: N/A at the end' if no_bgm else 'No special requirement (may include background music)'}",
        ]

        if extra_requirements and extra_requirements.strip():
            user_message_parts.append(f"[Extra Requirements] {extra_requirements.strip()}")

        user_message_parts.append(f"[Mode Hint] {mode_hints.get(generation_mode, '')}")
        user_message_parts.append(f"[User Original Prompt]\n{prompt_text_input}")

        # ── Collect image inputs ──
        image_inputs = [image_1, image_2, image_3, image_4, image_5]
        collected_images = []  # list of (label, data_uri_list)
        total_image_count = 0
        for idx, img in enumerate(image_inputs):
            if img is None:
                continue
            label = f"image_{idx + 1}"
            data_uris = _bsai_image_tensor_to_data_uri(img)
            if data_uris:
                collected_images.append((label, data_uris))
                total_image_count += len(data_uris)

        if total_image_count > 0:
            image_summary = ", ".join(
                f"{label} ({len(uris)} img)" for label, uris in collected_images
            )
            user_message_parts.append(
                f"[Reference Images] {total_image_count} image(s) uploaded: {image_summary}.\n"
                "Please write clear labels and usage for each image in the [Reference Description] section. "
                "Analyze subject appearance, scene style, composition, etc. from the images and incorporate into the prompt optimization."
            )
            # Switch to multimodal mode hint
            if generation_mode == "Text to Video":
                user_message_parts.append(
                    "[Note] Images detected. Please optimize using 'Image to Video' or 'Multimodal Fusion' mode."
                )

        user_message_parts.append(
            "\nBased on the above information, optimize the prompt according to H3 specification. Output the optimized prompt directly without any explanation."
        )

        user_message = "\n".join(user_message_parts)

        # ── Build messages: use multimodal content format when images are present ──
        if total_image_count > 0:
            user_content = []
            user_content.append({"type": "text", "text": user_message})
            for label, uris in collected_images:
                for uri in uris:
                    user_content.append(
                        {"type": "image_url", "image_url": {"url": uri}}
                    )
                    user_content.append(
                        {"type": "text", "text": f"(Above is {label})"}
                    )
            messages = [
                {"role": "system", "content": _H3_SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ]
            print(f"[BSAI H3] Multimodal inference: {total_image_count} image(s) attached")
        else:
            messages = [
                {"role": "system", "content": _H3_SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ]

        try:
            max_tokens_val = int(max_tokens)
        except (TypeError, ValueError):
            raise TypeError(
                f"max_tokens must be an integer, got {type(max_tokens).__name__}."
            )

        normalized_seed = _bsai_normalize_seed(seed)

        # ── max_tokens safety limit: prevent exceeding context length ──
        # In llama-cpp-python, n_ctx is a method, not a property; call it to get the int value
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
                f"[BSAI H3] Warning: prompt is long (~{est_prompt_tokens} tokens), "
                f"context length is only {n_ctx}, max_tokens limited to {safe_max_tokens}. "
                f"Consider increasing 'context_length' to 16384+ in ModelLoader."
            )
        elif safe_max_tokens < max_tokens_val:
            print(
                f"[BSAI H3] max_tokens reduced from {max_tokens_val} to {safe_max_tokens} "
                f"(context {n_ctx} - prompt ~{est_prompt_tokens} tokens - safety margin 256)"
            )

        # Only pass core parameters to avoid segfaults in the C++ layer.
        # Qwen-VL model chat_handler has poor compatibility with some params
        # (presence_penalty, frequency_penalty, top_k, repeat_penalty) → segfault.
        params = {
            "max_tokens": safe_max_tokens,
            "temperature": float(temperature),
            "top_p": float(top_p),
            "stream": False,
        }
        if normalized_seed is not None:
            params["seed"] = normalized_seed

        # Do NOT call _bsai_reset_llm_state(llm):
        # llm.reset() / ctx.memory_clear() causes segfault in some
        # llama-cpp-python + Qwen-VL combinations, crashing the Python process.
        # create_chat_completion handles context internally; no manual reset needed.

        try:
            out = _bsai_call_chat_completion(llm, messages=messages, params=params)
        except RuntimeError as e:
            if "Context Shift is explicitly disabled" in str(e):
                current_n_ctx = getattr(llm, "n_ctx", "unknown")
                raise RuntimeError(
                    "Context Shift is disabled by the C++ backend "
                    "(M-RoPE models do not support context sliding window).\n"
                    f"Current n_ctx = {current_n_ctx}, cannot fit the full conversation.\n"
                    "Please increase 'context_length' in BSAI_H3_ModelLoader:\n"
                    "  - Text only: recommend 16384\n"
                    "  - With images/video: recommend 32768 or higher\n"
                    f"Original error: {e}"
                ) from e
            raise

        try:
            text = out["choices"][0]["message"]["content"]
        except Exception:
            text = str(out)

        return (text.lstrip().removeprefix(": ").strip(),)


# ============================================================
# Model Unload Node
# ============================================================

class BSAI_H3_UnloadModel:
    """Unload the loaded LLM model to free VRAM."""

    @classmethod
    def INPUT_TYPES(s):
        return {"required": {"any_input": ("*",)}}

    RETURN_TYPES = ("*",)
    RETURN_NAMES = ("any_output",)
    FUNCTION = "run"
    CATEGORY = "BSAI"
    DESCRIPTION = "Unload the loaded LLM model to free VRAM."

    def run(self, any_input):
        _BSAI_QwenStorage.unload()
        return (any_input,)


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
