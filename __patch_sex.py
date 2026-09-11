#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Patch the medical_anatomy_male and medical_anatomy_female templates:
inject sex-specific content into the prompt body (not just text_fallback_prompt).
"""
import json
from collections import OrderedDict

# Sex-specific content snippets to insert at the top of each prompt (after the existing
# "参考图声明" block).
MALE_SEX_NOTE = (
    "\u3010\u4e25\u683c\u6027\u522b\u58f0\u660e / STRICT SEX DECLARATION\u3011\u672c\u6a21\u677f\u4e3a\u3010\u7537\u6027\u4eba\u4f53\u3011\u4e13\u7528\u3002"
    "\u9ed8\u8ba4\u53c2\u8003\u4eba\u4f53\u53c2\u6570\uff1a25 \u5c81 / 175cm / 70kg / \u4f53\u8102 15% / \u808c\u91cf ~35kg / \u8840\u7ea2\u86cb\u767d 13-17 g/dL / "
    "\u5fc3\u91cd ~300g / \u80be\u91cd ~150g / \u9aa8\u76d6\u5fc3\u5f62 / \u803b\u9aa8\u67b1\u5f27 < 90\u00b0 / \u808c\u91cf\u9ad8 / \u4f53\u6bdb\u591a\u3001"
    "\u80a1\u4e0a\u80a1\u8089\u53d1\u8fbe / \u5634\u5468\u8eab\u4e0a\u80a1\u4e0a / \u8eab\u4f53\u4e0a\u80a1\u53d1\u8fbe\u3002"
    "\u5982\u4f9b\u7ed9\u53c2\u8003\u56fe\u4e3a\u5973\u6027\u4eba\u7269\uff0c\u9700\u5728\u63cf\u8ff0\u4e2d\u660e\u786e\u8bf4\u660e\u4ee5\u4fdd\u8bc1\u4e0d\u8d70\u578b\u3002\n\n"
)

FEMALE_SEX_NOTE = (
    "\u3010\u4e25\u683c\u6027\u522b\u58f0\u660e / STRICT SEX DECLARATION\u3011\u672c\u6a21\u677f\u4e3a\u3010\u5973\u6027\u4eba\u4f53\u3011\u4e13\u7528\u3002"
    "\u9ed8\u8ba4\u53c2\u8003\u4eba\u4f53\u53c2\u6570\uff1a25 \u5c81 / 165cm / 57kg / \u4f53\u8102 25% / \u808c\u91cf ~24kg / \u8840\u7ea2\u86cb\u767d 12-15 g/dL / "
    "\u5fc3\u91cd ~260g / \u80be\u91cd ~135g / \u9aa8\u76d6\u692d\u5706 / \u803b\u9aa8\u67b1\u5f27 > 90\u00b0 / "
    "\u808c\u91cf\u4e0e\u4f53\u8102\u4f4e\u4e8e\u7537\u6027 / \u76ae\u4e0b\u8102\u80aa\u5728\u5c41\u90e8\u3001\u5927\u817d\u3001\u80f8\u90e8\u3001\u80a9\u624b\u80cc\u4fa7\u3001\u5c0f\u817d\u540e\u4fa7\u3001\u80a1\u9762\u53ca\u809b\u80a1\u9762\u4e0a\u809b\u80a1\u3001\u809b\u80a1\u80a1\u808c\u4e0a / "
    "\u4e73\u623f\u4e3a\u4e8c\u6b21\u6027\u5f81\uff0c\u542b\u4e73\u817a\u7ec4\u7ec7 + \u8102\u80aa\u7ec4\u7ec7 + Cooper \u97e7\u5e26 + \u4e73\u7ba1 + \u4e73\u5934\u4e0e\u4e73\u6657\uff1b"
    "\u751f\u6b96\u7cfb\u7edf\u542b\u5375\u5de2/\u8f93\u5375\u7ba1/\u5b50\u5bab/\u9634\u9053/\u5916\u9634\u3002"
    "\u5982\u4f9b\u7ed9\u53c2\u8003\u56fe\u4e3a\u7537\u6027\u4eba\u7269\uff0c\u9700\u5728\u63cf\u8ff0\u4e2d\u660e\u786e\u8bf4\u660e\u4ee5\u4fdd\u8bc1\u4e0d\u8d70\u578b\u3002\n\n"
)

# The existing prompt starts with "[参考图声明 / Reference Map] <Picture 1> = 人物整体..."
# We insert the SEX note BEFORE the "参考图声明" block.
ANCHOR = "\u53c2\u8003\u56fe\u58f0\u660e / Reference Map"

def patch(fp):
    with open(fp, "r", encoding="utf-8") as f:
        d = json.load(f)
    for cat in d["categories"]:
        if cat.get("id") == "xray_scan":
            for sub in cat["subcategories"]:
                if sub["id"] in ("medical_anatomy_male", "medical_anatomy_female"):
                    note = MALE_SEX_NOTE if sub["id"].endswith("_male") else FEMALE_SEX_NOTE
                    for t in sub["templates"]:
                        p = t["prompt"]
                        # Find first occurrence of "[参考图声明 / Reference Map]" and insert note BEFORE it
                        idx = p.find(ANCHOR)
                        if idx < 0:
                            print(f"  WARN: anchor not found in {t['id']} in {fp}")
                            continue
                        # If note already injected, skip
                        if p[:idx].strip().startswith("\u3010\u4e25\u683c\u6027\u522b\u58f0\u660e"):
                            continue
                        new_p = p[:idx] + note + p[idx:]
                        t["prompt"] = new_p
                    print(f"  PATCHED {sub['id']} in {fp}")
    with open(fp, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    print("saved", fp)


if __name__ == "__main__":
    for p in [
        r"C:\BSAI\ComfyUI-BSAI_pro_v39\ComfyUI\custom_nodes\BSAI-MiniMAX-H3-Prompt\templates\prompt_templates.json",
        r"C:\BSAI\ComfyUI-BSAI_pro_v39\ComfyUI\custom_nodes\BSAI-MiniMAX-H3-Prompt\web\templates_data.json",
    ]:
        patch(p)
