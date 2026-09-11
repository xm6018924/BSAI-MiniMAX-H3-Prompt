#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Test the post-process: crop watermark + add logo + title strip."""
import sys
sys.path.insert(0, r"C:\BSAI\ComfyUI-BSAI_pro_v39\ComfyUI\custom_nodes\BSAI-MiniMAX-H3-Prompt")
from _gen_all import crop_watermark_and_compose
import os

raw = r"C:\BSAI\ComfyUI-BSAI_pro_v39\ComfyUI\custom_nodes\BSAI-MiniMAX-H3-Prompt\test_skeleton.jpg"
out = r"C:\BSAI\ComfyUI-BSAI_pro_v39\ComfyUI\custom_nodes\BSAI-MiniMAX-H3-Prompt\web\previews\med_skeletal_system_male.webp"
ok = crop_watermark_and_compose(raw, out, (90, 180, 255), "male", "skeletal_system")
print("ok" if ok else "fail", "size:", os.path.getsize(out) if os.path.exists(out) else "missing")
