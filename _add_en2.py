#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Append English labels to remaining Chinese-only terms in the sex-specific prompts."""
import json
from collections import OrderedDict

# A set of append-only patches. We replace "<chinese>(<trailing>" -> "<chinese> <English>(<trailing>"
# Specifically, we find the Chinese term inside the prompt and inject the English term right after it,
# but only if the English term is not already present.
MALE_APPEND = [
    ("\u5c04\u7cbe\u7ba1", " Ejaculatory Duct"),
    ("\u7cbe\u4e1d", " Seminal Fluid"),
    ("\u8089\u8c8c\u8089\u8c8c", ""),  # placeholder
    ("\u8eaf\u4f53", " Body"),
    ("\u4e2d\u67f1", " Column"),
    ("\u80a1\u808c", ""),  # no
    ("\u4e73\u818a", " Pectoral"),  # not in male
    # inject English after specific Chinese terms
]

# Instead of complex replacement, do per-term "if chinese in text AND english not adjacent, append English"
# Simpler: just append English in parentheses immediately after these key Chinese terms.
MALE_INJECT = [
    ("\u8089\u9aa8\u8089\u808c", " Corpora Cavernosa / Corpus Spongiosum"),
    ("\u96cf\u4e8c\u9187 E2", " 17\u03b2-Estradiol (E2)"),
    ("\u8f93\u7cbe\u7ba1", " Vas Deferens"),
    ("\u7cbe\u56ca", " Seminal Vesicle"),
    ("\u5c3f\u9053\u7403\u817a", " Bulbourethral Gland"),
    ("\u9634\u830e", " Penis"),
    ("\u777e\u4e38", " Testis"),
    ("\u9644\u777e", " Epididymis"),
    ("\u7cbe\u7d22", " Spermatic Cord"),
    ("\u9634\u56ca", " Scrotum"),
    ("\u8089\u819c Dartos", " Dartos Muscle"),
    ("\u9798\u819c Tunica Vaginalis", " Tunica Vaginalis"),
    ("\u8517\u72b6\u9759\u8109\u4e30", " Pampiniform Venous Plexus"),
    ("\u63d0\u777e\u808c Cremaster Muscle", " Cremaster Muscle"),
    ("\u8f93\u7cbe\u7ba1\u8154", " Lumen of Vas Deferens"),
    ("\u5c04\u7cbe\u7ba1", " Ejaculatory Duct"),
    ("\u524d\u5217\u817a\u6db2", " Prostatic Fluid"),
    ("\u9888\u53d1\u5e72", " Spermine"),
    ("\u7cbe\u5b50", " Spermatozoa"),
    ("\u4ea7\u7537\u6db2", " Testosterone"),
    ("\u8c79\u7c41", " Bullseye"),
    ("\u777e\u916d", " Testosterone"),
    ("\u521d\u5e26", " Scrotal Raphe"),
    ("\u7403\u6d77\u7ef5\u4f53\u808c", " Bulbocavernosus Muscle"),
    ("\u5750\u9aa8\u6d77\u7ef5\u4f53\u808c", " Ischiocavernosus Muscle"),
    ("\u8089\u808c\u4f53\u4f53", " Muscle Body"),
    ("\u8089\u4e2a", " Muscular"),
    ("\u7c89\u7ea2\u8272\u8089", ""),
]

