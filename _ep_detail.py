# -*- coding: utf-8 -*-
import json, io, sys, subprocess, os, time, datetime
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0 Safari/537.36"
eps=[
 ("01","情绪运镜","BV1Vz596jEza"),
 ("02","首尾帧风格运镜","BV1s8L165ETs"),
 ("03","景别万能公式","BV163Gy6oEa7"),
 ("04","光影效果","BV1KhEw6vE14"),
 ("05","镜头风格","BV1vBEq62EsA"),
 ("06","色彩配方","BV14SjR6LEXq"),
 ("07","演技控制","BV1RuM16GEDu"),
 ("08","镜头生命力","BV1Z2g56YELp"),
 ("09","史诗科幻","BV1c4hP6FE7K"),
 ("10","中式美学色卡","BV1Dit36sETc"),
 ("11","构图技巧[DONE]","BV1Hxb56XEfe"),
]
out=os.path.join(os.environ['TEMP'],'ep.json')
for num,name,bv in eps:
    subprocess.run(["curl.exe","-s",f"https://api.bilibili.com/x/web-interface/view?bvid={bv}","-H",f"User-Agent: {UA}","-H","Referer: https://www.bilibili.com","-o",out])
    d=json.load(open(out,encoding='utf-8'))['data']
    dur=d['duration']; pd=datetime.datetime.fromtimestamp(d['pubdate']).strftime('%Y-%m-%d')
    print(f"=== ({num}) {name} {bv} | {pd} | {dur//60}:{dur%60:02d} ===")
    print("TITLE:",d['title'])
    print("DESC:",(d.get('desc') or '').replace('\n',' / '))
    time.sleep(0.3)
