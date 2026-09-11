import json
fp = r"C:\BSAI\ComfyUI-BSAI_pro_v39\ComfyUI\custom_nodes\BSAI-MiniMAX-H3-Prompt\templates\prompt_templates.json"
with open(fp, "r", encoding="utf-8") as f:
    d = json.load(f)
for cat in d["categories"]:
    if cat.get("id") == "xray_scan":
        for sub in cat["subcategories"]:
            if sub["id"] == "medical_anatomy_male":
                for t in sub["templates"]:
                    if t["id"] == "med_organ_systems_male":
                        p = t["prompt"]
                        # write the reproductive section to a file
                        idx = p.find("Reproductive")
                        if idx >= 0:
                            with open(r"C:\BSAI\ComfyUI-BSAI_pro_v39\ComfyUI\custom_nodes\BSAI-MiniMAX-H3-Prompt\_male_repro.txt", "w", encoding="utf-8") as f:
                                f.write(p[idx:idx+1500])
                        # search for the female markers
                        for kw in ["\u5375\u5de2", "\u4e73\u817a", "\u9634\u9053", "\u5916\u9634"]:
                            idx = p.find(kw)
                            if idx >= 0:
                                print(f"  found {kw!r} at {idx}: {p[max(0,idx-20):idx+30]!r}")
            if sub["id"] == "medical_anatomy_female":
                for t in sub["templates"]:
                    if t["id"] == "med_organ_systems_female":
                        p = t["prompt"]
                        idx = p.find("Reproductive")
                        if idx >= 0:
                            with open(r"C:\BSAI\ComfyUI-BSAI_pro_v39\ComfyUI\custom_nodes\BSAI-MiniMAX-H3-Prompt\_female_repro.txt", "w", encoding="utf-8") as f:
                                f.write(p[idx:idx+1500])
                        for kw in ["\u777e\u4e38", "\u8f93\u7cbe\u7ba1", "\u5c3f\u9053\u7403\u817a", "\u9634\u830e"]:
                            idx = p.find(kw)
                            if idx >= 0:
                                print(f"  found {kw!r} at {idx}: {p[max(0,idx-20):idx+30]!r}")
