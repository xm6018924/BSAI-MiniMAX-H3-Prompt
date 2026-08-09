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
import json
import base64
import inspect
import re

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
    import requests
except Exception:
    requests = None

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


def _bsai_video_to_data_uris(video_input, max_frames=4):
    """Extract key frames from a video (IMAGE tensor batch) and convert to data URIs.

    Takes evenly spaced frames (first, middle, last, etc.) to represent the video.
    Limits to max_frames to control token usage.
    """
    if video_input is None or PILImage is None or torch is None:
        return []

    images = video_input
    if images.ndim == 3:
        images = images.unsqueeze(0)

    total_frames = images.shape[0]
    if total_frames == 0:
        return []

    # Select key frames: evenly spaced across the video
    if total_frames <= max_frames:
        frame_indices = list(range(total_frames))
    else:
        frame_indices = [
            int(i * (total_frames - 1) / (max_frames - 1)) for i in range(max_frames)
        ]

    data_uris = []
    for idx in frame_indices:
        img_tensor = images[idx]
        img_np = (img_tensor.cpu().numpy() * 255.0).clip(0, 255).astype("uint8")
        pil_img = PILImage.fromarray(img_np)
        buf = io.BytesIO()
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


def _bsai_audio_to_description(audio_input, label="audio"):
    """Extract metadata from ComfyUI AUDIO input for text-based reference.

    ComfyUI AUDIO format: dict with "waveform" (torch.Tensor) and "sample_rate" (int).
    Since most LLM backends cannot directly process audio, we generate a text description
    noting the audio reference so the model can reference it in the prompt.

    Returns (description_str, base64_str_or_None) tuple.
    base64_str is available for remote APIs that support audio input.
    """
    if audio_input is None:
        return None, None

    try:
        if isinstance(audio_input, dict):
            waveform = audio_input.get("waveform")
            sample_rate = audio_input.get("sample_rate", 0)
        else:
            waveform = audio_input
            sample_rate = 0

        if waveform is None:
            return None, None

        # Get tensor info
        if torch is not None and hasattr(waveform, "shape"):
            shape = waveform.shape
            # ComfyUI AUDIO waveform shape: [batch, channels, samples] or [channels, samples]
            if len(shape) == 3:
                samples = shape[-1]
                channels = shape[-2]
            elif len(shape) == 2:
                samples = shape[-1]
                channels = shape[-2]
            elif len(shape) == 1:
                samples = shape[0]
                channels = 1
            else:
                samples = 0
                channels = 0
        else:
            samples = 0
            channels = 0

        sr = int(sample_rate) if sample_rate else 0
        duration = (samples / sr) if sr > 0 else 0

        desc = f"{label}: {channels}ch, {duration:.1f}s, {sr}Hz"

        # Generate base64 for remote API support
        b64 = None
        try:
            if torch is not None and hasattr(waveform, "cpu"):
                import wave

                wav_tensor = waveform
                if wav_tensor.ndim == 3:
                    wav_tensor = wav_tensor[0]  # remove batch dim
                if wav_tensor.ndim == 2:
                    # Transpose to [samples, channels]
                    wav_tensor = wav_tensor.T

                wav_np = wav_tensor.cpu().numpy()
                # Normalize to int16
                wav_np = (wav_np * 32767).clip(-32768, 32767).astype("int16")

                buf = io.BytesIO()
                with wave.open(buf, "wb") as wf:
                    wf.setnchannels(int(channels) if channels else 1)
                    wf.setsampwidth(2)
                    wf.setframerate(sr if sr else 44100)
                    wf.writeframes(wav_np.tobytes())
                b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
                b64 = f"data:audio/wav;base64,{b64}"
        except Exception:
            pass

        return desc, b64
    except Exception:
        return None, None


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
        # Check _ctx attribute directly (set to None after close())
        ctx = getattr(llm, "_ctx", None)
        if ctx is None:
            return False

        # n_ctx() will fail if the model has been closed
        n_ctx_raw = getattr(llm, "n_ctx", None)
        if n_ctx_raw is None:
            return False
        if callable(n_ctx_raw):
            n_ctx_val = n_ctx_raw()
            if n_ctx_val is None or n_ctx_val == 0:
                return False
        return True
    except Exception:
        return False


# ============================================================
# Creative Style Post-Processing
# ============================================================

def _bsai_parse_style_option(style_str):
    """Parse a bilingual style option string.

    Format: "English Name (中文名 | description)" or "English Name (中文名)"
    Returns: (english_name, chinese_name, description)
    """
    m = re.match(r'(.+?)\s*\(([^|)]+)(?:\s*\|\s*([^)]+))?\)', style_str)
    if m:
        return m.group(1).strip(), m.group(2).strip(), (m.group(3) or "").strip()
    return style_str.strip(), "", ""


def _bsai_style_in_text(text, style_str):
    """Check if a style name (English or Chinese) appears in the text."""
    en, cn, _ = _bsai_parse_style_option(style_str)
    if en and en.lower() in text.lower():
        return True
    if cn and cn in text:
        return True
    return False


