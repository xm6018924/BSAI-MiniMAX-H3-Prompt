# -*- coding: utf-8 -*-
import re, json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
h = open(r'C:\Users\xm204\AppData\Local\Temp\bs.html', encoding='utf-8', errors='ignore').read()
m = re.search(r'__INITIAL_STATE__=(.*?);\(function\(\)', h)
if not m:
    m = re.search(r'__INITIAL_STATE__=(.*?);</script>', h)
data = json.loads(m.group(1))
# find video list
def walk(o, out):
    if isinstance(o, dict):
        if 'bvid' in o and 'title' in o:
            out.append(o)
        for v in o.values():
            walk(v, out)
    elif isinstance(o, list):
        for v in o: walk(v, out)
items=[]
walk(data, items)
seen=set()
for it in items:
    bv=it.get('bvid'); title=re.sub(r'<.*?>','',it.get('title',''))
    author=it.get('author','')
    if bv in seen: continue
    seen.add(bv)
    if '电影感' in title or '提示词' in title:
        print(bv,'|',author,'|',title)
