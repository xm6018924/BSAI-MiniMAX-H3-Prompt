# -*- coding: utf-8 -*-
"""构建「电影感提示词 | Cinematic Prompts」分类（H3 三段式模板）。"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cinematic_data_part1 import T1
from cinematic_data_part2 import T2

DATA = T1 + T2

SUBCATS = [
    {"id":"comp_video","name":"构图技巧·视频原版","name_en":"Composition (from Vidu 100-series)","description":"来自B站《100组AI电影感提示词(11)构图技巧》的6组构图提示词 / 6 composition prompts extracted from the Bilibili video","templates":[]},
    {"id":"comp_more","name":"构图进阶","name_en":"Advanced Composition","description":"框中框、引导线、负空间、对称、对角线、特写等进阶构图 / Frame-in-frame, leading lines, negative space, symmetry, macro","templates":[]},
    {"id":"light","name":"光线与用光","name_en":"Lighting & Mood","description":"黄金时刻、蓝调时刻、伦勃朗光、逆光剪影、霓虹、烛光、体积光等 / Golden hour, blue hour, Rembrandt, backlight, neon, candle, volumetric","templates":[]},
    {"id":"camera","name":"镜头语言与运镜","name_en":"Camera Language & Movement","description":"推轨、一镜到底、慢动作、手持、环绕、航拍俯冲、甩镜、变焦冲击等 / Push-track, one-take, slow-mo, handheld, orbit, drone dive, whip pan, dolly zoom","templates":[]},
    {"id":"color","name":"色彩与调色","name_en":"Color & Grading","description":"青橙、黑白高对比、赛博朋克霓虹、莫兰迪、胶片颗粒等电影调色 / Teal-orange, B&W noir, cyberpunk, Morandi, film grain","templates":[]},
    {"id":"atmos","name":"氛围场景","name_en":"Atmosphere & Environment","description":"雨夜、雪景、晨雾、荒漠、废墟、海边、森林、烟火等氛围场景 / Rain, snow, fog, desert, ruins, seaside, forest, fireworks","templates":[]},
    {"id":"genre","name":"风格综合","name_en":"Genre & Cinematic Styles","description":"黑色电影、纪实、科幻、奇幻、战争史诗、音乐MV、大师风格等 / Noir, verite, sci-fi, fantasy, war epic, MV, master DoP styles","templates":[]},
]
SUBCAT_INDEX = {s["id"]: s for s in SUBCATS}

def build_prompt(dur, scene, sound, music):
    return (
        "integrated_multimodal_description:  [镜头1]【0-{}秒】{}\n\n"
        "overall_soundscape: {}\n\n"
        "non_diegetic_music: {}"
    ).format(dur, scene, sound, music)

for item in DATA:
    sub_id, tid, name, name_en, desc, tags, dur, scene, sound, music = item
    tpl = {
        "id": tid,
        "name": name,
        "name_en": name_en,
        "description": desc,
        "preview": "",
        "generation_mode": "Text to Video (文生视频)【图3可选场景】",
        "duration": dur,
        "needs_image": False,
        "needs_video": False,
        "needs_audio": False,
        "tags": tags,
        "prompt": build_prompt(dur, scene, sound, music),
    }
    SUBCAT_INDEX[sub_id]["templates"].append(tpl)

category = {
    "id": "cinematic_prompts",
    "name": "电影感提示词",
    "name_en": "Cinematic Prompts",
    "description": "电影感提示词模板：构图/光线/镜头语言/色彩/氛围/风格，纯文生视频即可出片 / Cinematic prompt templates covering composition, lighting, camera language, color, atmosphere and genre — pure text-to-video",
    "icon": "🎬",
    "subcategories": SUBCATS,
}

total = sum(len(s["templates"]) for s in SUBCATS)
print("templates built:", total)
for s in SUBCATS:
    print(" -", s["id"], len(s["templates"]))

out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cinematic_category.json")
with open(out, "w", encoding="utf-8") as f:
    json.dump(category, f, ensure_ascii=False, indent=2)
print("written:", out)
