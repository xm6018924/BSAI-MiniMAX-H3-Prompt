#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Step 1: Restore magic_mediator_wardrobe_change to its original (single-outfit) form.
Step 2: Add two new templates — single-outfit variant and multi-outfit variant.

Layout for both new templates:
  <Picture 1> = CHARACTER (always fixed position)
  <Picture 2> = INTERACTIVE MEDIATOR DEVICE (always fixed position)
  <Picture 3> = OUTFIT #1 (the rest of the slots are outfits, in order)
  ...
  <Picture N> = OUTFIT #(N-2)
  <Picture (N+1)> = SCENE (always the LAST slot)
"""
import json
from collections import OrderedDict

# ============== 1. Restore the original single-outfit magic_mediator_wardrobe_change ==============

ORIGINAL_PROMPT = """[STRICT MULTI-REFERENCE COMPLIANCE / 严格多参考声明]: EVERY <Picture N> referenced in this prompt is an independent reference and MUST be strictly followed. <Picture 1> is the CHARACTER reference — face, hairstyle, body proportions, identity AND initial outfit must be preserved EXACTLY throughout the whole video. <Picture 2> is the OUTFIT reference — after the magic change, the character MUST wear exactly this outfit; the garment's cut, color, pattern, fabric texture and every detail must come EXACTLY from <Picture 2>; never self-invent any clothing. <Picture 3> is the INTERACTIVE MEDIATOR DEVICE reference — the device must match <Picture 3>'s exact type, model, shape, color and details, and it MUST stay exactly that device for the whole video: if <Picture 3> shows eyeglasses, the device in the video is those very eyeglasses and nothing else — the device type never changes and no other device of any kind ever appears anywhere in the frame. The interactive item is this <Picture 3> device, held by a single operator's hand and aimed at the character; it is the ONLY new object in the frame; the character never wears, holds or touches it. <Picture 4> is the optional SCENE reference — if a scene image is provided, the whole transformation happens inside the environment from <Picture 4>: background, architecture, props, lighting, color tone and atmosphere must come EXACTLY from <Picture 4>, DO NOT replace with a neutral space, DO NOT generate a new background. If no scene image is provided, the environment/background from <Picture 1> is preserved. 本提示词中 <Picture 1> 是人物参考（面部/发型/体型/身份/初始服装严格保持，不得改变），<Picture 2> 是服装参考（版型/颜色/花纹/材质细节必须完全来自服装图）。互动物品为 <Picture 3> 的媒介设备（其类型/型号/外形/颜色/细节必须与图3完全一致且全程不变：图3是眼镜就一直是那副眼镜，设备类型绝不改变，画面绝不出现任何其他设备）。设备由画面中唯一的一只手持入并对准人物，人物全程不得佩戴/手持/接触该设备。若提供场景图，换装全过程发生在该场景内（背景/建筑/道具/灯光/色调/氛围完全来自场景图）；未提供则保持 <Picture 1> 的背景。\n\nFor the target video, at 0.00 seconds into the target video, <Picture 1> (from [Shot 1]) is fully referenced as the character. STRICT REFERENCE COMPLIANCE: the character's exact facial identity, hairstyle, body proportions and initial outfit must be preserved EXACTLY throughout the entire video — no alteration, replacement or redesign. <Picture 2>'s exact cut, color, pattern and fabric texture must be preserved — no substitution, no redesign. The environment/background from <Picture 1> is preserved.\n\nintegrated_multimodal_description:  [Shot 1] [0-8s] Live-action, cinematic. Medium shot. The character from <Picture 1> stands or sits in the scene; the background comes from <Picture 1>. 【ACTION】The operator's hand enters the frame from the edge holding the <Picture 3> device (eyeglasses, phone, mirror, wristband, fan, wand, etc.) and aims it at the character; the device is the ONLY new object. The operator's finger presses the device's button / touches the screen / frame edge or lens; the device lights up with magic light. A swirl of sparkling magical particles erupts from the device and sweeps over the character's whole body; the original clothes dissolve into magical light and particles, then reform into the <Picture 2> outfit, fitting the body naturally. The character is still looking elsewhere, NOT at the camera, unaware. The character looks down at the body, suddenly realizing the outfit has changed — eyes widen, eyebrows rise, mouth slightly open in surprise; facial identity unchanged, only the expression changes; the character still does NOT look at the camera. The operator's hand pulls the device out of the frame. A delighted smile spreads; the character stands up (if was sitting) and performs a happy in-place 360° spin to show the new <Picture 2> outfit from front, side and back. 【/ACTION】 Clean magical glow, no distortion, no extra limbs, no duplicated figure, no second object.\n\noverall_soundscape: Soft electronic chime as the device lights up, airy whoosh and sparkling shimmer during the magical transformation, a soft surprised gasp from the character, gentle fabric rustle, subtle room tone.\n\nnon_diegetic_music: A stylish fashion track — light synth pulse with sparkling accents, building to a confident reveal, ending on a delighted hit."""

ORIGINAL_FB = """[STRICT DEFAULT CONFIG / 默认配置声明]: 未连接参考图，本模板启用内置默认配置。 DEFAULT CHARACTER: a young woman in her mid-20s, delicate facial features, long black hair, slender well-proportioned figure. DEFAULT OUTFIT: an elegant black evening gown with a flowing skirt, slim waist and subtle sheen fabric. DEFAULT DEVICE: a sleek smart holographic wristband worn on her left wrist with a glowing blue display. 本模板运行于文生视频模式，使用内置默认配置。\n\nintegrated_multimodal_description:  [Shot 1] [0-8s] Live-action, cinematic, medium shot. Frame A — opening frame: ONLY the default character stands alone in a soft-lit neutral studio space with a subtle gradient backdrop — no other objects. 【ACTION】Step 1 — 互动物品入画: a holographic wardrobe slides gently into the scene beside her (the ONLY new object in the frame). Step 2 — 触摸触发: the item is touched on its button or frame edge; it glows with magic light. Step 3 — 魔法换装直接在人物身上发生: a swirl of sparkling magical particles sweeps over her whole body; the original clothes dissolve into magical light and particles, then reform into the elegant black evening gown — she does NOT notice yet, eyes lowered. Step 4 — 换装完成，人物才发现: she looks down at the gown, suddenly realizing it was changed — amazed expression: eyes widen, eyebrows rise, mouth slightly open in surprise. Step 5 — 互动物品移出画面: the item leaves the frame (fades out or is lowered away). Step 6 — 人物开心展示: a delighted smile spreads; she turns slowly, showing the gown from the front and the side with joy. 【/ACTION】 The face, hairstyle, figure and the default black evening gown remain consistent throughout; clean effects, no distortion, no extra limbs, no duplicated figure.\n\noverall_soundscape: Soft magical chime as the item glows, airy whoosh and sparkling shimmer during the transformation, a soft gasp of surprise, gentle fabric rustle, subtle room tone.\n\nnon_diegetic_music: A stylish fashion track — light synth pulse with sparkling accents, building to a confident reveal, ending on a delighted hit."""

ORIGINAL_DESC = (
    "单套服装换装·魔法媒介触发：参考图输入顺序与编号——"
    "图1=人物（必选，全程同一个人，初始服装由图1决定）；"
    "图2=目标服装（必选，换装后穿这套，版型/颜色/花纹完全照图2）；"
    "图3=互动媒介设备（必选，眼镜/手机/镜子/手环/扇子/魔杖等任一手持道具，全程同一台）；"
    "图4=场景（可选，按图4布置）。"
    "8 秒单镜头：图1人物在场景内（场景里有可坐之处就坐着，没有就站着），视线不看镜头；"
    "图3设备由操作者手持入画对准图1人物，手指按下按钮/触碰屏幕或边框后魔法换装直接上身；"
    "图1人物突然发现换装表现出惊讶（仍不看镜头）；"
    "图3设备完全移出画面后，图1人物起身+开心原地旋转一周展示图2新衣服。"
    "画面中只允许出现图3这一台设备，人物全程不佩戴/手持/接触设备。"
)

# ============== 2. Build SINGLE-OUTFIT template ==============

SINGLE_PROMPT = """[STRICT MULTI-REFERENCE COMPLIANCE / 严格多参考声明]: EVERY <Picture N> referenced in this prompt is an independent reference and MUST be strictly followed. The reference image slots are FIXED in this order: <Picture 1> is the CHARACTER reference, <Picture 2> is the INTERACTIVE MEDIATOR DEVICE reference, <Picture 3> is the OUTFIT reference, and the LAST picture slot is the optional SCENE reference. <Picture 1> is the CHARACTER reference — face, hairstyle, body proportions, identity AND initial outfit must be preserved EXACTLY throughout the whole video; the character is one single real person who never duplicates or splits into multiple figures. <Picture 2> is the INTERACTIVE MEDIATOR DEVICE reference — it can be eyeglasses / a phone / a mirror / a wristband / a fan / a wand / any hand-held prop; the device in the video must match <Picture 2>'s exact type, model, shape, color and details and stay exactly that device for the whole video; the device type never changes and NO other device of any kind ever appears anywhere in the frame. The interactive item is this <Picture 2> device, held by a single operator's hand and aimed at the character; it is the ONLY new object in the frame besides the character's body; the character never wears, holds or touches it. <Picture 3> is the OUTFIT reference — after the magic change, the character MUST wear exactly this outfit; the garment's cut, color, pattern, fabric texture and every detail must come EXACTLY from <Picture 3>; never self-invent any clothing. The LAST picture slot is the optional SCENE reference — if a scene image is provided, the whole transformation happens inside the environment from that picture: background, architecture, props, lighting, color tone and atmosphere must come EXACTLY from it, DO NOT replace with a neutral space, DO NOT generate a new background. If no scene image is provided, the environment/background from <Picture 1> is preserved. 本提示词中参考图顺序固定：<Picture 1> 人物（面部/发型/体型/身份/初始服装严格保持，全程为同一个真实人物，不得复制或拆分）；<Picture 2> 互动媒介设备（可为眼镜/手机/镜子/手环/扇子/魔杖等任一手持道具，类型/型号/外形/颜色/细节全程不变，画面中唯一互动道具，由操作者之手拿入并对准人物，人物全程不得佩戴/手持/接触）；<Picture 3> 目标服装（换装后必须严格按图3穿着，不得自创）；最后一图是可选场景参考（提供则全片在该场景内完成；未提供则沿用图1背景）。

