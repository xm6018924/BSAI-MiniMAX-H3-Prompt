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

# Only the original vendor source is used. Third-party mirrors were removed:
# downloading model archives from untrusted mirrors (then extracting them) is a
# supply-chain risk flagged in review. alphacephei.com is the official Vosk
# distribution site.
SOURCES = [
    "https://alphacephei.com/vosk/models/vosk-model-small-cn-0.22.zip",
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
                # Zip-slip guard: reject any member escaping the target directory.
                base = os.path.realpath(os.path.dirname(_MODEL_DIR))
                for info in z.infolist():
                    name = info.filename.replace("\\", "/")
                    if name.startswith("/") or ".." in name.split("/"):
                        raise RuntimeError(f"Unsafe zip member rejected: {info.filename}")
                    target = os.path.realpath(os.path.join(base, name))
                    if os.path.commonpath([base, target]) != base:
                        raise RuntimeError(f"Zip member escapes target dir: {info.filename}")
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
