# -*- coding: utf-8 -*-
import av, os, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
src = r"C:\Users\xm204\AppData\Local\Doubao\User Data\Default\.doubao\agent_mode\workspace\.skills\doubao-video-extract\downloads\bilibili_BV1KhEw6vE14_p1_480P.mp4"
outdir = r"C:\BSAI\ComfyUI-BSAI_pro_v39\ComfyUI\custom_nodes\BSAI-MiniMAX-H3-Prompt\_evidence\ep04"
c = av.open(src)
vs = c.streams.video[0]
print("duration:", float(vs.duration*vs.time_base) if vs.duration else '?', "frames:", vs.frames, "avg_rate:", float(vs.average_rate))
last_t = -1
idx = 0
save_every = 1.0  # seconds
next_save = 0.0
for frame in c.decode(video=0):
    t = float(frame.time)
    if t >= next_save:
        img = frame.to_image()
        p = os.path.join(outdir, f"seq_{int(t):03d}.jpg")
        img.save(p, quality=70)
        print("t=",round(t,1),"saved", os.path.basename(p))
        next_save += save_every
