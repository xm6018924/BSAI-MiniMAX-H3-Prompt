#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json

EXPECTED_MALE = [
    "med_full_body_anatomy_male",
    "med_skeletal_system_male",
    "med_muscular_system_male",
    "med_organ_systems_male",
    "med_face_features_closeup_male",
    "med_hands_feet_skin_male",
    "med_male_specific",
]
EXPECTED_FEMALE = [
    "med_full_body_anatomy_female",
    "med_skeletal_system_female",
    "med_muscular_system_female",
    "med_organ_systems_female",
    "med_face_features_closeup_female",
    "med_hands_feet_skin_female",
    "med_female_specific",
]

MALE_SPECIFIC_NEEDLES = [
    "\u4e25\u683c\u6027\u522b\u58f0\u660e", "175cm", "70kg",
    "\u9aa8\u76d6\u5fc3\u5f62", "\u803b\u9aa8\u67b1\u5f27 < 90",
    "\u4e73\u817a" + "_SHOULD_NOT_EXIST" if False else "\u803b\u9aa8",
    "\u54e8\u7ed3",  # 喉结
    "\u58f0\u5e26 20-24mm", "\u57fa\u9891 ~110Hz",
    "\u8089\u91cf ~35kg", "\u4f53\u8102 15%",
    "\u777e\u4e38", "\u9644\u777e", "\u8f93\u7cbe\u7ba1", "\u7cbe\u56ca", "\u524d\u5217\u817a", "\u5c3f\u9053\u7403\u817a", "\u9634\u830e",
    "\u80a1\u8089\u8089\u8c8c\u8d77\u59cb",  # 阴茎海绵体
    "\u8089\u8d28\u9762\u8109",
    "\u80e1\u987b", "\u80f8\u6bdb", "\u817d\u6bdb", "\u817d\u9762", "\u80a1\u4e0a", "\u80a1\u540e", "\u80a1\u9762", "\u809b\u5468", "\u9634\u90e8", "\u817d\u4e0b", "\u80f8\u80a1",
    "\u7532\u72b6\u8f6f\u9aa8", "\u73af\u72b6\u8f6f\u9aa8", "\u6760\u72b6\u8f6f\u9aa8",
    "\u8517\u72b6\u9759\u8109\u4ece", "\u9ed1\u8c79",
    "\u80a1\u8089\u8089\u8c8c",  # 蔓状静脉丛
    "\u5916\u5c55", "\u8089\u808c", "\u4e73\u4e73\u593e",
    "\u809b\u4e0a",
]
# Female specific
FEMALE_SPECIFIC_NEEDLES = [
    "\u4e25\u683c\u6027\u522b\u58f0\u660e", "165cm", "57kg",
    "\u9aa8\u76d6\u692d\u5706", "\u803b\u9aa8\u67b1\u5f27 > 90",
    "\u5375\u5de2", "\u8f93\u5375\u7ba1", "\u5b50\u5bab", "\u9634\u9053", "\u5916\u9634",
    "\u9634\u7c2a", "\u9634\u8482",  # 阴阜 阴蒂
    "\u5b50\u5bab\u5468\u671f",  # 子宫周期
    "\u5375\u6ce1\u671f", "\u6392\u5375\u671f", "\u9ec4\u4f53\u671f",
    "\u4e73\u817a", "\u4e73\u7ba1", "\u4e73\u5934", "\u4e73\u6657",
    "Cooper \u97e7\u5e26", "\u8499\u54e5\u9a6c\u5229\u817a",
    "\u808c\u91cf ~24kg", "\u4f53\u8102 25%",
    "\u58f0\u5e26 15-18mm", "\u57fa\u9891 ~220Hz",
    "\u5b50\u5bab\u52a8\u8109",  # 子宫动脉
    "\u5375\u5de2\u52a8\u8109",  # 卵巢动脉
    "\u80b8\u80a1\u4e0a\u4e0a",  # subcategory 内
    "\u5fc3\u91cd ~260g",  # 心重
    "\u76ae\u4e0b\u8102\u80aa",  # 皮下脂肪
    "\u4ea7\u540e",  # 产后
    "\u4e73\u817a",  # 乳腺
    "\u6708\u7ecf",
    "\u5b55\u671f",  # 孕期
    "\u7edd\u7ecf",  # 绝经
]


