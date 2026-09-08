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
    "adjust a shot's description, add a negative constraint) — never merely append the request "
    "at the end. "
    "Keep the exact same overall structure and field blocks of the original prompt "
    "(subject_definitions / summary / retention_analysis / detailed_description / "
    "integrated_multimodal_description with [Shot N] and [X-Xs] timeline / overall_soundscape / "
    "non_diegetic_music), cinematic and vivid. When the request is in Chinese, express it "
    "naturally in English inside the prompt. "
    "FORMAT RULES (mandatory): write every field name exactly as in the original at the start "
    "of its own line — e.g. 'subject_definitions:', 'summary:', 'retention_analysis:', "
    "'detailed_description:', 'overall_soundscape:', 'non_diegetic_music:' — with NO markdown, "
    "NO bold, NO bullet, NO numbering, NO code fences, NO indentation before the field name. "
    "Keep <Subject N> / <Picture N> / <d>…</d> tags intact. "
    "ABSOLUTELY FORBIDDEN: do NOT copy the original prompt verbatim and append the modification "
    "at the end. You MUST REWRITE the ENTIRE prompt and place the modification INSIDE the "
    "relevant field blocks — e.g. a 'no third person' constraint goes into summary, "
    "retention_analysis, and every shot's detailed_description; a transition change rewrites "
    "the affected [Shot N] lines and overall_soundscape. Every field must be re-emitted even if "
    "unchanged. "
    "NEGATIVE / FORBIDDEN CONSTRAINTS (e.g. 'no third person', '严禁出现…', 'only two people', "
    "'no extra characters'): enforce them as ABSOLUTE prohibitions, emphatically — (1) restate "
    "in summary; (2) add a 'Constraint:' line inside retention_analysis for EVERY subject "
    "('exactly one instance of <Subject N> on screen, no duplicate, no clone, no repeated "
    "character'); (3) repeat the prohibition INSIDE EVERY [Shot N] of detailed_description "
    "(e.g. 'Only <Subject 1> and <Subject 2> appear; absolutely no third person, no background "
    "extras, no duplicated people, no reflections that look like extra characters'). Use strong "
    "wording. "
    "CRITICAL: Do NOT include any reasoning, analysis, planning, thinking or commentary. "
    "Output ONLY the final complete rewritten H3 prompt, starting directly with "
    "subject_definitions: (or integrated_multimodal_description: if the original has no "
    "subject_definitions block), with no preamble and no extra text."
)

_llms = {}            # model_path -> llama_cpp.Llama (per-model resident instances)
_llms_lock = threading.Lock()
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


def _pick_merge_model_path():
    """For MERGING, prefer a small prompt-enhancer model that outputs directly
    (no long reasoning preamble), so the rewrite actually gets produced quickly
    and with less VRAM than the 15GB default. Falls back to the normal pick."""
    env = os.environ.get("BSAI_H3_LLM_MODEL", "").strip()
    if env and os.path.isfile(env):
        return env
    sulphur = os.path.join(_COMFY_ROOT, "models", "prompt_enhancer", "sulphur_prompt_enhancer_model-q8_0.gguf")
    if os.path.isfile(sulphur):
        return sulphur
    return _pick_model_path()


def _free_llm_except(keep_path):
    """Release all resident LLM instances except `keep_path` to free VRAM/RAM
    before loading a bigger model (e.g. when the fast merge model fails and we
    fall back to the 15GB default)."""
    global _llms
    with _llms_lock:
        for path in [p for p in _llms if p != keep_path]:
            _llms.pop(path, None)
    try:
        import gc
        gc.collect()
    except Exception:
        pass
    try:
        import torch
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    except Exception:
        pass


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


