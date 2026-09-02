"""
BSAI H3 Prompt Template Node

One-click ready-to-use H3 prompt templates.
Categorized by generation mode (I2VA/T2VA/FL2VA/Ref2VA) with subcategories
and specific templates. Includes GIF preview support via JS frontend.

Template data: templates/prompt_templates.json
"""

import os
import json

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_TEMPLATE_JSON = os.path.join(_THIS_DIR, "templates", "prompt_templates.json")


def _load_templates():
    try:
        with open(_TEMPLATE_JSON, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"categories": []}


_TEMPLATE_CACHE = None
_TEMPLATE_CACHE_MTIME = None


def _get_template_data():
    """Load template JSON with hot-reload: if the file's mtime changed since the
    last load, reload it — so editing templates/prompt_templates.json takes effect
    WITHOUT restarting ComfyUI."""
    global _TEMPLATE_CACHE, _TEMPLATE_CACHE_MTIME
    try:
        mtime = os.path.getmtime(_TEMPLATE_JSON)
    except Exception:
        mtime = None
    if _TEMPLATE_CACHE is None or mtime != _TEMPLATE_CACHE_MTIME:
        _TEMPLATE_CACHE = _load_templates()
        _TEMPLATE_CACHE_MTIME = mtime
    return _TEMPLATE_CACHE


def _find_template(label):
    if not label or label.startswith("("):
        return None
    data = _get_template_data()
    for cat in data.get("categories", []):
        for sub in cat.get("subcategories", []):
            for tpl in sub.get("templates", []):
                full = f"{cat['name']} > {sub['name']} > {tpl['name']}"
                if full == label:
                    return tpl
    return None


# ── Multi-select merging (H3 SKILL three-field composition) ──
_LABEL_SEP = "|||"


def _split_prompt(prompt):
    """Split a template prompt into H3 sections: header, desc, sound, music."""
    p = prompt or ""
    out = {"header": "", "desc": "", "sound": "", "music": ""}
    idx = p.find("integrated_multimodal_description:")
    if idx < 0:
        out["header"] = p.strip()
        return out
    out["header"] = p[:idx].strip()
    body = p[idx:]
    nxt = body.find("overall_soundscape:")
    if nxt < 0:
        nxt = len(body)
    out["desc"] = body[len("integrated_multimodal_description:"):nxt].strip()
    if nxt < len(body):
        tail = body[nxt:]
        m2 = tail.find("non_diegetic_music:")
        if m2 < 0:
            out["sound"] = tail[len("overall_soundscape:"):].strip()
        else:
            out["sound"] = tail[len("overall_soundscape:"):m2].strip()
            out["music"] = tail[m2 + len("non_diegetic_music:"):].strip()
    return out


def _is_na(s):
    return not s or s.strip().upper() in ("", "N/A", "NA", "无")


# ── External action override ──
_ACTION_OPEN = "【ACTION】"
_ACTION_CLOSE = "【/ACTION】"


def _apply_action_override(desc, ext):
    """Make the external prompt OVERRIDE the template's action instead of being appended.

    - Literal replacement for EVERY 【ACTION】...【/ACTION】 marker in the description.
    - Otherwise a strong directive is appended to the description so the external
      action replaces the built-in motion for every template.
    Returns (new_desc, overridden).
    """
    if not ext:
        return desc, False
    if _ACTION_OPEN in desc and _ACTION_CLOSE in desc:
        block = (
            f'The subject performs the action “{ext}” exactly as instructed. '
            f'All shot framing, camera movement, environment, lighting, timing '
            f'and subject identity remain unchanged; only the action/behavior is replaced.'
        )
        while True:
            open_i = desc.find(_ACTION_OPEN)
            close_i = desc.find(_ACTION_CLOSE, open_i + len(_ACTION_OPEN)) if open_i >= 0 else -1
            if open_i < 0 or close_i < 0:
                break
            desc = desc[:open_i] + block + desc[close_i + len(_ACTION_CLOSE):]
        return desc, True
    directive = (
        f'[Action Override / 动作覆盖] IMPORTANT: The subject performs “{ext}” '
        f'INSTEAD OF the motion/behavior described in the shots above. Keep all shot '
        f'framing, camera movement, environment, lighting, timing and subject identity '
        f'unchanged; only the action/behavior is replaced with: {ext}'
    )
    return desc + "\n\n" + directive, True