For the target video, at 0.00 seconds into the target video, <Picture 1> is fully referenced as the character wearing her initial outfit. STRICT REFERENCE COMPLIANCE: the character's exact facial identity, hairstyle, body proportions AND initial outfit must be preserved EXACTLY throughout the entire video — no alteration, replacement or redesign. <Picture 2> device is the only interactive prop and stays exactly that device throughout; the operator's hand brings it in, aims it at the character, and later removes it. <Picture 3>'s exact cut, color, pattern and fabric texture must be worn after the magic change — no substitution, no redesign. The environment/background comes from the LAST picture slot when provided (background, architecture, props, lighting, color tone and atmosphere EXACTLY as that scene reference), otherwise the environment/background from <Picture 1> is preserved.

integrated_multimodal_description:  [Shot 1] [0-8s] Live-action, cinematic, medium shot. Single continuous shot, NO camera cut, NO scene change. Frame A — opening frame: ONLY the character from <Picture 1> is alone in the LAST picture slot's scene (or inside the <Picture 1> background if no scene slot is provided). The character adapts posture to the scene — SITTING if the scene has somewhere natural to sit (a chair, sofa, bed, step, stone, railing, box, etc.), otherwise STANDING naturally. The character wears the INITIAL outfit from <Picture 1>. The character's gaze is directed elsewhere in the scene, NOT looking at the camera, expression calm and natural. No other person, no other object, no duplicates. 【ACTION】

