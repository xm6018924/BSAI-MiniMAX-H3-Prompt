#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Final verification: focus on count + fields + Chinese content presence."""
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

REQUIRED_FIELDS = ("id","name","name_en","description","preview","generation_mode",
                   "duration","tags","prompt","text_fallback_prompt","text_fallback_mode")

# Use only ASCII to avoid codepoint issues
MALE_ASCII_KEYS = ["STRICT SEX", "175cm", "70kg", "Male-Specific Structures",
                   "Adam's apple", "Sertoli", "Male Muscular", "Male Skeletal",
                   "Male Cardiovascular", "Prostate", "Scrotum", "Vocal Cords",
                   "Tunica", "Dartos", "Vaginalis", "Penis", "Testis", "Epididymis",
                   "Vas Deferens", "Seminal Vesicle", "Spermatic Cord", "testosterone",
                   "Corpus", "Pampiniform"]
FEMALE_ASCII_KEYS = ["STRICT SEX", "165cm", "57kg", "Female-Specific Structures",
                     "Ovary", "Fallopian", "Uterus", "Vagina", "Vulva", "Clitoris",
                     "Bartholin", "Skene", "Mammary", "Cooper", "Montgomery",
                     "Lactiferous", "Areola", "Nipple", "Menstrual", "Pregnancy",
                     "Menopause", "Perimenopause", "Postmenopause", "Follicular",
                     "Luteal", "Ovulation", "Estrogen", "Progesterone", "Estradiol",
                     "Uterine Artery", "Ovarian Artery", "Vaginal Artery", "Pudendal",
                     "Female Muscular", "Female Skeletal", "Female Cardiovascular",
                     "Labia Majora", "Labia Minora", "Mons Pubis", "Vestibular",
                     "Hymen", "Inhibin", "Activin", "Relaxin", "Estriol"]


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

    male_ids = [t["id"] for t in male["templates"]]
    female_ids = [t["id"] for t in female["templates"]]
    print(f"  medical_anatomy_male: {len(male_ids)} templates")
    for eid in EXPECTED_MALE:
        if eid not in male_ids:
            print(f"    MISS: {eid}")
            all_ok = False
    print(f"  medical_anatomy_female: {len(female_ids)} templates")
    for eid in EXPECTED_FEMALE:
        if eid not in female_ids:
            print(f"    MISS: {eid}")
            all_ok = False

    # Field check
    for sub, label in ((male, "male"), (female, "female")):
        for t in sub["templates"]:
            for field in REQUIRED_FIELDS:
                if field not in t:
                    print(f"  {label} {t.get('id')}: missing {field}")
                    all_ok = False

    # ASCII content check
    male_spec = next(t for t in male["templates"] if t["id"] == "med_male_specific")
    female_spec = next(t for t in female["templates"] if t["id"] == "med_female_specific")
    p_m = male_spec["prompt"]
    p_f = female_spec["prompt"]
    print(f"  male_specific prompt: {len(p_m)} chars")
    for kw in MALE_ASCII_KEYS:
        if kw not in p_m:
            print(f"    MALE MISS: '{kw}'")
            all_ok = False
    print(f"  female_specific prompt: {len(p_f)} chars")
    for kw in FEMALE_ASCII_KEYS:
        if kw not in p_f:
            print(f"    FEMALE MISS: '{kw}'")
            all_ok = False

    # Print summary
    for t in male["templates"]:
        print(f"    M - {t['id']:36s} | {t['name']:30s} | prompt={len(t['prompt'])}c")
    for t in female["templates"]:
        print(f"    F - {t['id']:36s} | {t['name']:30s} | prompt={len(t['prompt'])}c")

print()
print("RESULT:", "ALL OK" if all_ok else "FAILED")
with open(r"C:\BSAI\ComfyUI-BSAI_pro_v39\ComfyUI\custom_nodes\BSAI-MiniMAX-H3-Prompt\_verify_final_result.txt", "w", encoding="utf-8") as f:
    f.write("ALL OK\n" if all_ok else "FAILED\n")
