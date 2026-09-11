import json

EXPECTED = ["magic_mediator_wardrobe_change", "magic_mediator_wardrobe_single", "magic_mediator_wardrobe_multi"]

CHECKS = {
    "magic_mediator_wardrobe_change": [
        "<Picture 1> is the CHARACTER", "<Picture 2> is the OUTFIT", "<Picture 3> is the INTERACTIVE",
        "elven dress",  # female gown default
    ],
    "magic_mediator_wardrobe_single": [
        "<Picture 1> is the CHARACTER", "<Picture 2> is the INTERACTIVE", "<Picture 3> is the OUTFIT",
        "LAST picture slot", "Step 6",
    ],
    "magic_mediator_wardrobe_multi": [
        "M (where M \u2265 2)", "outfit #1 = <Picture 3>", "outfit #M = <Picture (M+2)>",
        "Cycle i", "exactly M magical outfit changes", "FINAL outfit",
    ],
}

ok_all = True
for fp in [
    r"C:\BSAI\ComfyUI-BSAI_pro_v39\ComfyUI\custom_nodes\BSAI-MiniMAX-H3-Prompt\templates\prompt_templates.json",
    r"C:\BSAI\ComfyUI-BSAI_pro_v39\ComfyUI\custom_nodes\BSAI-MiniMAX-H3-Prompt\web\templates_data.json",
]:
    print("=" * 60)
    print(fp.split("\\")[-1])
    with open(fp, "r", encoding="utf-8") as f:
        d = json.load(f)
    found = {}
    for cat in d["categories"]:
        for sub in cat.get("subcategories", []):
            for t in sub.get("templates", []):
                if t.get("id") in EXPECTED:
                    found[t["id"]] = t
    for eid in EXPECTED:
        if eid not in found:
            print(f"  MISSING: {eid}")
            ok_all = False
    for tid, needles in CHECKS.items():
        if tid not in found:
            continue
        p = found[tid]["prompt"]
        miss = [n for n in needles if n not in p]
        if miss:
            ok_all = False
            print(f"  {tid} MISS: {miss}")
        else:
            print(f"  {tid}: all needles pass")
    for tid, t in found.items():
        for field in ("id", "name", "name_en", "description", "preview", "generation_mode",
                      "duration", "tags", "prompt", "text_fallback_prompt", "text_fallback_mode"):
            if field not in t:
                print(f"  {tid} missing field {field}")
                ok_all = False
    for tid, t in found.items():
        print(f"  {tid:36s} | {t['name']:30s} | prompt={len(t['prompt'])}c | fb={len(t['text_fallback_prompt'])}c")
print()
print("RESULT:", "ALL OK" if ok_all else "FAILED")
with open(r"C:\BSAI\ComfyUI-BSAI_pro_v39\ComfyUI\custom_nodes\BSAI-MiniMAX-H3-Prompt\_verify_split_result.txt", "w", encoding="utf-8") as f:
    f.write("ALL OK\n" if ok_all else "FAILED\n")
