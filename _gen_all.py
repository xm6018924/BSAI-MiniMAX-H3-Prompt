#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Batch-generate 14 medical anatomy preview images via the matrix image
generation tool, then download each one, crop the MiniMax AI watermark from
the bottom-right, and finally composite the BSAI logo on top.

Each request is a single image; we run them sequentially because the matrix
service returns "all 1 failed" when we batch in one call (per smoke test) and
the individual tool path is reliable.
"""
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = Path(r"C:\BSAI\ComfyUI-BSAI_pro_v39\ComfyUI\custom_nodes\BSAI-MiniMAX-H3-Prompt")
PREVIEW_DIR = ROOT / "web" / "previews"
LOGO_PATH = ROOT / "百声AI-logo-圆形.png"
TMP_DIR = ROOT / "_gen_tmp"
TMP_DIR.mkdir(exist_ok=True)

# Each entry: (suffix, sex, prompt, accent)
# accent is a (R,G,B) tuple used for the title strip we'll add in post.
TEMPLATES = [
    # ===== MALE =====
    ("full_body_anatomy", "male",
     "Professional medical textbook illustration of the human male body, anterior view, "
     "photorealistic 3D rendering, neutral standing pose, full body silhouette. Bilingual "
     "labels in English and Simplified Chinese for major anatomical systems. Cool medical "
     "lighting 5500K, deep navy background. Clean educational style, no live person "
     "photograph, no graphic content, no facial expression, no narrative. Crisp ultra "
     "high definition, 4:3 aspect ratio, medical journal plate style.", (90, 180, 255)),

    ("skeletal_system", "male",
     "Professional medical textbook illustration of the human male skeletal system, "
     "anterior view, photorealistic 3D rendering, all 206 bones clearly visible including "
     "skull, cervical spine, thoracic spine, lumbar spine, sacrum, coccyx, ribcage, sternum, "
     "clavicles, scapulae, humerus, radius, ulna, carpals, metacarpals, phalanges, pelvis, "
     "femur, patella, tibia, fibula, tarsals, metatarsals, phalanges. Thin labelled lines "
     "pointing from each major bone to small bilingual English and Simplified Chinese "
     "labels. Cool medical lighting 5500K, deep navy background, ivory white labels. "
     "Clean, educational, no graphic content, no live person, 4:3 aspect ratio, medical "
     "journal plate style.", (90, 180, 255)),

    ("muscular_system", "male",
     "Professional medical textbook illustration of the human male muscular system, "
     "anterior view, photorealistic 3D rendering, the muscular body shown with broad "
     "shoulders and tapered waist, all major muscle groups visible including deltoids, "
     "pectorals, biceps, triceps, abdominal rectus, obliques, quadriceps, and calf muscles. "
     "Thin labelled lines pointing from each major muscle to small bilingual English and "
     "Simplified Chinese labels. Cool medical lighting 5500K, deep navy background, ivory "
     "white labels. Clean, educational, no graphic content, no live person, 4:3 aspect "
     "ratio, medical journal plate style.", (90, 180, 255)),

    ("organ_systems", "male",
     "Professional medical textbook illustration of the human internal organs, anterior "
     "view with cutaway, photorealistic 3D rendering, the heart centrally, two lungs, "
     "the liver, stomach, intestines, kidneys, bladder visible through a transparent body. "
     "Thin labelled lines pointing from each major organ to small bilingual English and "
     "Simplified Chinese labels. Cool medical lighting 5500K, deep navy background, ivory "
     "white labels. Clean, educational, no graphic content, no live person, no blood, "
     "4:3 aspect ratio, medical journal plate style.", (90, 180, 255)),

    ("face_features_closeup", "male",
     "Professional medical textbook illustration of the human male facial anatomy, close-up "
     "anterior view, photorealistic 3D rendering of the face with anatomical overlay showing "
     "the underlying skull, the eye, the nose, the mouth, the jaw, and the prominent "
     "thyroid cartilage at the throat. Bilingual labels in English and Simplified Chinese. "
     "Cool medical lighting 5500K, deep navy background, ivory white labels. Clean, "
     "educational, no live person photograph, no graphic content, 4:3 aspect ratio, medical "
     "journal plate style.", (90, 180, 255)),

    ("hands_feet_skin", "male",
     "Professional medical textbook illustration of a human hand and a human foot shown "
     "side by side at large scale, photorealistic 3D rendering, the skin semi-transparent "
     "to reveal the underlying carpal and tarsal bones, the metacarpals and metatarsals, "
     "and the phalanges. Bilingual labels in English and Simplified Chinese for each "
     "bone group. Cool medical lighting 5500K, deep navy background, ivory white labels. "
     "Clean, educational, no graphic content, no live person, 4:3 aspect ratio, medical "
     "journal plate style.", (90, 180, 255)),

    ("male_specific", "male",
     "Professional medical textbook illustration of male-specific anatomy, photorealistic "
     "3D medical rendering, showing the male endocrine glands, the male pelvic structure, "
     "and the male larynx with the prominent Adam's apple. Bilingual labels in English and "
     "Simplified Chinese for the key anatomical structures. Cool medical lighting 5500K, "
     "deep navy background, ivory white labels. Clean, educational, clinical reference "
     "style, 4:3 aspect ratio, medical journal plate style.", (90, 180, 255)),

    # ===== FEMALE =====
    ("full_body_anatomy", "female",
     "Professional medical textbook illustration of the human female body, anterior view, "
     "photorealistic 3D rendering, neutral standing pose, full body silhouette. Bilingual "
     "labels in English and Simplified Chinese for major anatomical systems. Cool medical "
     "lighting 5500K, deep navy background. Clean educational style, no live person "
     "photograph, no graphic content, no facial expression, no narrative. Crisp ultra "
     "high definition, 4:3 aspect ratio, medical journal plate style.", (255, 130, 200)),

    ("skeletal_system", "female",
     "Professional medical textbook illustration of the human female skeletal system, "
     "anterior view, photorealistic 3D rendering, all 206 bones clearly visible with a "
     "wider oval-shaped pelvic structure. Bilingual labels in English and Simplified "
     "Chinese for the major bones. Cool medical lighting 5500K, deep navy background, "
     "ivory white labels. Clean, educational, no graphic content, no live person, 4:3 "
     "aspect ratio, medical journal plate style.", (255, 130, 200)),

    ("muscular_system", "female",
     "Professional medical textbook illustration of the human female muscular system, "
     "anterior view, photorealistic 3D rendering, the body with a more gracile bone "
     "structure and visible muscle groups. Bilingual labels in English and Simplified "
     "Chinese for the major muscle groups. Cool medical lighting 5500K, deep navy "
     "background, ivory white labels. Clean, educational, no graphic content, no live "
     "person, 4:3 aspect ratio, medical journal plate style.", (255, 130, 200)),

    ("organ_systems", "female",
     "Professional medical textbook illustration of the human female internal organs, "
     "anterior view with cutaway, photorealistic 3D rendering, the heart, two lungs, "
     "liver, stomach, intestines, kidneys, and bladder visible through a transparent "
     "body. Bilingual labels in English and Simplified Chinese. Cool medical lighting "
     "5500K, deep navy background, ivory white labels. Clean, educational, no graphic "
     "content, no live person, no blood, 4:3 aspect ratio, medical journal plate style.",
     (255, 130, 200)),

    ("face_features_closeup", "female",
     "Professional medical textbook illustration of the human female facial anatomy, "
     "close-up anterior view, photorealistic 3D rendering of the face with anatomical "
     "overlay showing the underlying skull, the eye, the nose, the mouth, the jaw, "
     "and a small larynx without a prominent Adam's apple. Bilingual labels in English "
     "and Simplified Chinese. Cool medical lighting 5500K, deep navy background, ivory "
     "white labels. Clean, educational, no live person photograph, no graphic content, "
     "4:3 aspect ratio, medical journal plate style.", (255, 130, 200)),

    ("hands_feet_skin", "female",
     "Professional medical textbook illustration of a human hand and a human foot shown "
     "side by side at large scale, photorealistic 3D rendering, the skin semi-transparent "
     "to reveal the underlying carpal and tarsal bones, the metacarpals and metatarsals, "
     "and the phalanges. Bilingual labels in English and Simplified Chinese for each "
     "bone group. Cool medical lighting 5500K, deep navy background, ivory white labels. "
     "Clean, educational, no graphic content, no live person, 4:3 aspect ratio, medical "
     "journal plate style.", (255, 130, 200)),

    ("female_specific", "female",
     "Professional medical textbook illustration of female-specific anatomy, "
     "photorealistic 3D medical rendering, showing the female endocrine glands, the "
     "female pelvic structure, and the female larynx. Bilingual labels in English and "
     "Simplified Chinese for the key anatomical structures. Cool medical lighting 5500K, "
     "deep navy background, ivory white labels. Clean, educational, clinical reference "
     "style, 4:3 aspect ratio, medical journal plate style.", (255, 130, 200)),
]


def run_call(tool, args_path):
    """Run a connector call synchronously and return parsed JSON.

    Uses shell=True because mcode-tools is a .cmd shim and Python's
    subprocess on Windows does not always find it via PATH without shell.
    """
    # Use cmd.exe to locate mcode-tools via PATH
    cmd = f'mcode-tools connector call "{tool}" --args-file "{args_path}"'
    out = subprocess.run(
        cmd,
        capture_output=True, text=True, check=False,
        shell=True,
    )
    if out.returncode != 0:
        return {"code": out.returncode, "stderr": out.stderr, "stdout": out.stdout}
    try:
        return json.loads(out.stdout)
    except Exception:
        return {"raw": out.stdout, "stderr": out.stderr}


def get_asset_url(node_id):
    """Get the short-lived download URL for a generated asset."""
    cmd = f'mcode-tools get-asset-url "{node_id}"'
    out = subprocess.run(cmd, capture_output=True, text=True, check=False, shell=True)
    if out.returncode != 0:
        return None
    try:
        return json.loads(out.stdout).get("download_url")
    except Exception:
        return None


def generate_one(idx, kind, sex, prompt, accent, out_webp):
    args_path = TMP_DIR / f"_args_{idx:02d}.json"
    payload = {
        "requests": [{
            "prompt": prompt,
            "aspect_ratio": "4:3",
            "resolution": "1K",
            "output_file": f"med_{kind}_{sex}",
        }]
    }
    with open(args_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False)
    result = run_call("connector__matrix__generate_image", args_path)
    success = result.get("success_items") or []
    if not success:
        print(f"  [{idx:02d}] {kind}_{sex} FAILED: {result.get('failed_items') or result.get('message')}")
        return False
    node_id = success[0]["node_id"]
    file_name = success[0]["file_name"]
    print(f"  [{idx:02d}] {kind}_{sex} OK node_id={node_id} file_name={file_name}")

    # Get the download URL
    download_url = get_asset_url(str(node_id))
    if not download_url:
        print(f"    get-asset-url failed for {node_id}")
        return False

    # Download the file (use PowerShell Invoke-WebRequest on Windows)
    raw_path = TMP_DIR / f"raw_{idx:02d}.{file_name.split('.')[-1]}"
    ps_script = (
        f"$ProgressPreference = 'SilentlyContinue'; "
        f"try {{ "
        f"  Invoke-WebRequest -Uri '{download_url}' -OutFile '{raw_path}' -UseBasicParsing -ErrorAction Stop; "
        f"  exit 0 "
        f"}} catch {{ "
        f"  exit 1 "
        f"}}"
    )
    dl = subprocess.run(
        ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", ps_script],
        capture_output=True, text=True, check=False
    )
    if not raw_path.exists() or raw_path.stat().st_size < 1000:
        print(f"    download failed: {raw_path} size={raw_path.stat().st_size if raw_path.exists() else 'missing'}")
        return False
    return crop_watermark_and_compose(raw_path, out_webp, accent, sex, kind)


def crop_watermark_and_compose(raw_path, out_webp, accent, sex, kind):
    """Crop the MiniMax AI watermark from the bottom-right, then add a small
    title strip and the BSAI logo."""
    try:
        im = Image.open(raw_path).convert("RGB")
    except Exception as e:
        print(f"    open failed: {e}")
        return False
    W, H = im.size

    # Find the watermark: "由 MiniMax AI 生成" appears as white text on a dark
    # band. We crop the bottom ~7% on the right to remove the watermark.
    # The actual watermark in the test image spanned about 24% width x 5% height
    # in the lower-right. We crop a bit more generously to be safe.
    crop_w = int(W * 0.28)
    crop_h = int(H * 0.10)
    cx0 = W - crop_w
    cy0 = H - crop_h
    # Fill the cropped area with a smooth blur of its surroundings to hide the cut
    cropped_region = im.crop((cx0, cy0, W, H))
    blurred = cropped_region.filter(ImageFilter.GaussianBlur(radius=20))
    im.paste(blurred, (cx0, cy0))
    # Add a subtle dark vignette in that corner so it doesn't stand out
    overlay = Image.new("RGBA", im.size, (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    for i in range(20):
        a = int(20 * (1 - i / 20))
        od.rectangle([W - 30 - i, H - 30 - i, W, H], outline=(10, 22, 38, a), width=1)
    im = Image.alpha_composite(im.convert("RGBA"), overlay).convert("RGB")

    # Add the BSAI logo in the bottom-right
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

    # Add a sex-themed accent strip + title at the bottom
    try:
        from PIL import ImageFont
        # Try CJK font
        font_paths = [
            r"C:\Windows\Fonts\msyh.ttc",
            r"C:\Windows\Fonts\simhei.ttf",
            r"C:\Windows\Fonts\simsun.ttc",
        ]
        title_font = None
        for fp in font_paths:
            if Path(fp).exists():
                try:
                    title_font = ImageFont.truetype(fp, 28)
                    break
                except Exception:
                    pass
        if title_font is None:
            title_font = ImageFont.load_default()
        im_rgba = im.convert("RGBA")
        d = ImageDraw.Draw(im_rgba)
        strip_h = 56
        d.rectangle([0, H - strip_h, W, H], fill=(8, 18, 32, 230))
        sex_zh = "男性" if sex == "male" else "女性"
        kind_zh = {
            "full_body_anatomy":     "全身解剖图谱",
            "skeletal_system":       "全身骨骼系统",
            "muscular_system":       "全身肌肉系统",
            "organ_systems":         "九大系统内脏",
            "face_features_closeup": "五官精细解剖",
            "hands_feet_skin":       "手脚皮肤毛囊组织",
            "male_specific":         "男性专属解剖",
            "female_specific":       "女性专属解剖",
        }.get(kind, kind)
        title = f"\u533b\u7528\u4eba\u4f53\u00b7{sex_zh}\u00b7{kind_zh}"
        d.rectangle([20, H - strip_h + 12, 130, H - 12], fill=accent + (255,))
        d.text((42, H - strip_h + 18), sex_zh, font=title_font, fill=(10, 22, 38))
        d.text((150, H - strip_h + 16), title, font=title_font, fill=(240, 245, 252))
        im = im_rgba.convert("RGB")
    except Exception as e:
        print(f"    title strip failed: {e}")

    # Save as webp
    im.save(out_webp, "WEBP", quality=88, method=6)
    return True


def main():
    print("=== batch generating 14 medical anatomy previews ===")
    ok_count = 0
    fail_count = 0
    for idx, (kind, sex, prompt, accent) in enumerate(TEMPLATES, 1):
        out_webp = PREVIEW_DIR / f"med_{kind}_{sex}.webp"
        ok = generate_one(idx, kind, sex, prompt, accent, str(out_webp))
        if ok:
            ok_count += 1
            print(f"    -> saved {out_webp.name} ({out_webp.stat().st_size} bytes)")
        else:
            fail_count += 1
        time.sleep(1.0)
    print()
    print(f"=== done: {ok_count} ok, {fail_count} failed ===")


if __name__ == "__main__":
    main()
