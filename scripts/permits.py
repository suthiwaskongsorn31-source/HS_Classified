import gzip,sys,re,json,collections
base,out,today=sys.argv[1],sys.argv[2],int(sys.argv[3])
AG={"0994000011679":"กรมการอุตสาหกรรมทหาร","0994000036213":"กรมอุตสาหกรรมพื้นฐานและการเหมืองแร่","0994000036337":"กรมธุรกิจพลังงาน","0994000037015":"สำนักงานมาตรฐานสินค้าเกษตรและอาหารแห่งชาติ (มกอช.)","0994000041969":"กรมอุทยานแห่งชาติ สัตว์ป่าและพันธุ์พืช","0994000049447":"สำนักงาน กสทช.","0994000132115":"สำนักงานคณะกรรมการอ้อยและน้ำตาลทราย","0994000158921":"กรมวิชาการเกษตร","0994000159251":"กรมปศุสัตว์","0994000159544":"สำนักงานปรมาณูเพื่อสันติ","0994000159561":"กรมการค้าต่างประเทศ","0994000159897":"กรมป่าไม้","0994000160259":"กรมประมง","0994000160461":"กรมสรรพสามิต","0994000160682":"กรมวิทยาศาสตร์การแพทย์","0994000160887":"กรมทรัพยากรธรณี","0994000161450":"กรมการค้าภายใน","0994000162626":"กรมการปกครอง","0994000162847":"กรมศิลปากร","0994000165161":"สำนักงานมาตรฐานผลิตภัณฑ์อุตสาหกรรม (สมอ.)","0994000165676":"สำนักงานคณะกรรมการอาหารและยา (อย.)","0994000528116":"กรมโรงงานอุตสาหกรรม","0994001057192":"การยางแห่งประเทศไทย"}
CASE={'0':'I','1':'E','2':'T','3':'IE'}
L=gzip.open(base+'/REFPMG_Open.txt.gz').read().decode('cp874',errors='replace').splitlines()
R=collections.defaultdict(dict); st=collections.Counter(); ag=collections.Counter(); unk=collections.Counter()
for l in L:
    if len(l.strip())<30: continue
    hs=l[4:12]
    if not re.fullmatch(r'\d{8}',hs): continue
    case=CASE.get(l[15])
    m=re.search(r'\b(0994\d{9})\b',l); a=m.group(1) if m else ''
    dt=re.search(r'(\d{8})(\d{8})(\d{8})\s*$',l)
    if not dt or not case: st['skip']+=1; continue
    s,e=int(dt.group(2)),int(dt.group(3))
    if not (s<=today<=e): st['inactive']+=1; continue
    req=' Y ' in l
    body=re.sub(r'\d{24}\s*$','',l[15:])
    mm=re.search(r'\d{11}\.\d{3}\s{3}(.*)$',body)
    parts=(mm.group(1).strip().split('   ') if mm else [])
    parts=[p.strip() for p in parts if p.strip()]
    notice=parts.pop() if parts and re.fullmatch(r'[\d/]+',parts[-1]) else ''
    th=parts[0] if parts else ''; en=parts[1] if len(parts)>1 else ''
    agn=AG.get(a,'หน่วยงานควบคุม'); 
    if a not in AG: unk[a]+=1
    k=(agn,case,notice)
    ent=R[hs].setdefault(k,{'a':agn,'c':case,'n':notice,'r':req,'s':[]})
    if th or en:
        t=th + (f' ({en})' if en and en.lower()!=th.lower() else '')
        if t not in ent['s'] and len(ent['s'])<12: ent['s'].append(t)
    st['ok']+=1; ag[agn]+=1
out_d={hs:[[v['a'],v['c'],v['n'],1 if v['r'] else 0,v['s']] for v in d.values()] for hs,d in R.items()}
json.dump(out_d,open(out,'w'),ensure_ascii=False,separators=(',',':'))
print(st,len(out_d),unk); print(ag.most_common())