Step 1 — [0.0-2.0s] 互动媒介入画: a single operator's hand enters from the frame edge holding the <Picture 2> device itself (the hand and the device are partially visible at the frame edge); the device is aimed at the <Picture 1> character; the device is the ONLY new object in the frame. The character remains in her initial <Picture 1> outfit, still not looking at the camera, unaware of the device.

Step 2 — [2.0-2.6s] 手指触发: the operator's finger presses the device's button / taps the screen / touches the frame edge or lens, triggering the device — it lights up with magic light. The character still wears the initial <Picture 1> outfit and does not yet notice.

Step 3 — [2.6-4.2s] 魔法换装直接在人物身上发生: a swirl of sparkling magical particles erupts from the device and sweeps over the character's whole body; the character's original <Picture 1> clothes dissolve into magical light and particles, then reform into the <Picture 3> outfit, fitting the body naturally. During this, the character is still looking elsewhere in the scene, NOT at the camera, unaware. There is NO cut, NO camera change, NO scene change — the same single medium shot continues. There is exactly ONE character, never two.

Step 4 — [4.2-4.8s] 换装完成，人物突然发现: the character looks down at the body, suddenly realizing the clothes have been changed — a clear SURPRISED expression and reaction: eyes widen, eyebrows rise, mouth slightly open in surprise, accompanied by a small startle (slight head jerk, shoulders lift, hands lift a little) — facial identity unchanged, only the expression and body language change; the character still does NOT look at the camera. The character is now wearing the <Picture 3> outfit.

Step 5 — [4.8-5.4s] 互动媒介完全离开画面: the operator's hand pulls the <Picture 2> device out of the frame; the device is completely gone from the frame. The character stands/sits wearing <Picture 3>. No device, no other object.

Step 6 — [5.4-8.0s] 站立+开心原地旋转一周展示新衣服: a delighted smile spreads; if the character was sitting, she stands up; then she performs a happy in-place 360° spin to show the new <Picture 3> outfit from front, side and back; the motion is smooth, clean, and joyful. The video ends with the character smiling at the camera (only at the very end of the spin), wearing the <Picture 3> outfit. 【/ACTION】

[硬约束 / Hard constraints] 1. Same single character throughout — face, hairstyle, body, identity unchanged; only the clothes change. There is exactly ONE person on screen at all times; no duplicates, no clones. 2. Pre-change wear <Picture 1>'s initial outfit, post-change wear <Picture 3>'s outfit; never self-invent clothes. 3. <Picture 2> device appears only in [0-5.4s]; it is the ONLY device of any kind that ever appears; after Step 5 the device is completely gone. 4. The character never wears / holds / touches the device — it is always held by the operator's hand. 5. Gaze rule: throughout the 8 seconds, the character NEVER looks at the camera UNTIL the very end of the spin (Step 6) when the character may smile at the camera; otherwise gaze is directed at the scene or the outfit. 6. Showcase rule: must be "stand up (if was sitting) + happy in-place 360° spin" to display the new <Picture 3> outfit — no half-hearted turn or short walk. 7. NO camera cut, NO scene change, NO shot change — a single continuous medium shot from 0s to 8s. 8. Subject identity continuity: the character at the end is the SAME person as at the start — same face, same hairstyle, same body proportions; only her clothes differ.

