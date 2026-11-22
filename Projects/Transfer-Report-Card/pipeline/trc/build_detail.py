import pandas as pd,numpy as np,json,sys
exec(open('/home/claude/work/build3.py').read().split("# ---- stats sources")[0])
ST=pd.read_pickle('/home/claude/work/stats_scored.pkl')
# pool medians
pool=ST[(ST['min']>=450)&ST.pos.isin(['FW','AM','CM','DM','DF','FB','GK'])]
med=pool.groupby(['src','yr','pos'])[['x90','d90','gp90','xrel','inv','dq','aq','oph90','ppc','pacc','poph','prec']].median()
idx={k:g for k,g in ST.groupby(['league','yr','nn'])}
D=json.load(open('data.json'))
r6=lambda v:None if v is None or v!=v else round(float(v),2)
r0=lambda v:None if v is None or v!=v else round(float(v))
out=[]
for row in D:
    name,frm,to,lg,yr,pos,fee,st,se=row[:9]
    cid=next((k for k,v in CL.items() if v[0]==lg and v[1]==to),None)
    nn=' '.join(norm(name).split()); det=[]
    for s in se:
        y=s[0]; g=idx.get((lg,y,nn))
        if g is None: continue
        g=g[g.cands.map(lambda c:cid in c)]
        if g.empty: continue
        r=g.sort_values('min',ascending=False).iloc[0]
        try: m=med.loc[(r.src,y,r.pos)]
        except KeyError: m=None
        det.append([y,r6(r['min']),r6(r.x90),r0(r.pa),r6(r.d90),r0(r.pdf),r6(r.gp90),r0(r.pgk),r0(r.pct),
          r6(m.x90) if m is not None else None,r6(m.d90) if m is not None else None,r6(m.gp90) if m is not None else None,r.src,r.basis,
          r6(r.inv),r0(r.pinv),r6(m.inv) if m is not None else None,r6(r.dq),r0(r.pdq),r6(m.dq) if m is not None else None,r6(r.aq),r0(r.paq),r6(m.aq) if m is not None else None,r6(r.oph90),r0(r.pph),r6(m.oph90) if m is not None else None,r0(r.g),r0(r.a),r6(r.bon),r6(r.pbase),
          ({'pc':[r6(r.ppc),r0(r.qpc),r6(m.ppc) if m is not None else None],'ac':[r6(r.pacc),r0(r.qacc),r6(m.pacc) if m is not None else None],'op':[r6(r.poph),r0(r.qoph),r6(m.poph) if m is not None else None],'rc':[r6(r.prec),r0(r.qrec),r6(m.prec) if m is not None else None]} if r.pos=='CM' else None),
          ({'tx':[r6(r.xrel),r0(r.pta),r6(m.xrel) if m is not None else None]} if r.pos in ('FW','AM') else None)])
    out.append(det)
json.dump(out,open('detail.json','w'),separators=(',',':'),ensure_ascii=False)
print(len(out),sum(1 for d in out if d),len(open('detail.json').read())//1024,'KB')
