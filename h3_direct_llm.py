# -*- coding: utf-8 -*-
"""
Direct-mode LLM for the BSAI H3 Prompt Template node.
Turns a short user instruction (e.g. voice text) into a full MiniMax H3
three-field prompt (integrated_multimodal_description / overall_soundscape /
non_diegetic_music) following the official H3 prompt SKILL rules.

Engine priority:
  1. OpenAI-compatible remote API  (env BSAI_H3_LLM_API_KEY [+ BSAI_H3_LLM_API_BASE, BSAI_H3_LLM_MODEL])
  2. Local llama.cpp GGUF model    (env BSAI_H3_LLM_MODEL path, else auto-detect below)

The model is loaded lazily and kept resident (GPU offload).
"""
import os
import re
import threading

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
# node dir = <ComfyUI>/custom_nodes/BSAI-MiniMAX-H3-Prompt  →  ComfyUI root is 2 levels up
_COMFY_ROOT = os.path.normpath(os.path.join(_THIS_DIR, "..", ".."))

# Auto-detect candidate GGUFs (ordered by preference)
_CANDIDATES = [
    os.path.join(_COMFY_ROOT, "models", "LLM", "Gemma4-GGUF", "gemma-4-26B-A4B-it-heretic-ara.Q4_K_M.gguf"),
    os.path.join(_COMFY_ROOT, "models", "prompt_generator", "Qwen3.5-9B-Uncensored-HauhauCS-Aggressive-Q8_0.gguf"),
    os.path.join(_COMFY_ROOT, "models", "prompt_enhancer", "sulphur_prompt_enhancer_model-q8_0.gguf"),
    os.path.join(_COMFY_ROOT, "models", "LLM", "Huihui-Qwen3.5-27B-abliterated.Q4_K_M.gguf"),
]

_H3_SYSTEM_PROMPT = (
    "You are a professional video prompt engineer following the MiniMax H3 prompt SKILL. "
    "Strictly output ONLY the following three fields in English, with no explanations, "
    "no preamble, no markdown code fences and no extra text:\n"
    "integrated_multimodal_description: describe the shot-by-shot scene with [Shot N] labels, "
    "timeline [X-Xs] per shot, subject action and camera movement, cinematic and vivid.\n"
    "overall_soundscape: the ambient sound design.\n"
    "non_diegetic_music: the background music mood (or N/A if none).\n"
    "When the user gives a subject/action description in Chinese, translate it to English "
    "in the output."
)

_H3_MERGE_SYSTEM_PROMPT = (
    "You are a professional video prompt engineer following the MiniMax H3 prompt SKILL. "
    "You are given an EXISTING MiniMax H3 prompt and a user's modification request. "
    "REWRITE the H3 prompt so the modification is ACTUALLY IMPLEMENTED INSIDE the text "
    "(e.g. replace a hard match-cut transition with a natural walk-through, change an action, "
    "adjust a shot's description) — never merely append the request at the end. "
    "Keep the exact same overall structure and field blocks of the original prompt "
    "(subject_definitions / summary / retention_analysis / detailed_description / "
    "integrated_multimodal_description with [Shot N] and [X-Xs] timeline / overall_soundscape / "
    "non_diegetic_music), cinematic and vivid. When the request is in Chinese, express it "
    "naturally in English inside the prompt. "
    "Output ONLY the final complete rewritten H3 prompt, with no explanations, no preamble, "
    "no markdown code fences and no extra text."
)

_llm_lock = threading.Lock()
_llm = None
_llm_error = None


def _auto_install_llama():
    """Background, best-effort install of llama-cpp-python (heavy wheel)."""
    def _do():
        try:
            import subprocess
            import sys
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", "--quiet",
                 "--disable-pip-version-check", "llama-cpp-python>=0.3.0"],
                timeout=1800,
            )
        except Exception:
            pass
    try:
        threading.Thread(target=_do, daemon=True).start()
    except Exception:
        pass


def _pick_model_path():
    env = os.environ.get("BSAI_H3_LLM_MODEL", "").strip()
    if env and os.path.isfile(env):
        return env
    for p in _CANDIDATES:
        if os.path.isfile(p):
            return p
    return None


def _api_config():
    key = os.environ.get("BSAI_H3_LLM_API_KEY", "").strip()
    if not key:
        return None
    return {
        "key": key,
        "base": os.environ.get("BSAI_H3_LLM_API_BASE", "https://api.openai.com/v1").strip().rstrip("/"),
        "model": os.environ.get("BSAI_H3_LLM_MODEL", "gpt-4o-mini").strip(),
    }


def _strip_to_h3(raw):
    """Return a clean three-field H3 block from the model output."""
    text = (raw or "").strip()
    # drop any code fences
    text = re.sub(r"```[a-zA-Z]*", "", text)
    # drop anything before the first H3 field
    idx = text.find("integrated_multimodal_description:")
    if idx >= 0:
        text = text[idx:].strip()
    # cut trailing self-reflection / reasoning noise after the three fields
    stop = re.search(
        r"\n\s*(\*Wait|\*Usually|Here is|The final|Note:|Hope this|Hope you|\*\*)?\s*(\*wait|usually|wait,|note:|let's check|that's|ensure)", text, re.I
    )
    if stop:
        text = text[: stop.start()].strip()
    # if we found the music field, also cut everything after its line
    m = text.find("non_diegetic_music:")
    if m >= 0:
        after = text[m:]
        nl = after.find("\n")
        if nl >= 0:
            # only cut if the remaining lines look like chatter, not part of music value
            text = text[: m + nl].rstrip()
    return text or (raw or "").strip()