def _merge_template_prompts(tpls, ext=""):
    """Merge multiple template prompts into ONE coherent H3 prompt.
    Base = first template (scene/action), overlays = extra camera/directive templates.
    ext = external prompt: overrides the base template's action when provided."""
    if not tpls:
        return ""
    if len(tpls) == 1:
        p = tpls[0].get("prompt", "")
        if ext:
            sec = _split_prompt(p)
            nd, ov = _apply_action_override(sec["desc"], ext)
            if ov:
                sound = sec["sound"]
                if not _is_na(sound):
                    sound += f"\n(Adjust ambient sound and effects to match the overridden action “{ext}”)"
                parts = []
                if sec["header"]:
                    parts.append(sec["header"])
                parts.append("integrated_multimodal_description: \n" + (nd or "N/A"))
                parts.append("overall_soundscape: \n" + (sound or "N/A"))
                parts.append("non_diegetic_music: \n" + (sec["music"] or "N/A"))
                return "\n\n".join(parts)
        return p
    base = _split_prompt(tpls[0].get("prompt", ""))
    desc = base["desc"]
    sound = base["sound"]
    music = base["music"]
    if ext:
        desc, ov = _apply_action_override(desc, ext)
        if ov and not _is_na(sound):
            sound += f"\n(Adjust ambient sound and effects to match the overridden action “{ext}”)"
    for t in tpls[1:]:
        sec = _split_prompt(t.get("prompt", ""))
        label = f"{t.get('name','')} | {t.get('name_en','')}"
        if sec["desc"]:
            desc += f"\n\n# Overlay 叠加模板: {label}\n{sec['desc']}"
        if not _is_na(sec["sound"]):
            if _is_na(sound):
                sound = sec["sound"]
            else:
                sound += "\n" + sec["sound"]
        if _is_na(music) and not _is_na(sec["music"]):
            music = sec["music"]
    parts = []
    if base["header"]:
        parts.append(base["header"])
    parts.append("integrated_multimodal_description: \n" + (desc or "N/A"))
    parts.append("overall_soundscape: \n" + (sound or "N/A"))
    parts.append("non_diegetic_music: \n" + (music or "N/A"))
    return "\n\n".join(parts)


def _merge_custom(prompt, cust):
    """Apply the user customization INSIDE the prompt via the local/API LLM
    (rewrite transition/action/scene etc.), returning a (prompt, error) tuple.
    Falls back to the original prompt on any failure — the caller decides the
    fallback display (append vs original)."""
    import sys as _sys
    if _THIS_DIR not in _sys.path:
        _sys.path.insert(0, _THIS_DIR)
    from h3_direct_llm import merge_customization
    return merge_customization(prompt, cust)


def _append_custom(prompt, cust):
    return (prompt.rstrip() + "\n\n--- User Customization / 用户自定义 ---\n" + cust.strip())


# ── Scene reference (图3场景) dynamic clause ──
# Templates may embed {{SCENE_REF_RULE}} and {{SCENE_SUMMARY}} placeholders.
# If the optional scene_image input is connected (user provided a <Picture 3> scene),
# they are replaced with the "use the scene from <Picture 3>" wording; otherwise the
# "neutral default scene" wording is used.
_SCENE_REF_RULE_HAS = (
    "<Picture 3> (SCENE): provides the fighting environment — the output scene must be "
    "EXACTLY the scene, background, architecture, lighting, and atmosphere from <Picture 3>. "
    "Preserve this exact environment unchanged throughout the fight."
)
_SCENE_REF_RULE_NONE = (
    "(No scene reference image — the fighting environment is a neutral, uncluttered open "
    "space suitable for a standing fight; do not introduce any specific location.)"
)
_SCENE_SUMMARY_HAS = (
    "The fighting environment is EXACTLY the scene from <Picture 3> — same background, "
    "architecture, lighting, and atmosphere, preserved unchanged throughout the fight."
)
_SCENE_SUMMARY_NONE = (
    "The fighting environment is a neutral, uncluttered open space; no specific location is introduced."
)


