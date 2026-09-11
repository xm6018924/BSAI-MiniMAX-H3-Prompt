#!/usr/bin/env python3
"""Test actual output of wardrobe templates."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from BSAI_H3_PromptTemplate import BSAI_H3_PromptTemplate, _find_template, _merge_template_prompts

node = BSAI_H3_PromptTemplate()

# Test 1: Single template without ref images
print("="*60)
print("TEST 1: 单套换装·魔法媒介触发 (no ref images)")
print("="*60)
result = node.get_template("换装穿衣 | Wardrobe Change > 换装变装类 > 单套换装·魔法媒介触发")
prompt = result[0]
print(f"Output length: {len(prompt)}")
print(f"Contains 'hair ribbon': {'hair ribbon' in prompt.lower()}")
print(f"Contains 'hair scrunchie': {'hair scrunchie' in prompt.lower()}")
print(f"First 300 chars:\n{prompt[:300]}")
print()

# Test 2: With ref images (simulated)
print("="*60)
print("TEST 2: 单套换装·魔法媒介触发 (with ref_image_1 and ref_image_2)")
print("="*60)
# Simulate ref images by passing non-None values
result2 = node.get_template(
    "换装穿衣 | Wardrobe Change > 换装变装类 > 单套换装·魔法媒介触发",
    ref_image_1="fake_img_1",
    ref_image_2="fake_img_2",
)
prompt2 = result2[0]
print(f"Output length: {len(prompt2)}")
print(f"Contains 'hair ribbon': {'hair ribbon' in prompt2.lower()}")
print(f"Contains 'hair scrunchie': {'hair scrunchie' in prompt2.lower()}")
print(f"Contains 'black hair': {'black hair' in prompt2.lower()}")
# Check for repetitive content
if "hair ribbon" in prompt2.lower():
    count = prompt2.lower().count("hair ribbon")
    print(f"'hair ribbon' appears {count} times")
print(f"First 300 chars:\n{prompt2[:300]}")
print()

# Test 3: With external_prompt
print("="*60)
print("TEST 3: 单套换装·魔法媒介触发 (with external_prompt)")
print("="*60)
result3 = node.get_template(
    "换装穿衣 | Wardrobe Change > 换装变装类 > 单套换装·魔法媒介触发",
    external_prompt="black hair ribbon, black hair scrunchie",
)
prompt3 = result3[0]
print(f"Output length: {len(prompt3)}")
print(f"Contains 'hair ribbon': {'hair ribbon' in prompt3.lower()}")
print(f"'hair ribbon' count: {prompt3.lower().count('hair ribbon')}")
print()

# Test 4: Raw template merge
print("="*60)
print("TEST 4: Raw _merge_template_prompts (no post-processing)")
print("="*60)
tpl = _find_template("换装穿衣 | Wardrobe Change > 换装变装类 > 单套换装·魔法媒介触发")
if tpl:
    raw = _merge_template_prompts([tpl], "")
    print(f"Raw length: {len(raw)}")
    print(f"Contains 'hair ribbon': {'hair ribbon' in raw.lower()}")
    print(f"First 300 chars:\n{raw[:300]}")
