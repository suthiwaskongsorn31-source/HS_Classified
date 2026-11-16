import gzip,sys,re,json
base=sys.argv[1]
L=gzip.open(base+'/REFPRV_Open.txt.gz').read().decode('cp874',errors='replace').splitlines()
out={}
for l in L:
    if len(l.strip())<5: continue
    code=l[:3]; rest=l[3:]
    m=list(re.finditer(r'(\d{8})(\d{8}|99999999)',rest))
    s,e=(m[-1].group(1),m[-1].group(2)) if m else ('','')
    t=re.split(r'\s{2,}|\d{8}',rest.strip())[0].strip()
    out[code]={'t':t,'s':s,'e':e}
json.dump(out,open(sys.argv[2],'w'),ensure_ascii=False,indent=0)
for k,v in out.items():
    if not k.isdigit() or k[0] in '04' or k in('999','019','005','003'): print(k,v['s'],v['e'],v['t'][:150])
