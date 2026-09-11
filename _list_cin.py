# -*- coding: utf-8 -*-
import json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
be = json.load(open('templates/prompt_templates.json', encoding='utf-8'))
cin = [c for c in be['categories'] if c.get('id')=='cinematic_prompts'][0]
for s in cin['subcategories']:
    print("\n##### SUB", s['id'], s['name'], "n=", len(s['templates']))
    for t in s['templates']:
        print("  -", t['id'], "|", t['name'], "|", t.get('name_en',''))