def _generate_local(user_text, system_prompt, model_path=None):
    global _llm_error
    if model_path is None:
        model_path = _pick_model_path()
    if not model_path:
        raise RuntimeError(
            "No GGUF model found for direct mode. Set env BSAI_H3_LLM_MODEL or place a model "
            "under ComfyUI/models/LLM or prompt_generator. / 未找到本地模型，请设置 BSAI_H3_LLM_MODEL。"
        )
    llm = _llms.get(model_path)
    if llm is None:
        with _llms_lock:
            llm = _llms.get(model_path)
            if llm is None:
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
                llm = Llama(
                    model_path=model_path,
                    n_ctx=8192,
                    n_gpu_layers=gpu_layers,
                    verbose=False,
                )
                _llms[model_path] = llm
    out = llm.create_chat_completion(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_text},
        ],
        max_tokens=4096,
        temperature=0.6,
        top_p=0.9,
    )
    try:
        raw = out["choices"][0]["message"]["content"]
    except Exception:
        raw = ""
    return raw  # cleaned by the caller (H3-strip for generation, merge-strip for merging)


def _generate_api(user_text, cfg, system_prompt):
    import json
    import urllib.request

    body = json.dumps({
        "model": cfg["model"],
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_text},
        ],
        "max_tokens": 4096,
        "temperature": 0.6,
    }).encode("utf-8")
    req = urllib.request.Request(
        cfg["base"] + "/chat/completions",
        data=body,
        headers={"Content-Type": "application/json", "Authorization": "Bearer " + cfg["key"]},
    )
    with urllib.request.urlopen(req, timeout=300) as r:
        data = json.loads(r.read().decode("utf-8"))
    return data["choices"][0]["message"]["content"]  # cleaned by the caller


# H3 field names (the canonical blocks of an H3 prompt). Used by the merge
# output cleaner to locate the start of the real rewritten prompt even when the
# model decorates field names with markdown (**bold**, `code`, "- ", "# ", …).
_H3_FIELDS = (
    "subject_definitions",
    "integrated_multimodal_description",
    "summary",
    "retention_analysis",
    "detailed_description",
    "overall_soundscape",
    "non_diegetic_music",
)
_FIELD_PREFIX = r"[ \t]*[`*#>_\-\.\s]*"


def _field_pos(text, name):
    """Position of the first real occurrence of H3 field `name` (no colon),
    tolerating leading markdown decoration. Returns -1 if absent."""
    m = re.search(r"(?m)^" + _FIELD_PREFIX + re.escape(name) + r"[ \t]*:", text)
    return m.start() if m else -1


def _strip_merge_output(raw):
    """Clean a rewritten-H3-prompt output that may keep leading blocks such as
    subject_definitions / summary / retention_analysis before the three fields.
    Robust to models that emit a reasoning/thinking preamble first, and to field
    names decorated with markdown (**, `, -, #) inside the output."""
    text = (raw or "").strip()
    text = re.sub(r"```[a-zA-Z]*", "", text).strip()
    # Jump to the first genuine H3 field. Prefer the two anchors that appear at
    # the very start of real H3 outputs; fall back to summary: as a safe start.
    m = _field_pos(text, "subject_definitions")
    if m < 0:
        m = _field_pos(text, "integrated_multimodal_description")
    if m < 0:
        m = _field_pos(text, "summary")
    if m >= 0:
        text = text[m:].lstrip()
        # strip any leading markdown decoration from the first field name
        text = re.sub(
            r"^" + _FIELD_PREFIX + r"(subject_definitions|integrated_multimodal_description|summary)[ \t]*:",
            r"\1:",
            text,
        )
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


def _has_h3_field(text):
    """True when the text begins with a canonical H3 field (i.e. it is a usable
    rewritten prompt, not reasoning chatter)."""
    t = (text or "").strip()
    for f in _H3_FIELDS:
        if _field_pos(t, f) == 0:
            return True
    return False


