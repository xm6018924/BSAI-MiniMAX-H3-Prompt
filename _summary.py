import json

out = []
for p in [
    r"C:\BSAI\ComfyUI-BSAI_pro_v39\ComfyUI\custom_nodes\BSAI-MiniMAX-H3-Prompt\templates\prompt_templates.json",
    r"C:\BSAI\ComfyUI-BSAI_pro_v39\ComfyUI\custom_nodes\BSAI-MiniMAX-H3-Prompt\web\templates_data.json",
]:
    with open(p, "r", encoding="utf-8") as f:
        d = json.load(f)
    xray = next(c for c in d["categories"] if c.get("id") == "xray_scan")
    out.append(p.split("\\")[-1])
    out.append(f"  xray_scan: {xray['name']} | {xray['name_en']}")
    out.append(f"  description: {xray.get('description','')[:120]}...")
    for sub in xray["subcategories"]:
        out.append(f"  - sub: {sub['id']:30s} | {sub['name']:20s} | {sub['name_en']:35s} | templates={len(sub['templates'])}")
        for t in sub["templates"]:
            out.append(f"      * {t['id']:38s} | {t['name']:25s} | {t['name_en']}")
    out.append("")

with open(r"C:\BSAI\ComfyUI-BSAI_pro_v39\ComfyUI\custom_nodes\BSAI-MiniMAX-H3-Prompt\_summary.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(out))
print("written _summary.txt")
