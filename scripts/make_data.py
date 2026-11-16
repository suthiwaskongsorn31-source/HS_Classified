#!/usr/bin/env python3
"""Rebuild every file in data/ from the original sources.

Usage:
  python3 scripts/make_data.py --pdf <tariff.pdf> --itd <raw-data dir> --hs <harmonized-system.csv> [--date YYYYMMDD]

Sources:
  --pdf  The Royal Gazette PDF of the Customs Tariff Decree (No. 7) B.E. 2564 (Part 2 import tariff).
  --itd  Folder with the Thai Customs ITD master files REFDRT_Open_*.txt.gz, REFTRC_Open.txt.gz,
         REFPRV_Open.txt.gz, REFPMG_Open.txt.gz
         (e.g. src/raw-data of https://github.com/Soe-Moe/thai-customs-tariff-json, or fresh files from itd.customs.go.th).
  --hs   data/harmonized-system.csv from https://github.com/datasets/harmonized-system (HS 2022, English).
  --date The date the duty rates are computed for (default: today).

Needs: python3, pdftotext (poppler-utils).
"""
import argparse, datetime, gzip, json, os, re, subprocess, sys, tempfile, csv

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, '..', 'data')

ap = argparse.ArgumentParser()
ap.add_argument('--pdf', required=True); ap.add_argument('--itd', required=True); ap.add_argument('--hs', required=True)
ap.add_argument('--date', default=datetime.date.today().strftime('%Y%m%d'))
a = ap.parse_args()
tmp = tempfile.mkdtemp()
run = lambda *c: subprocess.run([sys.executable, '-I', *c], check=True, cwd=tmp)

# 1) tariff nomenclature from the PDF
subprocess.run(['pdftotext', '-layout', a.pdf, os.path.join(tmp, 'all.txt')], check=True)
run(os.path.join(HERE, 'parse.py'), 'all.txt', 'tariff.json')
run(os.path.join(HERE, 'build.py'))                       # -> data.min.json
d = json.load(open(os.path.join(tmp, 'data.min.json')))
t = json.load(open(os.path.join(tmp, 'tariff.json')))
fx = lambda s: re.sub(r' (?=[ัิ-ฺ็-๎])', '', s)
d['SN'] = {k: fx(v['n']) for k, v in t['sections'].items() if v['n'].strip()}
json.dump(d, open(os.path.join(OUT, 'tariff.json'), 'w'), ensure_ascii=False, separators=(',', ':'))

# 2) duty rates and privileges from ITD
run(os.path.join(HERE, 'prv.py'), a.itd, 'prv.json')
run(os.path.join(HERE, 'build_priv.py'), a.itd, 'priv.json', a.date)
pv = json.load(open(os.path.join(tmp, 'priv.json'))); prv = json.load(open(os.path.join(tmp, 'prv.json')))
def adv(r):
    m = re.match(r'([\d.]+)%', r); return float(m.group(1)) if m else (0.0 if r == '0' else None)
P = {}
for hs, L in pv['P'].items():
    g = [x for x in L if x[0] == '000']; ga = adv(g[-1][1]) if g else None
    same = lambda x, b: any(y[0] == b and y[1] == x[1] and y[2] == x[2] for y in L)
    keep = []
    for x in L:
        c = x[0]
        if c == 'WTO' and not (ga is not None and adv(x[1]) is not None and adv(x[1]) < ga): continue   # keep in-quota only
        if c == 'ASC' and same(x, 'ATG'): continue
        if c[0] == 'R' and c[2] == 'D' and same(x, c[:2] + 'C'): continue
        keep.append(x)
    P[hs] = keep
used = {x[0] for L in P.values() for x in L}
T = {k: re.sub(r'^.*?:\s*', '', v['t']) for k, v in prv.items() if k in used}
json.dump({'P': P, 'EN': pv['EN'], 'T': T, 'date': pv['date']}, open(os.path.join(OUT, 'rates.json'), 'w'), ensure_ascii=False, separators=(',', ':'))

# 3) restricted goods (permits)
run(os.path.join(HERE, 'permits.py'), a.itd, os.path.join(OUT, 'permits.json'), a.date)

# 4) English HS 2022 headings
H = {r['hscode']: r['description'] for r in csv.DictReader(open(a.hs, encoding='utf-8'))}
json.dump(H, open(os.path.join(OUT, 'hs_en.json'), 'w'), ensure_ascii=False, separators=(',', ':'))

if not os.path.exists(os.path.join(OUT, 'library.json')):
    json.dump([], open(os.path.join(OUT, 'library.json'), 'w'))
print('done ->', os.path.abspath(OUT))
