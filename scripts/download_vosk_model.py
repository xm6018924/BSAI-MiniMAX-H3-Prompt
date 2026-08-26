# -*- coding: utf-8 -*-
"""
Download the Vosk small Chinese model (vosk-model-small-cn-0.22, ~43 MB) for the
BSAI H3 Prompt Template node's voice-input (ASR) feature.

Usage:
    python scripts/download_vosk_model.py

The model is stored under models/vosk-model-small-cn-0.22/ (git-ignored).
"""
import os
import sys
import zipfile
import urllib.request

_HERE = os.path.dirname(os.path.abspath(__file__))
_NODE_ROOT = os.path.dirname(_HERE)
_MODEL_DIR = os.path.join(_NODE_ROOT, "models", "vosk-model-small-cn-0.22")
_ZIP_PATH = os.path.join(_NODE_ROOT, "models", "_vosk_model_small_cn.zip")

SOURCES = [
    "https://alphacephei.com/vosk/models/vosk-model-small-cn-0.22.zip",
    "https://raw.githubusercontent.com/kercre123/vosk-models/main/vosk-model-small-cn-0.22.zip",
    "https://gitcode.com/open-source-toolkit/efc8a/raw/main/vosk-model-small-cn-0.22.zip",
]


def _download(url, dest, timeout=120):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        with open(dest, "wb") as f:
            while True:
                chunk = r.read(1 << 20)
                if not chunk:
                    break
                f.write(chunk)


def main():
    if os.path.isdir(_MODEL_DIR) and os.listdir(_MODEL_DIR):
        print("Model already present:", _MODEL_DIR)
        return 0
    os.makedirs(os.path.dirname(_ZIP_PATH), exist_ok=True)
    if os.path.exists(_ZIP_PATH):
        os.remove(_ZIP_PATH)
    for url in SOURCES:
        try:
            print("Downloading from", url)
            _download(url, _ZIP_PATH, timeout=120)
            if os.path.getsize(_ZIP_PATH) < 1_000_000:
                print("  suspiciously small, skipping")
                continue
            with zipfile.ZipFile(_ZIP_PATH) as z:
                z.extractall(os.path.dirname(_MODEL_DIR))
            os.remove(_ZIP_PATH)
            print("OK ->", _MODEL_DIR)
            return 0
        except Exception as e:
            print("  failed:", e)
            continue
    print("All mirrors failed. Manually download vosk-model-small-cn-0.22.zip and extract into models/.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
