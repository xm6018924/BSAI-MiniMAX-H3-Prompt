#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Upgrade the magic_mediator_wardrobe_change template to support 3 outfits
(Picture 1 = character, Picture 2 = first target outfit, Picture 3 = second
target outfit, Picture 4 = interactive device, Picture 5 = optional scene).

Two consecutive magical wardrobe changes happen within 8 seconds.
"""
import json
from collections import OrderedDict

# ============== NEW PROMPT (3-outfit, 8s, dual transformation) ==============

NEW_PROMPT = """[STRICT MULTI-REFERENCE COMPLIANCE / 严格多参考声明]: EVERY <Picture N> referenced in this prompt is an independent reference and MUST be strictly followed. <Picture 1> is the CHARACTER reference — face, hairstyle, body proportions, identity AND initial outfit must be preserved EXACTLY throughout the whole video; the character is one single real person who never duplicates or splits into multiple figures. <Picture 2> is the FIRST TARGET OUTFIT reference — the character's initial <Picture 1> outfit transforms into THIS outfit during the FIRST magical change; the garment's cut, color, pattern, fabric texture and every detail must come EXACTLY from <Picture 2>; never self-invent any clothing. <Picture 3> is the SECOND TARGET OUTFIT reference — the character's <Picture 2> outfit then transforms into THIS outfit during the SECOND magical change; cut, color, pattern, fabric texture and every detail must come EXACTLY from <Picture 3>; the character ends the video wearing <Picture 3>. <Picture 4> is the INTERACTIVE MEDIATOR DEVICE reference — it can be eyeglasses / a phone / a mirror / a wristband / a fan / a wand / any hand-held prop; the device in the video must match <Picture 4>'s exact type, model, shape, color and details and stay exactly that device for the whole video; the device type never changes and NO other device of any kind ever appears anywhere in the frame. The interactive item is this <Picture 4> device, held by a single operator's hand and aimed at the character; it is the ONLY new object in the frame besides the character's body; the character never wears, holds or touches it. <Picture 5> is the optional SCENE reference — if a scene image is provided, the whole transformation happens inside the environment from <Picture 5>: background, architecture, props, lighting, color tone and atmosphere must come EXACTLY from <Picture 5>, DO NOT replace with a neutral space, DO NOT generate a new background. If no scene image is provided, the environment/background from <Picture 1> is preserved. 本提示词中 <Picture 1> 是人物参考（面部/发型/体型/身份/初始服装严格保持，全程为同一个真实人物，不得复制或拆分为多个）；<Picture 2> 是第 1 套目标服装（首次换装后穿这套，版型/颜色/花纹/材质细节必须完全来自图2，不得自创）；<Picture 3> 是第 2 套目标服装（第二次换装后穿这套，版型/颜色/花纹/材质细节必须完全来自图3，不得自创；视频结束前人物穿图3）；<Picture 4> 是互动媒介设备参考（可为眼镜/手机/镜子/手环/扇子/魔杖等任一手持道具，类型/型号/外形/颜色/细节全程不变，画面中唯一互动道具，由操作者之手拿入并对准人物，人物全程不得佩戴/手持/接触）；<Picture 5> 是可选场景参考（提供则全片在该场景内完成；未提供则沿用图1背景）。

For the target video, at 0.00 seconds into the target video, <Picture 1> (from [Shot 1]) is fully referenced as the character wearing her initial outfit from <Picture 1>. STRICT REFERENCE COMPLIANCE: the character's exact facial identity, hairstyle, body proportions AND initial outfit must be preserved EXACTLY throughout the entire video — no alteration, replacement or redesign. <Picture 2> must be worn after the FIRST magical change. <Picture 3> must be worn after the SECOND magical change and is the final outfit at the end of the video. <Picture 4> device is the only interactive prop and stays exactly that device throughout; the operator's hand brings it in twice (once for each transformation) and later removes it. The environment/background comes from the scene reference <Picture 5> when provided (background, architecture, props, lighting, color tone and atmosphere EXACTLY as the scene reference), otherwise the environment/background from <Picture 1> is preserved.

integrated_multimodal_description:  [Shot 1] [0-8s] Live-action, cinematic, medium shot. Frame A — opening frame: ONLY the character from <Picture 1> is alone in the scene from <Picture 5> (or inside the <Picture 1> background if no scene is provided). The character adapts posture to the scene — SITTING if the scene has somewhere natural to sit (a chair, sofa, bed, step, stone, railing, box, etc.), otherwise STANDING naturally. The character wears the INITIAL outfit from <Picture 1>. The character's gaze is directed elsewhere in the scene, NOT looking at the camera, expression calm and natural. No other person, no other object, no duplicates. 【ACTION — DUAL TRANSFORMATION / 双重魔法换装 / 0-8s timeline】