overall_soundscape: Soft magical chime when the device lights up, airy whoosh and sparkling shimmer during the transformation, a soft surprised gasp from the character, gentle fabric rustle, ambient scene tone.
non_diegetic_music: A stylish tech-fashion track — light synth pulse with sparkling accents, building to a confident reveal, ending on a strong confident hit."""

SINGLE_FB = """[STRICT DEFAULT CONFIG / 默认配置声明]: No reference images are connected for this wardrobe template — the video uses the built-in default character, default outfit and default device, running in TEXT-TO-VIDEO mode. DEFAULT CHARACTER (图1): a young woman in her mid-20s, delicate facial features, long black hair, slender well-proportioned figure. DEFAULT OUTFIT (图3): an elegant black evening gown with a flowing skirt, slim waist and subtle sheen fabric. DEFAULT DEVICE (图2): a sleek smart holographic wristband worn on the operator's left wrist with a glowing blue display. 本模板运行于文生视频模式，使用内置默认配置。

integrated_multimodal_description:  [0-8s] Live-action, cinematic, medium shot. Single continuous shot. The default character is alone in a soft-lit neutral studio space, sitting on a chair (or standing if no chair), gaze off-camera, wearing a relaxed white t-shirt + blue jeans + white sneakers (initial outfit). 【ACTION】Step 1 [0-2s]: an operator's hand enters from the frame edge holding a glowing holographic wristband; it is the ONLY new object. Step 2 [2-2.6s]: the operator's finger presses the wristband's screen; it lights up. Step 3 [2.6-4.2s]: sparkling blue particles sweep over the character; the t-shirt + jeans dissolve into light and reform into a black evening gown; the character is still looking off-camera, unaware. Step 4 [4.2-4.8s]: the character looks down, sees the change — eyes widen, eyebrows rise, mouth slightly open in surprise; still not looking at the camera. Step 5 [4.8-5.4s]: the operator's hand pulls the wristband out of the frame. Step 6 [5.4-8s]: a delighted smile spreads; the character stands up and performs a happy in-place 360° spin to show the new black evening gown from front, side, and back, smiling at the camera only at the very end of the spin. 【/ACTION】 One single character throughout, no duplicates, no cuts.

