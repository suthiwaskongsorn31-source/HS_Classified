import re, json, sys

src = sys.argv[1]
raw = open(src, encoding='utf-8').read()
BAD = ['กำร','ว่ำ','กล่ำว','หมำย','ตำม','อย่ำง','ประเภทย่อยอื่น','ขนำด','วัตถุทีใ่ ช้']
pages = raw.split('\f')
fixed = 0
for i,p in enumerate(pages):
    if sum(p.count(w) for w in BAD[:6]) >= 2:
        pages[i] = p.replace('ำ','า'); fixed += 1
print('am-fixed pages', fixed)
lines = '\n'.join(pages).split('\n')

PUA = {0xf700:'ฐ',0xf701:'ิ',0xf702:'ี',0xf703:'ึ',0xf704:'ื',0xf705:'่',0xf706:'้',0xf707:'๊',0xf708:'๋',0xf709:'์',
 0xf70a:'่',0xf70b:'้',0xf70c:'๊',0xf70d:'๋',0xf70e:'์',0xf70f:'ญ',0xf710:'ั',0xf711:'ํ',0xf712:'็',0xf713:'่',0xf714:'้',0xf71d:'ฬ'}
FIX = [('สาหรับ','สำหรับ'),('ทาด้วย','ทำด้วย'),('ทาจาก','ทำจาก'),('ทาความ','ทำความ'),('จาพวก','จำพวก'),('ทาให้','ทำให้'),
 ('กาลัง','กำลัง'),('จานวน','จำนวน'),('ทาเป็น','ทำเป็น'),('ประจา','ประจำ'),('กาหนด','กำหนด'),('จาแนก','จำแนก'),('ทาการ','ทำการ'),
 ('น้ามัน','น้ำมัน'),('น้าหนัก','น้ำหนัก'),('น้าตาล','น้ำตาล'),('น้าแข็ง','น้ำแข็ง'),('ทาสี','ทำสี'),('นาไป','นำไป'),('ทาขึ้น','ทำขึ้น'),('สาเร็จ','สำเร็จ'),('ทางาน','ทำงาน'),('จาหน่าย','จำหน่าย'),('ลาดับ','ลำดับ'),('อานาจ','อำนาจ'),('ตารับ','ตำรับ'),('ดาเนิน','ดำเนิน'),('กามะถัน','กำมะถัน'),('ทาจาก','ทำจาก'),('น้า','น้ำ'),('คาว่า','คำว่า'),('ส้าหรับ','สำหรับ'),('ซ้า','ซ้ำ'),('ทาเครื่อง','ทำเครื่อง'),('ทาโดย','ทำโดย'),('ตาแหน่ง','ตำแหน่ง'),('สีดา','สีดำ'),('จาเป็น','จำเป็น'),('ค้ายัน','ค้ำยัน'),('อุปกรณ์ทา','อุปกรณ์ทำ'),('ทาเหมือง','ทำเหมือง'),('ทาเกลียว','ทำเกลียว'),('ทาร่อง','ทำร่อง'),('ทาเย็น','ทำเย็น'),('ทาอาหาร','ทำอาหาร'),('ทาน้ำแข็ง','ทำน้ำแข็ง'),('ทากระดาษ','ทำกระดาษ'),('ทารองเท้า','ทำรองเท้า'),('ทาความร้อน','ทำความร้อน')]
def norm(s):
    s = s.translate(PUA)
    for a,b in FIX: s = s.replace(a,b)
    s = s.replace('ํา', 'ำ').replace('ํา', 'ำ')
    s = re.sub(r'\s+', ' ', s).strip()
    return s

RE_SEC = re.compile(r'^\s*หมวด\s+(\d+)\s*$')
RE_CH = re.compile(r'^\s*ตอนที่\s+(\d+)\s*$')
RE_PAGEHDR = re.compile(r'^\s*หมวด\s+\d+\s+ตอนที่\s+\d+')
RE_COLHDR = re.compile(r'^\s*ประเภท\s+ประเภท')
RE_SKIP = re.compile(r'^\s*(อัตราอากร|ตาม\s+ตามสภาพ|ราคา\s+หน|หน[่]?วย\s*$|ร[้]?อยละ\s+บาท|\d+\s*$)')
RE_HEAD = re.compile(r'^\s{0,16}(\d{2}\.\d{2})\s+(.*)$')
RE_CODE = re.compile(r'^\s+(\d{4}\.\d{2}(?:\.\d{2})?)\s+(.*)$')
RE_DASH = re.compile(r'^\s+((?:-\s)+)(.*)$')
FREE = re.compile(r'ไม[่]?\s*ต[้]?องเสียอากร')

def split_rate(rest):
    m = re.match(r'^(.*?)\s{2,}(\S.*)$', rest)
    if not m:
        f = FREE.search(rest)
        if f:
            return rest[:f.start()].strip(), 'ยกเว้นอากร'
        return rest.strip(), None
    d, r = m.group(1).strip(), m.group(2).strip()
    if FREE.search(r):
        return d, 'ยกเว้นอากร'
    return d, r

def dash_level(desc):
    m = re.match(r'^((?:-\s*)+)', desc)
    if not m: return 0, desc
    return m.group(1).count('-'), desc[m.end():].strip()

