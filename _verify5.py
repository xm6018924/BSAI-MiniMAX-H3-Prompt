#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json

# Just verify count and field completeness, and use a Chinese-character-free
# needle (using only English/ASCII) for content checks.

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

REQUIRED_FIELDS = ("id","name","name_en","description","preview","generation_mode",
                   "duration","tags","prompt","text_fallback_prompt","text_fallback_mode")

all_ok = True
for fp in [
    r"C:\BSAI\ComfyUI-BSAI_pro_v39\ComfyUI\custom_nodes\BSAI-MiniMAX-H3-Prompt\templates\prompt_templates.json",
    r"C:\BSAI\ComfyUI-BSAI_pro_v39\ComfyUI\custom_nodes\BSAI-MiniMAX-H3-Prompt\web\templates_data.json",
]:
    print("=" * 60)
    print(fp.split("\\")[-1])
    with open(fp, "r", encoding="utf-8") as f:
        d = json.load(f)
    xray = next(c for c in d["categories"] if c.get("id") == "xray_scan")
    male = next(s for s in xray["subcategories"] if s["id"] == "medical_anatomy_male")
    female = next(s for s in xray["subcategories"] if s["id"] == "medical_anatomy_female")

    # ID check
    male_ids = [t["id"] for t in male["templates"]]
    female_ids = [t["id"] for t in female["templates"]]
    for eid in EXPECTED_MALE:
        if eid not in male_ids:
            print(f"  male MISS: {eid}")
            all_ok = False
    for eid in EXPECTED_FEMALE:
        if eid not in female_ids:
            print(f"  female MISS: {eid}")
            all_ok = False

    # Field check
    for sub, ids in (("male", male_ids), ("female", female_ids)):
        for tid in ids:
            t = next(x for x in (male["templates"] if sub=="male" else female["templates"]) if x["id"] == tid)
            for field in REQUIRED_FIELDS:
                if field not in t:
                    print(f"  {sub} {tid}: missing {field}")
                    all_ok = False

    # English-keyword content checks (codepoint safe)
    male_spec = next(t for t in male["templates"] if t["id"] == "med_male_specific")
    female_spec = next(t for t in female["templates"] if t["id"] == "med_female_specific")
    MALE_ASCII = [
        "STRICT SEX", "175cm / 70kg", "175cm/70kg", "Male-Specific Structures",
        "Adam's apple", "Sertoli", "testosterone", "4-10mg/",
        "Penis", "Prostate", "Testis", "Epididymis", "Vas Deferens", "Seminal Vesicle",
        "Bulbourethral", "Corpus Cavernosum", "Corpus Spongiosum",
        "Spermatic Cord", "Scrotum", "Tunica Albuginea",
        "110Hz", "20-24mm", "Male Muscular", "Male Skeletal", "Male Cardiovascular",
    ]
    FEMALE_ASCII = [
        "STRICT SEX", "165cm / 57kg", "165cm/57kg", "Female-Specific Structures",
        "Ovary", "Fallopian Tube", "Uterus", "Vagina", "Vulva", "Clitoris",
        "Bartholin", "Skene", "Mammary Gland", "Cooper", "Montgomery",
        "220Hz", "15-18mm", "Female Muscular", "Female Skeletal", "Female Cardiovascular",
        "Menstrual", "Pregnancy", "Menopause",
    ]
    for kw in MALE_ASCII:
        if kw not in male_spec["prompt"]:
            print(f"  male_specific MISS kw: {kw!r}")
            all_ok = False
    for kw in FEMALE_ASCII:
        if kw not in female_spec["prompt"]:
            print(f"  female_specific MISS kw: {kw!r}")
            all_ok = False

    # Subcategory description should now say "7 \u4e2a\u6a21\u677f"
    if "7" not in male.get("description", ""):
        # check if it says 6 (old)
        if "6 \u4e2a\u6a21\u677f" in male["description"]:
            print("  male sub description still says '6 个模板'")
            all_ok = False
    if "7" not in female.get("description", ""):
        if "6 \u4e2a\u6a21\u677f" in female["description"]:
            print("  female sub description still says '6 个模板'")
            all_ok = False

    print(f"  medical_anatomy_male: {len(male['templates'])} templates")
    for t in male["templates"]:
        print(f"    - {t['id']:36s} | {t['name']:30s} | prompt={len(t['prompt'])}c | fb={len(t['text_fallback_prompt'])}c")
    print(f"  medical_anatomy_female: {len(female['templates'])} templates")
    for t in female["templates"]:
        print(f"    - {t['id']:36s} | {t['name']:30s} | prompt={len(t['prompt'])}c | fb={len(t['text_fallback_prompt'])}c")

print()
print("RESULT:", "ALL OK" if all_ok else "FAILED")
with open(r"C:\BSAI\ComfyUI-BSAI_pro_v39\ComfyUI\custom_nodes\BSAI-MiniMAX-H3-Prompt\_verify5_result.txt", "w", encoding="utf-8") as f:
    f.write("ALL OK\n" if all_ok else "FAILED\n")
