# final verification report
import json
for p in [
    r"C:\BSAI\ComfyUI-BSAI_pro_v39\ComfyUI\custom_nodes\BSAI-MiniMAX-H3-Prompt\templates\prompt_templates.json",
    r"C:\BSAI\ComfyUI-BSAI_pro_v39\ComfyUI\custom_nodes\BSAI-MiniMAX-H3-Prompt\web\templates_data.json",
]:
    with open(p, "r", encoding="utf-8") as f:
        d = json.load(f)
    xray = next(c for c in d["categories"] if c.get("id") == "xray_scan")
    med = next(s for s in xray["subcategories"] if s["id"] == "medical_anatomy")
    print(p.split("\\")[-1])
    print(f"  xray_scan: {xray['name']}")
    print(f"  subs: {[s['id'] for s in xray['subcategories']]}")
    print(f"  medical_anatomy: {med['name']} | {med['name_en']}")
    print(f"  templates: {len(med['templates'])}")
    for t in med["templates"]:
        print(f"    - {t['id']:30s} | {t['name']:25s} | {t['name_en']}")
    print()
