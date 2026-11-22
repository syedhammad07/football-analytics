import pandas as pd,numpy as np,json
exec(open('/home/claude/work/build3.py').read().split("# ---- stats sources")[0])
ST=pd.read_pickle('/home/claude/work/stats_scored.pkl')
STATS=['dr','kp','sh','tw','ic','cl','duw','aer','rec','prgp','prgc','sv','fl','yc','rc']
for c in STATS: ST['p_'+c]=ST[c]/(ST['min']/90)
pool=ST[(ST['min']>=450)&ST.pos.isin(['FW','AM','CM','DM','DF','FB','GK'])]
med={};pct={}
for k,g in pool.groupby(['src','yr','pos']):
    for c in STATS:
        v=g['p_'+c]
        if v.notna().sum()>=15:
            med[(k,c)]=v.median(); ST.loc[v.dropna().index,'q_'+c]=v.dropna().rank(pct=True,method='average')*100
for c in STATS:
    if 'q_'+c not in ST: ST['q_'+c]=np.nan
idx={k:g for k,g in ST.groupby(['league','yr','nn'])}
D=json.load(open('/home/claude/trc/data.json'))
out=[]
for row in D:
    name,frm,to,lg,yr,pos,fee,st,se=row[:9]
    cid=next((k for k,v in CL.items() if v[0]==lg and v[1]==to),None)
    nn=' '.join(norm(name).split()); rows=[]
    for s in se:
        g=idx.get((lg,s[0],nn))
        if g is None: continue
        g=g[g.cands.map(lambda c:cid in c)]
        if g.empty: continue
        rows.append(g.sort_values('min',ascending=False).iloc[0])
    ev=[]
    if rows:
        for c in STATS:
            vals=[(r['min'],r[c],r['q_'+c],med.get(((r.src,r.yr,r.pos),c))) for r in rows if r['min']==r['min'] and r[c]==r[c]]
            if not vals: continue
            m=sum(v[0] for v in vals); tot=sum(v[1] for v in vals)
            p90=tot/m*90
            qs=[(v[0],v[2]) for v in vals if v[2]==v[2] and v[0]>=450]; ms=[(v[0],v[3]) for v in vals if v[3] is not None and v[3]==v[3] and v[0]>=450]
            q=sum(a*b for a,b in qs)/sum(a for a,b in qs) if qs else None
            md=sum(a*b for a,b in ms)/sum(a for a,b in ms) if ms else None
            ev.append([c,round(p90,2),None if md is None else round(md,2),None if q is None else round(q),int(tot) if c in('yc','rc') else round(tot)])
    out.append(ev)
json.dump(out,open('/home/claude/trc/evidence.json','w'),separators=(',',':'))
print(len(out),sum(1 for e in out if e),len(open('/home/claude/trc/evidence.json').read())//1024,'KB')