overall_soundscape: Soft magical chime when the wristband lights up, airy whoosh and sparkling shimmer, soft surprised gasp, gentle fabric rustle, ambient room tone.
non_diegetic_music: Stylish tech-fashion track, light synth pulse with sparkling accents, building to a confident reveal, ending on a strong confident hit."""

SINGLE_DESC = (
    "单套服装换装·魔法媒介触发：参考图输入顺序与编号固定为——"
    "图1=人物（必选，全程同一个人，初始服装由图1决定）；"
    "图2=互动媒介设备（必选，眼镜/手机/镜子/手环/扇子/魔杖等任一手持道具，全程同一台）；"
    "图3=目标服装（必选，换装后穿这套，版型/颜色/花纹完全照图3）；"
    "图4=场景（可选，最后一张图作场景，按图4布置；未提供则沿用图1背景）。"
    "8 秒单镜头：图1人物在场景内（场景里有可坐之处就坐着，没有就站着），视线不看镜头；"
    "图2设备由操作者手持入画对准图1人物，手指按下按钮/触碰屏幕或边框后魔法换装直接上身；"
    "图1人物突然发现换装表现出惊讶（仍不看镜头）；"
    "图2设备完全移出画面后，图1人物起身+开心原地旋转一周展示图3新衣服。"
    "画面中只允许出现图2这一台设备，人物全程不佩戴/手持/接触设备。"
)

# ============== 3. Build MULTI-OUTFIT template (N outfits, auto-detected) ==============

# Number of outfits: N = (number of reference images) - 3
#   (subtract: 1 character + 1 device + 1 scene = 3 fixed slots)
# This prompt uses PLACEHOLDERS <Picture 3>, <Picture 4>, ..., <Picture (N+2)> for outfits
# and <Picture (N+3)> for the scene.
# The model is told the formula and to iterate over the outfit slots.

MULTI_PROMPT = """[STRICT MULTI-REFERENCE COMPLIANCE / 严格多参考声明]: EVERY <Picture N> referenced in this prompt is an independent reference and MUST be strictly followed. The reference image slots are FIXED in this order: <Picture 1> is the CHARACTER reference, <Picture 2> is the INTERACTIVE MEDIATOR DEVICE reference, <Picture 3> through <Picture (K-1)> are the OUTFIT references in chronological wear order, and the LAST picture slot <Picture K> is the optional SCENE reference. The number of outfit pictures is detected from the user's input — call it M (where M ≥ 2). The total number of reference pictures is K = 1 character + 1 device + M outfits + 1 optional scene (scene may be omitted, in which case K = 1 + 1 + M). So outfit #1 = <Picture 3>, outfit #2 = <Picture 4>, ..., outfit #M = <Picture (M+2)>, and (if provided) the scene = <Picture (M+3)>. <Picture 1> is the CHARACTER reference — face, hairstyle, body proportions, identity AND initial outfit must be preserved EXACTLY throughout the whole video; the character is one single real person who never duplicates or splits into multiple figures. <Picture 2> is the INTERACTIVE MEDIATOR DEVICE reference — it can be eyeglasses / a phone / a mirror / a wristband / a fan / a wand / any hand-held prop; the device in the video must match <Picture 2>'s exact type, model, shape, color and details and stay exactly that device for the whole video; the device type never changes and NO other device of any kind ever appears anywhere in the frame. The interactive item is this <Picture 2> device, held by a single operator's hand and aimed at the character; it is the ONLY new object in the frame besides the character's body; the character never wears, holds or touches it. <Picture 3> ... <Picture (M+2)> are the OUTFIT references in chronological order — the character's outfit transforms sequentially through each one in turn. Outfit #1 (<Picture 3>) is the first target outfit; outfit #M (<Picture (M+2)>) is the FINAL outfit the character wears at the end of the video. For each outfit, the garment's cut, color, pattern, fabric texture and every detail must come EXACTLY from that picture; never self-invent any clothing. The LAST picture slot <Picture K> is the optional SCENE reference — if provided, the whole transformation happens inside the environment from <Picture K>: background, architecture, props, lighting, color tone and atmosphere must come EXACTLY from <Picture K>, DO NOT replace with a neutral space, DO NOT generate a new background. If no scene picture is provided, the environment/background from <Picture 1> is preserved. 本提示词中参考图顺序固定：<Picture 1> 人物（面部/发型/体型/身份/初始服装严格保持，全程为同一个真实人物，不得复制或拆分）；<Picture 2> 互动媒介设备（可为眼镜/手机/镜子/手环/扇子/魔杖等任一手持道具，类型/型号/外形/颜色/细节全程不变，画面中唯一互动道具，由操作者之手拿入并对准人物，人物全程不得佩戴/手持/接触）；<Picture 3> 至 <Picture (M+2)> 为 M 套目标服装（按时间顺序连环换装，第 1 套 = 图3，第 M 套 = 图(M+2)，视频终态穿第 M 套）；<Picture K> 为可选场景参考（提供则全片在该场景内完成；未提供则沿用图1背景）。

For the target video, at 0.00 seconds into the target video, <Picture 1> is fully referenced as the character wearing her initial outfit. STRICT REFERENCE COMPLIANCE: the character's exact facial identity, hairstyle, body proportions AND initial outfit must be preserved EXACTLY throughout the entire video — no alteration, replacement or redesign. <Picture 2> device is the only interactive prop and stays exactly that device throughout; the operator's hand brings it in, aims it at the character, and later removes it after each transformation. The character sequentially wears the M outfits, one at a time, in chronological order: initial outfit (Picture 1) → outfit #1 (Picture 3) → outfit #2 (Picture 4) → ... → outfit #M (Picture M+2). The video ends with the character wearing outfit #M (Picture M+2). The environment/background comes from the LAST picture slot when provided (background, architecture, props, lighting, color tone and atmosphere EXACTLY as that scene reference), otherwise the environment/background from <Picture 1> is preserved.

[CRITICAL TIMING RULE / 时间分配规则] The total video length is 8 seconds. The M transformations must fit into the 8-second timeline. Each transformation cycle (device enters → finger triggers → magical outfit change → character reacts surprised → device leaves) takes ~3.5 seconds, and a small intro (~1s) plus a final spin showcase (~1.5s) frame the whole sequence. For M=2 outfits, use: intro 1.0s + 2 transformation cycles of 3.0s each + final spin 1.0s. For M=3, use: intro 0.8s + 3 cycles of 2.4s each + final spin 0.8s. For M=4 or more, compress each cycle further but always keep: (a) one final spin showcasing outfit #M at the end, and (b) the device ALWAYS leaving the frame between cycles (no overlapping devices). The full 8-second timeline MUST contain exactly M magical outfit changes — no more, no less — and the final outfit at 8.0s MUST be outfit #M.

integrated_multimodal_description:  [Shot 1] [0-8s] Live-action, cinematic, medium shot. Single continuous shot, NO camera cut, NO scene change. Frame A — opening frame: ONLY the character from <Picture 1> is alone in the LAST picture slot's scene (or inside the <Picture 1> background if no scene slot is provided). The character adapts posture to the scene — SITTING if the scene has somewhere natural to sit (a chair, sofa, bed, step, stone, railing, box, etc.), otherwise STANDING naturally. The character wears the INITIAL outfit from <Picture 1>. The character's gaze is directed elsewhere in the scene, NOT looking at the camera, expression calm and natural. No other person, no other object, no duplicates. The M outfit changes happen sequentially inside this single 8-second shot. 【ACTION — M-OUTFIT SEQUENTIAL TRANSFORMATION / M 套服装连环魔法换装】

