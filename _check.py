import json
# read actual file content and check key strings
fp = r"C:\BSAI\ComfyUI-BSAI_pro_v39\ComfyUI\custom_nodes\BSAI-MiniMAX-H3-Prompt\templates\prompt_templates.json"
with open(fp, "r", encoding="utf-8") as f:
    d = json.load(f)

# Find each medical template and run the full check
def get_t(tid):
    for cat in d["categories"]:
        if cat.get("id") == "xray_scan":
            for s in cat["subcategories"]:
                if s["id"] == "medical_anatomy":
                    for t in s["templates"]:
                        if t["id"] == tid:
                            return t

CHECKS = {
    "med_full_body_anatomy": [
        "参考图声明", "206", "640", "九大系统", "中英对照", "硬约束",
        "心脏", "肺", "胝", "肾", "脑", "皮肤", "五官",
    ],
    "med_skeletal_system": [
        "参考图声明", "206", "颅骨 23", "脊柱 33", "听小骨 6", "胸骨 1", "肋骨 24", "中英对照",
    ],
    "med_muscular_system": [
        "参考图声明", "640", "头颈肌", "躯干肌", "上肢肌", "下肢肌", "起止点", "神经支配",
    ],
    "med_organ_systems": [
        "参考图声明", "九大系统", "消化", "呼吸", "循环", "泌尿", "生殖", "内分泌",
        "神经", "免疫", "心脏", "肺", "胝", "肾", "小脑",
    ],
    "med_face_features_closeup": [
        "参考图声明", "眼", "耳", "鼻", "口", "舌", "32", "面神经", "三叉神经", "中英对照",
    ],
    "med_hands_feet_skin": [
        "参考图声明", "腕 8 骨", "跗骨", "足弓", "表皮", "真皮", "毛囊", "汗腺", "指甲",
        "组织切片", "HE 染色", "上皮", "结缔", "肌组织", "神经组织", "血液",
    ],
}

all_ok = True
for tid, needles in CHECKS.items():
    t = get_t(tid)
    p = t["prompt"]
    print(f"=== {tid} ===")
    miss = []
    for n in needles:
        if n not in p:
            miss.append(n)
            all_ok = False
    if miss:
        print("  MISS:", miss)
    else:
        print("  ALL PASS")

# Also do the same for web version
fp2 = r"C:\BSAI\ComfyUI-BSAI_pro_v39\ComfyUI\custom_nodes\BSAI-MiniMAX-H3-Prompt\web\templates_data.json"
with open(fp2, "r", encoding="utf-8") as f:
    d2 = json.load(f)

def get_t2(tid):
    for cat in d2["categories"]:
        if cat.get("id") == "xray_scan":
            for s in cat["subcategories"]:
                if s["id"] == "medical_anatomy":
                    for t in s["templates"]:
                        if t["id"] == tid:
                            return t

print()
print("=== web/templates_data.json ===")
for tid, needles in CHECKS.items():
    t = get_t2(tid)
    p = t["prompt"]
    miss = [n for n in needles if n not in p]
    if miss:
        all_ok = False
        print(f"  {tid}: MISS {miss}")
    else:
        print(f"  {tid}: ALL PASS")

print()
print("RESULT:", "ALL OK" if all_ok else "FAILED")
with open(r"C:\BSAI\ComfyUI-BSAI_pro_v39\ComfyUI\custom_nodes\BSAI-MiniMAX-H3-Prompt\_check_result.txt", "w", encoding="utf-8") as f:
    f.write("ALL OK\n" if all_ok else "FAILED\n")