def _generate_local(user_text, system_prompt):
    global _llm, _llm_error
    model_path = _pick_model_path()
    if not model_path:
        raise RuntimeError(
            "No GGUF model found for direct mode. Set env BSAI_H3_LLM_MODEL or place a model "
            "under ComfyUI/models/LLM or prompt_generator. / 未找到本地模型，请设置 BSAI_H3_LLM_MODEL。"
        )
    if _llm is None:
        with _llm_lock:
            if _llm is None:
                try:
                    from llama_cpp import Llama
                except Exception as e:
                    _llm_error = f"llama_cpp not installed: {e}"
                    _auto_install_llama()  # background install; tell the user to retry
                    raise RuntimeError(
                        "llama_cpp not installed — auto-install started in background, "
                        "please retry in a moment. / llama_cpp 未安装，已自动开始后台安装，"
                        "请稍候重试。也可手动执行：pip install llama-cpp-python"
                    )
                gpu_layers = int(os.environ.get("BSAI_H3_LLM_GPU_LAYERS", "-1"))
                _llm = Llama(
                    model_path=model_path,
                    n_ctx=8192,
                    n_gpu_layers=gpu_layers,
                    verbose=False,
                )
    out = _llm.create_chat_completion(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_text},
        ],
        max_tokens=2000,
        temperature=0.6,
        top_p=0.9,
    )
    try:
        raw = out["choices"][0]["message"]["content"]
    except Exception:
        raw = ""
    return _strip_to_h3(raw)


def _generate_api(user_text, cfg, system_prompt):
    import json
    import urllib.request

    body = json.dumps({
        "model": cfg["model"],
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_text},
        ],
        "max_tokens": 2000,
        "temperature": 0.6,
    }).encode("utf-8")
    req = urllib.request.Request(
        cfg["base"] + "/chat/completions",
        data=body,
        headers={"Content-Type": "application/json", "Authorization": "Bearer " + cfg["key"]},
    )
    with urllib.request.urlopen(req, timeout=300) as r:
        data = json.loads(r.read().decode("utf-8"))
    raw = data["choices"][0]["message"]["content"]
    return _strip_to_h3(raw)


def _strip_merge_output(raw):
    """Clean a rewritten-H3-prompt output that may keep leading blocks such as
    subject_definitions / summary / retention_analysis before the three fields."""
    text = (raw or "").strip()
    text = re.sub(r"```[a-zA-Z]*", "", text).strip()
    # Drop any preamble before the first meaningful field
    idx = text.find("subject_definitions:")
    if idx < 0:
        idx = text.find("integrated_multimodal_description:")
    if idx >= 0:
        text = text[idx:].strip()
    # Cut trailing out-of-band chatter after the last H3 field — but keep the
    # full value block of non_diegetic_music (it may wrap onto following lines).
    m = text.rfind("non_diegetic_music:")
    if m >= 0:
        tail = text[m:]
        s = re.search(
            r"\n\s*(\*Wait|\*Usually|Here is|The final|Note:|Hope this|Hope you|Let me know|That should|Please let me know|I hope)",
            tail,
        )
        if s:
            text = text[: m + s.start()].rstrip()
    return text or (raw or "").strip()


def merge_customization(prompt, customization):
    """Rewrite an existing H3 prompt so the user's customization is applied INSIDE
    the text (transition/action/scene changes etc.), not appended at the end.
    Returns the rewritten prompt, or the original on any failure (caller decides)."""
    p = (prompt or "").strip()
    c = (customization or "").strip()
    if not p or not c:
        return p
    user_msg = "Existing MiniMax H3 prompt:\n" + p + "\n\nUser modification to apply:\n" + c

    def _clean(raw):
        return _strip_merge_output(raw)

    cfg = _api_config()
    if cfg:
        try:
            return _clean(_generate_api(user_msg, cfg, _H3_MERGE_SYSTEM_PROMPT))
        except Exception:
            pass
    try:
        return _clean(_generate_local(user_msg, _H3_MERGE_SYSTEM_PROMPT))
    except Exception:
        return p


def generate_h3_prompt(user_text):
    """Generate a MiniMax-H3-compliant prompt from a short user instruction (Chinese OK)."""
    text = (user_text or "").strip()
    if not text:
        raise ValueError("empty instruction / 指令为空")
    cfg = _api_config()
    if cfg:
        try:
            return _generate_api(text, cfg, _H3_SYSTEM_PROMPT)
        except Exception as e:
            # fall back to local on API failure
            try:
                return _generate_local(text, _H3_SYSTEM_PROMPT)
            except Exception:
                raise RuntimeError(f"Direct mode API failed ({e}) and local model unavailable.")
    return _generate_local(text, _H3_SYSTEM_PROMPT)