[INTRO 0-1.0s] 互动媒介第 1 次入画: a single operator's hand enters from the frame edge holding the <Picture 2> device itself (the hand and the device are partially visible at the frame edge); the device is aimed at the <Picture 1> character; the device is the ONLY new object in the frame. The character remains in her initial <Picture 1> outfit, still not looking at the camera, unaware of the device. DO NOT add a second operator, DO NOT add a second device.

[TRANSFORMATION CYCLE i, for i = 1 to M — total ~3.0s per cycle for M=2, ~2.4s per cycle for M=3, scaled shorter for M≥4]

Cycle i — Phase A (手指触发): the operator's finger presses the device's button / taps the screen / touches the frame edge or lens, triggering the device — it lights up with magic light (warm cyan, magenta or golden glow). The character is still wearing the previous outfit and does not yet notice.

Cycle i — Phase B (魔法换装): a swirl of sparkling magical particles erupts from the device and sweeps over the character's whole body; the character's CURRENT outfit dissolves into magical light and particles, then reforms into the OUTFIT #i reference (outfit #1 = <Picture 3>, outfit #2 = <Picture 4>, outfit #3 = <Picture 5>, ..., outfit #M = <Picture (M+2)>), fitting the body naturally. During this, the character is still looking elsewhere in the scene, NOT at the camera, unaware. There is NO cut, NO camera change, NO scene change. There is exactly ONE character, never two.

Cycle i — Phase C (人物发现 + 惊讶): the character looks down at the body, suddenly realizing the outfit has changed — a clear SURPRISED expression and reaction: eyes widen, eyebrows rise, mouth slightly open in surprise, accompanied by a small startle (slight head jerk, shoulders lift, hands lift a little) — facial identity unchanged, only the expression and body language change; the character still does NOT look at the camera. The bigger the cumulative count of transformations already done, the more surprised and excited the reaction (the 1st change is mild surprise, the last change is wide-eyed surprise + delighted smile).

Cycle i — Phase D (互动媒介离开画面) [for cycles 1 to M-1]: the operator's hand pulls the <Picture 2> device out of the frame; the device is completely gone from the frame. The character stands/sits in the new outfit. No device, no other object. The device then re-enters for the next cycle from the frame edge, held by the SAME hand, the SAME device, aimed at the character again — the character reacts with a brief confused second look (slight head tilt) because the device is back, but still does not look at the camera.

[FINAL CYCLE COMPLETION — after cycle M] 互动媒介最终离开画面: the operator's hand pulls the <Picture 2> device out of the frame for the LAST time; the device is completely gone.