sections, chapters, headings, items = {}, {}, {}, []
state = 'notes'
cur_sec = cur_ch = None
pending_title = None  # ('sec'|'ch', num)
notes_buf = []
stack = []  # list of (level, text)
cur_head = None
last = None  # last item dict for continuation (heading or entry)

def flush_notes():
    global notes_buf
    if cur_ch and notes_buf:
        chapters[cur_ch]['notes'] += '\n'.join(notes_buf).strip() + '\n'
    elif cur_sec and notes_buf:
        sections[cur_sec]['notes'] += '\n'.join(notes_buf).strip() + '\n'
    notes_buf = []

for ln in lines:
    if not ln.strip():
        continue
    if 'ราชกิจจานุเบกษา' in ln or re.match(r'^\s*หน้า\s', ln) or '-----' in ln:
        continue
    m = RE_SEC.match(ln)
    if m:
        flush_notes(); cur_sec = m.group(1); sections[cur_sec] = {'title': '', 'notes': ''}
        pending_title = ('sec', cur_sec); state = 'notes'; cur_ch = None; continue
    m = RE_CH.match(ln)
    if m:
        flush_notes(); cur_ch = m.group(1).zfill(2)
        chapters[cur_ch] = {'title': '', 'notes': '', 'sec': cur_sec}
        pending_title = ('ch', cur_ch); state = 'notes'; continue
    if RE_PAGEHDR.match(ln):
        continue
    if RE_COLHDR.match(ln):
        flush_notes(); state = 'table'; pending_title = None; continue
    if pending_title and RE_SKIP.match(ln):
        continue
    if pending_title:
        t = norm(ln)
        if t.startswith('หมายเหตุ'):
            pending_title = None
        else:
            kind, num = pending_title
            d = sections if kind == 'sec' else chapters
            d[num]['title'] = (d[num]['title'] + ' ' + t).strip()
            continue
    if RE_SKIP.match(ln):
        continue
    if state == 'notes':
        if norm(ln).startswith('หมายเหตุ') and not notes_buf:
            continue
        notes_buf.append(norm(ln)); continue
    # table
    t = ln.rstrip()
    m = RE_HEAD.match(t)
    if m and cur_ch and m.group(1)[:2] == cur_ch and (cur_head is None or m.group(1) > cur_head or cur_head[:2] != cur_ch):
        hcode, rest = m.group(1), m.group(2)
        m2 = re.match(r'^(\d{4}\.\d{2}\.\d{2})\s+(.*)$', rest)
        stack = []
        if m2:
            d, r = split_rate(m2.group(2))
            headings[hcode] = {'d': norm(d), 'ch': cur_ch}
            it = {'c': m2.group(1), 'h': hcode, 'd': norm(d), 'p': [], 'r': r, 'lv': 0}
            items.append(it); last = it; cur_head = hcode
        else:
            d, r = split_rate(rest)
            headings[hcode] = {'d': norm(d), 'ch': cur_ch}
            cur_head = hcode; last = headings[hcode]
        continue
    m = RE_CODE.match(t)
    if m and cur_head and m.group(1)[:2]+'.'+m.group(1)[2:4] == cur_head and m.group(2).startswith('-'):
        code, rest = m.group(1), m.group(2)
        d, r = split_rate(rest)
        lv, txt = dash_level(d)
        while stack and stack[-1][0] >= lv: stack.pop()
        parents = [s[2] for s in stack]
        if len(code) == 10:
            it = {'c': code, 'h': cur_head, 'd': norm(txt), 'p': parents, 'r': r, 'lv': lv}
            items.append(it); last = it
            stack.append((lv, norm(txt), it))
        else:
            node = {'d': norm(txt)}
            stack.append((lv, norm(txt), node)); last = node
        continue
    m = RE_DASH.match(t)
    if m and cur_head:
        d, r = split_rate(m.group(0).strip())
        lv, txt = dash_level(d)
        while stack and stack[-1][0] >= lv: stack.pop()
        node = {'d': norm(txt)}
        stack.append((lv, norm(txt), node)); last = node
        continue
    if re.match(r'^\s+\d{1,2}\.\s+[\u0e00-\u0e7f]', t):
        last = None; continue
    # continuation
    if last is not None:
        d, r = split_rate(t.strip())
        last['d'] = (last['d'] + ' ' + norm(d)).strip() if 'd' in last else norm(d)
        if r and 'r' in last and not last['r']:
            last['r'] = r
        # update stack text if node is on stack
        if stack and stack[-1][2] is last:
            stack[-1] = (stack[-1][0], last['d'], last)
        continue

flush_notes()

# rebuild parents text from stack nodes (continuations may have extended)
out_items = []
for it in items:
    out_items.append([it['c'], it['h'], it['d'], [p['d'] for p in it['p']], it['r'] or ''])

data = {
    'sections': {k: {'t': v['title'], 'n': v['notes'][:6000]} for k, v in sections.items()},
    'chapters': {k: {'t': v['title'], 's': v['sec'], 'n': v['notes']} for k, v in chapters.items()},
    'headings': {k: [v['d'], v['ch']] for k, v in headings.items()},
    'items': out_items,
}
json.dump(data, open(sys.argv[2], 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
print('sections', len(sections), 'chapters', len(chapters), 'headings', len(headings), 'items', len(items))
print('no rate', sum(1 for i in items if not i['r']))
