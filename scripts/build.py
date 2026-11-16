import json,re,collections,sys
d=json.load(open('tariff.json'))
fixsp=lambda s: re.sub(r' (?=[ัิ-ฺ็-๎])','',s)
PUA={0xf70a:'่',0xf70b:'้'}
MAN={'3911.10.00':'40','8421.39.30':'35','8703.40.28':'200','8703.60.28':'200','4817.20.00':'40','0105.99.40':'40','2908.99.00':'30'}
def rate(r):
    r=r.translate(PUA).strip()
    if 'ยกเว้น' in r or 'เสียอากร' in r: return 'ยกเว้น'
    m=re.search(r'(\d+(?:\.\d+)?|-)\s+(\S+)\s+(\d[\d.,]*|-)\s*[”"]?$',r)
    if not m: return '?'+r
    a,u,b=m.groups()
    parts=[]
    if a!='-': parts.append(a+'%')
    if b!='-' and u!='-': parts.append(f'{b} บาท/{u}')
    return ' หรือ '.join(parts) if parts else '?'+r
N=[];Ni={}
def ni(t):
    t=fixsp(t)
    if t not in Ni: Ni[t]=len(N); N.append(t)
    return Ni[t]
I=[]; bad=collections.Counter()
for c,h,desc,par,r in d['items']:
    if c in MAN:
        rr=MAN[c]+'%'; desc=re.sub(r'\s'+MAN[c]+r'(\s|$)',' ',desc).strip()
    else: rr=rate(r)
    if rr.startswith('?'): bad[r]+=1
    I.append([c.replace('.',''),fixsp(desc),[ni(p) for p in par],rr])
out={'S':{k:fixsp(v['t']) for k,v in d['sections'].items()},
     'C':{k:[fixsp(v['t']),v['s'],fixsp(v['n'])] for k,v in d['chapters'].items()},
     'H':{k:fixsp(v[0]) for k,v in d['headings'].items()},'N':N,'I':I}
s=json.dumps(out,ensure_ascii=False,separators=(',',':'))
open('data.min.json','w').write(s)
print(len(s.encode()), bad.most_common(20))
print(collections.Counter(x[3] for x in I).most_common(12))
print(sum(len(v[2]) for v in out['C'].values()))
