import gzip, sys, re, json, collections

base, out_path, today = sys.argv[1], sys.argv[2], int(sys.argv[3])
dec = lambda f: gzip.open(f'{base}/{f}').read().decode('cp874', errors='replace').splitlines()

# English + Thai descriptions per HS8
EN, TH = {}, {}
for l in dec('REFTRC_Open.txt.gz'):
    if len(l) < 20: continue
    hs = l[4:12]
    TH[hs] = l[12:3012].strip()
    EN[hs] = re.sub(r'\s+', ' ', l[3012:6012].strip())

UNIT = {'KGM': 'กก.', 'LTR': 'ลิตร', 'MTR': 'เมตร', 'C62': 'หน่วย', 'TNE': 'ตัน', 'NMB': 'หน่วย', 'GRO': 'กรอส'}
SKIP = {'220', '226', '227', '332', '335', '999'}  # universal (apply to every line) or statutory ceiling

def num(s):
    try: return float(s)
    except: return 0.0
def fmt(x): return ('%g' % x)

def rate_text(l):
    adv, spc, unit, flag = num(l[21:39]), num(l[39:57]), l[57:60].strip(), l[20]
    if adv == 0 and spc == 0: return '0'
    parts = []
    if adv: parts.append(fmt(adv) + '%')
    if spc: parts.append(f'{fmt(spc)} บ./{UNIT.get(unit, unit)}')
    return ' หรือ '.join(parts)

def norm(s): return re.sub(r'[\s\-–]', '', s)

recs = collections.defaultdict(list)   # (hs, code) -> list of (start, end, rate, note)
for l in dec('REFDRT_Open_20220101.txt.gz'):
    if len(l) < 60: continue
    hs, code = l[4:12], l[17:20].strip()
    if code in SKIP: continue
    m = list(re.finditer(r'(20\d{6})(20\d{6}|99999999)', l))
    if not m: continue
    s, e = int(m[-1].group(1)), int(m[-1].group(2))
    note = l[m[-1].end():].strip()
    if norm(note) == norm(TH.get(hs, '')) or not note: note = ''
    recs[(hs, code)].append((s, e, rate_text(l), note))

P = collections.defaultdict(list)
stat = collections.Counter()
for (hs, code), rs in recs.items():
    act = [r for r in rs if r[0] <= today <= r[1]]
    fut = sorted(r for r in rs if r[0] > today)
    if not act:
        stat['noactive'] += 1
        continue
    seen = set()
    for s, e, rt, note in sorted(act, key=lambda r: -r[0]):
        if (rt, note) in seen: continue
        seen.add((rt, note))
        nxt = ''
        f2 = [f for f in fut if f[3] == note and f[2] != rt]
        if f2: nxt = f'{f2[0][2]} ตั้งแต่ {str(f2[0][0])[:4]}'
        until = '' if e == 99999999 else f'{str(e)[6:8]}/{str(e)[4:6]}/{str(e)[:4]}'
        P[hs].append([code, rt, note, nxt, until])
        stat[code] += 1

json.dump({'P': P, 'EN': EN, 'date': today}, open(out_path, 'w'), ensure_ascii=False, separators=(',', ':'))
print(len(P), len(EN), stat.most_common(80))
