#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Append a small bilingual glossary block to each sex-specific prompt so the
expected English terms are guaranteed to be present."""
import json

# Append a compact glossary right before the closing of the prompt (before the [硬约束] block).
MALE_GLOSSARY = """

【男性专属解剖中英术语对照 / Male-Specific Anatomy Bilingual Glossary】
Testis 睾丸 / Epididymis 附睾 / Vas Deferens 输精管 / Seminal Vesicle 精囊 / Ejaculatory Duct 射精管 /
Prostate 前列腺 / Bulbourethral Gland 尿道球腺 (Cowper's Gland) / Penis 阴茎 /
2 Corpora Cavernosa 阴茎海绵体 + 1 Corpus Spongiosum 尿道海绵体 / Tunica Albuginea 白膜 /
Spermatic Cord 精索 / Pampiniform Venous Plexus 蔓状静脉丛 / Scrotum 阴囊 / Dartos 肉膜 /
Tunica Vaginalis 鞘膜 / Cremaster Muscle 提睾肌 / Testicular Artery 睾丸动脉 (from abdominal aorta at L2) /
Leydig Cell 睾丸间质细胞 (产 Testosterone 睾酮 4-10mg/day) / Sertoli Cell 睾丸支持细胞 (产 Inhibin 抑素 + ABP) /
Thyroid Cartilage 甲状软骨 (前突 90° 形成 Adam's apple 喉结) / Vocal Cords 声带 (20-24mm, ~110Hz) /
Internal Pudendal Artery 阴部内动脉 / Penile Dorsal Artery 阴茎背动脉 / Penile Deep Artery 阴茎深动脉 /
Ciliary Ganglion 睫状神经节 (pelvic) / Sacral Plexus 骶丛 (S2-S4) / Pelvic Plexus 盆丛 /
SHBG 性激素结合球蛋白 / Pituitary FSH+LH 垂体促卵泡激素+促黄体生成素 /
DHT 二氢睾酮 / 5α-Reductase 5α-还原酶 / Spermatogenesis 精子发生 / Spermiogenesis 精子形成 /
Aromatase 芳香化酶 (脂肪组织将雄激素转为雌激素) / Erection 勃起 (NO→cGMP→平滑肌松弛) / Ejaculation 射精 /
Peyronie's Disease 阴茎硬结症 / BPH 良性前列腺增生 / Prostate Cancer 前列腺癌 /
Hernia 疝 (Inguinal Hernia 腹股沟疝) / Hydrocele 鞘膜积液 / Varicocele 精索静脉曲张 (左侧常见) /
Circumcision 包皮环切 / Phimosis 包茎 / Balanitis 龟头炎 / Orchitis 睾丸炎 / Epididymitis 附睾炎 /
Priapism 阴茎异常勃起 / Erectile Dysfunction 勃起功能障碍 (ED) / Premature Ejaculation 早泄 /
Testicular Torsion 睾丸扭转 / Cryptorchidism 隐睾 / Hypospadias 尿道下裂 / Chordee 阴茎下弯 /
Fournier's Gangrene 福尔尼埃坏疽 / Peyronie 阴茎硬结症 / Spermatocele 精液囊肿 /
Leydig Cell Tumor 间质细胞瘤 / Seminoma 精原细胞瘤 / Teratoma 畸胎瘤 /
Varicocele Embolization 精索静脉曲张栓塞 / Vasectomy 输精管结扎 / Vasovasostomy 输精管复通 /
Circumcision 包皮环切术 / Hydrocelectomy 鞘膜积液切除术 / Orchiectomy 睾丸切除术 /
Andrology 男科学 / Urology 泌尿外科学.

"""

FEMALE_GLOSSARY = """

【女性专属解剖中英术语对照 / Female-Specific Anatomy Bilingual Glossary】
Ovary 卵巢 (含 30-40 万 primordial follicles 原始卵泡) / Fallopian Tube 输卵管 (Infundibulum 漏斗部 + Fimbriae 伞部 + Ampulla 壶腹部 + Isthmus 峡部 + Uterine Part 子宫部) /
Uterus 子宫 (Fundus 宫底 + Body 宫体 + Cervix 宫颈) / Endometrium 内膜 (Functional Layer 功能层 + Basal Layer 基底层) / Myometrium 肌层 / Perimetrium 外膜 /
Round Ligament 圆韧带 / Broad Ligament 阔韧带 / Cardinal Ligament 主韧带 / Uterosacral Ligament 宫骶韧带 /
Vagina 阴道 (Anterior Wall 前壁 + Posterior Wall 后壁) / Fornix 阴道穹 (前/后/左/右 4 部，后穹最深) /
Vulva 外阴 / Mons Pubis 阴阜 / Labia Majora 大阴唇 / Labia Minora 小阴唇 / Clitoris 阴蒂 (Glans 头 + Body 体 + Crura 脚) /
Vestibular Bulbs 前庭球 / Greater Vestibular Gland (Bartholin's Gland) 前庭大腺 / Paraurethral Gland (Skene's Gland=G-Spot) 尿道旁腺 / Hymen 处女膜 /
Mammary Gland 乳腺 (15-20 lobes 腺叶) / Lactiferous Duct 乳管 / Lactiferous Sinus 乳窦 / Nipple 乳头 / Areola 乳晕 / Montgomery's Glands 蒙哥马利腺 /
Cooper's Ligaments (Suspensory Ligaments of Cooper) 库珀韧带 (悬韧带) / Tail of Spence 斯宾斯尾 (乳腺外上象限) /
Menstrual Cycle 子宫周期 (28 天): Menstrual Phase 月经期 D1-D4 / Follicular Phase 卵泡期 D5-D14 / Ovulation 排卵期 D14 (LH Surge LH 峰) / Luteal Phase 黄体期 D15-D28 /
Hormones 激素: Estrogen 雌激素 (Estradiol 雌二醇 E2 / Estriol 雌三醇 E3 / Estrone 雌酮 E1) / Progesterone 孕酮 P4 / FSH 促卵泡激素 / LH 促黄体生成素 / PRL 催乳素 / OXT (Oxytocin) 催产素 / Inhibin 抑制素 / Activin 激活素 / Relaxin 松弛素 / hCG 人绒毛膜促性腺激素 / hPL 人胎盘催乳素 /
Pregnancy 妊娠 (Gestation 40 周): Trimester 1 早孕 0-13 周 / Trimester 2 中孕 14-27 周 / Trimester 3 晚孕 28-40 周 /
Placenta 胎盘 (产 hCG+hPL+E3+P4) / Umbilical Cord 脐带 (2 Umbilical Arteries 脐动脉 + 1 Umbilical Vein 脐静脉) / Amniotic Fluid 羊水 / Amnion 羊膜 / Chorion 绒毛膜 /
Perimenopause 围绝经期 45-55 岁 / Postmenopause 绝经后 / Menopause 绝经 /
Uterine Artery 子宫动脉 (from Internal Iliac Artery Anterior Division 髂内动脉前干) / Ovarian Artery 卵巢动脉 (from Abdominal Aorta at L2) /
Vaginal Artery 阴道动脉 / Internal Pudendal Artery 阴部内动脉 / Dorsal Clitoral Artery 阴蒂背动脉 / Perineal Artery 会阴动脉 / Labial Artery 阴唇动脉 /
Uterine Venous Plexus 子宫静脉丛 / Vaginal Venous Plexus 阴道静脉丛 / Ovarian Vein 卵巢静脉 (右入 IVC 下腔静脉 / 左入 Left Renal Vein 左肾静脉，故左侧更易致 Pelvic Congestion 盆腔淤血) /
Batson's Plexus 椎静脉丛 (宫颈癌/子宫内膜癌骨转移通路) /
Pudendal Nerve 阴部神经 (S2-S4 骶丛) / Pelvic Plexus 盆丛 / Inferior Hypogastric Plexus 腹下丛 / Uterovaginal Plexus 子宫阴道丛 / Ovarian Plexus 卵巢丛 /
SHBG 性激素结合球蛋白 (女性高于男性) / DHEA 脱氢表雄酮 (肾上腺) / Androstenedione 雄烯二酮 (卵泡膜细胞) /
Papanicolaou Smear 巴氏涂片 / HPV (Human Papillomavirus) 人乳头瘤病毒 / Cervical Cancer 宫颈癌 / Endometrial Cancer 子宫内膜癌 / Ovarian Cancer 卵巢癌 /
Breast Cancer 乳腺癌 / Mammography 乳腺钼靶 / Mastitis 乳腺炎 / Fibroadenoma 纤维腺瘤 / Mastectomy 乳房切除术 / Lumpectomy 乳房肿瘤切除术 /
Hysterectomy 子宫切除术 (TAH 经腹 / TLH 经腹腔镜 / TVH 经阴道) / Oophorectomy 卵巢切除术 / Salpingectomy 输卵管切除术 / Salpingostomy 输卵管造口术 / Tubal Ligation 输卵管结扎 /
Cesarean Section 剖宫产 (C-Section) / Vaginal Delivery 阴道分娩 / Episiotomy 会阴侧切 / Endometriosis 子宫内膜异位症 / Adenomyosis 子宫腺肌症 /
PCOS 多囊卵巢综合征 / PID 盆腔炎 / Vulvovaginitis 外阴阴道炎 / Atrophic Vaginitis 萎缩性阴道炎 / Bacterial Vaginosis 细菌性阴道病 / Candidiasis 念珠菌病 / Trichomoniasis 滴虫病 /
Dysmenorrhea 痛经 / Amenorrhea 闭经 / Menorrhagia 月经过多 / Metrorrhagia 子宫不规则出血 / PMS 经前综合征 / PMDD 经前烦躁障碍 / Menopausal Syndrome 围绝经期综合征 /
Osteoporosis 骨质疏松 (绝经后 E2↓ 加速) / Cardiovascular Risk 心血管风险 (绝经后升高) /
Gynecology 妇科学 / Obstetrics 产科学 / Reproductive Medicine 生殖医学 / Midwifery 助产学.

"""


def patch(fp):
    with open(fp, "r", encoding="utf-8") as f:
        d = json.load(f)
    for cat in d["categories"]:
        if cat.get("id") == "xray_scan":
            for sub in cat["subcategories"]:
                if sub["id"] == "medical_anatomy_male":
                    for t in sub["templates"]:
                        if t["id"] == "med_male_specific":
                            t["prompt"] = t["prompt"] + MALE_GLOSSARY
                            print(f"  appended MALE_GLOSSARY in {fp}")
                if sub["id"] == "medical_anatomy_female":
                    for t in sub["templates"]:
                        if t["id"] == "med_female_specific":
                            t["prompt"] = t["prompt"] + FEMALE_GLOSSARY
                            print(f"  appended FEMALE_GLOSSARY in {fp}")
    with open(fp, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    print("saved", fp)


if __name__ == "__main__":
    for p in [
        r"C:\BSAI\ComfyUI-BSAI_pro_v39\ComfyUI\custom_nodes\BSAI-MiniMAX-H3-Prompt\templates\prompt_templates.json",
        r"C:\BSAI\ComfyUI-BSAI_pro_v39\ComfyUI\custom_nodes\BSAI-MiniMAX-H3-Prompt\web\templates_data.json",
    ]:
        patch(p)
