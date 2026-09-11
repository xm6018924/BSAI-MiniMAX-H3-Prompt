#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Generate 14 medical-anatomy preview webp images with the BSAI logo overlay.

Each image is 1024x768 (good for UI), dark blue medical background, sex-themed
accent color (blue-cyan for male, magenta-pink for female), title + 5 tags
+ line-art hint of the relevant anatomy, plus the rounded logo in the bottom-right.
"""
import os
import math
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = r"C:\BSAI\ComfyUI-BSAI_pro_v39\ComfyUI\custom_nodes\BSAI-MiniMAX-H3-Prompt"
PREVIEW_DIR = os.path.join(ROOT, "web", "previews")
LOGO_PATH = os.path.join(ROOT, "百声AI-logo-圆形.png")
W, H = 1024, 768
ACCENT = {
    "male":   ((90, 180, 255), (130, 220, 255)),     # blue-cyan
    "female": ((255, 130, 200), (255, 180, 220)),    # pink-magenta
}

# 14 templates to generate
TEMPLATES = [
    # (id_suffix, sex, zh_title, en_title, lines)
    ("full_body_anatomy", "male",
     "医用人体·男性·全身解剖图谱",
     "Male Full-Body Anatomy Atlas",
     ["全身 6 层叠加", "骨骼 206 / 肌肉 ~640", "九大系统 / 神经血管", "五官 / 皮肤", "3D 医学图谱 渲染"]),

    ("skeletal_system", "male",
     "医用人体·男性·全身骨骼系统",
     "Male Skeletal System · 206 Bones",
     ["颅骨 23 / 脊柱 33 / 肋骨 24", "上肢 64 / 下肢 62", "听小骨 6 / 胸骨 1", "关节 ~360", "X 光 + 3D 渲染"]),

    ("muscular_system", "male",
     "医用人体·男性·全身肌肉系统",
     "Male Muscular System · ~640 Muscles",
     ["头颈 ~60 / 躯干 ~150", "上肢 ~80 / 下肢 ~80", "肌量 ~35kg / 体脂 15%", "每肌起止点 / 神经", "表层→深层逐级"]),

    ("organ_systems", "male",
     "医用人体·男性·九大系统内脏",
     "Male Nine Organ Systems",
     ["消化 / 呼吸 / 循环", "泌尿 / 生殖 / 内分泌", "神经 / 免疫（淋巴）", "心 300g / 肾 150g", "9 段 0.9s 分镜"]),

    ("face_features_closeup", "male",
     "医用人体·男性·五官精细解剖",
     "Male Facial Features Anatomy",
     ["喉结明显 (前突 90°)", "声带 20-24mm / ~110Hz", "甲状/环状/杓状软骨", "20+ 表情肌", "面部 3D 解剖"]),

    ("hands_feet_skin", "male",
     "医用人体·男性·手脚皮肤毛囊组织",
     "Male Hands / Feet / Skin / Follicles",
     ["腕 8 / 掌 5 / 指 14", "跗 7 / 跖 5 / 趾 14", "胡须/胸/腹/腿毛", "表皮 4 / 真皮 2 层", "HE 染色切片 5 类"]),

    ("male_specific", "male",
     "医用人体·男性·男性专属解剖",
     "Male-Specific Anatomy",
     ["喉结 / 声带 / 胡须 / 体毛", "睾丸→附睾→输精管→精囊", "前列腺→尿道球腺→阴茎", "睾酮 4-10mg/日", "勃起机制：NO→cGMP"]),

    ("full_body_anatomy", "female",
     "医用人体·女性·全身解剖图谱",
     "Female Full-Body Anatomy Atlas",
     ["全身 6 层叠加", "骨骼 206 / 肌肉 ~640", "九大系统 / 神经血管", "五官 / 皮肤", "3D 医学图谱 渲染"]),

    ("skeletal_system", "female",
     "医用人体·女性·全身骨骼系统",
     "Female Skeletal System · 206 Bones",
     ["颅骨 23 / 脊柱 33 / 肋骨 24", "上肢 64 / 下肢 62", "听小骨 6 / 胸骨 1", "椭圆形骨盆 / 耻骨弓 > 90°", "X 光 + 3D 渲染"]),

    ("muscular_system", "female",
     "医用人体·女性·全身肌肉系统",
     "Female Muscular System · ~640 Muscles",
     ["头颈 ~60 / 躯干 ~150", "上肢 ~80 / 下肢 ~80", "肌量 ~24kg / 体脂 25%", "每肌起止点 / 神经", "盆底肌更易受损"]),

    ("organ_systems", "female",
     "医用人体·女性·九大系统内脏",
     "Female Nine Organ Systems",
     ["消化 / 呼吸 / 循环", "泌尿 / 生殖 / 内分泌", "神经 / 免疫（淋巴）", "心 ~260g / 肾 ~135g", "月经周期 28 天"]),

    ("face_features_closeup", "female",
     "医用人体·女性·五官精细解剖",
     "Female Facial Features Anatomy",
     ["喉结不显 (前突 ~120°)", "声带 15-18mm / ~220Hz", "甲状/环状/杓状软骨", "20+ 表情肌", "面部 3D 解剖"]),

    ("hands_feet_skin", "female",
     "医用人体·女性·手脚皮肤毛囊组织",
     "Female Hands / Feet / Skin / Follicles",
     ["腕 8 / 掌 5 / 指 14", "跗 7 / 跖 5 / 趾 14", "体毛密度低", "妊娠纹 / 黄褐斑", "HE 染色切片 5 类"]),

    ("female_specific", "female",
     "医用人体·女性·女性专属解剖",
     "Female-Specific Anatomy",
     ["卵巢→输卵管→子宫→阴道", "外阴 / 乳腺 (15-20 腺叶)", "月经 / 妊娠 / 绝经", "E2 / P4 / hCG / hPL", "子宫动脉 / 卵巢动脉"]),
]


def find_chinese_font(size):
    """Try several common CJK fonts on Windows."""
    candidates = [
        r"C:\Windows\Fonts\msyh.ttc",     # Microsoft YaHei
        r"C:\Windows\Fonts\msyh.ttf",
        r"C:\Windows\Fonts\simhei.ttf",   # SimHei
        r"C:\Windows\Fonts\simsun.ttc",
        r"C:\Windows\Fonts\Deng.ttf",
        r"C:\Windows\Fonts\NotoSansCJK-Regular.ttc",
        r"C:\Windows\Fonts\NotoSerifCJK-Regular.ttc",
    ]
    for p in candidates:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                continue
    return ImageFont.load_default()


def find_ascii_font(size):
    candidates = [
        r"C:\Windows\Fonts\segoeuib.ttf",   # Segoe UI Bold
        r"C:\Windows\Fonts\seguisb.ttf",
        r"C:\Windows\Fonts\segoeui.ttf",
        r"C:\Windows\Fonts\arialbd.ttf",
        r"C:\Windows\Fonts\arial.ttf",
        r"C:\Windows\Fonts\calibrib.ttf",
        r"C:\Windows\Fonts\calibri.ttf",
    ]
    for p in candidates:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                continue
    return ImageFont.load_default()


def draw_anatomy_hint(draw, accent, sex, kind):
    """Draw a simple line-art silhouette hint for the relevant anatomy."""
    cx, cy = W // 2, H // 2
    if kind in ("full_body_anatomy",):
        # body outline + head circle
        head_r = 70
        head_cy = cy - 220
        draw.ellipse([cx - head_r, head_cy - head_r, cx + head_r, head_cy + head_r],
                     outline=accent, width=4)
        # torso
        draw.line([(cx, head_cy + head_r), (cx, cy + 180)], fill=accent, width=6)
        # arms
        draw.line([(cx, head_cy + head_r + 30), (cx - 130, cy + 60)], fill=accent, width=5)
        draw.line([(cx, head_cy + head_r + 30), (cx + 130, cy + 60)], fill=accent, width=5)
        # legs
        draw.line([(cx, cy + 180), (cx - 60, cy + 280)], fill=accent, width=5)
        draw.line([(cx, cy + 180), (cx + 60, cy + 280)], fill=accent, width=5)
    elif kind in ("skeletal_system",):
        # skull outline + ribcage
        head_r = 75
        head_cy = cy - 220
        draw.ellipse([cx - head_r, head_cy - head_r, cx + head_r, head_cy + head_r],
                     outline=accent, width=4)
        # ribcage
        for i in range(6):
            y = head_cy + head_r + 30 + i * 18
            draw.arc([cx - 80 - i * 2, y - 25, cx + 80 + i * 2, y + 25],
                     start=0, end=180, fill=accent, width=3)
        # spine
        for i in range(20):
            y = head_cy + head_r + 30 + i * 14
            draw.ellipse([cx - 6, y, cx + 6, y + 8], outline=accent, width=2)
        # pelvis
        draw.ellipse([cx - 60, cy + 80, cx + 60, cy + 130], outline=accent, width=3)
    elif kind in ("muscular_system",):
        # muscular body silhouette (shoulders + V-taper)
        head_r = 65
        head_cy = cy - 230
        draw.ellipse([cx - head_r, head_cy - head_r, cx + head_r, head_cy + head_r],
                     outline=accent, width=4)
        # shoulders broad
        draw.polygon([(cx - 150, head_cy + head_r + 30),
                      (cx + 150, head_cy + head_r + 30),
                      (cx + 60, head_cy + head_r + 100),
                      (cx - 60, head_cy + head_r + 100)],
                     outline=accent, width=4)
        # chest line (pecs)
        draw.line([(cx - 50, head_cy + head_r + 60), (cx + 50, head_cy + head_r + 60)],
                  fill=accent, width=3)
        # six-pack hints
        for r in range(2):
            for c in range(3):
                x0 = cx - 40 + c * 30
                y0 = head_cy + head_r + 80 + r * 30
                draw.rectangle([x0, y0, x0 + 25, y0 + 25], outline=accent, width=2)
    elif kind in ("organ_systems",):
        # internal organs icon: heart, lungs, stomach
        # heart shape
        hx, hy = cx - 100, cy - 50
        draw.polygon([(hx, hy + 20), (hx - 30, hy - 10), (hx - 30, hy - 25),
                      (hx, hy - 5), (hx + 30, hy - 25), (hx + 30, hy - 10),
                      (hx, hy + 20)], outline=accent, width=3)
        # lungs (two ovals)
        draw.ellipse([cx - 30 - 30, cy - 60, cx - 30 + 30, cy + 40], outline=accent, width=3)
        draw.ellipse([cx + 30 - 30, cy - 60, cx + 30 + 30, cy + 40], outline=accent, width=3)
        # stomach
        draw.ellipse([cx - 40, cy + 50, cx + 40, cy + 110], outline=accent, width=3)
    elif kind in ("face_features_closeup",):
        # face circle with features
        head_r = 200
        head_cy = cy
        draw.ellipse([cx - head_r, head_cy - head_r, cx + head_r, head_cy + head_r],
                     outline=accent, width=4)
        # eyes
        for dx in (-50, 50):
            draw.ellipse([cx + dx - 18, head_cy - 50, cx + dx + 18, head_cy - 20],
                         outline=accent, width=2)
        # nose
        draw.polygon([(cx, head_cy - 20), (cx - 12, head_cy + 30), (cx + 12, head_cy + 30)],
                     outline=accent, width=2)
        # mouth
        draw.arc([cx - 50, head_cy + 50, cx + 50, head_cy + 90],
                 start=0, end=180, fill=accent, width=3)
        # adam's apple hint (male) or no (female)
        if sex == "male":
            draw.ellipse([cx - 12, head_cy + 100, cx + 12, head_cy + 124],
                         outline=accent, width=2)
    elif kind in ("hands_feet_skin",):
        # hand silhouette + foot
        # hand (palm + 5 fingers)
        palm_x, palm_y = cx - 120, cy
        draw.rounded_rectangle([palm_x, palm_y, palm_x + 100, palm_y + 160],
                               radius=20, outline=accent, width=3)
        for i, dx in enumerate([10, 35, 60, 85, 100]):
            draw.rounded_rectangle([palm_x + dx, palm_y - 50 + (5 if i in (0, 4) else 0),
                                    palm_x + dx + 20, palm_y + 10],
                                   radius=8, outline=accent, width=2)
        # foot
        foot_x, foot_y = cx + 40, cy
        draw.ellipse([foot_x, foot_y, foot_x + 160, foot_y + 80], outline=accent, width=3)
        # 5 toes
        for i in range(5):
            draw.ellipse([foot_x + 20 + i * 25, foot_y - 10, foot_x + 35 + i * 25, foot_y + 5],
                         outline=accent, width=2)
    elif kind in ("male_specific",):
        # male-specific icon: stylized pelvis + reproductive
        draw.ellipse([cx - 100, cy - 60, cx + 100, cy + 60], outline=accent, width=3)
        # arrows down to indicate reproductive
        draw.line([(cx, cy + 60), (cx, cy + 130)], fill=accent, width=3)
        draw.line([(cx - 10, cy + 120), (cx, cy + 130)], fill=accent, width=3)
        draw.line([(cx + 10, cy + 120), (cx, cy + 130)], fill=accent, width=3)
        # small circle for larynx icon (top-left)
        draw.ellipse([cx - 200, cy - 200, cx - 130, cy - 130], outline=accent, width=3)
        # beard/face icon (top-right)
        draw.ellipse([cx + 130, cy - 200, cx + 200, cy - 130], outline=accent, width=3)
    elif kind in ("female_specific",):
        # female-specific icon: uterus shape
        # pear-shaped uterus
        draw.polygon([(cx, cy - 80), (cx - 50, cy - 20), (cx - 50, cy + 40),
                      (cx, cy + 80), (cx + 50, cy + 40), (cx + 50, cy - 20)],
                     outline=accent, width=3)
        # fallopian tubes (curves on each side)
        draw.arc([cx - 110, cy - 60, cx - 30, cy + 20], start=270, end=90, fill=accent, width=3)
        draw.arc([cx + 30, cy - 60, cx + 110, cy + 20], start=90, end=270, fill=accent, width=3)
        # ovaries (small circles at end of tubes)
        draw.ellipse([cx - 130, cy - 30, cx - 110, cy - 10], outline=accent, width=2)
        draw.ellipse([cx + 110, cy - 30, cx + 130, cy - 10], outline=accent, width=2)
        # breasts (top corners)
        for dx in (-150, 150):
            draw.arc([cx + dx - 30, cy - 220, cx + dx + 30, cy - 160],
                     start=0, end=180, fill=accent, width=3)


def make_preview(sex, kind, zh_title, en_title, lines, idx):
    accent, accent2 = ACCENT[sex]
    img = Image.new("RGB", (W, H), (10, 22, 38))   # deep navy
    draw = ImageDraw.Draw(img, "RGBA")

    # Radial-ish gradient by drawing concentric rectangles with alpha
    for i in range(0, 40):
        alpha = max(0, 60 - i * 1.5)
        col = (accent[0] // 4, accent[1] // 4, accent[2] // 4, int(alpha))
        draw.rectangle([i * 6, i * 4, W - i * 6, H - i * 4], outline=col, width=2)

    # Big translucent accent band on the right
    band = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    bd = ImageDraw.Draw(band)
    for i in range(0, 200, 4):
        a = max(0, 100 - i // 2)
        bd.line([(W - i, 0), (W - i, H)], fill=accent + (a,), width=1)
    img = Image.alpha_composite(img.convert("RGBA"), band)
    draw = ImageDraw.Draw(img, "RGBA")

    # Anatomy hint
    draw_anatomy_hint(draw, accent + (220,), sex, kind)

    # Title block (bottom-left)
    title_box_y = H - 280
    draw.rectangle([40, title_box_y, W - 40, H - 40],
                   fill=(8, 18, 32, 230), outline=accent + (255,), width=3)

    # Sex badge
    badge_w = 110
    badge_color = accent
    draw.rounded_rectangle([60, title_box_y + 20, 60 + badge_w, title_box_y + 70],
                            radius=10, fill=badge_color + (255,))
    badge_font = find_chinese_font(28)
    badge_text = "\u7537\u6027" if sex == "male" else "\u5973\u6027"
    draw.text((60 + 22, title_box_y + 28), badge_text, font=badge_font, fill=(10, 22, 38))

    # Chinese title
    zh_font = find_chinese_font(34)
    draw.text((60 + badge_w + 30, title_box_y + 20), zh_title,
              font=zh_font, fill=(240, 245, 252))

    # English title
    en_font = find_ascii_font(22)
    draw.text((60 + badge_w + 30, title_box_y + 60), en_title,
              font=en_font, fill=accent)

    # Bullet lines
    line_font = find_chinese_font(20)
    for i, line in enumerate(lines):
        y = title_box_y + 110 + i * 30
        # dot
        draw.ellipse([68, y + 6, 76, y + 14], fill=accent)
        draw.text((88, y), line, font=line_font, fill=(220, 228, 240))

    # Logo bottom-right
    if os.path.exists(LOGO_PATH):
        logo = Image.open(LOGO_PATH).convert("RGBA")
        logo_size = 96
        logo = logo.resize((logo_size, logo_size), Image.LANCZOS)
        pad = 18
        # Add a subtle white circular halo
        halo = Image.new("RGBA", (logo_size + 16, logo_size + 16), (0, 0, 0, 0))
        hd = ImageDraw.Draw(halo)
        hd.ellipse([0, 0, logo_size + 15, logo_size + 15],
                   fill=(255, 255, 255, 220), outline=accent + (255,), width=3)
        halo = halo.filter(ImageFilter.GaussianBlur(2))
        pos_halo = (W - logo_size - pad - 8, H - logo_size - pad - 8)
        img.paste(halo, pos_halo, halo)
        img.paste(logo, (W - logo_size - pad, H - logo_size - pad), logo)

    # Save as webp
    out_path = os.path.join(PREVIEW_DIR, f"med_{kind}_{sex}.webp")
    img.convert("RGB").save(out_path, "WEBP", quality=88, method=6)
    return out_path


def main():
    os.makedirs(PREVIEW_DIR, exist_ok=True)
    for idx, (kind, sex, zh, en, lines) in enumerate(TEMPLATES, 1):
        out = make_preview(sex, kind, zh, en, lines, idx)
        size = os.path.getsize(out)
        print(f"  {idx:2d}. {os.path.basename(out):50s} {size:>7d} bytes")


if __name__ == "__main__":
    main()
