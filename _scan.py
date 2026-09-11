import json
for fp in [
    r"C:\BSAI\ComfyUI-BSAI_pro_v39\ComfyUI\custom_nodes\BSAI-MiniMAX-H3-Prompt\templates\prompt_templates.json",
    r"C:\BSAI\ComfyUI-BSAI_pro_v39\ComfyUI\custom_nodes\BSAI-MiniMAX-H3-Prompt\web\templates_data.json",
]:
    with open(fp, "r", encoding="utf-8") as f:
        d = json.load(f)
    print("FILE:", fp.split("\\")[-1])
    found = False
    for cat in d["categories"]:
        if cat.get("id") == "xray_scan":
            found = True
            print("  xray_scan found. subs:")
            for sub in cat.get("subcategories", []):
                print("   -", sub.get("id"), "|", sub.get("name"), "| templates:", [t["id"] for t in sub.get("templates", [])])
            print("  description:", cat.get("description"))
            print("  icon:", cat.get("icon"))
    if not found:
        print("  xray_scan NOT FOUND in", fp.split("\\")[-1])
    print()