def _apply_scene_placeholder(prompt, has_scene):
    """Replace {{SCENE_REF_RULE}} / {{SCENE_SUMMARY}} with scene-vs-default wording."""
    if not prompt:
        return prompt
    ref = _SCENE_REF_RULE_HAS if has_scene else _SCENE_REF_RULE_NONE
    summ = _SCENE_SUMMARY_HAS if has_scene else _SCENE_SUMMARY_NONE
    return prompt.replace("{{SCENE_REF_RULE}}", ref).replace("{{SCENE_SUMMARY}}", summ)


class BSAI_H3_PromptTemplate:
    """One-click H3 prompt template selector with categorized templates and GIF preview."""

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "template_select": (
                    "STRING",
                    {
                        "default": "(None / 自定义 / Custom)",
                        "tooltip": "Selected via visual template browser below / 通过下方可视化模板浏览器选择\nClick templates to stack (multi-select), separated by ||| / 点击模板叠加多选，以 ||| 分隔\nCombined into one H3 prompt / 合并输出为一个 H3 提示词",
                    },
                ),
                "user_customization": (
                    "STRING",
                    {
                        "default": "",
                        "multiline": True,
                        "tooltip": "Optional: append custom modifications to the selected template / 可选：在选中模板后追加自定义修改\nThis text will be appended to the prompt output / 此文本将追加到提示词输出中",
                    },
                ),
            },
            "optional": {
                "scene_image": (
                    "IMAGE",
                    {
                        "tooltip": "图3场景参考图 (可选) / Scene reference image <Picture 3> (optional)\n提供时提示词按图3场景生成；不提供时按默认场景生成\nIf connected, the prompt uses the scene from <Picture 3>; otherwise it uses a neutral default scene.",
                    },
                ),
                "external_prompt": (
                    "STRING",
                    {
                        "default": "",
                        "multiline": True,
                        "forceInput": True,
                        "tooltip": "External prompt text input port / 外部提示词文本输入端口\nConnect from another node to OVERRIDE the template's action / 可从其他节点连接外部文本，用于覆盖模板中的动作描述\nE.g. input \"抬腿\" to replace the template's walking/motion with leg-lifting / 例如输入“抬腿”可将模板中的行走动作替换为抬腿",
                    },
                ),
                "direct_prompt": (
                    "STRING",
                    {
                        "default": "",
                        "multiline": True,
                        "tooltip": "Direct mode / 直通模式\nWhen non-empty, output this text as the complete prompt, bypassing templates / 非空时直接输出该文本作为完整提示词，绕过模板\nGenerated by the 🎤 voice dialog's Direct mode / 由语音对话框的直通模式生成",
                    },
                ),
            },
        }

    RETURN_TYPES = ("STRING", "STRING", "STRING", "STRING", "INT", "STRING")
    RETURN_NAMES = (
        "prompt_output (提示词输出)",
        "template_name (模板名称)",
        "generation_mode (生成模式)",
        "description (描述)",
        "video_duration (视频时长)",
        "preview_file (预览文件)",
    )
    FUNCTION = "get_template"
    CATEGORY = "BSAI"
    OUTPUT_IS_LIST = (False, False, False, False, False, False)
    DESCRIPTION = """
One-click H3 prompt template selector / 一键式 H3 提示词模板选择器

Categorized templates: I2VA / T2VA / FL2VA / Ref2VA + Expression + Growth + Timelapse + Combat + Cinematic
分类模板：图生视频 / 文生视频 / 首尾帧生成 / 多模态融合 + 人物表情 + 生长类 + 延时摄影 + 武打对打 + 电影运镜

Features / 功能特点:
- Visual template browser with search / 可视化模板浏览器，支持搜索
- Cascading selection: Category > Subcategory > Template / 级联选择：分类 > 子类 > 模板
- Multi-select stacking: combine 2+ templates (e.g. combat + camera move) into one H3 prompt / 多选叠加：组合 2+ 个模板（如武打+运镜）合并为一个 H3 提示词
- GIF/WebP preview on the right panel / 右侧预览动画
- Optional user customization textarea / 可选的补充修改文本框
- External prompt input port (external_prompt) OVERRIDES the template's action, e.g. "抬腿" replaces walking / 外部提示词输入端口（external_prompt）覆盖模板中的动作，如“抬腿”替换行走动作
- 🎤 Voice input button: speak into the mic → offline local ASR (Vosk, vosk-model-small-cn-0.22) → fills external_prompt / 语音输入按钮：麦克风说话 → 本地离线识别（Vosk 中文模型）→ 填入外部提示词
- ⚡ Direct mode (直通模式): voice/text instruction → local LLM → full H3 prompt (bypasses templates) / 直通模式：语音/文本指令 → 本地大模型 → 完整 H3 提示词（绕过模板）
- Bilingual template names (中文 | English) / 模板名称中英双语对照
- 46 expression & micro-expression templates / 46个表情与微表情模板
- All new templates follow MiniMax H3 prompt SKILL rules / 新增模板严格遵循 MiniMax H3 提示词 SKILL 规则
"""

    def get_template(self, template_select, user_customization="", external_prompt="", direct_prompt="", scene_image=None):
        direct = (direct_prompt or "").strip()
        if direct:
            # ── Direct mode / 直通模式: bypass templates, output the prompt as-is ──
            prompt = direct
            cust = (user_customization or "").strip()
            if cust:
                # Try to apply the customization INSIDE the direct prompt (best effort)
                try:
                    merged, merr = _merge_custom(prompt, cust)
                    if merged and merged.strip() and merged != prompt:
                        prompt = merged
                    else:
                        prompt = _append_custom(prompt, cust)
                except Exception:
                    prompt = _append_custom(prompt, cust)
            return (prompt, "直通模式 | Direct Mode", "Direct / 直通", "Direct H3 prompt / 直通 H3 提示词", 0, "")

        # Support multi-select: labels joined by "|||", e.g. "武打打斗模板 > 多图成战类 > 贴身缠斗 ||| 电影运镜模板 > 跟随与环绕类 > 环绕镜头"
        labels = [x.strip() for x in (template_select or "").split(_LABEL_SEP) if x.strip()]
        tpls = []
        for lbl in labels:
            t = _find_template(lbl)
            if t is not None:
                tpls.append(t)

        ext = (external_prompt or "").strip()
        cust = (user_customization or "").strip()

        if not tpls:
            custom_text = (template_select or "").strip()
            if custom_text and not custom_text.startswith("("):
                prompt = custom_text
            else:
                prompt = ""
            if ext:
                prompt = (prompt + "\n\n" if prompt.strip() else "") + f"生成的视频画面严禁出现external_prompt输入的关键字问题：{ext}"
            if cust:
                try:
                    merged, merr = _merge_custom(prompt, cust) if prompt.strip() else ("", None)
                    if merged and merged.strip() and merged != prompt:
                        prompt = merged
                    else:
                        prompt = _append_custom(prompt, cust)
                except Exception:
                    prompt = _append_custom(prompt, cust)
            return (prompt, "Custom / 自定义", "System Recommended / 系统推荐", "Custom prompt / 自定义提示词", 0, "")

        # Merge all selected templates. external_prompt 作为"反向提示词 / 严禁出现的关键字列表"，
        # 不再作为动作覆盖（避免负向词如"五官扭曲"被当成要生成的动作）。
        prompt = _merge_template_prompts(tpls, "")
        if ext:
            prompt = (prompt + "\n\n" if prompt.strip() else "") + f"生成的视频画面严禁出现external_prompt输入的关键字问题：{ext}"
        if cust:
            # Apply the customization INSIDE the merged prompt via the local LLM;
            # fall back to a plain append when no LLM is available.
            try:
                merged, merr = _merge_custom(prompt, cust)
                if merged and merged.strip() and merged != prompt:
                    prompt = merged
                else:
                    prompt = _append_custom(prompt, cust)
            except Exception:
                prompt = _append_custom(prompt, cust)

        primary = tpls[0]
        # Bilingual merged name list: "贴身缠斗 | Close Grappling + 环绕镜头 | Orbit (Arc Shot)"
        name_label = " + ".join(
            f"{t.get('name','')} | {t.get('name_en','')}" if t.get("name_en") else t.get("name", "")
            for t in tpls
        )
        # ── Scene reference (图3场景): if scene_image connected → use <Picture 3> scene wording ──
        prompt = _apply_scene_placeholder(prompt, scene_image is not None)
        mode = primary.get("generation_mode", "System Recommended / 系统推荐")
        if len(tpls) > 1:
            mode = f"{mode} | 多模板叠加 Multi-Stack"
        desc = primary.get("description", "")
        if len(tpls) > 1:
            desc += " | 叠加 Overlay: " + " + ".join(t.get("name", "") for t in tpls[1:])
        duration = int(primary.get("duration", 0))
        preview = primary.get("preview", "")

        return (prompt, name_label, mode, desc, duration, preview)

    @classmethod
    def IS_CHANGED(s, template_select, user_customization="", external_prompt="", direct_prompt="", scene_image=None):
        return float("nan")


