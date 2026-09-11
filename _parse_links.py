# -*- coding: utf-8 -*-
import re, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
h = open(r'C:\Users\xm204\AppData\Local\Temp\bs.html', encoding='utf-8', errors='ignore').read()
# find all /video/BVxxx occurrences and a window of surrounding text, strip tags
pairs = {}
for m in re.finditer(r'/video/(BV[0-9A-Za-z]{10})', h):
    bv = m.group(1)
    seg = h[m.start():m.start()+400]
    # extract title: look for title="..." or <em> or aria-label
    tm = re.search(r'title="([^"]+)"', seg)
    title = tm.group(1) if tm else ''
    if bv not in pairs:
        pairs[bv] = title
for bv,t in pairs.items():
    if '电影感' in t or '提示词' in t or 'Vidu' in t:
        print(bv, '|', t)
print('--- all with nonempty title ---')
for bv,t in pairs.items():
    if t:
        print(bv,'|',t)
