#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Generate 2 wardrobe preview images (single + multi) via matrix image gen."""
import json
import os
import subprocess
import time
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = Path(r"C:\BSAI\ComfyUI-BSAI_pro_v39\ComfyUI\custom_nodes\BSAI-MiniMAX-H3-Prompt")
PREVIEW_DIR = ROOT / "web" / "previews"
LOGO_PATH = ROOT / "百声AI-logo-圆形.png"
TMP_DIR = ROOT / "_gen_tmp"
TMP_DIR.mkdir(exist_ok=True)

TEMPLATES = [
    ("magic_mediator_wardrobe_single", (200, 130, 255), "Single-outfit Magic Wardrobe",
     "Single-outfit transformation via holographic device. Cool medical-tech style. "
     "A young woman in casual outfit sits on a bed; an operator's hand brings a glowing "
     "holographic wristband into the frame; the device lights up; sparkling particles "
     "sweep over her; her casual outfit transforms into an elegant evening gown; she "
     "looks down in surprise; the device leaves the frame; she stands and spins with "
     "joy. 4:3 aspect ratio, deep navy background, no live person photograph, no "
     "graphic content, no facial expression changes other than surprise and joy."),

    ("magic_mediator_wardrobe_multi", (255, 130, 200), "Multi-outfit Magic Wardrobe",
     "Sequential multi-outfit transformation via holographic device. Cool medical-tech "
     "style. A young woman in casual outfit sits in a soft-lit room; an operator's hand "
     "brings a glowing holographic wristband into the frame; the device lights up three "
     "separate times; each time sparkling particles sweep over her; her outfit changes "
     "from casual to business to cocktail to evening gown (three sequential "
     "transformations); each time she reacts with surprise; the device leaves between "
     "transformations; final spin to show the evening gown. 4:3 aspect ratio, deep navy "
     "background, no live person photograph, no graphic content, no facial expression "
     "changes other than surprise and joy."),
]


def run_call(tool, args_path):
    cmd = f'mcode-tools connector call "{tool}" --args-file "{args_path}"'
    out = subprocess.run(cmd, capture_output=True, text=True, check=False, shell=True)
    if out.returncode != 0:
        return {"code": out.returncode, "stderr": out.stderr, "stdout": out.stdout}
    try:
        return json.loads(out.stdout)
    except Exception:
        return {"raw": out.stdout, "stderr": out.stderr}


def get_asset_url(node_id):
    cmd = f'mcode-tools get-asset-url "{node_id}"'
    out = subprocess.run(cmd, capture_output=True, text=True, check=False, shell=True)
    if out.returncode != 0:
        return None
    try:
        return json.loads(out.stdout).get("download_url")
    except Exception:
        return None


def find_chinese_font(size):
    for p in [r"C:\Windows\Fonts\msyh.ttc", r"C:\Windows\Fonts\simhei.ttf",
              r"C:\Windows\Fonts\simsun.ttc"]:
        if Path(p).exists():
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                continue
    return ImageFont.load_default()


def crop_watermark_and_compose(raw_path, out_webp, accent, title_zh):
    try:
        im = Image.open(raw_path).convert("RGB")
    except Exception as e:
        print(f"    open failed: {e}")
        return False
    W, H = im.size
    crop_w = int(W * 0.28)
    crop_h = int(H * 0.10)
    cx0 = W - crop_w
    cy0 = H - crop_h
    cropped_region = im.crop((cx0, cy0, W, H))
    blurred = cropped_region.filter(ImageFilter.GaussianBlur(radius=20))
    im.paste(blurred, (cx0, cy0))

    if LOGO_PATH.exists():
        logo = Image.open(LOGO_PATH).convert("RGBA")
        logo_size = 96
        logo = logo.resize((logo_size, logo_size), Image.LANCZOS)
        pad = 18
        halo = Image.new("RGBA", (logo_size + 16, logo_size + 16), (0, 0, 0, 0))
        hd = ImageDraw.Draw(halo)
        hd.ellipse([0, 0, logo_size + 15, logo_size + 15],
                   fill=(255, 255, 255, 220), outline=accent + (255,), width=3)
        halo = halo.filter(ImageFilter.GaussianBlur(2))
        im_rgba = im.convert("RGBA")
        im_rgba.paste(halo, (W - logo_size - pad - 8, H - logo_size - pad - 8), halo)
        im_rgba.paste(logo, (W - logo_size - pad, H - logo_size - pad), logo)
        im = im_rgba.convert("RGB")

    # Title strip
    try:
        font = find_chinese_font(26)
        im_rgba = im.convert("RGBA")
        d = ImageDraw.Draw(im_rgba)
        strip_h = 56
        d.rectangle([0, H - strip_h, W, H], fill=(8, 18, 32, 230))
        d.rectangle([20, H - strip_h + 12, 130, H - 12], fill=accent + (255,))
        d.text((42, H - strip_h + 18), "\u533b\u7528", font=font, fill=(10, 22, 38))
        d.text((150, H - strip_h + 16), title_zh, font=font, fill=(240, 245, 252))
        im = im_rgba.convert("RGB")
    except Exception as e:
        print(f"    title strip failed: {e}")

    im.save(out_webp, "WEBP", quality=88, method=6)
    return True


def main():
    for idx, (kind, accent, _, prompt) in enumerate(TEMPLATES, 1):
        out_webp = PREVIEW_DIR / f"{kind}.webp"
        title_zh = "\u533b\u7528\u4eba\u4f53\u00b7\u533b\u7528\u6362\u88c5\u00b7\u5e7b\u672f\u9b54\u6cd5\u89e6\u53d1"
        args_path = TMP_DIR / f"_args_wardrobe_{idx}.json"
        payload = {
            "requests": [{
                "prompt": prompt,
                "aspect_ratio": "4:3",
                "resolution": "1K",
                "output_file": kind,
            }]
        }
        with open(args_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False)
        print(f"  [{idx}] generating {kind}...")
        result = run_call("connector__matrix__generate_image", args_path)
        success = result.get("success_items") or []
        if not success:
            print(f"    FAILED: {result.get('failed_items') or result.get('message')}")
            time.sleep(2.0)
            continue
        node_id = success[0]["node_id"]
        download_url = get_asset_url(str(node_id))
        if not download_url:
            print(f"    no download_url for {node_id}")
            time.sleep(2.0)
            continue
        raw_path = TMP_DIR / f"raw_wardrobe_{idx}.jpg"
        ps_script = (
            f"$ProgressPreference = 'SilentlyContinue'; "
            f"Invoke-WebRequest -Uri '{download_url}' -OutFile '{raw_path}' -UseBasicParsing -ErrorAction Stop"
        )
        dl = subprocess.run(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", ps_script],
            capture_output=True, text=True, check=False
        )
        if not raw_path.exists() or raw_path.stat().st_size < 1000:
            print(f"    download failed: {raw_path}")
            time.sleep(2.0)
            continue
        ok = crop_watermark_and_compose(raw_path, str(out_webp), accent, title_zh)
        if ok:
            print(f"    -> saved {out_webp.name} ({out_webp.stat().st_size} bytes)")
        time.sleep(2.0)


if __name__ == "__main__":
    main()
