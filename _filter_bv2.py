# -*- coding: utf-8 -*-
import re, json, io, sys, subprocess, os, time, datetime
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0 Safari/537.36"
OWNER=3546707509906117
bvs=set()
keywords=["100组AI电影感提示词","Vidu 电影感 提示词","ViduAI 电影课","100个AI电影感提示词"]
tmp=os.path.join(os.environ['TEMP'],'s.html')
for kw in keywords:
    from urllib.parse import quote
    for page in range(1,5):
        url=f"https://search.bilibili.com/all?keyword={quote(kw)}&page={page}"
        subprocess.run(["curl.exe","-s",url,"-H",f"User-Agent: {UA}","-o",tmp])
        h=open(tmp,encoding='utf-8',errors='ignore').read()
        found=re.findall(r'BV[0-9A-Za-z]{10}',h)
        bvs.update(found)
        time.sleep(0.5)
print("candidate BVs:", len(bvs))
out=os.path.join(os.environ['TEMP'],'vj.json')
hits=[]
for bv in sorted(bvs):
    subprocess.run(["curl.exe","-s",f"https://api.bilibili.com/x/web-interface/view?bvid={bv}","-H",f"User-Agent: {UA}","-H","Referer: https://www.bilibili.com","-o",out])
    try:
        d=json.load(open(out,encoding='utf-8'))
    except Exception:
        continue
    data=d.get('data') or {}
    if data.get('owner',{}).get('mid')==OWNER:
        hits.append((data.get('pubdate',0),bv,data.get('title',''),data.get('duration',0)))
    time.sleep(0.25)
hits.sort()
print("OWNER MATCHES:",len(hits))
for pd,bv,title,dur in hits:
    print(datetime.datetime.fromtimestamp(pd).strftime('%Y-%m-%d'),bv,f"{dur//60}:{dur%60:02d}",'|',title)
