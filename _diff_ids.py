# -*- coding: utf-8 -*-
import json, io, sys, subprocess
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# committed version
old_raw = subprocess.check_output(['git','show','HEAD:templates/prompt_templates.json'])
old = json.loads(old_raw.decode('utf-8'))
new = json.load(open('templates/prompt_templates.json', encoding='utf-8'))

def collect(d):
    out = {}
    for c in d['categories']:
        cid = c.get('id')
        for s in c.get('subcategories') or []:
            sid = s.get('id')
            for t in s.get('templates') or []:
                if 'id' not in t:
                    continue
                out[t['id']] = (cid, sid, t['name'])
        for t in c.get('templates') or []:
            if 'id' not in t:
                continue
            out[t['id']] = (cid, None, t['name'])
    return out

o = collect(old); n = collect(new)
added = [k for k in n if k not in o]
removed = [k for k in o if k not in n]
print("OLD total:", len(o), "NEW total:", len(n))
print("ADDED ids:", len(added))
for k in added:
    print("  +", k, "|", n[k][0], "/", n[k][1], "|", n[k][2])
print("REMOVED ids:", removed)

# also show subcategory structure of new cinematic_prompts
cin = [c for c in new['categories'] if c.get('id')=='cinematic_prompts'][0]
print("\nNEW cinematic_prompts subs:")
for s in cin['subcategories']:
    print("  ", s['id'], s['name'], "n=", len(s['templates']))
