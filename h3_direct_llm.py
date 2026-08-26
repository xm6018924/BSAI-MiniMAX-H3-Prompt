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

_llm_lock = threading.Lock()
_llm = None
_llm_error = None


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


def _generate_local(user_text):
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
                    raise RuntimeError(_llm_error)
                gpu_layers = int(os.environ.get("BSAI_H3_LLM_GPU_LAYERS", "-1"))
                _llm = Llama(
                    model_path=model_path,
                    n_ctx=8192,
                    n_gpu_layers=gpu_layers,
                    verbose=False,
                )
    out = _llm.create_chat_completion(
        messages=[
            {"role": "system", "content": _H3_SYSTEM_PROMPT},
            {"role": "user", "content": user_text},
        ],
        max_tokens=1500,
        temperature=0.6,
        top_p=0.9,
    )
    try:
        raw = out["choices"][0]["message"]["content"]
    except Exception:
        raw = ""
    return _strip_to_h3(raw)


def _generate_api(user_text, cfg):
    import json
    import urllib.request

    body = json.dumps({
        "model": cfg["model"],
        "messages": [
            {"role": "system", "content": _H3_SYSTEM_PROMPT},
            {"role": "user", "content": user_text},
        ],
        "max_tokens": 1500,
        "temperature": 0.6,
    }).encode("utf-8")
    req = urllib.request.Request(
        cfg["base"] + "/chat/completions",
        data=body,
        headers={"Content-Type": "application/json", "Authorization": "Bearer " + cfg["key"]},
    )
    with urllib.request.urlopen(req, timeout=180) as r:
        data = json.loads(r.read().decode("utf-8"))
    raw = data["choices"][0]["message"]["content"]
    return _strip_to_h3(raw)


def generate_h3_prompt(user_text):
    """Generate a MiniMax-H3-compliant prompt from a short user instruction (Chinese OK)."""
    text = (user_text or "").strip()
    if not text:
        raise ValueError("empty instruction / 指令为空")
    cfg = _api_config()
    if cfg:
        try:
            return _generate_api(text, cfg)
        except Exception as e:
            # fall back to local on API failure
            try:
                return _generate_local(text)
            except Exception:
                raise RuntimeError(f"Direct mode API failed ({e}) and local model unavailable.")
    return _generate_local(text)