NODE_CLASS_MAPPINGS = {
    "BSAI_H3_PromptTemplate": BSAI_H3_PromptTemplate,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "BSAI_H3_PromptTemplate": "BSAI H3 Prompt Template (提示词模板)",
}


# ══════════════════════════════════════════════════════════════════════════════
#  Voice input (ASR) — local offline transcription via Vosk (vosk-model-small-cn)
#  The browser records audio → encodes 16kHz mono WAV → POST /bsai_h3/asr →
#  transcribed text is filled back into external_prompt / user_customization.
# ══════════════════════════════════════════════════════════════════════════════
import io
import struct
import threading
import wave

_VOSK_MODEL_DIR = os.path.join(_THIS_DIR, "models", "vosk-model-small-cn-0.22")
_vosk_model = None
_vosk_lock = threading.Lock()
_vosk_import_error = None


def _ensure_vosk_deps():
    """Best-effort auto-install: vosk module + the small CN model.

    This is the runtime fallback for machines where install.py did not run
    (no ComfyUI auto-exec, no network at startup, etc.). Never raises — the
    caller re-checks and reports the real error if it still fails.
    """
    import importlib.util
    import subprocess
    import sys
    try:
        if importlib.util.find_spec("vosk") is None:
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", "--quiet",
                 "--disable-pip-version-check", "vosk"],
                timeout=900,
            )
    except Exception:
        pass
    try:
        if not (os.path.isdir(_VOSK_MODEL_DIR) and os.listdir(_VOSK_MODEL_DIR)):
            script = os.path.join(_THIS_DIR, "scripts", "download_vosk_model.py")
            if os.path.isfile(script):
                subprocess.check_call([sys.executable, script], timeout=1800)
    except Exception:
        pass


