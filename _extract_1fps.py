# -*- coding: utf-8 -*-
"""顺序抽帧：每秒1帧，保存到 outdir。用法: python _extract_1fps.py <video_path> <outdir>"""
import av, os, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
src, outdir = sys.argv[1], sys.argv[2]
os.makedirs(outdir, exist_ok=True)
c = av.open(src)
vs = c.streams.video[0]
print("duration_s:", round(float(vs.duration*vs.time_base),1) if vs.duration else '?')
next_save = 0.0
for frame in c.decode(video=0):
    t = float(frame.time)
    if t >= next_save:
        frame.to_image().save(os.path.join(outdir, f"t{int(t):03d}.jpg"), quality=72)
        next_save += 1.0
print("done, frames in", outdir)