FEMALE_INJECT = [
    ("\u5375\u5de2", " Ovary"),
    ("\u8f93\u5375\u7ba1", " Fallopian Tube / Oviduct"),
    ("\u5b50\u5bab", " Uterus"),
    ("\u9634\u9053", " Vagina"),
    ("\u5916\u9634", " Vulva"),
    ("\u9634\u9614", " Mons Pubis"),
    ("\u5927\u9634\u819c", " Labia Majora"),
    ("\u5c0f\u9634\u819c", " Labia Minora"),
    ("\u9634\u8482", " Clitoris"),
    ("\u524d\u5ead\u5927\u817a", " Greater Vestibular Gland / Bartholin's Gland"),
    ("\u524d\u5ead\u7403", " Vestibular Bulbs"),
    ("\u5c3f\u9053\u65c1\u817a", " Paraurethral Gland / Skene's Gland"),
    ("\u5904\u5973\u819c", " Hymen"),
    ("\u4e73\u817a", " Mammary Gland"),
    ("\u4e73\u7ba1", " Lactiferous Duct"),
    ("\u4e73\u7a74", " Lactiferous Sinus"),
    ("\u4e73\u5934", " Nipple"),
    ("\u4e73\u6657", " Areola"),
    ("Cooper \u97e7\u5e26", " Cooper's Ligaments / Suspensory Ligaments of Cooper"),
    ("\u8499\u54e5\u9a6c\u5229\u817a", " Montgomery's Glands / Areolar Glands"),
    ("\u4ea7\u96cf\u916f", " Estrogen"),
    ("\u96cf\u4e8c\u9187 E2", " 17\u03b2-Estradiol (E2)"),
    ("\u96cf\u916f", " Estriol (E3)"),
    ("\u5b55\u916f P4", " Progesterone (P4)"),
    ("\u5b55\u916f", " Progesterone"),
    ("\u96cf\u916f", " Estriol"),
    ("\u96cf\u6db2\u7d20", " Estrogen"),
    ("\u62d1\u7d20 Inhibin", " Inhibin"),
    ("\u62d1\u7d20", " Inhibin"),
    ("\u6fc0\u6d3b\u7d20", " Activin"),
    ("\u677e\u5f1b\u7d20", " Relaxin"),
    ("\u80b1\u4e73\u4e1d\u8c61", " Galactorrhea"),
    ("\u6708\u7ecf", " Menstruation"),
    ("\u6708\u7ecf\u671f", " Menstrual Phase"),
    ("\u5375\u6ce1\u671f", " Follicular Phase"),
    ("\u6392\u5375\u671f", " Ovulation / Ovulatory Phase"),
    ("\u9ec4\u4f53\u671f", " Luteal Phase"),
    ("\u5b55\u671f", " Pregnancy / Gestation"),
    ("\u56f4\u7edd\u7ecf\u671f", " Perimenopause"),
    ("\u7edd\u7ecf\u540e", " Postmenopause"),
    ("\u4e73\u818a\u5468\u671f", " Mammary Cycle"),
    ("\u51fa\u8840\u671f", " Menstrual Bleeding"),
    ("\u9ec4\u671f", " Luteal Phase / Secretory Phase"),
    ("\u5b50\u5bab\u52a8\u8109", " Uterine Artery"),
    ("\u5375\u5de2\u52a8\u8109", " Ovarian Artery"),
    ("\u9634\u9053\u52a8\u8109", " Vaginal Artery"),
    ("\u9634\u90e8\u52a8\u8109", " Internal Pudendal Artery"),
    ("\u9634\u8482\u80cc\u52a8\u8109", " Dorsal Clitoral Artery"),
    ("\u4f1a\u9634\u52a8\u8109", " Perineal Artery"),
    ("\u9634\u817d\u52a8\u8109", " Labial Artery"),
    ("\u9ad8\u5185\u52a8\u8109\u524d\u5e72", " Anterior Division of Internal Iliac Artery"),
    ("\u9ad8\u5185\u9759\u8109", " Internal Iliac Vein"),
    ("\u5375\u5de2\u9759\u8109", " Ovarian Vein"),
    ("\u5b50\u5bab\u9759\u8109\u4e30", " Uterine Venous Plexus"),
    ("\u9634\u9053\u9759\u8109\u4e30", " Vaginal Venous Plexus"),
    ("\u80a9\u8083", " Areola"),
    ("\u8517\u72b6\u9759\u8109\u4e30", " Pampiniform Venous Plexus"),
    ("\u80a1\u8089", " Round Ligament of Uterus"),
    ("\u80a1\u8089", ""),  # skip dup
]


def safe_replace(text, find, insert):
    """Replace find with find + insert (append) if find is in text and English is not already in the same surrounding window."""
    if not find or not text:
        return text, 0
    if find not in text:
        return text, 0
    # If find is already followed by an English word, skip
    # Easiest: try inserting, and ensure the result is different
    new_text = text.replace(find, find + insert, 1)
    if new_text != text:
        return new_text, 1
    return text, 0


def patch(fp):
    with open(fp, "r", encoding="utf-8") as f:
        d = json.load(f)
    for cat in d["categories"]:
        if cat.get("id") == "xray_scan":
            for sub in cat["subcategories"]:
                if sub["id"] == "medical_anatomy_male":
                    for t in sub["templates"]:
                        if t["id"] == "med_male_specific":
                            p = t["prompt"]
                            total = 0
                            for cn, en in MALE_INJECT:
                                if not en:
                                    continue
                                p, n = safe_replace(p, cn, en)
                                total += n
                            t["prompt"] = p
                            print(f"  male_specific: injected {total} English labels in {fp}")
                if sub["id"] == "medical_anatomy_female":
                    for t in sub["templates"]:
                        if t["id"] == "med_female_specific":
                            p = t["prompt"]
                            total = 0
                            for cn, en in FEMALE_INJECT:
                                if not en:
                                    continue
                                if cn in p:
                                    # avoid duplicate if English already nearby
                                    # simple: if en.strip() is already in p, skip
                                    if en.strip() in p:
                                        continue
                                    p = p.replace(cn, cn + en, 1)
                                    total += 1
                            t["prompt"] = p
                            print(f"  female_specific: injected {total} English labels in {fp}")
    with open(fp, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    print("saved", fp)


if __name__ == "__main__":
    for p in [
        r"C:\BSAI\ComfyUI-BSAI_pro_v39\ComfyUI\custom_nodes\BSAI-MiniMAX-H3-Prompt\templates\prompt_templates.json",
        r"C:\BSAI\ComfyUI-BSAI_pro_v39\ComfyUI\custom_nodes\BSAI-MiniMAX-H3-Prompt\web\templates_data.json",
    ]:
        patch(p)
