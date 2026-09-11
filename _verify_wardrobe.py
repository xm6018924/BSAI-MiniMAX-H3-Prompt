import json
all_ok = True
for fp in [
    r"C:\BSAI\ComfyUI-BSAI_pro_v39\ComfyUI\custom_nodes\BSAI-MiniMAX-H3-Prompt\templates\prompt_templates.json",
    r"C:\BSAI\ComfyUI-BSAI_pro_v39\ComfyUI\custom_nodes\BSAI-MiniMAX-H3-Prompt\web\templates_data.json",
]:
    print("=" * 60)
    print(fp.split("\\")[-1])
    with open(fp, "r", encoding="utf-8") as f:
        d = json.load(f)
    found = None
    for cat in d["categories"]:
        for sub in cat.get("subcategories", []):
            for t in sub.get("templates", []):
                if t.get("id") == "magic_mediator_wardrobe_change":
                    found = t
    assert found is not None
    p = found["prompt"]
    # check key new terms
    checks = {
        "Picture 2 FIRST": "FIRST TARGET OUTFIT" in p,
        "Picture 3 SECOND": "SECOND TARGET OUTFIT" in p,
        "Picture 4 device": "Picture 4" in p,
        "Picture 5 scene": "Picture 5" in p,
        "DUAL TRANSFORMATION": "DUAL TRANSFORMATION" in p,
        "Step 0 device enter": "Step 0" in p and "1.6s" in p,
        "Step 7 SECOND change": "Step 7" in p and "SECOND" in p,
        "Step 10 spin final": "Step 10" in p and "360" in p,
        "Single character rule": "exactly ONE character" in p,
        "NO camera cut": "NO camera cut" in p,
        "Text fallback updated": "DEFAULT OUTFIT 2" in found["text_fallback_prompt"],
        "Tags dual": "双重换装" in found["tags"],
    }
    for k, v in checks.items():
        print(f"  {'PASS' if v else 'FAIL'}: {k}")
        if not v:
            all_ok = False
    print(f"  description len: {len(found['description'])}, prompt len: {len(p)}, fb len: {len(found['text_fallback_prompt'])}")
print()
print("RESULT:", "ALL OK" if all_ok else "FAILED")