def _get_vosk_model():
    global _vosk_model, _vosk_import_error
    if _vosk_model is not None:
        return _vosk_model
    with _vosk_lock:
        if _vosk_model is not None:
            return _vosk_model
        try:
            import vosk
        except Exception as e:
            # Auto-install vosk (best effort) then retry once.
            _ensure_vosk_deps()
            try:
                import vosk
            except Exception as e2:
                _vosk_import_error = (
                    f"vosk not installed and auto-install failed: {e2}. "
                    "Run: pip install vosk / 请运行 pip install vosk"
                )
                raise RuntimeError(_vosk_import_error)
        if not (os.path.isdir(_VOSK_MODEL_DIR) and os.listdir(_VOSK_MODEL_DIR)):
            # Auto-download the CN model (best effort) then re-check.
            _ensure_vosk_deps()
        if not (os.path.isdir(_VOSK_MODEL_DIR) and os.listdir(_VOSK_MODEL_DIR)):
            raise RuntimeError(
                "Vosk Chinese model not found and auto-download failed. Run: "
                "python scripts/download_vosk_model.py (or place "
                "vosk-model-small-cn-0.22 under models/). / 未找到中文模型且自动下载失败，"
                "请运行 scripts/download_vosk_model.py 下载。"
            )
        _vosk_model = vosk.Model(_VOSK_MODEL_DIR)
        return _vosk_model


