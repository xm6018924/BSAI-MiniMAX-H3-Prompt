#!/usr/bin/env python3
"""Verify wardrobe templates output correctly with ref images."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from BSAI_H3_PromptTemplate import BSAI_H3_PromptTemplate, _find_template

node = BSAI_H3_PromptTemplate()

templates_to_test = [
    "换装穿衣 | Wardrobe Change > 换装变装类 > 魔法换装变装",
    "换装穿衣 | Wardrobe Change > 换装变装类 > 换装穿衣",
    "换装穿衣 | Wardrobe Change > 换装变装类 > 多图换装·魔法媒介触发",
    "换装穿衣 | Wardrobe Change > 换装变装类 > 单套换装·魔法媒介触发",
    "换装穿衣 | Wardrobe Change > 换装变装类 > 多套换装·魔法媒介触发",
    "变装转场 > 卡点硬切换装 > 首尾帧丝滑卡点换装",
    "变装转场 > 卡点硬切换装 > 虚拟试衣硬切换装",
    "变装转场 > 卡点硬切换装 > 动作锚点瞬移换装",
    "变装转场 > 丝滑过渡换装 > 转身推镜无缝换装",
    "变装转场 > 丝滑过渡换装 > 手掌擦镜转场",
    "变装转场 > 丝滑过渡换装 > 时代穿越换装",
    "变装转场 > 丝滑过渡换装 > 四季/日转夜换装延时",
]

ok = 0
fail = 0
fail_details = []

for label in templates_to_test:
    # Test without ref images
    r1 = node.get_template(label)
    p1 = r1[0]
    # Test with 2 ref images
    r2 = node.get_template(label, ref_image_1="fake1", ref_image_2="fake2")
    p2 = r2[0]

    issues = []
    if "hair ribbon" in p1.lower() or "hair scrunchie" in p1.lower():
        issues.append("NO-REF: contains hair ribbon garbage")
    if "hair ribbon" in p2.lower() or "hair scrunchie" in p2.lower():
        issues.append("WITH-REF: contains hair ribbon garbage")
    if not p1.strip():
        issues.append("NO-REF: empty output")
    if not p2.strip():
        issues.append("WITH-REF: empty output")
    # Check ref image mandate is present when refs are connected
    if "fake1" != "fake1":  # always true, just to check
        pass
    if "ABSOLUTE REFERENCE MANDATE" not in p2 and "fake1" == "fake1":
        # Text-only templates (动作锚点瞬移换装) don't have ref mandate - that's OK
        if "动作锚点" not in label and "瞬移" not in label:
            issues.append("WITH-REF: missing ABSOLUTE REFERENCE MANDATE")

    if issues:
        fail += 1
        fail_details.append((label, issues))
    else:
        ok += 1
        print(f"OK: {label} (no-ref: {len(p1)} chars, with-ref: {len(p2)} chars)")

print(f"\n{'='*60}")
print(f"Results: {ok} OK, {fail} Failed out of {len(templates_to_test)}")
if fail_details:
    for label, issues in fail_details:
        print(f"FAILED: {label}")
        for issue in issues:
            print(f"  - {issue}")
else:
    print("ALL TEMPLATES PASS")

# Also test _is_repetitive_garbage
print(f"\n{'='*60}")
print("Testing _is_repetitive_garbage:")
from h3_direct_llm import _is_repetitive_garbage
garbage = "black hair ribbon, black hair scrunchie, black hair tie, black hair barrette, black hair comb, black hair pick, black hair brush, black hair iron, black hair dryer, black hair curler, black hair straightener, black hair clip, black hair bow, black hair band, black hair ribbon, black hair scrunchie, black hair tie, black hair barrette, black hair comb, black hair pick, black hair brush, black hair iron, black hair dryer, black hair curler, black hair straightener"
print(f"Garbage detected: {_is_repetitive_garbage(garbage)}")
clean = "integrated_multimodal_description: A cinematic scene with a character walking through a park.\noverall_soundscape: birdsong and gentle breeze.\nnon_diegetic_music: soft piano."
print(f"Clean text detected as garbage: {_is_repetitive_garbage(clean)}")
