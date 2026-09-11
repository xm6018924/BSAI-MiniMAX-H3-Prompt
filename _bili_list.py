# -*- coding: utf-8 -*-
import json, io, sys, time, hashlib, urllib.parse, subprocess, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
MID = 3546707509906117

def curl(url, referer="https://www.bilibili.com"):
    out = os.path.join(os.environ['TEMP'], 'bi.json')
    subprocess.run(["curl.exe","-s",url,"-H",f"User-Agent: {UA}","-H",f"Referer: {referer}","-o",out], check=True)
    return json.load(open(out, encoding='utf-8'))

# 1. nav -> wbi keys
nav = curl("https://api.bilibili.com/x/web-interface/nav")
wi = nav['data']['wbi_img']
img_key = wi['img_url'].rsplit('/',1)[1].split('.')[0]
sub_key = wi['sub_url'].rsplit('/',1)[1].split('.')[0]
raw = img_key + sub_key
PERM = [46,47,18,2,53,8,23,32,15,50,10,31,58,3,45,35,27,43,5,49,33,9,42,19,29,28,14,39,12,38,41,13,37,48,7,16,24,55,40,61,26,17,0,1,60,51,30,4,22,25,54,21,56,59,6,63,57,62,11,36,20,34,44,52]
mixin = ''.join(raw[i] for i in PERM)[:32]
print("mixin ok, isLogin=", nav['data'].get('isLogin'))

def sign(params):
    params['wts'] = int(time.time())
    items = sorted(params.items())
    q = urllib.parse.urlencode(items)
    params['w_rid'] = hashlib.md5((q + mixin).encode()).hexdigest()
    return urllib.parse.urlencode(sorted(params.items()))

allv = []
for pn in range(1,6):
    q = sign({'mid':MID,'ps':30,'pn':pn,'order':'pubdate'})
    d = curl("https://api.bilibili.com/x/space/wbi/arc/search?"+q, referer=f"https://space.bilibili.com/{MID}")
    if d.get('code')!=0:
        print("ERR page",pn,d.get('code'),d.get('message')); break
    vl = d['data']['list']['vlist']
    if not vl: break
    allv.extend(vl)
    if len(vl)<30: break

print("TOTAL videos:", len(allv))
import datetime
for x in allv:
    t = datetime.datetime.fromtimestamp(x['created']).strftime('%Y-%m-%d')
    print(t, x['bvid'], '|', x['title'])
