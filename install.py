# -*- coding: utf-8 -*-
"""
BSAI MiniMax H3 Prompt — auto-install dependencies & the Vosk ASR model.

ComfyUI executes this file automatically on startup (custom_nodes/<name>/install.py),
so a fresh install on any machine gets:
  1. `vosk`  — offline Chinese ASR for the 🎤 voice button (core, installed synchronously)
  2. `llama-cpp-python` — local LLM for ⚡ Direct Mode (heavy wheel, installed in a
     background thread so it never blocks ComfyUI startup)
  3. vosk-model-small-cn-0.22 (~43 MB) — downloaded under models/ via
     scripts/download_vosk_model.py (multi-mirror)

Everything is best-effort: if a dependency is already present or a step fails,
startup continues normally. The node also re-tries these steps at runtime when
the voice feature is first used (see BSAI_H3_PromptTemplate.py).
"""
import importlib.util
import os
import subprocess
import sys
import threading

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_PY = sys.executable


def _pip(pkgs):
    print(f"[BSAI H3 Prompt] Installing dependencies: {pkgs} ...")
    try:
        subprocess.check_call(
            [_PY, "-m", "pip", "install", "--quiet", "--no-warn-script-location",
             "--disable-pip-version-check"] + pkgs,
            timeout=1800,
        )
        return True
    except Exception as e:  # noqa: BLE001
        print(f"[BSAI H3 Prompt] pip install failed for {pkgs}: {e}")
        return False


def _ensure_vosk():
    """Core voice input: install vosk module + download the small CN model (~43 MB)."""
    if importlib.util.find_spec("vosk") is None:
        _pip(["vosk"])
    model_dir = os.path.join(_THIS_DIR, "models", "vosk-model-small-cn-0.22")
    if not (os.path.isdir(model_dir) and os.listdir(model_dir)):
        print("[BSAI H3 Prompt] Downloading Vosk Chinese model (~43 MB) ...")
        try:
            script = os.path.join(_THIS_DIR, "scripts", "download_vosk_model.py")
            subprocess.check_call([_PY, script], timeout=1800)
        except Exception as e:  # noqa: BLE001
            print(f"[BSAI H3 Prompt] Vosk model download failed: {e}")


def _ensure_llama():
    """Direct Mode LLM runtime (heavy wheel) — background so it never blocks startup."""
    if importlib.util.find_spec("llama_cpp") is None:
        _pip(["llama-cpp-python>=0.3.0"])


def _run():
    try:
        _ensure_vosk()  # synchronous — core feature
    except Exception as e:  # noqa: BLE001
        print(f"[BSAI H3 Prompt] install error: {e}")
    try:
        threading.Thread(target=_ensure_llama, daemon=True).start()
    except Exception as e:  # noqa: BLE001
        print(f"[BSAI H3 Prompt] background dep install error: {e}")


_run()