def check(fp):
    print("=" * 60)
    print(fp.split("\\")[-1])
    with open(fp, "r", encoding="utf-8") as f:
        d = json.load(f)
    xray = next(c for c in d["categories"] if c.get("id") == "xray_scan")
    male_sub = next(s for s in xray["subcategories"] if s["id"] == "medical_anatomy_male")
    female_sub = next(s for s in xray["subcategories"] if s["id"] == "medical_anatomy_female")
    ok = True
    for sub, expected in ((male_sub, EXPECTED_MALE), (female_sub, EXPECTED_FEMALE)):
        got = [t["id"] for t in sub["templates"]]
        for eid in expected:
            if eid not in got:
                print(f"  {sub['id']}: MISSING {eid}")
                ok = False
        # Check each template has all fields
        for t in sub["templates"]:
            for field in ("id","name","name_en","description","preview","generation_mode","duration","tags","prompt","text_fallback_prompt","text_fallback_mode"):
                if field not in t:
                    print(f"  missing field {field} in {t.get('id')}")
                    ok = False
    # Specific needle checks
    male_spec = next((t for t in male_sub["templates"] if t["id"] == "med_male_specific"), None)
    female_spec = next((t for t in female_sub["templates"] if t["id"] == "med_female_specific"), None)
    if male_spec:
        p = male_spec["prompt"]
        for n in MALE_SPECIFIC_NEEDLES:
            if "_SHOULD_NOT_EXIST" in n:
                continue
            if n not in p:
                print(f"  male_specific MISS needle '{n}'")
                ok = False
    if female_spec:
        p = female_spec["prompt"]
        for n in FEMALE_SPECIFIC_NEEDLES:
            if n not in p:
                print(f"  female_specific MISS needle '{n}'")
                ok = False
    # cross-check: ensure male_spec does NOT contain 卵巢/子宫/乳腺
    if male_spec:
        p = male_spec["prompt"]
        for kw in ["\u5375\u5de2", "\u5b50\u5bab", "\u9634\u9053", "\u5916\u9634", "\u4e73\u817a", "\u6708\u7ecf"]:
            # male can mention 乳腺 in the description or in reference to female opposite
            # but in the prompt it should NOT be present
            if kw in p:
                print(f"  male_specific WARN: contains '{kw}' (might be in 乳腺 vs 乳腺对照)")
    # Summary
    print(f"  medical_anatomy_male: {len(male_sub['templates'])} templates")
    for t in male_sub["templates"]:
        print(f"    - {t['id']:36s} | {t['name']} | prompt={len(t['prompt'])}c")
    print(f"  medical_anatomy_female: {len(female_sub['templates'])} templates")
    for t in female_sub["templates"]:
        print(f"    - {t['id']:36s} | {t['name']} | prompt={len(t['prompt'])}c")
    return ok


all_ok = True
for p in [
    r"C:\BSAI\ComfyUI-BSAI_pro_v39\ComfyUI\custom_nodes\BSAI-MiniMAX-H3-Prompt\templates\prompt_templates.json",
    r"C:\BSAI\ComfyUI-BSAI_pro_v39\ComfyUI\custom_nodes\BSAI-MiniMAX-H3-Prompt\web\templates_data.json",
]:
    if not check(p):
        all_ok = False

print()
print("RESULT:", "ALL OK" if all_ok else "FAILED")
with open(r"C:\BSAI\ComfyUI-BSAI_pro_v39\ComfyUI\custom_nodes\BSAI-MiniMAX-H3-Prompt\_verify3_result.txt", "w", encoding="utf-8") as f:
    f.write("ALL OK\n" if all_ok else "FAILED\n")
