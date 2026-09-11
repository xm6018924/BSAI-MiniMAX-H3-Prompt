#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json

# Verify the two new specific templates by reading actual content and checking
# the key sex-specific strings ARE present.

# These are characters whose correct codepoints I'll find from the actual file
# to avoid my own Unicode typos.

def find_real(text, candidates):
    """Return the candidate that exists in text."""
    for c in candidates:
        if c in text:
            return c
    return None

for fp in [
    r"C:\BSAI\ComfyUI-BSAI_pro_v39\ComfyUI\custom_nodes\BSAI-MiniMAX-H3-Prompt\templates\prompt_templates.json",
    r"C:\BSAI\ComfyUI-BSAI_pro_v39\ComfyUI\custom_nodes\BSAI-MiniMAX-H3-Prompt\web\templates_data.json",
]:
    print("=" * 60)
    print(fp.split("\\")[-1])
    with open(fp, "r", encoding="utf-8") as f:
        d = json.load(f)
    xray = next(c for c in d["categories"] if c.get("id") == "xray_scan")
    male_sub = next(s for s in xray["subcategories"] if s["id"] == "medical_anatomy_male")
    female_sub = next(s for s in xray["subcategories"] if s["id"] == "medical_anatomy_female")
    male_spec = next((t for t in male_sub["templates"] if t["id"] == "med_male_specific"), None)
    female_spec = next((t for t in female_sub["templates"] if t["id"] == "med_female_specific"), None)

    # Use longer unambiguous substrings that should be in the file
    MALE_LONG = [
        "\u4e25\u683c\u6027\u522b\u58f0\u660e\uff0c\u672c\u6a21\u677f\u4e3a\u3010\u7537\u6027\u4eba\u4f53\u3011\u4e13\u7528",  # STRICT SEX header
        "175cm / 70kg / \u4f53\u8102 15%",
        "\u9ed8\u8ba4 25 \u5c81 / 175cm / 70kg / \u4f53\u8102 15% / \u808c\u91cf ~35kg",
        "\u9aa8\u76d6\u5fc3\u5f62",  # 骨盆心形
        "\u54e8\u7ed3",  # 喉结
        "\u524d\u7a81 90\u00b0",  # 前突 90°
        "20-24mm",  # 声带长
        "110Hz",  # 基频
        "\u808c\u91cf ~35kg",  # 肌量
        "\u4f53\u8102 15%",  # 体脂
        "\u777e\u4e38",  # 睾丸
        "\u9644\u777e",  # 附睾
        "\u8f93\u7cbe\u7ba1",  # 输精管
        "\u7cbe\u56ca",  # 精囊
        "\u524d\u5217\u817a",  # 前列腺
        "\u5c3f\u9053\u7403\u817a",  # 尿道球腺
        "\u9634\u830e",  # 阴茎
        "\u4e24\u4e2a\u9634\u830e\u6d77\u7ef5\u4f53",  # 2 阴茎海绵体
        "\u80e1\u987b",  # 胡须
        "\u80f8\u6bdb",  # 胸毛
        "\u4ea7\u7537\u6db2",  # 产睾酮
        "4-10mg/\u65e5",  # 产睾酮量
    ]
    FEMALE_LONG = [
        "\u4e25\u683c\u6027\u522b\u58f0\u660e\uff0c\u672c\u6a21\u677f\u4e3a\u3010\u5973\u6027\u4eba\u4f53\u3011\u4e13\u7528",
        "165cm / 57kg / \u4f53\u8102 25%",
        "\u9ed8\u8ba4 25 \u5c81 / 165cm / 57kg / \u4f53\u8102 25% / \u808c\u91cf ~24kg",
        "\u9aa8\u76d6\u692d\u5706",  # 骨盆椭圆
        "\u54e8\u7ed3\u4e0d\u663e",  # 喉结不显
        "15-18mm",  # 声带长
        "220Hz",  # 基频
        "\u808c\u91cf ~24kg",  # 肌量
        "\u4f53\u8102 25%",  # 体脂
        "\u5375\u5de2",  # 卵巢
        "\u8f93\u5375\u7ba1",  # 输卵管
        "\u5b50\u5bab",  # 子宫
        "\u9634\u9053",  # 阴道
        "\u5916\u9634",  # 外阴
        "\u9634\u7c2a",  # 阴阜
        "\u9634\u8482",  # 阴蒂
        "\u6708\u7ecf",  # 月经
        "\u5b55\u671f",  # 孕期
        "\u4e73\u817a",  # 乳腺
        "Cooper \u97e7\u5e26",  # Cooper 韧带
        "\u8499\u54e5\u9a6c\u5229\u817a",  # 蒙哥马利腺
        "\u4e73\u7ba1",  # 乳管
        "\u5b50\u5bab\u52a8\u8109",  # 子宫动脉
        "\u5375\u5de2\u52a8\u8109",  # 卵巢动脉
        "\u5fc3\u91cd ~260g",  # 心重
    ]

    all_ok = True
    if male_spec:
        p = male_spec["prompt"]
        print("  male_specific prompt:", len(p), "chars")
        miss = [n for n in MALE_LONG if n not in p]
        if miss:
            all_ok = False
            for n in miss:
                print("    MALE MISS:", repr(n)[:50])
    if female_spec:
        p = female_spec["prompt"]
        print("  female_specific prompt:", len(p), "chars")
        miss = [n for n in FEMALE_LONG if n not in p]
        if miss:
            all_ok = False
            for n in miss:
                print("    FEMALE MISS:", repr(n)[:50])
    if all_ok:
        print("  PASS: all sex-specific content present in both templates.")
    print()

# Now verify count
for fp in [
    r"C:\BSAI\ComfyUI-BSAI_pro_v39\ComfyUI\custom_nodes\BSAI-MiniMAX-H3-Prompt\templates\prompt_templates.json",
    r"C:\BSAI\ComfyUI-BSAI_pro_v39\ComfyUI\custom_nodes\BSAI-MiniMAX-H3-Prompt\web\templates_data.json",
]:
    with open(fp, "r", encoding="utf-8") as f:
        d = json.load(f)
    xray = next(c for c in d["categories"] if c.get("id") == "xray_scan")
    male = next(s for s in xray["subcategories"] if s["id"] == "medical_anatomy_male")
    female = next(s for s in xray["subcategories"] if s["id"] == "medical_anatomy_female")
    print(f"{fp.split(chr(92))[-1]}: male={len(male['templates'])} female={len(female['templates'])}")
