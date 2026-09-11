# -*- coding: utf-8 -*-
import av, os, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
src = r"C:\Users\xm204\AppData\Local\Doubao\User Data\Default\.doubao\agent_mode\workspace\.skills\doubao-video-extract\downloads\bilibili_BV1KhEw6vE14_p1_480P.mp4"
outdir = r"C:\BSAI\ComfyUI-BSAI_pro_v39\ComfyUI\custom_nodes\BSAI-MiniMAX-H3-Prompt\_evidence\ep04"
os.makedirs(outdir, exist_ok=True)
tgt = [3,8,13,18,23,28,33,38,43]
c = av.open(src)
stream = c.streams.video[0]
fps = stream.average_rate
for t in tgt:
    c.seek(int(t*1000000), stream=stream)
    for frame in c.decode(video=0):
        if frame.time >= t:
            img = frame.to_image()
            p = os.path.join(outdir, f"t{t:03d}.jpg")
            img.save(p, quality=80)
            print("saved", p, img.size)
            break