def _is_copy_append(orig, result):
    """True when `result` is the source with stuff only appended — i.e. the model
    copied the template verbatim instead of merging the edit inside its fields.
    Used to reject such outputs so a stronger model / fallback can be tried."""
    if orig is None or result is None:
        return False
    if result == orig:
        return True
    o = [l for l in orig.split("\n") if l.strip()]
    r = [l for l in result.split("\n") if l.strip()]
    if not o:
        return False
    i = 0
    for line in r:
        if i < len(o) and line == o[i]:
            i += 1
    return i >= len(o)


def _is_too_similar(orig, result, min_changed=60):
    """True when `result` barely differs from `orig` -- e.g. the model renamed
    one token without actually merging the user's edit. We require at least
    `min_changed` characters of net change to accept a merge result."""
    if orig is None or result is None:
        return True
    if orig == result:
        return True
    try:
        import difflib
        sm = difflib.SequenceMatcher(None, orig, result, autojunk=False)
        changed = 0
        for tag, i1, i2, j1, j2 in sm.get_opcodes():
            if tag != "equal":
                changed += abs((i2 - i1) - (j2 - j1)) + min(i2 - i1, j2 - j1) * 2
        return changed < min_changed
    except Exception:
        return False


def _is_repetitive_garbage(text, min_repeats=5):
    """Detect repetitive tag-list garbage (e.g. a model that loops on
    'black hair ribbon, black hair scrunchie, ...' hundreds of times).
    Returns True when the output is dominated by short repeated comma-separated
    fragments — a pattern typical of prompt-enhancer models misused for merging."""
    if not text:
        return False
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    if not lines:
        return False
    # Collect all comma-separated fragments across the text
    fragments = []
    for line in lines:
        parts = [p.strip().lower() for p in line.split(",") if p.strip()]
        fragments.extend(parts)
    if len(fragments) < min_repeats * 3:
        return False
    from collections import Counter
    counts = Counter(fragments)
    # Check 1: exact fragment duplication
    most_common = counts.most_common(1)
    if most_common:
        top_word, top_count = most_common[0]
        if top_count >= min_repeats and top_count > len(fragments) * 0.1:
            return True
    # Check 2: common prefix — if >60% of fragments start with the same 2-word
    # prefix, it's a looping pattern (e.g. "black hair ..." repeated)
    unique_frags = list(counts.keys())
    if len(unique_frags) >= 5:
        prefix_counts = Counter()
        for frag in unique_frags:
            words = frag.split()
            if len(words) >= 2:
                prefix = " ".join(words[:2])
                prefix_counts[prefix] += 1
        if prefix_counts:
            top_prefix, top_prefix_count = prefix_counts.most_common(1)[0]
            if top_prefix_count >= 5 and top_prefix_count > len(unique_frags) * 0.5:
                return True
    # Check 3: if >60% of lines are near-identical (Jaccard), it's garbage
    if len(lines) >= min_repeats * 2:
        sample = lines[:50]
        unique = set()
        for l in sample:
            words = frozenset(l.lower().split())
            unique.add(words)
        if len(unique) < len(sample) * 0.4:
            return True
    return False


# Small LRU cache for merged results so re-running the same template+edit is instant
# (the first call still loads the LLM; later identical requests hit the cache).
_merge_cache = {}
_merge_cache_order = []
_MERGE_CACHE_MAX = 64

# Last merge failure reason, so callers/frontend can surface WHY a merge did not
# take effect (e.g. VRAM OOM while an H3 job is running, model missing, etc.).
_last_merge_error = None


