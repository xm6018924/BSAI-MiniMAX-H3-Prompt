#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json

MALE_IDS = [b + "_male" for b in [
    "med_full_body_anatomy", "med_skeletal_system", "med_muscular_system",
    "med_organ_systems", "med_face_features_closeup", "med_hands_feet_skin"
]]
FEMALE_IDS = [b + "_female" for b in [
    "med_full_body_anatomy", "med_skeletal_system", "med_muscular_system",
    "med_organ_systems", "med_face_features_closeup", "med_hands_feet_skin"
]]

# Use longer unambiguous substrings
MALE_NEEDLES = {
    "med_full_body_anatomy_male": [
        "\u4e25\u683c\u6027\u522b\u58f0\u660e", "175cm / 70kg", "\u4f53\u8102 15%",
    ],
    "med_skeletal_system_male": [
        "\u4e25\u683c\u6027\u522b\u58f0\u660e", "175cm / 70kg", "\u4f53\u8102 15%",
    ],
    "med_muscular_system_male": [
        "\u4e25\u683c\u6027\u522b\u58f0\u660e", "175cm / 70kg", "\u4f53\u8102 15%",
    ],
    "med_organ_systems_male": [
        "\u4e25\u683c\u6027\u522b\u58f0\u660e", "175cm / 70kg", "\u4f53\u8102 15%",
        "\u777e\u4e38", "\u524d\u5217\u817a", "\u5c3f\u9053\u7403\u817a", "\u9634\u830e",
    ],
    "med_face_features_closeup_male": [
        "\u4e25\u683c\u6027\u522b\u58f0\u660e", "175cm / 70kg", "\u4f53\u8102 15%",
    ],
    "med_hands_feet_skin_male": [
        "\u4e25\u683c\u6027\u522b\u58f0\u660e", "175cm / 70kg", "\u4f53\u8102 15%",
    ],
}
FEMALE_NEEDLES = {
    "med_full_body_anatomy_female": [
        "\u4e25\u683c\u6027\u522b\u58f0\u660e", "165cm / 57kg", "\u4f53\u8102 25%",
    ],
    "med_skeletal_system_female": [
        "\u4e25\u683c\u6027\u522b\u58f0\u660e", "165cm / 57kg", "\u4f53\u8102 25%",
    ],
    "med_muscular_system_female": [
        "\u4e25\u683c\u6027\u522b\u58f0\u660e", "165cm / 57kg", "\u4f53\u8102 25%",
    ],
    "med_organ_systems_female": [
        "\u4e25\u683c\u6027\u522b\u58f0\u660e", "165cm / 57kg", "\u4f53\u8102 25%",
        "\u5375\u5de2", "\u8f93\u5375\u7ba1", "\u5b50\u5bab", "\u9634\u9053", "\u4e73\u817a",
    ],
    "med_face_features_closeup_female": [
        "\u4e25\u683c\u6027\u522b\u58f0\u660e", "165cm / 57kg", "\u4f53\u8102 25%",
    ],
    "med_hands_feet_skin_female": [
        "\u4e25\u683c\u6027\u522b\u58f0\u660e", "165cm / 57kg", "\u4f53\u8102 25%",
    ],
}

all_ok = True
for p in [
    r"C:\BSAI\ComfyUI-BSAI_pro_v39\ComfyUI\custom_nodes\BSAI-MiniMAX-H3-Prompt\templates\prompt_templates.json",
    r"C:\BSAI\ComfyUI-BSAI_pro_v39\ComfyUI\custom_nodes\BSAI-MiniMAX-H3-Prompt\web\templates_data.json",
]:
    print("=" * 60)
    print(p.split("\\")[-1])
    with open(p, "r", encoding="utf-8") as f:
        d = json.load(f)
    xray = next(c for c in d["categories"] if c.get("id") == "xray_scan")
    sub_ids = [s["id"] for s in xray["subcategories"]]
    if "medical_anatomy" in sub_ids:
        print("  FAIL: old medical_anatomy still present")
        all_ok = False
    for sid in ("medical_anatomy_male", "medical_anatomy_female"):
        if sid not in sub_ids:
            print(f"  FAIL: missing {sid}")
            all_ok = False
    male_sub = next((s for s in xray["subcategories"] if s["id"] == "medical_anatomy_male"), None)
    female_sub = next((s for s in xray["subcategories"] if s["id"] == "medical_anatomy_female"), None)
    if not male_sub or not female_sub:
        continue

    for sub, expected_ids, needles in (
        (male_sub, MALE_IDS, MALE_NEEDLES),
        (female_sub, FEMALE_IDS, FEMALE_NEEDLES),
    ):
        got_ids = [t["id"] for t in sub["templates"]]
        for eid in expected_ids:
            if eid not in got_ids:
                print(f"  {sub['id']}: MISSING {eid}")
                all_ok = False
        for t in sub["templates"]:
            for field in ("id","name","name_en","description","preview","generation_mode","duration","tags","prompt","text_fallback_prompt","text_fallback_mode"):
                if field not in t:
                    print(f"  missing field {field} in {t.get('id')}")
                    all_ok = False
        for t in sub["templates"]:
            if t["id"] in needles:
                for n in needles[t["id"]]:
                    if n not in t["prompt"]:
                        print(f"  {sub['id']} / {t['id']}: MISS needle '{n}'")
                        all_ok = False

    # Cross-check: ensure opposite-sex content is NOT in the wrong template
    # Male organ_systems should NOT contain "卵巢" (ovary, female-only)
    male_organ = next((t for t in male_sub["templates"] if t["id"] == "med_organ_systems_male"), None)
    female_organ = next((t for t in female_sub["templates"] if t["id"] == "med_organ_systems_female"), None)
    if male_organ and female_organ:
        female_only = ["\u5375\u5de2", "\u4e73\u817a", "\u9634\u9053", "\u5916\u9634"]
        male_only = ["\u777e\u4e38", "\u8f93\u7cbe\u7ba1", "\u5c3f\u9053\u7403\u817a", "\u9634\u830e"]
        for kw in female_only:
            if kw in male_organ["prompt"]:
                print(f"  WARN: male_organ contains female-only '{kw}'")
        for kw in male_only:
            if kw in female_organ["prompt"]:
                print(f"  WARN: female_organ contains male-only '{kw}'")

    # Print summary
    for t in male_sub["templates"]:
        print(f"  M - {t['id']:38s} | {t['name']} | tags={len(t['tags'])} | prompt={len(t['prompt'])}c | fb={len(t['text_fallback_prompt'])}c")
    for t in female_sub["templates"]:
        print(f"  F - {t['id']:38s} | {t['name']} | tags={len(t['tags'])} | prompt={len(t['prompt'])}c | fb={len(t['text_fallback_prompt'])}c")

print()
print("RESULT:", "ALL OK" if all_ok else "FAILED")
with open(r"C:\BSAI\ComfyUI-BSAI_pro_v39\ComfyUI\custom_nodes\BSAI-MiniMAX-H3-Prompt\_verify2_result.txt", "w", encoding="utf-8") as f:
    f.write("ALL OK\n" if all_ok else "FAILED\n")
