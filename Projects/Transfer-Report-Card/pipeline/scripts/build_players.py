import pandas as pd,numpy as np,json,gzip,base64,re,unicodedata,collections
ST=pd.read_pickle('/home/claude/work/stats_scored.pkl')
ST=ST[ST['min'].fillna(0)>0].copy()
nrm=lambda x:' '.join(re.sub(r'[^a-z0-9 ]',' ',unicodedata.normalize('NFKD',str(x)).encode('ascii','ignore').decode().lower()).split())
fb=ST[ST.src=='FBref']; n2u=fb.groupby('nn').url.agg(lambda s:set(s.dropna()))
def key(r):
    if r.src=='FBref' and isinstance(r.url,str): return r.url
    u=n2u.get(r.nn,set())
    return next(iter(u)) if len(u)==1 else 'n:'+str(r.nn)
ST=ST[ST.yr>=2017].copy()  # scope
ST['pk']=[key(r) for r in ST.itertuples()]
ST['gp_only']=ST.ga_only.fillna(False)
def reason(r):
    if r.pct==r.pct: return 0
    if r['min']<450: return 1
    if not isinstance(r.pos,str): return 2
    if r.pos=='GK': return 4
    return 3
ST['mn']=ST['min']
ST['rs']=[reason(r) for _,r in ST.iterrows()]
ST['w']=ST['min']/(ST['min']+300.0)
ST['adj']=np.where(ST.pct.notna(),50+ST.w*(ST.pct-50),np.nan)
# typicals per source/year/role (players 450+ min)
pool=ST[(ST['min']>=450)&ST.pos.isin(['FW','AM','CM','DM','DF','FB','GK'])]
med=pool.groupby(['src','yr','pos'])[['x90','d90']].median()
MED={f"{a}|{b}|{c}":[round(float(r.x90),2) if r.x90==r.x90 else None,round(float(r.d90),2) if r.d90==r.d90 else None] for (a,b,c),r in med.iterrows()}
SC={'FBref':'F','Opta':'O','SofaScore':'S'}
r2=lambda v:None if v is None or v!=v else round(float(v),2)
r1=lambda v:None if v is None or v!=v else round(float(v),1)
people={};
for pk,g in ST.groupby('pk'):
    g=g.sort_values(['yr','min'],ascending=[True,False])
    nm=g.name.value_counts().index[0]
    gr=g[g.adj.notna()]
    sc=float(gr.adj.mean()) if len(gr) else None
    role=g.groupby('pos')['min'].sum().idxmax() if g.pos.notna().any() else ''
    topclub=g.groupby('team')['min'].sum().idxmax()
    # strip alias artefacts of club names are left as in the source
    rows=[[int(r.yr),r.team,r.league,SC[r.src],int(r.mn),r.pos if isinstance(r.pos,str) else '',r1(r.pct),int(r.rs),None if r.g!=r.g else int(r.g),None if r.a!=r.a else int(r.a),r2(r.x90),r2(r.d90),1 if r.gp_only else 0] for r in g.itertuples()]
    people[pk]=dict(name=nm,y0=int(g.yr.min()),y1=int(g.yr.max()),mins=int(g['min'].sum()),score=r1(sc),role=role,ng=int(len(gr)),top=topclub,rows=rows)
ids=sorted(people,key=lambda k:(-people[k]['mins']))
idx=[];bk=collections.defaultdict(dict)
for i,k in enumerate(ids):
    p=people[k]
    if p['mins']<90: continue
    b=nrm(p['name'])[:1]; b=b if b.isalpha() else '#'
    idx.append([i,p['name'],p['y0'],p['y1'],p['mins'],p['score'],p['role'],p['ng'],p['top'],b,','.join(sorted({r[2] for r in p['rows']}))])
    bk[b][i]=p['rows']
gz=lambda o:base64.b64encode(gzip.compress(json.dumps(o,separators=(',',':'),ensure_ascii=False).encode(),9)).decode()
json.dump(dict(idx=gz(idx),ch={b:gz(v) for b,v in sorted(bk.items())},med=MED),open('/home/claude/trc/players.json','w'))
print(len(people),len(idx),sum(len(v) for v in bk.values()),'season rows;',len(open('/home/claude/trc/players.json').read())//1024,'KB')
print(collections.Counter(r[7] for v in bk.values() for rows in v.values() for r in rows))
out=ST[['pk','name','yr','team','league','src','mn','pos','pct','rs','g','a','x90','d90']].rename(columns={'pk':'person_key','yr':'season_start','mn':'minutes','pos':'role','pct':'score','rs':'ungraded_reason'})
out['ungraded_reason']=out.ungraded_reason.map({0:'',1:'under 450 minutes',2:'role unknown',3:'attack data only',4:'no goalkeeper stats'})
out.round(2).to_csv('/home/claude/work/player_seasons_2009_2025.csv',index=False); print(len(out),'csv rows')