def merge_customization(prompt, customization):
    """Rewrite an existing H3 prompt so the user's customization is applied INSIDE
    the text (transition/action/scene changes etc.), not appended at the end.

    Returns a tuple (result, error):
      - (rewritten_prompt, None)      on success (result differs from source)
      - (original_prompt, error_msg)  on failure, with the reason surfaced to the
                                      caller so it is never mistaken for success.
    """
    global _last_merge_error
    p = (prompt or "").strip()
    c = (customization or "").strip()
    if not p or not c:
        _last_merge_error = None
        return p, None
    key = (p, c)
    hit = _merge_cache.get(key)
    if hit is not None:
        _last_merge_error = hit[1]
        return hit
    user_msg = "Existing MiniMax H3 prompt:\n" + p + "\n\nUser modification to apply:\n" + c

    def _clean(raw):
        """Strip reasoning/preamble from the model output and validate that a real
        H3 field survives; returns None when the output is unusable."""
        out = _strip_merge_output(raw or "")
        if out.strip() and not _has_h3_field(out):
            # retry: take from the first canonical field occurrence anywhere
            best = -1
            for f in _H3_FIELDS:
                p = _field_pos(out, f)
                if p >= 0 and (best < 0 or p < best):
                    best = p
            if best >= 0:
                out = out[best:].lstrip()
        if out.strip() and _has_h3_field(out):
            return out
        return None

    result = p
    error = None
    cfg = _api_config()
    if cfg:
        try:
            r = _clean(_generate_api(user_msg, cfg, _H3_MERGE_SYSTEM_PROMPT))
            if r and not _is_copy_append(p, r) and not _is_too_similar(p, r) and not _is_repetitive_garbage(r):
                result = r
            elif r and _is_repetitive_garbage(r):
                error = "API output detected as repetitive garbage / API输出检测到重复垃圾内容"
        except Exception as e:
            error = "API: %s" % e
    if result == p or _is_copy_append(p, result) or _is_too_similar(p, result) or _is_repetitive_garbage(result):
        # Local attempts: try the fast merge model (sulphur) first, then a
        # stronger one (e.g. gemma). Reject outputs that merely copy the template
        # or produce repetitive garbage (e.g. "hair ribbon, hair scrunchie, ..." loops).
        tried = []
        for mp in (_pick_merge_model_path(), _pick_model_path()):
            if not mp or mp in tried:
                continue
            tried.append(mp)
            _free_llm_except(mp)
            try:
                r = _clean(_generate_local(
                    user_msg, _H3_MERGE_SYSTEM_PROMPT, model_path=mp))
                if r and r != p and not _is_copy_append(p, r) and not _is_too_similar(p, r) and not _is_repetitive_garbage(r):
                    result = r
                    error = None
                    break
                elif r and _is_repetitive_garbage(r):
                    error = "Local LLM (%s) output detected as repetitive garbage / 本地模型输出检测到重复垃圾内容" % os.path.basename(mp)
            except Exception as e:
                error = "Local LLM (%s): %s" % (os.path.basename(mp), e)
        if result == p or _is_copy_append(p, result) or _is_too_similar(p, result) or _is_repetitive_garbage(result):
            if error is None:
                error = ("models only copied the template without merging the edit "
                         "(no rewrite produced, change too small) / 模型仅复制模板而未将修改融入字段（改动过小）")
    _last_merge_error = error
    # cache (LRU)
    if key not in _merge_cache:
        if len(_merge_cache) >= _MERGE_CACHE_MAX and _merge_cache_order:
            old = _merge_cache_order.pop(0)
            _merge_cache.pop(old, None)
        _merge_cache[key] = (result, error)
        _merge_cache_order.append(key)
    return result, error


def generate_h3_prompt(user_text):
    """Generate a MiniMax-H3-compliant prompt from a short user instruction (Chinese OK)."""
    text = (user_text or "").strip()
    if not text:
        raise ValueError("empty instruction / 指令为空")
    cfg = _api_config()
    if cfg:
        try:
            return _strip_to_h3(_generate_api(text, cfg, _H3_SYSTEM_PROMPT))
        except Exception as e:
            # fall back to local on API failure
            try:
                return _strip_to_h3(_generate_local(text, _H3_SYSTEM_PROMPT))
            except Exception:
                raise RuntimeError(f"Direct mode API failed ({e}) and local model unavailable.")
    return _strip_to_h3(_generate_local(text, _H3_SYSTEM_PROMPT))