def _wav_to_16k_mono_int16(data_bytes):
    """Decode a browser-recorded WAV (any rate/channels) → list[int] 16 kHz mono PCM16."""
    import array
    try:
        w = wave.open(io.BytesIO(data_bytes), "rb")
    except Exception as e:
        raise ValueError(f"Not a valid WAV: {e}")
    try:
        n_ch = w.getnchannels()
        rate = w.getframerate()
        sw = w.getsampwidth()
        raw = w.readframes(w.getnframes())
    finally:
        w.close()
    if sw == 2:
        samples = list(array.array("h", raw))
    elif sw == 1:
        samples = [((b - 128) << 8) for b in raw]
    elif sw == 4:
        samples = [x >> 16 for x in array.array("i", raw)]
    else:
        raise ValueError(f"Unsupported sample width {sw}")
    if n_ch > 1:
        samples = [sum(samples[i:i + n_ch]) // n_ch for i in range(0, len(samples), n_ch)]
    if rate == 16000:
        return samples
    # linear resample to 16 kHz
    n_out = int(len(samples) * 16000 / rate)
    out = []
    for i in range(n_out):
        pos = i * rate / 16000.0
        j = int(pos)
        if j + 1 < len(samples):
            frac = pos - j
            out.append(int(samples[j] * (1 - frac) + samples[j + 1] * frac))
        else:
            out.append(samples[-1] if samples else 0)
    return out


def _register_asr_route():
    """Register POST /bsai_h3/asr on the ComfyUI server (guarded import)."""
    try:
        from server import PromptServer
        from aiohttp import web
    except Exception:
        return None
    server = getattr(PromptServer, "instance", None)
    if server is None:
        return None

    @server.routes.post("/bsai_h3/asr")
    async def bsai_h3_asr(request):
        try:
            data = await request.read()
            if not data:
                return web.json_response({"ok": False, "error": "empty audio / 音频为空"})
            samples = _wav_to_16k_mono_int16(data)
            try:
                model = _get_vosk_model()
            except RuntimeError as e:
                return web.json_response({"ok": False, "error": str(e)})
            import vosk
            rec = vosk.KaldiRecognizer(model, 16000)
            pcm = struct.pack("<%dh" % len(samples), *samples)
            rec.AcceptWaveform(pcm)
            text = (json.loads(rec.FinalResult()).get("text") or "").strip()
            return web.json_response({"ok": True, "text": text})
        except Exception as e:
            return web.json_response({"ok": False, "error": str(e)})

    @server.routes.post("/bsai_h3/direct")
    async def bsai_h3_direct(request):
        """Direct mode: expand a short instruction into a full H3 prompt via local LLM."""
        import asyncio
        try:
            body = await request.json()
            text = (body.get("text") or "").strip()
            if not text:
                return web.json_response({"ok": False, "error": "empty instruction / 指令为空"})
        except Exception:
            return web.json_response({"ok": False, "error": "bad request / 请求格式错误"})

        def _run():
            import sys
            # ensure this node's directory is importable at runtime
            if _THIS_DIR not in sys.path:
                sys.path.insert(0, _THIS_DIR)
            from h3_direct_llm import generate_h3_prompt
            return generate_h3_prompt(text)

        try:
            prompt = await asyncio.get_event_loop().run_in_executor(None, _run)
            return web.json_response({"ok": True, "prompt": prompt})
        except Exception as e:
            return web.json_response({"ok": False, "error": str(e)})

    @server.routes.post("/bsai_h3/merge")
    async def bsai_h3_merge(request):
        """Apply a customization INSIDE an existing H3 prompt via the local/API LLM.
        Used by the frontend to live-preview the merged result."""
        import asyncio
        try:
            body = await request.json()
            prompt = (body.get("prompt") or "").strip()
            customization = (body.get("customization") or "").strip()
            if not prompt or not customization:
                return web.json_response({"ok": False, "error": "missing prompt/customization / 缺少提示词或修改"})
        except Exception:
            return web.json_response({"ok": False, "error": "bad request / 请求格式错误"})

        def _run():
            import sys
            if _THIS_DIR not in sys.path:
                sys.path.insert(0, _THIS_DIR)
            from h3_direct_llm import merge_customization
            return merge_customization(prompt, customization)

        try:
            merged, merr = await asyncio.get_event_loop().run_in_executor(None, _run)
            if merr:
                # real failure — never report success with an unchanged prompt
                return web.json_response({"ok": False, "prompt": merged, "error": merr})
            return web.json_response({"ok": True, "prompt": merged})
        except Exception as e:
            return web.json_response({"ok": False, "prompt": prompt, "error": str(e)})

    return server


_register_asr_route()
