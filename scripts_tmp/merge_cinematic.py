# -*- coding: utf-8 -*-
"""把电影感提示词分类合并进 templates/prompt_templates.json 与 web/templates_data.json，并校验。"""
import json, os, sys

ROOT = r"C:\BSAI\ComfyUI-BSAI_pro_v39\ComfyUI\custom_nodes\BSAI-MiniMAX-H3-Prompt"
CAT_FILE = os.path.join(ROOT, "scripts_tmp", "cinematic_category.json")
FILES = [
    os.path.join(ROOT, "templates", "prompt_templates.json"),
    os.path.join(ROOT, "web", "templates_data.json"),
]

with open(CAT_FILE, encoding="utf-8") as f:
    category = json.load(f)

existing_sub_ids = set()
for path in FILES:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    # 收集现有分类/子分类 id，检查冲突
    ids = set(c.get("id") for c in data["categories"])
    for c in data["categories"]:
        for s in c.get("subcategories", []):
            if s.get("id"):
                existing_sub_ids.add(s["id"])
    if category["id"] in ids:
        print("CATEGORY ALREADY EXISTS in", path, "-> skip")
        continue
    # 检查新子分类 id 冲突
    for s in category["subcategories"]:
        if s["id"] in existing_sub_ids:
            raise SystemExit("subcategory id conflict: " + s["id"])
    data["categories"].append(category)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print("merged into", os.path.basename(path))

# 校验
for path in FILES:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    n = sum(len(s.get("templates", [])) for c in data["categories"] for s in c.get("subcategories", []))
    cats = len(data["categories"])
    new_cat = [c for c in data["categories"] if c["id"] == "cinematic_prompts"]
    new_n = sum(len(s.get("templates", [])) for s in new_cat[0]["subcategories"]) if new_cat else 0
    print("OK", os.path.basename(path), "| categories:", cats, "| templates:", n, "| new templates:", new_n)
print("ALL VALID")
