import json

# Find a unique anchor in T1 prompt
T1_ANCHOR = "Step 4 \u2014 \u5185\u810f\u5c42"  # "Step 4 — 内脏层"
T1_INSERT_BEFORE = "Step 5 \u2014 \u5faa\u73af\u4e0e\u795e\u7ecf\u5c42"
T1_INSERT_TEXT = "\u3002\u672c\u6bb5\u4ee5\u300c\u4e5d\u5927\u7cfb\u7edf\u300d\u2014\u2014\u6d88\u5316\u3001\u547c\u5438\u3001\u5faa\u73af\u3001\u6ccc\u5c3f\u3001\u751f\u6b96\u3001\u5185\u5206\u6ccc\u3001\u795e\u7ecf\u3001\u514d\u75ab\uff08\u6dcb\u5df4\uff09\u4e0e\u76ae\u80a4\u2014\u2014\u4e3a\u4e3b\u7ebf\u67b6\u6784\uff0c\u4e0e\u808c\u8089\u3001\u9aa8\u9abc\u3001\u795e\u7ecf\u8840\u7ba1\u4e92\u4e3a\u8865\u5145\uff0c\u67b6\u8d77\u5b8c\u6574\u4eba\u4f53\u4e09\u7ef4\u89e3\u5256"

T2_PATCH_OLD = "\u6bcf\u5757\u9aa8\u6709\u7ec6\u7ebf\u5f15\u51fa\u81f3\u4e2d\u82f1\u540d\u6807\u7b7e"
T2_PATCH_NEW = "\u6bcf\u5757\u9aa8\u6709\u7ec6\u7ebf\u5f15\u51fa\u81f3\u4e2d\u82f1\u5bf9\u7167\u540d\u79f0\u6807\u7b7e"

def patch(fp):
    with open(fp, "r", encoding="utf-8") as f:
        d = json.load(f)
    for cat in d["categories"]:
        if cat.get("id") == "xray_scan":
            for sub in cat["subcategories"]:
                if sub["id"] == "medical_anatomy":
                    for t in sub["templates"]:
                        if t["id"] == "med_full_body_anatomy":
                            p = t["prompt"]
                            if T1_INSERT_BEFORE in p:
                                t["prompt"] = p.replace(T1_INSERT_BEFORE, T1_INSERT_TEXT + T1_INSERT_BEFORE, 1)
                                print("  T1 PATCHED", fp)
                            else:
                                # try em dash variant
                                alt = "Step 5 \u2014 \u5faa\u73af\u4e0e\u795e\u7ecf\u5c42"
                                if alt in p:
                                    t["prompt"] = p.replace(alt, T1_INSERT_TEXT + alt, 1)
                                    print("  T1 PATCHED (alt)", fp)
                                else:
                                    print("  WARN: T1 insert-before anchor not found", fp)
                        if t["id"] == "med_skeletal_system":
                            if T2_PATCH_OLD in t["prompt"]:
                                t["prompt"] = t["prompt"].replace(T2_PATCH_OLD, T2_PATCH_NEW, 1)
                                print("  T2 PATCHED", fp)
    with open(fp, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    print("saved", fp)


for p in [
    r"C:\BSAI\ComfyUI-BSAI_pro_v39\ComfyUI\custom_nodes\BSAI-MiniMAX-H3-Prompt\templates\prompt_templates.json",
    r"C:\BSAI\ComfyUI-BSAI_pro_v39\ComfyUI\custom_nodes\BSAI-MiniMAX-H3-Prompt\web\templates_data.json",
]:
    patch(p)
