#!/usr/bin/env python3
"""Compile scripts/dict/*.txt (CODE: term, term) into data/dict.json, validating codes against data/tariff.json."""
import glob, json, os, re
here = os.path.dirname(os.path.abspath(__file__)); root = os.path.join(here, '..')
T = json.load(open(os.path.join(root, 'data/tariff.json')))
codes = {x[0] for x in T['I']}; p4 = {c[:4] for c in codes}; p6 = {c[:6] for c in codes}
out, bad, n = {}, [], 0
for f in sorted(glob.glob(os.path.join(here, 'dict', '*.txt'))):
    for ln in open(f, encoding='utf-8'):
        ln = ln.strip()
        if not ln or ln.startswith('#'): continue
        m = re.match(r'^(\d{4}|\d{6}|\d{8}):\s*(.+)$', ln)
        if not m: bad.append(ln[:40]); continue
        c, terms = m.group(1), [t.strip() for t in m.group(2).split(',') if t.strip()]
        ok = (len(c) == 4 and c in p4) or (len(c) == 6 and c in p6) or (len(c) == 8 and c in codes)
        if not ok: bad.append(c); continue
        out.setdefault(c, [])
        for t in terms:
            if t not in out[c]: out[c].append(t); n += 1
json.dump(out, open(os.path.join(root, 'data/dict.json'), 'w'), ensure_ascii=False, separators=(',', ':'))
print(f'{len(out)} codes, {n} terms, heading coverage {len([c for c in out if len(c)==4])}/{len(p4)}; invalid: {bad}')