def _bsai_enforce_style_output(text, director_style, cinematography_style,
                               film_genre, score_style):
    """Post-process LLM output: inject missing creative styles into H3 fields.

    If the LLM failed to mention selected styles, this function injects them
    directly into the appropriate H3 fields:
    - Director / Cinematography / Genre  → integrated_multimodal_description
    - Score Style                        → non_diegetic_music

    Handles both the Chinese and English sections of the bilingual output.
    """
    if not text or not text.strip():
        return text

    # ── Determine which styles are selected and missing ──
    checks = [
        ("director",        director_style),
        ("cinematography",  cinematography_style),
        ("genre",           film_genre),
        ("score",           score_style),
    ]
    missing = {}
    for key, val in checks:
        if val and "System Recommended" not in val:
            if not _bsai_style_in_text(text, val):
                missing[key] = val

    if not missing:
        return text  # All styles already present

    print(f"[BSAI H3] Style enforcement: injecting missing styles: {list(missing.keys())}")

    # ── Build injection strings ──
    vis_en_parts = []
    vis_cn_parts = []
    score_en = ""
    score_cn = ""

    if "director" in missing:
        en, cn, desc = _bsai_parse_style_option(missing["director"])
        part_en = f"In the style of {en}"
        part_cn = f"导演风格参考{cn}"
        if cn:
            part_en += f" ({cn})"
        if en:
            part_cn += f"（{en}）"
        if desc:
            part_en += f", {desc}"
            part_cn += f"，{desc}"
        vis_en_parts.append(part_en)
        vis_cn_parts.append(part_cn)

    if "cinematography" in missing:
        en, cn, desc = _bsai_parse_style_option(missing["cinematography"])
        part_en = f"cinematography by {en}"
        part_cn = f"摄影风格{cn}"
        if cn:
            part_en += f" ({cn})"
        if en:
            part_cn += f"（{en}）"
        if desc:
            part_en += f", {desc}"
            part_cn += f"，{desc}"
        vis_en_parts.append(part_en)
        vis_cn_parts.append(part_cn)

    if "genre" in missing:
        en, cn, desc = _bsai_parse_style_option(missing["genre"])
        part_en = f"{en} genre aesthetic"
        part_cn = f"{cn}类型美学"
        if cn:
            part_en += f" ({cn})"
        if en:
            part_cn += f"（{en}）"
        if desc:
            part_en += f", {desc}"
            part_cn += f"，{desc}"
        vis_en_parts.append(part_en)
        vis_cn_parts.append(part_cn)

    if "score" in missing:
        en, cn, desc = _bsai_parse_style_option(missing["score"])
        score_en = f"In the style of {en}"
        score_cn = f"配乐风格参考{cn}"
        if cn:
            score_en += f" ({cn})"
        if en:
            score_cn += f"（{en}）"
        if desc:
            score_en += f", {desc}"
            score_cn += f"，{desc}"

    vis_en_str = ". ".join(vis_en_parts) + ". " if vis_en_parts else ""
    vis_cn_str = "。".join(vis_cn_parts) + "。" if vis_cn_parts else ""

    # ── Helper: inject after a field name within a text region ──
    def _inject_after_field(segment, field_name, injection):
        """Insert *injection* right after 'field_name:' in *segment*."""
        pattern = re.compile(
            r'(' + re.escape(field_name) + r'\s*:\s*)',
            re.IGNORECASE,
        )
        m = pattern.search(segment)
        if m:
            return segment[:m.end()] + injection + segment[m.end():]
        return None  # field not found

    # ── Split output into Chinese / English sections ──
    cn_marker = "---中文版本---"
    en_marker = "---English Version---"

    has_cn = cn_marker in text
    has_en = en_marker in text

    if has_cn and has_en:
        cn_start = text.index(cn_marker) + len(cn_marker)
        en_start = text.index(en_marker) + len(en_marker)

        cn_section = text[cn_start:en_start]
        en_section = text[en_start:]
        prefix = text[:cn_start]

        # Inject into Chinese section
        if vis_cn_str:
            result = _inject_after_field(cn_section, "integrated_multimodal_description", vis_cn_str)
            if result is not None:
                cn_section = result
            else:
                cn_section = vis_cn_str + "\n" + cn_section
        if score_cn:
            result = _inject_after_field(cn_section, "non_diegetic_music", score_cn + "。")
            if result is not None:
                cn_section = result

        # Inject into English section
        if vis_en_str:
            result = _inject_after_field(en_section, "integrated_multimodal_description", vis_en_str)
            if result is not None:
                en_section = result
            else:
                en_section = vis_en_str + "\n" + en_section
        if score_en:
            result = _inject_after_field(en_section, "non_diegetic_music", score_en + ". ")
            if result is not None:
                en_section = result

        text = prefix + cn_section + en_marker + en_section

    elif has_cn:
        # Only Chinese section
        cn_start = text.index(cn_marker) + len(cn_marker)
        prefix = text[:cn_start]
        cn_section = text[cn_start:]

        if vis_cn_str:
            result = _inject_after_field(cn_section, "integrated_multimodal_description", vis_cn_str)
            if result is not None:
                cn_section = result
            else:
                cn_section = vis_cn_str + "\n" + cn_section
        if score_cn:
            result = _inject_after_field(cn_section, "non_diegetic_music", score_cn + "。")
            if result is not None:
                cn_section = result

        text = prefix + cn_section

    elif has_en:
        # Only English section
        en_start = text.index(en_marker) + len(en_marker)
        prefix = text[:en_start]
        en_section = text[en_start:]

        if vis_en_str:
            result = _inject_after_field(en_section, "integrated_multimodal_description", vis_en_str)
            if result is not None:
                en_section = result
            else:
                en_section = vis_en_str + "\n" + en_section
        if score_en:
            result = _inject_after_field(en_section, "non_diegetic_music", score_en + ". ")
            if result is not None:
                en_section = result

        text = prefix + en_section

    else:
        # No language markers — inject into the whole text
        # Try English field names first (H3 fields are always in English)
        if vis_en_str:
            result = _inject_after_field(text, "integrated_multimodal_description", vis_en_str)
            if result is not None:
                text = result
            else:
                # No field found — prepend a style annotation header
                header_parts = []
                if vis_en_parts:
                    header_parts.append("[Creative Styles] " + ". ".join(vis_en_parts) + ".")
                if vis_cn_parts:
                    header_parts.append("【创意风格】" + "。".join(vis_cn_parts) + "。")
                if score_en:
                    header_parts.append("[Score] " + score_en + ".")
                if score_cn:
                    header_parts.append("【配乐】" + score_cn + "。")
                header = "\n".join(header_parts) + "\n\n"
                text = header + text

        if score_en:
            result = _inject_after_field(text, "non_diegetic_music", score_en + ". ")
            if result is not None:
                text = result

    return text


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

        mmproj = config.get("mmproj", "None (无)")
        mmproj_path = None
        if mmproj and mmproj not in ("None (无)", "None", "无", ""):
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
            if family in ("Qwen3.5-VL (通义千问3.5-VL)", "Qwen3.6-VL (通义千问3.6-VL)"):
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
            elif family == "Qwen3-VL (通义千问3-VL)":
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
            elif family == "Gemma4 (谷歌宝石4)":
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
        mmproj_list = ["None (无)"] + [
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
                    ["Qwen3-VL (通义千问3-VL)", "Qwen3.5-VL (通义千问3.5-VL)", "Qwen3.6-VL (通义千问3.6-VL)", "Gemma4 (谷歌宝石4)"],
                    {"default": "Qwen3.6-VL (通义千问3.6-VL)", "tooltip": "Model family / 模型系列"},
                ),
                "model_file": (
                    model_list,
                    {"tooltip": "Main model file (.gguf recommended) in ComfyUI/models/LLM/ / 主模型文件"},
                ),
                "mmproj": (
                    mmproj_list,
                    {"default": "None (无)", "tooltip": "Multimodal mmproj file; 'None' for text-only / 视觉投影文件"},
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

        if model_family in ("Qwen3-VL (通义千问3-VL)", "Qwen3.5-VL (通义千问3.5-VL)", "Qwen3.6-VL (通义千问3.6-VL)", "Gemma4 (谷歌宝石4)"):
            if mmproj == "None (无)":
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
# Creative Style Options
# ============================================================

_BSAI_DIRECTOR_STYLES = [
    "System Recommended (系统推荐)",
    "Alfred Hitchcock (希区柯克 | 悬念大师)",
    "Wong Kar-wai (王家卫)",
    "Orson Welles (奥逊·威尔斯)",
    "Ingmar Bergman (英格玛·伯格曼 | 哲学电影大师)",
    "Federico Fellini (费德里科·费里尼 | 魔幻现实主义)",
    "Akira Kurosawa (黑泽明 | 东方电影标杆)",
    "Sergei Eisenstein (谢尔盖·爱森斯坦 | 蒙太奇)",
    "Steven Spielberg (史蒂文·斯皮尔伯格)",
    "Francis Ford Coppola (弗朗西斯·福特·科波拉)",
    "Martin Scorsese (马丁·斯科塞斯)",
    "Stanley Kubrick (斯坦利·库布里克)",
    "Billy Wilder (比利·怀尔德)",
    "Ang Lee (李安)",
    "Zhang Yimou (张艺谋)",
    "Satoshi Kon (今敏 | 动画电影大师)",
    "Takeshi Kitano (北野武)",
    "Christopher Nolan (克里斯托弗·诺兰)",
    "Quentin Tarantino (昆汀·塔伦蒂诺)",
    "James Cameron (詹姆斯·卡梅隆)",
    "Alfonso Cuaron (阿方索·卡隆)",
    "David Lynch (大卫·林奇)",
    "Wes Anderson (韦斯·安德森)",
    "Denis Villeneuve (丹尼斯·维伦纽瓦)",
    "Bong Joon-ho (奉俊昊)",
    "Hayao Miyazaki (宫崎骏)",
    "Makoto Shinkai (新海诚)",
    "Park Chan-wook (朴赞郁)",
    "Fritz Lang (弗里茨·朗)",
    "Jean-Luc Godard (让-吕克·戈达尔)",
    "Andrei Tarkovsky (安德烈·塔可夫斯基)",
    "Michelangelo Antonioni (米开朗基罗·安东尼奥尼)",
    "Robert Bresson (罗伯特·布列松)",
    "Yasujirō Ozu (小津安二郎)",
    "John Woo (吴宇森)",
    "Ann Hui (许鞍华)",
    "Jia Zhangke (贾樟柯)",
    "Bi Gan (毕赣)",
]

_BSAI_CINEMATOGRAPHY_STYLES = [
    "System Recommended (系统推荐)",
    "Gregg Toland (格雷格·托兰德 | 深焦摄影)",
    "Gordon Willis (戈登·威利斯 | 黑暗王子低调照明)",
    "Freddie Young (弗雷迪·扬 | 70mm宽银幕史诗)",
    "Roger Deakins (罗杰·狄金斯 | 克制写实主义)",
    "Emmanuel Lubezki (卢贝兹基 | 自然光长镜头)",
    "Greig Fraser (格雷格·弗莱瑟 | 粗粝物理质感)",
    "Janusz Kaminski (雅努什·卡明斯基 | 逆光光晕)",
    "Hoyte van Hoytema (霍伊特·范·霍伊特玛 | IMAX胶片实拍)",
    "Vittorio Storaro (斯托拉罗 | 色彩心理学用光写作)",
    "Sven Nykvist (斯文·尼奎斯特 | 极简自然光)",
    "Christopher Doyle (杜可风 | 都市情绪光影诗人)",
    "Mark Lee Ping-Bin (李屏宾 | 东方诗意自然光)",
    "Peter Pau (鲍德熹 | 唯美写意逆光)",
    "Robby Müller (罗比·穆勒 | 霓虹粗粝质感)",
    "Conrad Hall (康拉德·霍尔 | 纹理阴影)",
    "Robert Richardson (罗伯特·理查德森 | 高对比顶光)",
    "Dariusz Wolski (达里乌什·沃尔斯基 | 暗黑哥特光泽)",
    "Matthew Libatique (马修·利巴提克 | 高对比颗粒感)",
    "Claudio Miranda (克劳迪奥·米兰达 | 冷调数字洁净)",
    "Lin Liang-Zhong (林良忠 | 乡土写实柔光)",
]

_BSAI_FILM_GENRES = [
    "System Recommended (系统推荐)",
    "Realism (写实主义)",
    "Neo-Realism (新现实主义)",
    "Poetic Realism (诗意写实)",
    "Expressionism (表现主义)",
    "Magical Realism (魔幻现实主义)",
    "Surrealism (超现实主义)",
    "French New Wave (法国新浪潮)",
    "Classical Hollywood (古典好莱坞)",
    "Film Noir (黑色电影)",
    "Vintage Film (胶片复古风)",
    "Theatrical Drama (舞台化戏剧)",
    "2D Hand-drawn Animation (二维手绘动画)",
    "Ghibli/Miyazaki Animation (吉卜力/宫崎骏风格)",
    "Shinkai Animation (新海诚风格)",
    "Satoshi Kon Animation (今敏风格)",
    "3D CG Animation (三维CG动画)",
    "Stop Motion (定格动画)",
    "Ink Wash Animation (水墨国风动画)",
    "Live Action (真人实拍)",
    "Live Action + CG (真人CG混合)",
    "Drama (剧情片)",
    "Art-house Drama (文艺剧情片)",
    "Mystery (悬疑片)",
    "Crime (犯罪片)",
    "Gangster (黑帮片)",
    "Psychological Thriller (心理惊悚)",
    "Horror (恐怖片)",
    "Action (动作片)",
    "Wuxia (武侠片)",
    "Kung Fu (功夫片)",
    "Adventure (冒险片)",
    "Epic (史诗片)",
    "Sci-Fi (科幻片)",
    "Fantasy (奇幻片)",
    "Superhero (超级英雄)",
    "Romantic Comedy (浪漫喜剧)",
    "Dark Comedy (黑色喜剧)",
    "Slapstick Comedy (无厘头喜剧)",
    "Absurdist Comedy (荒诞喜剧)",
    "Romance (爱情片)",
    "Urban Romance (都市爱情)",
    "Road Movie (公路电影)",
    "Western (西部片)",
    "Musical (歌舞片)",
    "War Film (战争片)",
    "Historical Biopic (历史传记片)",
    "Period Epic (古装史诗片)",
    "Documentary (纪录片)",
    "Mockumentary (伪纪录片)",
    "Experimental (先锋实验)",
]

_BSAI_CUT_STYLES = [
    "One Shot (一镜到底)",
    "2 Segments (2段)",
    "3 Segments (3段)",
    "4 Segments (4段)",
    "5 Segments (5段)",
    "6 Segments (6段)",
    "7 Segments (7段)",
    "8 Segments (8段)",
    "9 Segments (9段)",
    "10 Segments (10段)",
    "11 Segments (11段)",
    "12 Segments (12段)",
    "13 Segments (13段)",
    "14 Segments (14段)",
    "15 Segments (15段)",
]

_BSAI_SCORE_STYLES = [
    "System Recommended (系统推荐)",
    "John Williams (约翰·威廉姆斯 | 史诗管弦主导动机)",
    "Hans Zimmer (汉斯·季默 | 电子管弦混合)",
    "Ennio Morricone (埃尼奥·莫里康内 | 意大利西部 haunting旋律)",
    "Bernard Herrmann (伯纳德·赫尔曼 | 弦乐悬疑)",
    "Danny Elfman (丹尼·艾夫曼 | 哥特怪诞)",
    "Howard Shore (霍华德·肖 | 奇幻史诗主题)",
    "Thomas Newman (托马斯·纽曼 | 氛围极简主义)",
    "Nino Rota (尼诺·罗塔 | 意大利旋律古典)",
    "Vangelis (范吉利斯 | 合成器电子)",
    "Ryuichi Sakamoto (坂本龙一 | 东西方融合)",
    "Joe Hisaishi (久石让 | 旋律钢琴与弦乐)",
    "Tan Dun (谭盾 | 跨文化打击乐)",
    "Shigeru Umebayashi (梅林茂 | 忧郁沉郁)",
    "Clint Mansell (克林特·曼塞尔 | 极简重复)",
    "Trent Reznor & Atticus Ross (特伦特·雷泽诺与阿提克斯·罗斯 | 工业电子)",
    "Alexandre Desplat (亚历山大·德斯普拉 | 优雅管弦)",
    "Michael Giacchino (迈克尔·吉亚奇诺 | 情感旋律)",
    "Ludwig Goransson (路德维希·戈兰松 | 非洲未来主义打击乐)",
    "Mica Levi (米卡·利维 | 不安不协和)",
    "Johann Johannsson (约翰·约翰松 | 持续音极简)",
    "Carter Burwell (卡特·伯威尔 | 民谣简约)",
    "Gustavo Santaolalla (古斯塔沃·桑塔欧拉拉 | 独奏吉他)",
    "A.R. Rahman (A.R.拉赫曼 | 宝莱坞融合)",
    "Hildur Gudnadottir (希尔杜·古德纳多蒂尔 | 大提琴持续音暗黑)",
    "Philip Glass (菲利普·格拉斯 | 极简重复模式)",
    "Angelo Badalamenti (安吉洛·巴达拉门蒂 | 超现实梦幻爵士)",
    "James Horner (詹姆斯·霍纳 | 凯尔特情感)",
    "Alan Silvestri (艾伦·西尔维斯特里 | 冒险英雄)",
    "Bear McCreary (贝尔·麦克里 | 太鼓打击民族风)",
    "Max Steiner (马克斯·斯坦纳 | 古典好莱坞交响)",
    "Jerry Goldsmith (杰瑞·戈德史密斯 | 多变前卫)",
    "Dimitri Tiomkin (迪米特里·蒂奥姆金 | 美国边疆)",
    "Elmer Bernstein (埃尔默·伯恩斯坦 | 爵士大乐队)",
    "Maurice Jarre (莫里斯·贾尔 | 史诗合唱异域)",
    "Kitaro (喜多郎 | 新世纪合成器)",
    "Shirō Sagisu (鹭巢诗郎 | 动漫管弦摇滚融合)",
    "Yuki Kajiura (梶浦由记 | 哥特合唱空灵)",
    "Taku Iwasaki (岩崎琢 | 嘻哈管弦混合)",
    "Hiroyuki Sawano (泽野弘之 | 史诗动漫摇滚)",
    "Cho Young-wuk (赵英旭 | 韩国悲剧旋律)",
    "Zhao Jiping (赵季平 | 中国传统电影配乐)",
]


# ============================================================
# H3 提示词优化系统提示词（根据 H3 官方 Prompt Writing Guide 整理）
# 官方文档：https://github.com/MiniMax-AI/MiniMax-H3/tree/main/skills/h3-prompt-writing
# ============================================================

_H3_SYSTEM_PROMPT = """You are a MiniMax H3 video model prompt optimization expert. Your task is to rewrite user input into H3-compliant structured video generation prompts following the official H3 Prompt Writing Guide.

**⚠ TOP PRIORITY — Creative Style Output**: If the user message contains any of these tags — [Director Style], [Cinematography Style], [Film Genre], [Score Style] — you MUST explicitly write the selected style name AND its characteristic techniques directly in the output text. The director's name goes in the opening of integrated_multimodal_description. The cinematographer's lighting/camera style goes in the visual description. The genre's aesthetic goes in the scene description. The composer's name and musical style goes in non_diegetic_music. Applying styles silently without naming them in the output is a CRITICAL ERROR.

## 1. Official Prompt Structure

The final prompt uses three core fields in this exact order:

```
integrated_multimodal_description: [0-3s] ... [3-8s] ... [8-12s] ...
overall_soundscape: ...
non_diegetic_music: ...
```

- **integrated_multimodal_description**: The main body. Describes visual style, composition, subjects, scene, actions, camera transitions, dialogue, singing, and diegetic audio along the timeline. MUST be segmented by time ranges.
- **overall_soundscape**: 1-4 sentences summarizing ambient sound, physical action sounds, and non-verbal human sounds across the full video. Do NOT repeat dialogue or diegetic music already in the multimodal description.
- **non_diegetic_music**: 1-3 sentences describing background music only the audience hears. Use N/A when there is no non-diegetic music.

## 2. Input Modes

- **T2VA** (Text to Video): No image instruction. Begin directly with the three core fields.
- **I2VA** (Image to Video): First-frame instruction + T2VA body.
- **FL2VA** (First+Last frame): Alignment instruction + T2VA body.
- **L2VA** (Last frame): Alignment instruction + T2VA body.

Image alignment instructions (must be the first line, followed by one blank line):

- I2VA: `For the target video, at 0.00 seconds into the target video, <Picture 1> is fully referenced.`
- FL2VA: `How the reference pictures align with the target video — Picture 1 aligns with the 0.00-second mark of the target video; Picture 2 aligns with the S.SS-second mark of the target video.`
- L2VA: `How the reference pictures align with the target video — <Picture 1> aligns with the S.SS-second mark of the target video.`

## 3. Writing the Multimodal Description

### 3.1 Time-Range Segmentation (按时长分段)
The `integrated_multimodal_description` field MUST be segmented by time ranges based on the video duration:

**Format:**
- English version: `[0-3s] ... [3-8s] ... [8-12s] ...`
- Chinese version: `【0-3秒】... 【3-8秒】... 【8-12秒】...`

**Rules:**
1. Divide the total video duration into logical segments based on scene changes, camera cuts, or narrative beats.
2. Each segment covers a continuous time range (e.g., `0-3s`, `3-8s`, `8-12s` for a 12s video).
3. Time ranges must be continuous and cover the full video duration with no gaps.
4. The first segment always starts at `0` (or `0s`/`0秒`).
5. The last segment must end at the exact video duration.
6. Each segment should contain: shot type/framing, content description, camera movement, actions, dialogue, and sound.
7. Use `the camera cuts to` or `切镜到` to indicate transitions between segments.
8. Cross-dissolve, fade, or wipe only when explicitly requested.
9. If dialogue spans across segments, note it with "continues from the previous segment" or `接着上个分段继续说`.

**Example (English, 12s video):**
```
integrated_multimodal_description: [0-3s] Live-action, cinematic, a wide shot frames a young woman walking into a cherry blossom courtyard. The camera pushes in with small amplitude. [3-8s] The camera cuts to a medium shot as she draws her sword and begins her stance. Petals scatter. [8-12s] Cut to a close-up, the sword flashes in slow motion as petals are scattered by the sword's energy.
```

**Example (Chinese, 12s video):**
```
integrated_multimodal_description: 【0-3秒】实拍，电影感，全景镜头，一位年轻女子走入樱花庭院。镜头缓慢推进。【3-8秒】切镜到中景，她拔出长剑，缓缓起势，樱花瓣从树上飘落。镜头继续推进。【8-12秒】切镜到特写，剑光一闪，慢动作，樱花被剑气激得四散。
```

### 3.2 Opening Style
At the beginning of the first time segment, state the overall style: Cinematic, Live-action, 2D-animated, 3D CG, Claymation, Watercolor, Vintage film, etc.

**CRITICAL — Creative Style Integration**: When the user message includes [Director Style], [Cinematography Style], [Film Genre], or [Score Style] tags, you MUST explicitly incorporate these styles into the output:
1. In the opening of `integrated_multimodal_description`, state the director's name and their signature visual techniques (e.g., "in the style of Wong Kar-wai (王家卫), with step-printing, saturated colors, and melancholic urban atmosphere").
2. Describe the cinematographer's lighting and camera approach explicitly (e.g., "cinematography inspired by Christopher Doyle (杜可风), handheld camera with neon-drenched high-contrast lighting and soft focus").
3. Reference the film genre's visual conventions in the description (e.g., "art-house drama aesthetic with contemplative pacing").
4. In `non_diegetic_music`, explicitly describe the music using the selected composer's signature style (e.g., "in the style of Joe Hisaishi (久石让), with tender piano melodies and lush string arrangements").

Do NOT silently apply styles — the style names and their characteristic techniques MUST be explicitly visible in the output text.

### 3.3 Camera Motion (Motion Type + Amplitude + Speed)
Write camera motion as natural English action within the shot:

| Motion Type | Examples |
|-|-|
| Zoom | Zoom In / Zoom Out |
| Push/Pull | Push In / Pull Out |
| Pan | Pan Left / Pan Right |
| Truck | Truck Left / Truck Right |
| Tilt | Tilt Up / Tilt Down |
| Pedestal | Pedestal Up / Pedestal Down |
| Arc | Arc Shot |
| Tracking | Tracking Shot |
| Static | Static Shot |
| POV | POV |
| Shake | Shake Slightly / Shake Strongly |

- Amplitude: `with small amplitude` / `with large amplitude` (omit if medium)
- Speed: `at slow speed` / `at fast speed` (omit if normal)

Example: `The camera pushes in with small amplitude at slow speed toward the folded letter in her hands.`

### 3.4 Speakers and Dialogue
- Speaking characters get stable IDs: (S1), (S2), (S1,S2) for group speech.
- Speaker identity (age, gender, timbre, accent) goes OUTSIDE `<d>`.
- Inside `<d>`, include only the language tag and the actual spoken content. Preserve every word verbatim.

Example: `The young woman with a quiet, breathy voice (S1) says: <d>[English] I get off at the next station.</d>`
Example: `The young woman with a quiet, breathy voice (S1) says: <d>[Chinese] 你来了，剑等你好久了。</d>`

- Voiceover: `says in an off-screen voiceover: <d>[English] ...</d> while his lips remain completely closed.`
- Dialogue crossing a segment boundary: use `<scenetrans>` at connecting points and state the audio continues across the segment boundary.
- Truncated speech: use `<cutoff>`.

### 3.5 On-Screen Text
Place visible text (banners, signs, labels, subtitles, neon text) in English double quotation marks. Preserve the original text verbatim.

Example: `A red neon sign reading "营业中" glows above the doorway.`

### 3.6 Sound (MANDATORY — No Silence Allowed)
- **overall_soundscape**: Ambient sounds, physical action sounds, non-verbal human sounds (wind, rain, traffic, footsteps, breathing, laughter). NOT dialogue or singing.
- **non_diegetic_music**: Background music (instruments, tempo, rhythm, dynamics). NOT diegetic music (radio, live performance). Use `N/A` ONLY when the user explicitly requests no background music.

#### Mandatory Sound Coverage
Unless the user has explicitly provided custom sound/music descriptions or explicitly requested no sound effects, the `overall_soundscape` field MUST ALWAYS include ALL of the following categories appropriate to the scene:

1. **Scene ambient sounds** — Environmental atmosphere: wind, rain, waves, traffic, crowd murmur, birdsong, city noise, etc.
2. **Background sound effects** — Continuous or semi-continuous sounds that define the setting: machinery hum, clock ticking, distant thunder, room tone, etc.
3. **Character action sounds** — Sounds produced by people on screen: footsteps, clothing rustle, breathing, sighing, coughing, tapping, grabbing objects, door opening, etc.
4. **Object movement sounds** — Sounds from physical objects and their interactions: glass clinking, paper rustling, sword swoosh, ball bouncing, chair scraping, water splashing, etc.

**CRITICAL**: The video must NEVER have moments of complete silence. Every moment must have at least one audible sound source. If a scene is inherently quiet (e.g., a still room at night), still include subtle ambient sounds (distant crickets, clock ticking, wind against windows, breathing).

#### Exceptions
- If the user has provided custom sound/music descriptions in `[Extra Requirements]` or the original prompt, respect those descriptions and fill in any gaps with appropriate ambient/action sounds.
- If the user has explicitly checked "no_bgm" (no background music), still include all sound effects in `overall_soundscape` — only `non_diegetic_music` is set to N/A.
- If the user explicitly states no sound effects at all (rare), only then may `overall_soundscape` be minimal.

## 4. Reference Labels (for I2VA / FL2VA / L2VA modes)

When images are uploaded, use these labels:
- `<Picture N>`: Reference image as a concrete frame anchor (first frame, last frame, keyframe).
- When an image defines a character/scene/style only (not a frame anchor), describe it in the text without a standalone label.

For multimodal fusion mode, reference labels can also include:
- `<Subject N>`: Reusable visible content (person, scene, clothing, style) from reference assets.
- `<Video N>`: Reference video for editing, continuation, or temporal structure.
- `<Audio N>`: Audio asset for copying or referencing.

## 5. Writing Rules

1. Write descriptions in English; preserve dialogue, lyrics, and visible scene text in their ORIGINAL language (Chinese stays Chinese, English stays English).
2. Each time segment must include: shot type/framing, subjects, environment, actions, camera movement, sound, and dialogue where applicable.
3. Avoid plot summaries — write what is visible and audible at each moment.
4. Keep dialogue length proportional to segment length (avoid long dialogue in a 3s segment).
5. The speaker's identifying phrase, ID, and delivery go outside `<d>`; inside `<d>` only the language tag and actual spoken content.
6. If no reference images: skip the alignment instruction, begin with `integrated_multimodal_description`.
7. **MANDATORY SOUND**: The `overall_soundscape` field must ALWAYS contain sound effects — never leave it empty or write "none/silence". Cover scene ambience, character actions, and object interactions. Even in quiet scenes, include subtle ambient sounds. The only exception is when the user explicitly requests no sound.
8. **Non-diegetic music**: Do not add N/A unless the user explicitly requests no background music. If the user has not specified, describe appropriate background music that matches the scene's mood and tone.
9. When the user provides custom sound/music descriptions, integrate them naturally and supplement with additional ambient/action sounds to ensure full coverage.
10. **Segmentation**: The `integrated_multimodal_description` must be divided into continuous time-range segments covering the full video duration. Use `[0-3s]` format for English and `【0-3秒】` format for Chinese. Never write the entire description as a single unsegmented block.

## 5.5 Creative Style Parameters

When the user message includes any of the following style tags, apply them to the prompt:

- **[Director Style]**: Apply the named director's signature techniques — pacing, visual language, thematic motifs, editing rhythm, and directorial sensibilities. For example, Hitchcock = suspense building, slow reveals, subjective camera; Wong Kar-wai = step-printing, saturated colors, voiceover, urban longing; Kubrick = symmetry, one-point perspective, cold precision; Kurosawa = dynamic movement, weather as emotion, multi-camera action; Nolan = non-linear narrative, practical effects, IMAX scale; Tarantino = non-linear editing, pop culture dialogue, stylized violence; Spielberg = emotional close-ups, sweeping camera, golden-hour warmth; Scorsese = tracking shots, voiceover, kinetic editing; Fellini = surreal spectacle, circus-like pageantry; Bergman = intimate close-ups, philosophical silence, stark lighting.
- **[Cinematography Style]**: Apply the named cinematographer's signature lighting, lens characteristics, color palette, and camera movement. For example, Deakins = restrained realism, soft naturalistic light, muted palette; Lubezki = available light, long takes, golden-hour warmth; Storaro = bold color symbolism, psychological color coding, smoke-and-light beams; Doyle = handheld, neon-drenched, high-contrast, soft focus; Hoyte van Hoytema = IMAX film, solid physical lighting, warm-cool contrast; Willis = low-key chiaroscuro, deliberate underexposure, shadow-heavy; Toland = deep focus, wide-angle depth, sharp foreground-to-background; Kaminski = strong backlight, lens flare, high-key overflow; Fraser = rugged physical texture, grain-forward, muted earth tones; Nykvist = minimalist natural light, soft side light, breathable shadows; Mark Lee Ping-Bin = Eastern poetic natural light, slow long takes, warm retro tones.
- **[Film Genre]**: Match the visual conventions, narrative tone, pacing, and aesthetic of the specified genre. For example, Film Noir = high-contrast shadows, venetian-blind light, urban night; Sci-Fi = sleek or gritty futurism, technological environments; Wuxia = wire-fu choreography, sweeping landscapes, silk costumes; Stop Motion = tactile textures, handcrafted look, slight jitter; Ghibli/Miyazaki = hand-drawn warmth, lush nature, gentle pacing; Shinkai = hyper-detailed skies, saturated colors, emotional lens flares; New Wave = jump cuts, handheld, breaking conventions; Magical Realism = grounded reality with dreamlike intrusions; Expressionism = distorted sets, extreme light/shadow, psychological unease.
- **[Segmentation]**: The user has specified the exact number of time-range segments. Divide the video into exactly that many segments, each representing a distinct camera cut with its own shot type, content, and camera movement. Ensure all segments are continuous and cover the full video duration.
- **[Score Style]**: Apply the named composer's signature musical style to the `non_diegetic_music` field. Match their instrumentation preferences, harmonic language, rhythmic patterns, and emotional texture. For example, John Williams = sweeping brass-led leitmotifs, full romantic orchestra; Hans Zimmer = electronic-orchestral hybrid, driving ostinatos, deep braams; Ennio Morricone = whistled melodies, harmonica, solitary trumpet, sparse eerie arrangements; Bernard Herrmann = strings-only tension, shrieking glissandi; Danny Elfman = gothic choral, quirky orchestral, Burton-esque dark whimsy; Joe Hisaishi = tender piano melodies, lush string arrangements, Ghibli warmth; Vangelis = analog synthesizer pads, retro-futuristic electronic; Ryuichi Sakamoto = melancholic piano, East-West harmonic fusion; Tan Dun = Chinese percussion, cello solos, cross-cultural timbres; Clint Mansell = obsessive minimalist repetition, building intensity; Trent Reznor & Atticus Ross = industrial textures, dark ambient electronics; Hildur Gudnadottir = cello drone, dissonant dark textures; Philip Glass = arpeggiated minimalist patterns, gradual harmonic shifts; Angelo Badalamenti = dreamlike jazz-noir, slow saxophone, ambient synth pads; Gustavo Santaolalla = lonely detuned guitar, ronroco, sparse emotional melodies.

When a style parameter is set to "System Recommended (系统推荐)", use your own best judgment to select appropriate styles based on the user's prompt content.

**MANDATORY OUTPUT REQUIREMENT**: When any creative style tag is present in the user message, the selected style MUST be explicitly reflected in the output prompt:
- The director's name and signature techniques MUST appear in the opening of `integrated_multimodal_description`
- The cinematographer's lighting/camera style MUST be described in the visual description
- The film genre's aesthetic conventions MUST be referenced in the scene description
- The composer's name and musical characteristics MUST appear in `non_diegetic_music`
- Failure to explicitly mention the selected styles in the output is a critical error

## 6. Output Format

Output the prompt in BOTH Chinese and English versions, separated by a divider line:

```
---中文版本---

[alignment instruction if applicable]

integrated_multimodal_description: 【0-3秒】... 【3-8秒】... 【8-12秒】...
overall_soundscape: ...
non_diegetic_music: ...

---English Version---

[alignment instruction if applicable]

integrated_multimodal_description: [0-3s] ... [3-8s] ... [8-12s] ...
overall_soundscape: ...
non_diegetic_music: ...
```

### Example WITH Creative Styles Applied

When the user message contains [Director Style], [Cinematography Style], [Film Genre], or [Score Style] tags, the output MUST explicitly name and describe the selected styles. Compare the difference:

**WITHOUT styles (System Recommended):**
```
integrated_multimodal_description: [0-3s] Live-action, cinematic, a wide shot frames a young woman walking into a cherry blossom courtyard. The camera pushes in with small amplitude. [3-8s] The camera cuts to a medium shot as she draws her sword and begins her stance. [8-12s] Cut to a close-up, the sword flashes in slow motion.
overall_soundscape: ...
non_diegetic_music: Soft orchestral strings with gentle woodwind accents, building tension during the sword draw.
```

**WITH [Director Style] Wong Kar-wai, [Cinematography Style] Christopher Doyle, [Film Genre] Wuxia, [Score Style] Tan Dun:**
```
integrated_multimodal_description: [0-3s] In the style of Wong Kar-wai (王家卫), with step-printing and saturated colors, a wide shot frames a young woman walking into a cherry blossom courtyard. Cinematography by Christopher Doyle (杜可风): handheld camera with neon-drenched high-contrast lighting and soft focus. Wuxia (武侠) genre aesthetic with silk costumes and sweeping landscapes. The camera pushes in with small amplitude. [3-8s] The camera cuts to a medium shot as she draws her sword and begins her stance, Doyle's signature humid atmosphere and朦胧 light. [8-12s] Cut to a close-up, the sword flashes in slow motion, Wong Kar-wai's melancholic urban longing permeating the frame.
overall_soundscape: ...
non_diegetic_music: In the style of Tan Dun (谭盾), with Chinese percussion, cello solos, and cross-cultural timbres building tension during the sword draw.
```

**CRITICAL**: The style names (director, cinematographer, genre, composer) and their signature techniques MUST appear explicitly in the output text. Do NOT apply styles silently — the user must be able to see which styles were used by reading the output.

### Rules for bilingual output:
1. **English Version**: Descriptions in English, dialogue/lyrics/visible text in original language with `<d>[Language] ...</d>` tags. Use `[0-3s]` time-range segments.
2. **Chinese Version**: Same content as the English version but with the description parts in Chinese. Dialogue, lyrics, and visible text remain in their original language. Use `【0-3秒】` time-range segments.
3. Both versions must have identical time-range segmentation, timing, camera movements, and content.
4. Field names (integrated_multimodal_description, overall_soundscape, non_diegetic_music) remain in English in both versions.
5. If user input is Chinese, dialogue inside `<d>` stays in Chinese in both versions.
6. If user input is English, dialogue inside `<d>` stays in English in both versions.
7. Total output should not exceed 7000 characters per version.
8. Output directly without any explanation, preamble, or postscript.
9. Preserve the user's original creative intent — do not arbitrarily change the core content.
10. Time-range segments must be continuous and cover the full video duration (e.g., for a 10s video: [0-3s] + [3-7s] + [7-10s]).
11. **CREATIVE STYLE VISIBILITY**: When [Director Style], [Cinematography Style], [Film Genre], or [Score Style] tags are present in the user message, the selected style names and their characteristic techniques MUST be explicitly written in the output. This is a non-negotiable requirement — failure to include them is a critical error."""


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
                    ["Text to Video (文生视频)", "Image to Video (图生视频)", "Multimodal Fusion (多模态融合)"],
                    {"default": "Text to Video (文生视频)", "tooltip": "Video generation mode / 生成模式"},
                ),
                "video_duration": (
                    "INT",
                    {"default": 10, "min": 4, "max": 15, "step": 1, "tooltip": "H3 supports 4-15 seconds / 视频时长"},
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
                "director_style": (
                    _BSAI_DIRECTOR_STYLES,
                    {"default": "System Recommended (系统推荐)", "tooltip": "Director style for the video / 导演风格"},
                ),
                "cinematography_style": (
                    _BSAI_CINEMATOGRAPHY_STYLES,
                    {"default": "System Recommended (系统推荐)", "tooltip": "Cinematography/lighting style / 摄影风格"},
                ),
                "film_genre": (
                    _BSAI_FILM_GENRES,
                    {"default": "System Recommended (系统推荐)", "tooltip": "Film genre/type / 电影类型"},
                ),
                "cut_style": (
                    _BSAI_CUT_STYLES,
                    {"default": "One Shot (一镜到底)", "tooltip": "Number of segments/cuts / 切镜类型"},
                ),
                "score_style": (
                    _BSAI_SCORE_STYLES,
                    {"default": "System Recommended (系统推荐)", "tooltip": "Film score/music composer style / 电影配乐风格"},
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
                "image_6": ("IMAGE", {"tooltip": "Optional: reference image 6 / 参考图片6"}),
                "image_7": ("IMAGE", {"tooltip": "Optional: reference image 7 / 参考图片7"}),
                "image_8": ("IMAGE", {"tooltip": "Optional: reference image 8 / 参考图片8"}),
                "image_9": ("IMAGE", {"tooltip": "Optional: reference image 9 / 参考图片9"}),
                "image_10": ("IMAGE", {"tooltip": "Optional: reference image 10 / 参考图片10"}),
                "video_1": ("IMAGE", {"tooltip": "Optional: reference video 1 (key frames extracted) / 参考视频1"}),
                "video_2": ("IMAGE", {"tooltip": "Optional: reference video 2 (key frames extracted) / 参考视频2"}),
                "video_3": ("IMAGE", {"tooltip": "Optional: reference video 3 (key frames extracted) / 参考视频3"}),
                "video_4": ("IMAGE", {"tooltip": "Optional: reference video 4 (key frames extracted) / 参考视频4"}),
                "audio_1": ("AUDIO", {"tooltip": "Optional: reference audio 1 / 参考音频1"}),
                "audio_2": ("AUDIO", {"tooltip": "Optional: reference audio 2 / 参考音频2"}),
                "audio_3": ("AUDIO", {"tooltip": "Optional: reference audio 3 / 参考音频3"}),
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
        no_bgm,
        extra_requirements,
        director_style,
        cinematography_style,
        film_genre,
        cut_style,
        score_style,
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
        image_6=None,
        image_7=None,
        image_8=None,
        image_9=None,
        image_10=None,
        video_1=None,
        video_2=None,
        video_3=None,
        video_4=None,
        audio_1=None,
        audio_2=None,
        audio_3=None,
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
            "Text to Video (文生视频)": "Current mode: Text to Video (no reference materials). Ensure the prompt contains detailed subject appearance, scene details, action descriptions, and style. Skip the [Reference Description] section.",
            "Image to Video (图生视频)": "Current mode: Image to Video. The user will upload images. Please indicate in the prompt whether @image_1 is a first frame or last frame reference. If two images are provided, specify first frame + last frame.",
            "Multimodal Fusion (多模态融合)": "Current mode: Multimodal Fusion. The user may upload character images, action videos, scene images, audio references, etc. Write clear labels and usage for each material (e.g., image_1 -> character reference, video_1 -> action reference, audio_1 -> voice/music reference, etc.).",
        }

        bgm_instruction = (
            "No background music needed. Set non_diegetic_music: N/A. "
            "BUT overall_soundscape MUST still include all scene ambient sounds, character action sounds, and object movement sounds — never silent."
            if no_bgm
            else "No special requirement (may include appropriate background music). "
            "overall_soundscape MUST include scene ambient sounds, character action sounds, and object movement sounds — never silent."
        )
        user_message_parts = [
            f"[Generation Mode] {generation_mode}",
            f"[Video Duration] {video_duration}s (H3 supports 4-15s)",
            f"[Sound & Music] {bgm_instruction}",
        ]

        # ── Creative style parameters ──
        selected_styles = []
        if director_style != "System Recommended (系统推荐)":
            user_message_parts.append(f"[Director Style] {director_style} — You MUST explicitly mention this director's name and their signature visual techniques in the opening of integrated_multimodal_description.")
            selected_styles.append(f"Director: {director_style}")
        if cinematography_style != "System Recommended (系统推荐)":
            user_message_parts.append(f"[Cinematography Style] {cinematography_style} — You MUST explicitly describe this cinematographer's lighting, lens, and camera style in the visual description.")
            selected_styles.append(f"Cinematography: {cinematography_style}")
        if film_genre != "System Recommended (系统推荐)":
            user_message_parts.append(f"[Film Genre] {film_genre} — You MUST reference this genre's visual conventions and aesthetic tone in the scene description.")
            selected_styles.append(f"Genre: {film_genre}")
        if cut_style != "One Shot (一镜到底)":
            num_match = re.search(r'(\d+)', cut_style)
            num_segments = int(num_match.group(1)) if num_match else 2
            user_message_parts.append(f"[Segmentation] Divide the video into exactly {num_segments} time-range segments. Each segment should represent a distinct camera cut with its own shot type, content, and camera movement. Use 'the camera cuts to' between segments.")
        if score_style != "System Recommended (系统推荐)":
            user_message_parts.append(f"[Score Style] {score_style} — You MUST explicitly mention this composer's name and their signature musical style in the non_diegetic_music field.")
            selected_styles.append(f"Score: {score_style}")
        if selected_styles:
            user_message_parts.append(
                f"[⚠ STYLE OUTPUT CHECKLIST] The following creative styles were selected and MUST appear explicitly in the output:\n"
                + "\n".join(f"  - {s}" for s in selected_styles)
                + "\nBefore outputting, verify that each style name and its characteristic techniques are visible in the text. If any style is missing, add it."
            )

        if extra_requirements and extra_requirements.strip():
            user_message_parts.append(f"[Extra Requirements] {extra_requirements.strip()}")

        user_message_parts.append(f"[Mode Hint] {mode_hints.get(generation_mode, '')}")
        user_message_parts.append(f"[User Original Prompt]\n{prompt_text_input}")

        # ── Collect image inputs (up to 10) ──
        image_inputs = [image_1, image_2, image_3, image_4, image_5,
                        image_6, image_7, image_8, image_9, image_10]
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

        # ── Collect video inputs (up to 4, extract key frames) ──
        video_inputs = [video_1, video_2, video_3, video_4]
        collected_videos = []  # list of (label, data_uri_list)
        total_video_frame_count = 0
        for idx, vid in enumerate(video_inputs):
            if vid is None:
                continue
            label = f"video_{idx + 1}"
            data_uris = _bsai_video_to_data_uris(vid)
            if data_uris:
                collected_videos.append((label, data_uris))
                total_video_frame_count += len(data_uris)

        # ── Collect audio inputs (up to 3) ──
        audio_inputs_list = [audio_1, audio_2, audio_3]
        collected_audios = []  # list of (label, description)
        for idx, aud in enumerate(audio_inputs_list):
            if aud is None:
                continue
            label = f"audio_{idx + 1}"
            desc, _b64 = _bsai_audio_to_description(aud, label)
            if desc:
                collected_audios.append((label, desc))

        has_media = total_image_count > 0 or total_video_frame_count > 0 or len(collected_audios) > 0

        # ── Build reference summary text ──
        ref_parts = []
        if total_image_count > 0:
            image_summary = ", ".join(
                f"{label} ({len(uris)} img)" for label, uris in collected_images
            )
            ref_parts.append(
                f"[Reference Images] {total_image_count} image(s) uploaded: {image_summary}.\n"
                "Analyze subject appearance, scene style, composition, etc. from the images and incorporate into the prompt optimization."
            )
        if total_video_frame_count > 0:
            video_summary = ", ".join(
                f"{label} ({len(uris)} keyframes)" for label, uris in collected_videos
            )
            ref_parts.append(
                f"[Reference Videos] {len(collected_videos)} video(s) uploaded: {video_summary}.\n"
                "Key frames have been extracted from each video. Analyze action, motion, temporal progression, and scene continuity from the video frames."
            )
        if collected_audios:
            audio_summary = ", ".join(desc for _, desc in collected_audios)
            ref_parts.append(
                f"[Reference Audio] {len(collected_audios)} audio clip(s) uploaded: {audio_summary}.\n"
                "Use these audio clips as voice/music/sound references in the prompt. "
                "Note: Audio content cannot be directly analyzed by the vision model; describe its intended use based on the user's prompt context."
            )

        if ref_parts:
            user_message_parts.extend(ref_parts)
            # Switch to multimodal mode hint
            if generation_mode == "Text to Video (文生视频)":
                user_message_parts.append(
                    "[Note] Media inputs detected. Please optimize using 'Image to Video' or 'Multimodal Fusion' mode."
                )

        user_message_parts.append(
            "\nBased on the above information, optimize the prompt according to H3 specification. Any selected creative styles (director, cinematography, genre, score) MUST be explicitly mentioned in the output. Output the optimized prompt directly without any explanation."
        )

        user_message = "\n".join(user_message_parts)

        # ── Build messages: use multimodal content format when media is present ──
        if has_media:
            user_content = []
            user_content.append({"type": "text", "text": user_message})
            # Add images
            for label, uris in collected_images:
                for uri in uris:
                    user_content.append(
                        {"type": "image_url", "image_url": {"url": uri}}
                    )
                    user_content.append(
                        {"type": "text", "text": f"(Above is {label})"}
                    )
            # Add video keyframes
            for label, uris in collected_videos:
                for i, uri in enumerate(uris):
                    user_content.append(
                        {"type": "image_url", "image_url": {"url": uri}}
                    )
                    frame_desc = f"(Above is {label} keyframe {i + 1}/{len(uris)})"
                    user_content.append(
                        {"type": "text", "text": frame_desc}
                    )
            messages = [
                {"role": "system", "content": _H3_SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ]
            media_info = f"{total_image_count} image(s)"
            if total_video_frame_count > 0:
                media_info += f", {total_video_frame_count} video keyframe(s)"
            if collected_audios:
                media_info += f", {len(collected_audios)} audio clip(s)"
            print(f"[BSAI H3] Multimodal inference: {media_info}")
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

        # ── Inference with auto-recovery: if the model was closed (e.g. by
        # BSAI_H3_UnloadModel in a previous run), ComfyUI may still pass the
        # stale model object. Retry once after reloading. ──
        try:
            out = _bsai_call_chat_completion(llm, messages=messages, params=params)
        except (RuntimeError, KeyError, ValueError, Exception) as e:
            # Check if the error is due to an invalid/closed model
            if _bsai_is_model_valid(llm) and "Context Shift is explicitly disabled" not in str(e):
                # Model seems valid but inference failed for another reason
                if "Context Shift" in str(e):
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

            # Model is invalid → try auto-reload and retry once
            print(f"[BSAI H3] Inference failed ({type(e).__name__}: {e}), attempting auto-reload...")
            if _BSAI_QwenStorage.settings is not None:
                llm = _BSAI_QwenStorage.load(_BSAI_QwenStorage.settings)
                # Re-read n_ctx after reload
                try:
                    n_ctx_raw = getattr(llm, "n_ctx", 4096)
                    n_ctx = int(n_ctx_raw()) if callable(n_ctx_raw) else int(n_ctx_raw)
                except Exception:
                    n_ctx = 4096
                safe_max_tokens = min(max_tokens_val, n_ctx - est_prompt_tokens - 256)
                if safe_max_tokens < 512:
                    safe_max_tokens = min(max_tokens_val, max(256, n_ctx // 4))
                params["max_tokens"] = safe_max_tokens
                print("[BSAI H3] Model reloaded, retrying inference...")
                out = _bsai_call_chat_completion(llm, messages=messages, params=params)
            else:
                raise RuntimeError(
                    "Model became invalid during inference and no cached settings "
                    "available for auto-reload. Please re-run BSAI_H3_ModelLoader."
                ) from e

        try:
            text = out["choices"][0]["message"]["content"]
        except Exception:
            text = str(out)

        text = text.lstrip().removeprefix(": ").strip()
        text = _bsai_enforce_style_output(
            text, director_style, cinematography_style,
            film_genre, score_style,
        )
        return (text,)


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


# ============================================================
# Remote API Node (OpenAI / DashScope compatible)
# ============================================================

class BSAI_H3_RemoteAPI:
    """Call a remote LLM API (OpenAI/DashScope compatible) for H3 prompt optimization.

    Supports any OpenAI-compatible endpoint:
    - OpenAI: https://api.openai.com/v1 (gpt-4o, gpt-4o-mini, etc.)
    - DashScope: https://dashscope.aliyuncs.com/compatible-mode/v1 (qwen-plus, qwen-max, etc.)
    - Other compatible services (Ollama, LM Studio, vLLM, etc.)
    """

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "user_prompt": (
                    "STRING",
                    {
                        "default": "",
                        "multiline": True,
                        "tooltip": "User's original prompt to be optimized / 用户原始提示词",
                    },
                ),
                "api_base_url": (
                    "STRING",
                    {
                        "default": "https://dashscope.aliyuncs.com/compatible-mode/v1",
                        "tooltip": "OpenAI-compatible API base URL / API地址",
                    },
                ),
                "api_key": (
                    "STRING",
                    {
                        "default": "",
                        "tooltip": "API key for authentication / API密钥",
                    },
                ),
                "model_name": (
                    "STRING",
                    {
                        "default": "qwen-plus",
                        "tooltip": "Model name (e.g. gpt-4o, qwen-plus, qwen-max) / 模型名称",
                    },
                ),
                "generation_mode": (
                    ["Text to Video (文生视频)", "Image to Video (图生视频)", "Multimodal Fusion (多模态融合)"],
                    {"default": "Text to Video (文生视频)", "tooltip": "Video generation mode / 生成模式"},
                ),
                "video_duration": (
                    "INT",
                    {"default": 10, "min": 4, "max": 15, "step": 1, "tooltip": "H3 supports 4-15 seconds / 视频时长"},
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
                "director_style": (
                    _BSAI_DIRECTOR_STYLES,
                    {"default": "System Recommended (系统推荐)", "tooltip": "Director style for the video / 导演风格"},
                ),
                "cinematography_style": (
                    _BSAI_CINEMATOGRAPHY_STYLES,
                    {"default": "System Recommended (系统推荐)", "tooltip": "Cinematography/lighting style / 摄影风格"},
                ),
                "film_genre": (
                    _BSAI_FILM_GENRES,
                    {"default": "System Recommended (系统推荐)", "tooltip": "Film genre/type / 电影类型"},
                ),
                "cut_style": (
                    _BSAI_CUT_STYLES,
                    {"default": "One Shot (一镜到底)", "tooltip": "Number of segments/cuts / 切镜类型"},
                ),
                "score_style": (
                    _BSAI_SCORE_STYLES,
                    {"default": "System Recommended (系统推荐)", "tooltip": "Film score/music composer style / 电影配乐风格"},
                ),
                "max_tokens": ("INT", {"default": 4096, "min": 256, "max": 65536, "step": 1, "tooltip": "Max generation tokens / 最大生成token"}),
                "temperature": ("FLOAT", {"default": 0.7, "min": 0.0, "max": 2.0, "step": 0.01}),
                "top_p": ("FLOAT", {"default": 0.9, "min": 0.0, "max": 1.0, "step": 0.01}),
                "seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff, "step": 1}),
            },
            "optional": {
                "image_1": ("IMAGE", {"tooltip": "Optional: reference image 1 / 参考图片1"}),
                "image_2": ("IMAGE", {"tooltip": "Optional: reference image 2 / 参考图片2"}),
                "image_3": ("IMAGE", {"tooltip": "Optional: reference image 3 / 参考图片3"}),
                "image_4": ("IMAGE", {"tooltip": "Optional: reference image 4 / 参考图片4"}),
                "image_5": ("IMAGE", {"tooltip": "Optional: reference image 5 / 参考图片5"}),
                "image_6": ("IMAGE", {"tooltip": "Optional: reference image 6 / 参考图片6"}),
                "image_7": ("IMAGE", {"tooltip": "Optional: reference image 7 / 参考图片7"}),
                "image_8": ("IMAGE", {"tooltip": "Optional: reference image 8 / 参考图片8"}),
                "image_9": ("IMAGE", {"tooltip": "Optional: reference image 9 / 参考图片9"}),
                "image_10": ("IMAGE", {"tooltip": "Optional: reference image 10 / 参考图片10"}),
                "video_1": ("IMAGE", {"tooltip": "Optional: reference video 1 (key frames extracted) / 参考视频1"}),
                "video_2": ("IMAGE", {"tooltip": "Optional: reference video 2 (key frames extracted) / 参考视频2"}),
                "video_3": ("IMAGE", {"tooltip": "Optional: reference video 3 (key frames extracted) / 参考视频3"}),
                "video_4": ("IMAGE", {"tooltip": "Optional: reference video 4 (key frames extracted) / 参考视频4"}),
                "audio_1": ("AUDIO", {"tooltip": "Optional: reference audio 1 / 参考音频1"}),
                "audio_2": ("AUDIO", {"tooltip": "Optional: reference audio 2 / 参考音频2"}),
                "audio_3": ("AUDIO", {"tooltip": "Optional: reference audio 3 / 参考音频3"}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("prompt_output",)
    FUNCTION = "optimize_prompt_remote"
    CATEGORY = "BSAI"
    DESCRIPTION = """
Call a remote LLM API (OpenAI/DashScope compatible) to optimize prompts into H3-compliant structured prompts.
No local model loading required - saves VRAM for video generation.
Supports multimodal models (e.g. gpt-4o, qwen-vl-plus) for image analysis.
"""

    def optimize_prompt_remote(
        self,
        user_prompt,
        api_base_url,
        api_key,
        model_name,
        generation_mode,
        video_duration,
        no_bgm,
        extra_requirements,
        director_style,
        cinematography_style,
        film_genre,
        cut_style,
        score_style,
        max_tokens,
        temperature,
        top_p,
        seed,
        image_1=None,
        image_2=None,
        image_3=None,
        image_4=None,
        image_5=None,
        image_6=None,
        image_7=None,
        image_8=None,
        image_9=None,
        image_10=None,
        video_1=None,
        video_2=None,
        video_3=None,
        video_4=None,
        audio_1=None,
        audio_2=None,
        audio_3=None,
    ):
        if requests is None:
            raise RuntimeError(
                "The 'requests' library is not installed. Please install it: pip install requests"
            )

        prompt_text_input = (user_prompt or "").strip()
        if not prompt_text_input:
            raise ValueError("user_prompt cannot be empty. Please enter a prompt to optimize.")

        if not api_key.strip():
            raise ValueError("api_key cannot be empty. Please enter your API key.")

        mode_hints = {
            "Text to Video (文生视频)": "Current mode: Text to Video (no reference materials). Ensure the prompt contains detailed subject appearance, scene details, action descriptions, and style. Skip the [Reference Description] section.",
            "Image to Video (图生视频)": "Current mode: Image to Video. The user will upload images. Please indicate in the prompt whether @image_1 is a first frame or last frame reference. If two images are provided, specify first frame + last frame.",
            "Multimodal Fusion (多模态融合)": "Current mode: Multimodal Fusion. The user may upload character images, action videos, scene images, audio references, etc. Write clear labels and usage for each material (e.g., image_1 -> character reference, video_1 -> action reference, audio_1 -> voice/music reference, etc.).",
        }

        bgm_instruction = (
            "No background music needed. Set non_diegetic_music: N/A. "
            "BUT overall_soundscape MUST still include all scene ambient sounds, character action sounds, and object movement sounds — never silent."
            if no_bgm
            else "No special requirement (may include appropriate background music). "
            "overall_soundscape MUST include scene ambient sounds, character action sounds, and object movement sounds — never silent."
        )
        user_message_parts = [
            f"[Generation Mode] {generation_mode}",
            f"[Video Duration] {video_duration}s (H3 supports 4-15s)",
            f"[Sound & Music] {bgm_instruction}",
        ]

        # ── Creative style parameters ──
        selected_styles = []
        if director_style != "System Recommended (系统推荐)":
            user_message_parts.append(f"[Director Style] {director_style} — You MUST explicitly mention this director's name and their signature visual techniques in the opening of integrated_multimodal_description.")
            selected_styles.append(f"Director: {director_style}")
        if cinematography_style != "System Recommended (系统推荐)":
            user_message_parts.append(f"[Cinematography Style] {cinematography_style} — You MUST explicitly describe this cinematographer's lighting, lens, and camera style in the visual description.")
            selected_styles.append(f"Cinematography: {cinematography_style}")
        if film_genre != "System Recommended (系统推荐)":
            user_message_parts.append(f"[Film Genre] {film_genre} — You MUST reference this genre's visual conventions and aesthetic tone in the scene description.")
            selected_styles.append(f"Genre: {film_genre}")
        if cut_style != "One Shot (一镜到底)":
            num_match = re.search(r'(\d+)', cut_style)
            num_segments = int(num_match.group(1)) if num_match else 2
            user_message_parts.append(f"[Segmentation] Divide the video into exactly {num_segments} time-range segments. Each segment should represent a distinct camera cut with its own shot type, content, and camera movement. Use 'the camera cuts to' between segments.")
        if score_style != "System Recommended (系统推荐)":
            user_message_parts.append(f"[Score Style] {score_style} — You MUST explicitly mention this composer's name and their signature musical style in the non_diegetic_music field.")
            selected_styles.append(f"Score: {score_style}")
        if selected_styles:
            user_message_parts.append(
                f"[⚠ STYLE OUTPUT CHECKLIST] The following creative styles were selected and MUST appear explicitly in the output:\n"
                + "\n".join(f"  - {s}" for s in selected_styles)
                + "\nBefore outputting, verify that each style name and its characteristic techniques are visible in the text. If any style is missing, add it."
            )

        if extra_requirements and extra_requirements.strip():
            user_message_parts.append(f"[Extra Requirements] {extra_requirements.strip()}")

        user_message_parts.append(f"[Mode Hint] {mode_hints.get(generation_mode, '')}")
        user_message_parts.append(f"[User Original Prompt]\n{prompt_text_input}")

        # ── Collect image inputs (up to 10) ──
        image_inputs = [image_1, image_2, image_3, image_4, image_5,
                        image_6, image_7, image_8, image_9, image_10]
        collected_images = []
        total_image_count = 0
        for idx, img in enumerate(image_inputs):
            if img is None:
                continue
            label = f"image_{idx + 1}"
            data_uris = _bsai_image_tensor_to_data_uri(img)
            if data_uris:
                collected_images.append((label, data_uris))
                total_image_count += len(data_uris)

        # ── Collect video inputs (up to 4, extract key frames) ──
        video_inputs = [video_1, video_2, video_3, video_4]
        collected_videos = []
        total_video_frame_count = 0
        for idx, vid in enumerate(video_inputs):
            if vid is None:
                continue
            label = f"video_{idx + 1}"
            data_uris = _bsai_video_to_data_uris(vid)
            if data_uris:
                collected_videos.append((label, data_uris))
                total_video_frame_count += len(data_uris)

        # ── Collect audio inputs (up to 3) ──
        audio_inputs_list = [audio_1, audio_2, audio_3]
        collected_audios = []
        for idx, aud in enumerate(audio_inputs_list):
            if aud is None:
                continue
            label = f"audio_{idx + 1}"
            desc, _b64 = _bsai_audio_to_description(aud, label)
            if desc:
                collected_audios.append((label, desc))

        has_media = total_image_count > 0 or total_video_frame_count > 0 or len(collected_audios) > 0

        # ── Build reference summary text ──
        ref_parts = []
        if total_image_count > 0:
            image_summary = ", ".join(
                f"{label} ({len(uris)} img)" for label, uris in collected_images
            )
            ref_parts.append(
                f"[Reference Images] {total_image_count} image(s) uploaded: {image_summary}.\n"
                "Analyze subject appearance, scene style, composition, etc. from the images and incorporate into the prompt optimization."
            )
        if total_video_frame_count > 0:
            video_summary = ", ".join(
                f"{label} ({len(uris)} keyframes)" for label, uris in collected_videos
            )
            ref_parts.append(
                f"[Reference Videos] {len(collected_videos)} video(s) uploaded: {video_summary}.\n"
                "Key frames have been extracted from each video. Analyze action, motion, temporal progression, and scene continuity from the video frames."
            )
        if collected_audios:
            audio_summary = ", ".join(desc for _, desc in collected_audios)
            ref_parts.append(
                f"[Reference Audio] {len(collected_audios)} audio clip(s) uploaded: {audio_summary}.\n"
                "Use these audio clips as voice/music/sound references in the prompt. "
                "Note: Audio content cannot be directly analyzed by the vision model; describe its intended use based on the user's prompt context."
            )

        if ref_parts:
            user_message_parts.extend(ref_parts)
            if generation_mode == "Text to Video (文生视频)":
                user_message_parts.append(
                    "[Note] Media inputs detected. Please optimize using 'Image to Video' or 'Multimodal Fusion' mode."
                )

        user_message_parts.append(
            "\nBased on the above information, optimize the prompt according to H3 specification. Any selected creative styles (director, cinematography, genre, score) MUST be explicitly mentioned in the output. Output the optimized prompt directly without any explanation."
        )

        user_message = "\n".join(user_message_parts)

        # ── Build messages ──
        if has_media:
            user_content = [{"type": "text", "text": user_message}]
            # Add images
            for label, uris in collected_images:
                for uri in uris:
                    user_content.append({"type": "image_url", "image_url": {"url": uri}})
                    user_content.append({"type": "text", "text": f"(Above is {label})"})
            # Add video keyframes
            for label, uris in collected_videos:
                for i, uri in enumerate(uris):
                    user_content.append({"type": "image_url", "image_url": {"url": uri}})
                    frame_desc = f"(Above is {label} keyframe {i + 1}/{len(uris)})"
                    user_content.append({"type": "text", "text": frame_desc})
            messages = [
                {"role": "system", "content": _H3_SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ]
            media_info = f"{total_image_count} image(s)"
            if total_video_frame_count > 0:
                media_info += f", {total_video_frame_count} video keyframe(s)"
            if collected_audios:
                media_info += f", {len(collected_audios)} audio clip(s)"
            print(f"[BSAI H3 RemoteAPI] Multimodal request: {media_info}")
        else:
            messages = [
                {"role": "system", "content": _H3_SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ]

        # ── Build request payload ──
        payload = {
            "model": model_name.strip(),
            "messages": messages,
            "max_tokens": int(max_tokens),
            "temperature": float(temperature),
            "top_p": float(top_p),
            "stream": False,
        }
        if seed > 0:
            payload["seed"] = int(seed)

        # ── Build headers ──
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key.strip()}",
        }

        # ── Make API call ──
        url = api_base_url.strip().rstrip("/") + "/chat/completions"
        print(f"[BSAI H3 RemoteAPI] Calling: {url} | model: {model_name}")

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=120)
        except requests.exceptions.Timeout:
            raise RuntimeError(
                f"API request timed out (120s). The service may be slow or unreachable.\n"
                f"URL: {url}"
            )
        except requests.exceptions.ConnectionError as e:
            raise RuntimeError(
                f"Failed to connect to API: {e}\n"
                f"URL: {url}\n"
                "Please check the api_base_url and your network connection."
            )

        if response.status_code != 200:
            error_detail = ""
            try:
                error_body = response.json()
                error_detail = json.dumps(error_body, indent=2, ensure_ascii=False)
            except Exception:
                error_detail = response.text
            raise RuntimeError(
                f"API returned error {response.status_code}:\n{error_detail}"
            )

        try:
            result = response.json()
            text = result["choices"][0]["message"]["content"]
        except (KeyError, IndexError, json.JSONDecodeError) as e:
            raise RuntimeError(
                f"Failed to parse API response: {e}\n"
                f"Response: {response.text[:500]}"
            )

        text = text.lstrip().removeprefix(": ").strip()
        text = _bsai_enforce_style_output(
            text, director_style, cinematography_style,
            film_genre, score_style,
        )
        return (text,)


# ============================================================
# BSAI LineCount - 行数统计节点
# 功能与 WWAA_LineCount 完全一致，用于替换缺失的 WWAA 节点
# ============================================================

class BSAI_LineCount:
    DESCRIPTION = "Reads a multi-line string and counts how many lines exist while ignoring blank lines. Useful for determining the number of prompts or entries in text data."

    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "string_text": ("STRING", {
                    "multiline": True,
                    "default": "String goes here\nSecond line."
                }),
            },
        }

    RETURN_TYPES = ("INT",)
    RETURN_NAMES = ("Line Count",)

    FUNCTION = "executeLineCount"
    CATEGORY = "BSAI/String"

    def executeLineCount(self, string_text):
        # Count lines - same logic as WWAA_LineCount
        string_text = string_text.strip()  # strip extra line feeds
        string_text = string_text.strip()
        string_text = re.sub(r'((\n){2,})', '\n', string_text)
        lines = string_text.split('\n')
        num_lines = len(lines)
        return (num_lines,)


NODE_CLASS_MAPPINGS = {
    "BSAI_MiniMAX H3 prompt": BSAI_MiniMAX_H3_Prompt,
    "BSAI_H3_ModelLoader": BSAI_H3_ModelLoader,
    "BSAI_H3_UnloadModel": BSAI_H3_UnloadModel,
    "BSAI_H3_RemoteAPI": BSAI_H3_RemoteAPI,
    "BSAI_LineCount": BSAI_LineCount,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "BSAI_MiniMAX H3 prompt": "BSAI MiniMAX H3 Prompt",
    "BSAI_H3_ModelLoader": "BSAI H3 Model Loader",
    "BSAI_H3_UnloadModel": "BSAI H3 Unload Model",
    "BSAI_H3_RemoteAPI": "BSAI H3 Remote API",
    "BSAI_LineCount": "BSAI LineCount",
}
