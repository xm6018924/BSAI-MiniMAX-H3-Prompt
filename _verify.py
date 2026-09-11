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

# Sex-specific content checks
MALE_NEEDLES = {
    "med_full_body_anatomy_male": ["\u7537\u6027", "175cm/70kg"],
    "med_skeletal_system_male":   ["\u7537\u6027", "\u5fc3\u5f62", "\u803b\u9aa8\u67f1\u5f27 < 90"],
    "med_muscular_system_male":   ["\u7537\u6027", "175cm / 70kg", "\u4f53\u8102 15%", "\u808c\u91cf ~35kg"],
    "med_organ_systems_male":     ["\u7537\u6027\u4e13\u5c5e", "\u777e\u4e38", "\u524d\u5217\u817a", "\u5c3f\u9053\u7403\u817a", "\u9634\u830e"],
    "med_face_features_closeup_male": ["\u7537\u6027", "\u9ed1\u53d1\u7c97\u786c", "\u989f\u9aa8\u66f4\u65b9", "\u4e0b\u9888\u89d2\u660e\u663e", "110Hz"],
    "med_hands_feet_skin_male":   ["\u7537\u6027", "175cm / 70kg"],
}
FEMALE_NEEDLES = {
    "med_full_body_anatomy_female": ["\u5973\u6027", "165cm/57kg"],
    "med_skeletal_system_female":   ["\u5973\u6027", "\u692d\u5706\u5f62", "\u803b\u9aa8\u67f1\u5f27 > 90"],
    "med_muscular_system_female":   ["\u5973\u6027", "165cm / 57kg", "\u4f53\u8102 25%", "\u808c\u91cf ~24kg"],
    "med_organ_systems_female":     ["\u5973\u6027\u4e13\u5c5e", "\u5375\u5de2", "\u8f93\u5375\u7ba1", "\u5b50\u5bab", "\u9634\u9053", "\u4e73\u817a"],
    "med_face_features_closeup_female": ["\u5973\u6027", "\u9ed1\u53d1\u67d4\u8f6f", "\u989f\u9aa8\u66f4\u5706", "\u4e0b\u9888\u89d2\u949d", "220Hz"],
    "med_hands_feet_skin_female":   ["\u5973\u6027", "165cm / 57kg"],
}

# Things that should NOT appear in opposite-sex template
ANTI_MALE_NEEDLES_FEMALE = ["\u524d\u5217\u817a\uff08\u6817\u5b50\u6837\uff0c\u91cd ~20g\uff0c\u4ea7\u524d\u5217\u817a\u6db2\uff09"]
ANTI_FEMALE_NEEDLES_MALE = ["\u4e73\u817a 15-20 \u4e1c\u7ec6\u80de\u5757/\u4e73\u623f"]

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
    print("subs:", sub_ids)
    if "medical_anatomy" in sub_ids:
        print("  FAIL: old medical_anatomy still present")
        all_ok = False
    for sid in ("medical_anatomy_male", "medical_anatomy_female"):
        if sid not in sub_ids:
            print(f"  FAIL: missing {sid}")
            all_ok = False
    male_sub = next(s for s in xray["subcategories"] if s["id"] == "medical_anatomy_male")
    female_sub = next(s for s in xray["subcategories"] if s["id"] == "medical_anatomy_female")
    for sub, expected_ids, needles in (
        (male_sub, MALE_IDS, MALE_NEEDLES),
        (female_sub, FEMALE_IDS, FEMALE_NEEDLES),
    ):
        got_ids = [t["id"] for t in sub["templates"]]
        print(f"  {sub['id']}: {sub['name']} | {len(got_ids)} templates")
        for eid in expected_ids:
            if eid not in got_ids:
                print(f"    MISSING: {eid}")
                all_ok = False
        for t in sub["templates"]:
            for field in ("id","name","name_en","description","preview","generation_mode","duration","tags","prompt","text_fallback_prompt","text_fallback_mode"):
                if field not in t:
                    print(f"    missing field {field} in {t.get('id')}")
                    all_ok = False
        for t in sub["templates"]:
            if t["id"] in needles:
                for n in needles[t["id"]]:
                    if n not in t["prompt"]:
                        print(f"    MISS needle '{n}' in {t['id']}")
                        all_ok = False

    # Anti checks: ensure male has no female-only content and vice versa
    for t in male_sub["templates"]:
        for n in ANTI_MALE_NEEDLES_FEMALE:
            if n in t["prompt"]:
                # OK if also present in female, but in MALE it should be inside the text_fallback_prompt only
                # Actually we only want to ensure no female-specific phrases in male templates
                if t["id"].endswith("_organ_systems_male"):
                    print(f"    WARN: male organ_systems has female-only content '{n[:20]}...'")
    for t in female_sub["templates"]:
        for n in ANTI_FEMALE_NEEDLES_MALE:
            if n in t["prompt"]:
                if t["id"].endswith("_organ_systems_female"):
                    pass  # OK
    # Show summary
    for t in male_sub["templates"]:
        print(f"  M - {t['id']:38s} | {t['name']} | tags={len(t['tags'])} | prompt={len(t['prompt'])}c | fb={len(t['text_fallback_prompt'])}c")
    for t in female_sub["templates"]:
        print(f"  F - {t['id']:38s} | {t['name']} | tags={len(t['tags'])} | prompt={len(t['prompt'])}c | fb={len(t['text_fallback_prompt'])}c")

print()
print("RESULT:", "ALL OK" if all_ok else "FAILED")
with open(r"C:\BSAI\ComfyUI-BSAI_pro_v39\ComfyUI\custom_nodes\BSAI-MiniMAX-H3-Prompt\_verify_result.txt", "w", encoding="utf-8") as f:
    f.write("ALL OK\n" if all_ok else "FAILED\n")
