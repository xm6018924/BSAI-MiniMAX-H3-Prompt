import json
TARGET = "magic_mediator_wardrobe_change"

def walk(o, path=""):
    if isinstance(o, dict):
        for k, v in o.items():
            if k == "id" and v == TARGET:
                return o
            r = walk(v, path + "/" + str(k))
            if r is not None:
                return r
    elif isinstance(o, list):
        for i, x in enumerate(o):
            r = walk(x, path + f"[{i}]")
            if r is not None:
                return r
    return None

out_lines = []
for path in [
    r"C:\BSAI\ComfyUI-BSAI_pro_v39\ComfyUI\custom_nodes\BSAI-MiniMAX-H3-Prompt\templates\prompt_templates.json",
    r"C:\BSAI\ComfyUI-BSAI_pro_v39\ComfyUI\custom_nodes\BSAI-MiniMAX-H3-Prompt\web\templates_data.json",
]:
    with open(path, "r", encoding="utf-8") as f:
        d = json.load(f)
    t = walk(d)
    out_lines.append("=" * 60)
    out_lines.append("FILE: " + path)
    out_lines.append("name        : " + t["name"])
    out_lines.append("name_en     : " + t["name_en"])
    out_lines.append("description : " + t["description"])
    out_lines.append("")
    out_lines.append("--- prompt ---")
    out_lines.append(t["prompt"])
    out_lines.append("--- /prompt ---")

with open(r"C:\BSAI\ComfyUI-BSAI_pro_v39\ComfyUI\custom_nodes\BSAI-MiniMAX-H3-Prompt\_diag_result.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(out_lines))
print("written")