Step 0 — [0.0-1.6s] 互动媒介第 1 次入画 (Interactive device enters for the 1st time): a single operator's hand enters from the frame edge holding the <Picture 4> device itself (the hand and the device are partially visible at the frame edge); the device is aimed at the <Picture 1> character; the device is the ONLY new object in the frame. The character remains in her initial <Picture 1> outfit, still not looking at the camera, unaware of the device. DO NOT add a second operator, DO NOT add a second device.

Step 1 — [1.6-2.2s] 手指第 1 次触发 (Finger triggers 1st time): the operator's finger presses the device's button / taps the screen / touches the frame edge or lens, triggering the device — it lights up with magic light (warm cyan, magenta or golden glow depending on the device's color). The character still wears the initial <Picture 1> outfit and does not yet notice.

Step 2 — [2.2-3.4s] 第 1 次魔法换装发生在人物身上 (FIRST magical wardrobe change on the character): a swirl of sparkling magical particles erupts from the device and sweeps over the character's whole body; the character's original <Picture 1> outfit dissolves into magical light and particles, then reforms into the <Picture 2> outfit, fitting the body naturally. During this, the character is still looking elsewhere in the scene, NOT at the camera, unaware. There is NO cut, NO camera change, NO scene change — the same single medium shot continues. There is exactly ONE character, never two.

Step 3 — [3.4-4.0s] 人物发现首次换装 + 第一次惊讶 (Character notices 1st change + first surprise): the character looks down at her own body, suddenly realizing the outfit has changed — a clear SURPRISED expression and reaction: eyes widen, eyebrows rise, mouth slightly open in surprise, accompanied by a small startle (slight head jerk, shoulders lift, hands lift a little) — facial identity unchanged, only the expression and body language change; the character still does NOT look at the camera. The character is now wearing the <Picture 2> outfit.

Step 4 — [4.0-4.4s] 互动媒介暂时离开画面 (Device temporarily leaves): the operator's hand pulls the <Picture 4> device out of the frame; the device is completely gone from the frame. The character stands/sits wearing <Picture 2>. No device, no other object.

Step 5 — [4.4-5.4s] 互动媒介第 2 次入画 (Interactive device enters for the 2nd time): the SAME operator's hand (same skin tone, same sleeve) re-enters from the frame edge holding the SAME <Picture 4> device; the device is aimed at the character again. The character reacts with a confused second look (eyebrows knit briefly, slight head tilt) because the device is back, but still does not look at the camera.

Step 6 — [5.4-6.0s] 手指第 2 次触发 (Finger triggers 2nd time): the operator's finger presses the same button / same screen / same frame edge; the device lights up with the same magic glow as Step 1.

Step 7 — [6.0-7.0s] 第 2 次魔法换装发生在人物身上 (SECOND magical wardrobe change on the character): another swirl of sparkling magical particles erupts from the device and sweeps over the character's whole body; the character's <Picture 2> outfit dissolves into magical light and particles, then reforms into the <Picture 3> outfit, fitting the body naturally. The character is now wearing <Picture 3>. There is NO cut, NO camera change. There is exactly ONE character.

Step 8 — [7.0-7.4s] 人物发现再次换装 + 第二次惊讶+惊喜 (Character notices 2nd change + second surprise + joy): the character looks down at her own body and realizes the outfit has changed AGAIN — bigger surprised + happy expression: eyes widen bigger, eyebrows rise, mouth opens, then a delighted smile spreads, accompanied by a small laugh-like body shake.

Step 9 — [7.4-7.7s] 互动媒介完全离开画面 (Device finally leaves): the operator's hand pulls the <Picture 4> device out of the frame; the device is completely gone.

Step 10 — [7.7-8.0s] 站立+开心原地旋转一周展示最终服装 (Stand up + happy in-place 360° spin to show the FINAL <Picture 3> outfit): if the character was sitting, she stands up; then she performs a happy in-place 360° spin to show the new <Picture 3> outfit from front, side and back; the motion is smooth, clean, and joyful. The video ends with the character smiling, facing the camera (only at the very end of the spin), wearing the <Picture 3> outfit. 【/ACTION】

[硬约束] 1. 严格遵循医学/图谱事实……不适用——以下为视频硬约束。 [Hard constraints / 硬约束] 1. Same single character throughout — face, hairstyle, body, identity unchanged; only the clothes change. There is exactly ONE person on screen at all times; no duplicates, no clones, no second operator's second face visible. 2. Pre-change wear <Picture 1>'s initial outfit, after 1st change wear <Picture 2>'s outfit, after 2nd change wear <Picture 3>'s outfit; never self-invent any clothing. 3. <Picture 4> device appears only in [0-4.4s] and [4.4-7.7s]; it is the ONLY device of any kind that ever appears; after Step 9 the device is completely gone. 4. The character never wears / holds / touches the device — it is always held by the operator's hand. 5. Gaze rule: throughout the 8 seconds, the character NEVER looks at the camera UNTIL the very end of the spin (Step 10) when the character may smile at the camera; otherwise gaze is directed at the scene or the outfit. 6. Showcase rule: must be "stand up (if was sitting) + happy in-place 360° spin" to display the new <Picture 3> outfit — no half-hearted turn or short walk. 7. NO camera cut, NO scene change, NO shot change — a single continuous medium shot from 0s to 8s. 8. Subject identity continuity: the character in the second half is the SAME person as the first half — same face, same hairstyle, same body proportions; only her clothes differ. 9. The two magical transformations are visually distinct: the first one dissolves <Picture 1>'s outfit into particles, the second one dissolves <Picture 2>'s outfit into particles; the character is wearing the appropriate outfit during each phase.

overall_soundscape: Soft magical chime when the device lights up (twice), airy whoosh and sparkling shimmer during each transformation, a soft surprised gasp after the 1st change, a bigger surprised gasp + soft delighted laugh after the 2nd change, gentle fabric rustle, ambient room tone. 整个视频全程有清晰可辨的 2 次魔法音效：第 1 次较轻，第 2 次更华丽。
non_diegetic_music: A stylish tech-fashion track — light synth pulse with sparkling accents, building once for the 1st transformation and then to a larger, more confident reveal at the 2nd transformation, ending on a strong confident hit."""

NEW_FB = """[STRICT DEFAULT CONFIG / 默认配置声明]: No reference images are connected for this wardrobe template — the video uses the built-in default character and 2 default outfits, running in TEXT-TO-VIDEO mode. DEFAULT CHARACTER: a young woman in her mid-20s, delicate facial features, long black hair, slender well-proportioned figure. DEFAULT OUTFIT 1 (initial / 图1): a relaxed everyday casual look — a soft white cotton t-shirt and high-waisted blue jeans with white sneakers. DEFAULT OUTFIT 2 (first target / 图2): a fitted navy-blue blazer over a beige silk blouse with a black pencil skirt and black low heels — office/business look. DEFAULT OUTFIT 3 (second target / 图3, FINAL OUTFIT worn at end): an elegant floor-length black evening gown with a flowing skirt, slim waist, subtle sheen fabric, and a pair of silver high-heeled sandals — gala/evening look. DEFAULT DEVICE: a sleek smart holographic wristband worn on the operator's left wrist with a glowing blue display. 未连接任何参考图，本模板启用内置默认配置并转为文生视频模式：默认人物=年轻女性（黑色长发、五官精致、身材匀称），默认初始服装=白色 T 恤+高腰蓝牛仔裤+白色运动鞋，第 1 套目标服装=藏青西装外套+米色真丝衬衫+黑色铅笔裙+黑色低跟（商务装），第 2 套目标服装=黑色长款晚礼服+银色高跟凉鞋（晚宴装，终态），默认设备=智能全息手环（蓝色发光屏）。整个视频人物外貌身份全程保持一致；按时间轴完成 2 次连续魔法换装，最终穿第 2 套目标服装。

integrated_multimodal_description:  [Shot 1] [0-8s] Live-action, cinematic, medium shot. Single continuous shot, NO cut. The character is one single real person who never duplicates. 【ACTION / 双重魔法换装】Step 0 [0.0-1.6s]: an operator's hand enters from the frame edge holding a holographic wristband; it is the ONLY new object; the character is alone in a soft-lit neutral studio space wearing a white t-shirt + blue jeans + white sneakers, sitting on a chair (or standing if the scene has nowhere to sit), gaze off-camera. Step 1 [1.6-2.2s]: the operator's finger presses the wristband's screen; it lights up with blue magic glow. Step 2 [2.2-3.4s]: sparkling blue particles sweep over the character; the white t-shirt + jeans dissolve into light and reform into a navy blazer + beige blouse + black pencil skirt; character is still looking off-camera, unaware. Step 3 [3.4-4.0s]: the character looks down, sees the new outfit — eyes widen, eyebrows rise, mouth slightly open in surprise; still not looking at the camera. Step 4 [4.0-4.4s]: the operator's hand pulls the wristband out of the frame. Step 5 [4.4-5.4s]: the same hand re-enters holding the same wristband; character reacts with a slight confused look. Step 6 [5.4-6.0s]: the operator's finger presses the wristband again; it lights up. Step 7 [6.0-7.0s]: sparkling particles sweep over the character; the navy blazer outfit dissolves into light and reform into a floor-length black evening gown + silver heels; character is now in the 3rd outfit. Step 8 [7.0-7.4s]: the character looks down, sees another change — bigger surprise + delighted smile, soft laugh. Step 9 [7.4-7.7s]: the operator's hand pulls the wristband out of the frame. Step 10 [7.7-8.0s]: the character stands up (if was sitting) and performs a happy in-place 360° spin to show the final black evening gown from front, side, and back, smiling at the camera only at the very end of the spin. 【/ACTION】 The face, hairstyle, and body proportions remain identical throughout; the character is one single person who never duplicates; clean magical effects, no distortion, no extra limbs, no second character.

overall_soundscape: Soft magical chime when the wristband lights up (twice), airy whoosh and sparkling shimmer during each transformation, a soft surprised gasp after the 1st change, a bigger surprised gasp + soft delighted laugh after the 2nd change, gentle fabric rustle, ambient room tone. 2 段清晰可辨的魔法音效。
non_diegetic_music: A stylish tech-fashion track — light synth pulse with sparkling accents, building once for the 1st transformation and then to a larger, more confident reveal at the 2nd transformation, ending on a strong confident hit."""


def patch(fp):
    with open(fp, "r", encoding="utf-8") as f:
        d = json.load(f)
    patched = 0
    for cat in d["categories"]:
        if cat.get("id") == "xray_scan":
            continue
        for sub in cat.get("subcategories", []):
            for t in sub.get("templates", []):
                if t.get("id") == "magic_mediator_wardrobe_change":
                    # Update description + prompt + text_fallback_prompt
                    new_desc = (
                        "【3 套衣服版】多图参考+可选场景图，参考图输入顺序与编号："
                        "图1=人物（必选，全程同一个人，2 次换装不复制不拆分）；"
                        "图2=第 1 套目标服装（首次换装后穿）；"
                        "图3=第 2 套目标服装（二次换装后穿，**视频终态穿图3**）；"
                        "图4=互动媒介设备（必选，眼镜/手机/镜子/手环/扇子/魔杖等任一手持道具，全程同一台）；"
                        "图5=场景（可选）。"
                        "通用版：8 秒单镜头分两段连续换装——"
                        "[0-1.6s] 图1人物独自在场景内，姿态按场景自适应（场景里有可坐之处就坐着，没有就站着），视线不看镜头；"
                        "[1.6-2.2s] 操作者手从画面边缘伸入，手里拿图4设备对准图1人物，手指按下按钮/触碰屏幕/边框，设备亮起魔法光；"
                        "[2.2-3.4s] 第 1 次魔法换装：粒子从设备喷出扫过图1全身，图1的初始衣服化作光粒消散，再凝聚为图2衣服，期间人物仍不看镜头无察觉；"
                        "[3.4-4.0s] 人物低头发现首次换装，表现出惊讶（眼睛睁大/眉毛抬起/嘴微张+轻微惊跳），仍不看镜头；"
                        "[4.0-4.4s] 图4设备完全移出画面；"
                        "[4.4-5.4s] 同一只手持同一台图4设备再次入画对准人物，人物出现困惑表情；"
                        "[5.4-6.0s] 手指再次触发，设备再次亮起；"
                        "[6.0-7.0s] 第 2 次魔法换装：图2衣服化作光粒消散，再凝聚为图3衣服；"
                        "[7.0-7.4s] 人物发现再次换装，表现出更大的惊讶+惊喜+轻笑；"
                        "[7.4-7.7s] 图4设备完全移出画面；"
                        "[7.7-8.0s] 人物起身（坐着时）+ 开心原地旋转一周展示图3终态衣服。画面中只允许出现图4这一台设备，人物全程不佩戴/手持/接触设备，2 次换装为同一人物同一镜头无剪辑。"
                    )
                    t["description"] = new_desc
                    t["prompt"] = NEW_PROMPT
                    t["text_fallback_prompt"] = NEW_FB
                    t["generation_mode"] = (
                        "Reference to Video (参考生视频)【图1人物+图2第1套服装+图3第2套服装+图4媒介+图5场景可选】"
                    )
                    # Update tags
                    new_tags = [
                        "换装", "变装", "多图", "媒介", "手机", "眼镜", "镜子", "魔法",
                        "场景", "多图参考", "双重换装", "3套衣服", "8秒", "单镜头"
                    ]
                    t["tags"] = new_tags
                    patched += 1
    with open(fp, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    print(f"  patched {patched} template(s) in {fp}")


if __name__ == "__main__":
    for p in [
        r"C:\BSAI\ComfyUI-BSAI_pro_v39\ComfyUI\custom_nodes\BSAI-MiniMAX-H3-Prompt\templates\prompt_templates.json",
        r"C:\BSAI\ComfyUI-BSAI_pro_v39\ComfyUI\custom_nodes\BSAI-MiniMAX-H3-Prompt\web\templates_data.json",
    ]:
        patch(p)
