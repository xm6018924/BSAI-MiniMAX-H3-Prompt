# -*- coding: utf-8 -*-
import re, json, io, sys, subprocess, os, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
h = open(r'C:\Users\xm204\AppData\Local\Temp\bs.html', encoding='utf-8', errors='ignore').read()
bvs = sorted(set(re.findall(r'BV[0-9A-Za-z]{10}', h)))
UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0 Safari/537.36"
OWNER=3546707509906117
out=os.path.join(os.environ['TEMP'],'vj.json')
hits=[]
for bv in bvs:
    subprocess.run(["curl.exe","-s",f"https://api.bilibili.com/x/web-interface/view?bvid={bv}","-H",f"User-Agent: {UA}","-H","Referer: https://www.bilibili.com","-o",out])
    try:
        d=json.load(open(out,encoding='utf-8'))
    except Exception:
        continue
    data=d.get('data') or {}
    own=data.get('owner',{})
    if own.get('mid')==OWNER:
        hits.append((data.get('pubdate',0), bv, data.get('title',''), data.get('duration',0)))
    time.sleep(0.3)
hits.sort()
print("OWNER MATCHES:", len(hits))
import datetime
for pd,bv,title,dur in hits:
    print(datetime.datetime.fromtimestamp(pd).strftime('%Y-%m-%d'), bv, f"{dur//60}:{dur%60:02d}", '|', title)