[FINAL SHOWCASE 7.4-8.0s] 站立+开心原地旋转一周展示终态服装: a delighted smile spreads; if the character was sitting, she stands up; then she performs a happy in-place 360° spin to show the FINAL outfit (outfit #M) from front, side and back; the motion is smooth, clean, and joyful. The video ends with the character smiling at the camera (only at the very end of the spin), wearing the FINAL outfit. 【/ACTION】

[硬约束 / Hard constraints] 1. Same single character throughout — face, hairstyle, body, identity unchanged; only the clothes change. There is exactly ONE person on screen at all times; no duplicates, no clones, no second operator's second face visible. 2. Outfit sequence is STRICTLY chronological: initial (Picture 1) → outfit #1 (Picture 3) → outfit #2 (Picture 4) → ... → outfit #M (Picture M+2). The character wears exactly one outfit at any time. 3. <Picture 2> device is the ONLY device of any kind that ever appears; it must completely leave the frame between cycles (no overlapping devices on screen). 4. The character never wears / holds / touches the device — it is always held by the operator's hand. 5. Gaze rule: throughout the 8 seconds, the character NEVER looks at the camera UNTIL the very end of the final spin when the character may smile at the camera; otherwise gaze is directed at the scene or the outfit. 6. Showcase rule: must be "stand up (if was sitting) + happy in-place 360° spin" to display the FINAL outfit; no half-hearted turn or short walk. 7. NO camera cut, NO scene change, NO shot change — a single continuous medium shot from 0s to 8s. 8. Subject identity continuity: the character at the end is the SAME person as at the start — same face, same hairstyle, same body proportions; only her clothes differ. 9. The M magical transformations are visually distinct: the i-th transformation dissolves the (i-1)-th outfit into particles and reforms the i-th outfit. 10. The total number of magical outfit changes in the video MUST be exactly M (one per outfit reference), and the final outfit at 8.0s MUST be outfit #M.

overall_soundscape: Soft magical chime when the device lights up (M times, each with a slightly stronger effect for later cycles), airy whoosh and sparkling shimmer during each transformation, a soft surprised gasp after the 1st change, larger surprised gasps + soft delighted laughs for later changes, gentle fabric rustle, ambient scene tone. 整个视频全程有 M 段清晰可辨的魔法音效，每段音效逐渐华丽。
non_diegetic_music: A stylish tech-fashion track — light synth pulse with sparkling accents, building for each transformation and reaching the largest, most confident reveal at the FINAL transformation, ending on a strong confident hit."""

MULTI_FB = """[STRICT DEFAULT CONFIG / 默认配置声明]: No reference images are connected for this wardrobe template — the video uses the built-in default character and M default outfits, running in TEXT-TO-VIDEO mode. M is fixed to 3 by default (when no reference images are provided). DEFAULT CHARACTER (图1): a young woman in her mid-20s, delicate facial features, long black hair, slender well-proportioned figure. DEFAULT INITIAL OUTFIT (图1): a relaxed everyday casual look — a soft white cotton t-shirt and high-waisted blue jeans with white sneakers. DEFAULT OUTFIT #1 (图3): a fitted navy-blue blazer over a beige silk blouse with a black pencil skirt and black low heels — office/business look. DEFAULT OUTFIT #2 (图4): a sleeveless burgundy velvet cocktail dress with gold accessories — party/evening look. DEFAULT OUTFIT #3 (图5, FINAL OUTFIT worn at end): an elegant floor-length black evening gown with a flowing skirt, slim waist, subtle sheen fabric, and a pair of silver high-heeled sandals — gala/evening look. DEFAULT DEVICE (图2): a sleek smart holographic wristband worn on the operator's left wrist with a glowing blue display. 本模板运行于文生视频模式，使用内置默认配置；M 默认 = 3。

integrated_multimodal_description:  [0-8s] Live-action, cinematic, medium shot. Single continuous shot. The default character is alone in a soft-lit neutral studio space, sitting on a chair (or standing if no chair), gaze off-camera, wearing a white t-shirt + blue jeans + white sneakers (initial outfit). 【ACTION — 3-OUTFIT SEQUENTIAL TRANSFORMATION】[INTRO 0-1s]: an operator's hand enters from the frame edge holding a holographic wristband. [Cycle 1: 1-3.4s] the operator's finger presses the wristband; it lights up; sparkling blue particles sweep over the character; the t-shirt + jeans dissolve into light and reform into a navy blazer + beige blouse + black pencil skirt; the character is still looking off-camera, unaware; the operator's hand pulls the wristband out. [Cycle 2: 3.4-5.8s] the same hand re-enters with the same wristband; the character reacts with a slight confused look; the operator's finger presses the wristband again; it lights up; sparkling particles sweep over the character; the blazer outfit dissolves into light and reform into a sleeveless burgundy velvet cocktail dress; the character is surprised and a tiny smile appears. [Cycle 3: 5.8-7.4s] the same hand re-enters with the same wristband; the operator's finger presses it again; sparkling particles sweep over the character; the cocktail dress dissolves into light and reform into a floor-length black evening gown + silver heels; the character shows bigger surprise + a delighted laugh. [FINAL 7.4-7.7s] the operator's hand pulls the wristband out of the frame. [SHOWCASE 7.7-8s] the character stands up and performs a happy in-place 360° spin to show the final black evening gown from front, side, and back, smiling at the camera only at the very end of the spin. 【/ACTION】 One single character throughout, no duplicates, no cuts, exactly 3 magical outfit changes in chronological order; final outfit at 8.0s = the black evening gown.

overall_soundscape: 3 distinct magical chimes when the wristband lights up (each progressively stronger), airy whoosh and sparkling shimmer during each transformation, soft surprised gasps + soft delighted laughs for later changes, gentle fabric rustle, ambient room tone.
non_diegetic_music: Stylish tech-fashion track, light synth pulse with sparkling accents, building for each transformation and reaching the largest, most confident reveal at the final transformation, ending on a strong confident hit."""

MULTI_DESC = (
    "多套服装连环换装·魔法媒介触发：参考图输入顺序与编号固定为——"
    "图1=人物（必选，全程同一个人，初始服装由图1决定）；"
    "图2=互动媒介设备（必选，眼镜/手机/镜子/手环/扇子/魔杖等任一手持道具，全程同一台）；"
    "图3 ... 图(N+2) = N 套目标服装（必选，按时间顺序连环换装，第 1 套=图3，第 N 套=图(N+2)，视频终态穿第 N 套）；"
    "图(N+3) = 场景（可选，最后一张图作场景；未提供则沿用图1背景）。"
    "**服装套数 N 由用户输入的参考图数量自动推断**——"
    "若用户输入 4 张图（无场景），N = 4 - 1(人物) - 1(设备) = 2 套服装；"
    "若用户输入 5 张图（无场景），N = 5 - 1 - 1 = 3 套服装；"
    "若用户输入 6 张图（含 1 张场景），N = 6 - 1 - 1 - 1 = 3 套服装，依此类推。"
    "8 秒单镜头分 N 段连续换装："
    "每段=设备入画→手指触发→魔法粒子扫身→旧衣化光粒消散→新衣凝聚上身→人物发现+惊讶→设备离开画面；"
    "N 段后设备最终离开，人物起身+开心原地旋转一周展示第 N 套终态衣服。"
    "画面中只允许出现图2这一台设备，人物全程不佩戴/手持/接触设备，N 段换装为同一人物同一镜头无剪辑。"
)


def make_tpl(tid, name, name_en, description, preview, generation_mode, duration,
             tags, prompt, text_fallback_prompt, text_fallback_mode):
    return OrderedDict([
        ("id", tid),
        ("name", name),
        ("name_en", name_en),
        ("description", description),
        ("preview", preview),
        ("generation_mode", generation_mode),
        ("duration", duration),
        ("needs_image", True),
        ("needs_video", False),
        ("needs_audio", False),
        ("tags", tags),
        ("prompt", prompt),
        ("text_fallback_prompt", text_fallback_prompt),
        ("text_fallback_mode", text_fallback_mode),
    ])


SINGLE_TPL = make_tpl(
    tid="magic_mediator_wardrobe_single",
    name="单套换装·魔法媒介触发",
    name_en="Single-outfit magic mediator wardrobe change",
    description=SINGLE_DESC,
    preview="magic_mediator_wardrobe_single.webp",
    generation_mode="Reference to Video (参考生视频)【图1人物+图2设备+图3服装+图4场景可选】",
    duration=8,
    tags=["换装", "变装", "单套", "媒介", "手机", "眼镜", "镜子", "魔法", "场景", "多图参考", "8秒", "单镜头"],
    prompt=SINGLE_PROMPT,
    text_fallback_prompt=SINGLE_FB,
    text_fallback_mode="Text to Video (文生视频)【默认人物+默认服装+默认设备】",
)

MULTI_TPL = make_tpl(
    tid="magic_mediator_wardrobe_multi",
    name="多套换装·魔法媒介触发",
    name_en="Multi-outfit magic mediator wardrobe change",
    description=MULTI_DESC,
    preview="magic_mediator_wardrobe_multi.webp",
    generation_mode="Reference to Video (参考生视频)【图1人物+图2设备+图3..图N+2 N套服装+图N+3场景可选】",
    duration=8,
    tags=["换装", "变装", "多套", "媒介", "手机", "眼镜", "镜子", "魔法", "场景", "多图参考", "连环换装", "动态套数", "8秒", "单镜头"],
    prompt=MULTI_PROMPT,
    text_fallback_prompt=MULTI_FB,
    text_fallback_mode="Text to Video (文生视频)【默认3套服装】",
)


def process(fp):
    with open(fp, "r", encoding="utf-8") as f:
        d = json.load(f)
    # Step 1: locate and restore magic_mediator_wardrobe_change
    found_old = None
    target_cat = None
    target_sub = None
    for cat in d["categories"]:
        for sub in cat.get("subcategories", []):
            for t in sub.get("templates", []):
                if t.get("id") == "magic_mediator_wardrobe_change":
                    found_old = t
                    target_cat = cat
                    target_sub = sub
    if found_old is None:
        print(f"  magic_mediator_wardrobe_change not found in {fp}")
        return
    # Restore original
    found_old["description"] = ORIGINAL_DESC
    found_old["prompt"] = ORIGINAL_PROMPT
    found_old["text_fallback_prompt"] = ORIGINAL_FB
    found_old["generation_mode"] = "Reference to Video (参考生视频)【图1人物+图2服装+图3媒介+图4场景可选】"
    found_old["tags"] = ["换装", "变装", "多图", "媒介", "手机", "眼镜", "镜子", "魔法", "场景", "多图参考"]
    found_old["preview"] = "magic_mediator_wardrobe_change.webp"
    print(f"  restored magic_mediator_wardrobe_change in {fp}")

    # Step 2: add single + multi templates to the same subcategory
    existing_ids = [t["id"] for t in target_sub["templates"]]
    if "magic_mediator_wardrobe_single" not in existing_ids:
        target_sub["templates"].append(SINGLE_TPL)
        print(f"  added magic_mediator_wardrobe_single in {fp}")
    else:
        print(f"  magic_mediator_wardrobe_single already present in {fp}")
    if "magic_mediator_wardrobe_multi" not in existing_ids:
        target_sub["templates"].append(MULTI_TPL)
        print(f"  added magic_mediator_wardrobe_multi in {fp}")
    else:
        print(f"  magic_mediator_wardrobe_multi already present in {fp}")

    with open(fp, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    print(f"  saved {fp}")


if __name__ == "__main__":
    for p in [
        r"C:\BSAI\ComfyUI-BSAI_pro_v39\ComfyUI\custom_nodes\BSAI-MiniMAX-H3-Prompt\templates\prompt_templates.json",
        r"C:\BSAI\ComfyUI-BSAI_pro_v39\ComfyUI\custom_nodes\BSAI-MiniMAX-H3-Prompt\web\templates_data.json",
    ]:
        process(p)
