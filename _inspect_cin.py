# -*- coding: utf-8 -*-
import json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def load(p):
    return json.load(open(p, encoding='utf-8'))

be = load('templates/prompt_templates.json')
fe = load('web/templates_data.json')

print("=== BACKEND categories ===")
for c in be['categories']:
    print(repr(c.get('id')), '|', repr(c.get('name')), '| sub:', [s.get('id') for s in c.get('subcategories', [])] if c.get('subcategories') else None, '| n_tpl:', len(c.get('templates', [])))

# find cinematic category
def find_cat(d, key):
    for c in d['categories']:
        if key.lower() in (c.get('name','')+str(c.get('id',''))).lower():
            return c
    return None

cin = find_cat(be, '电影感') or find_cat(be, 'Cinematic')
print("\n=== CINEMATIC (backend) ===")
print("id:", cin.get('id'), "name:", cin.get('name'))
for s in cin.get('subcategories', []):
    print(" sub:", repr(s.get('id')), repr(s.get('name')), 'n=', len(s.get('templates', [])))
print("top-level templates in cin cat:", len(cin.get('templates', [])))

# sample one template
if cin.get('subcategories') and cin['subcategories'][0].get('templates'):
    t = cin['subcategories'][0]['templates'][0]
    print("\n=== SAMPLE TEMPLATE ===")
    print(json.dumps(t, ensure_ascii=False, indent=2)[:3000])

print("\n=== FRONTEND top ===")
print(type(fe), list(fe.keys()) if isinstance(fe, dict) else len(fe))
