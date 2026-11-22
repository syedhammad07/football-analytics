import pandas as pd,numpy as np,json,re,sys
exec(open('build3b.py').read().split("# ---- stats sources")[0])
ST=pd.read_pickle('stats_all.pkl')
tp=pd.read_csv(D+'tm_players.csv.gz',usecols=['player_id','position','sub_position','name']).set_index('player_id')
sig=pd.read_csv('top5_signings_2010_2025.csv')
def role(position,sub):
    if position=='Midfield':
        return {'Defensive Midfield':'DM','Central Midfield':'CM','Attacking Midfield':'AM','Left Midfield':'AM','Right Midfield':'AM'}.get(sub,'CM')
    if position=='Defender': return 'FB' if sub in('Left-Back','Right-Back') else 'DF'
    return {'Attack':'FW','Goalkeeper':'GK'}.get(position)
tp['role']=[role(a,b) for a,b in zip(tp.position,tp.sub_position)]
sig['pos']=sig.player_id.map(tp.role)
sig['pos']=sig.pos.fillna(sig.pos_text)
sig.loc[sig.gk==True,'pos']='GK'
# ---- per-90 score for every stats row: (xG+xA)/90, percentile within source+season+position group (min>=450)
ST['pid']=np.nan
nm=tp.reset_index(); nm['nn']=nm.name.map(lambda x:' '.join(norm(x).split()))
byn=nm.groupby('nn').player_id.apply(list)
ST['pos']=ST.nn.map(lambda n:None)
# position per stats row via TM when name unique, else leave None
nm['role']=[role(a,b) for a,b in zip(nm.position,nm.sub_position)]
u=nm.drop_duplicates('nn',keep=False).set_index('nn').role
ST['pos']=ST.nn.map(u)
sg={}
for _,r in sig.iterrows():
    cid_=next((k for k,v in CL.items() if v[0]==r.league and v[1]==r.to_club),None)
    if isinstance(r.pos,str): sg[(r.league,' '.join(norm(r.player).split()),cid_)]=r.pos
sp=[next((sg[(l,n,c_)] for c_ in cs if (l,n,c_) in sg),None) for l,n,cs in zip(ST.league,ST.nn,ST.cands)]
ST['pos']=pd.Series(sp,index=ST.index).fillna(ST.pos)
fp=ST.fpos.map(lambda x:{'FW':'FW','DF':'DF'}.get(x) if isinstance(x,str) else None)
ST['pos']=ST.pos.fillna(fp)
# role overrides from the role check (stats profile and FBref position agree against the Transfermarkt label)
_OV={'erik pieters':'FB','daryl janmaat':'FB','marcos alonso':'FB','jetro willems':'FB','vlad chiriches':'DF'}
_nn=lambda x:' '.join(norm(x).split())
sig['pos']=[_OV.get(_nn(p),r) for p,r in zip(sig.player,sig.pos)]
ST['pos']=[_OV.get(n,r) if isinstance(r,str) and r in('DF','FB','DM') else r for n,r in zip(ST.nn,ST.pos)]
ST['x90']=np.where(ST.xg.notna()&ST.xa.notna(),ST.xg+ST.xa,ST.g+ST.a)/(ST['min']/90)
ST['ga_only']=ST.xg.isna()|ST.xa.isna()
ST['d90']=(ST.tk+ST.ic+ST.cl)/(ST['min']/90)
ST['gp90']=ST.gp/(ST['min']/90)
ST['xnum']=np.where(ST.xg.notna()&ST.xa.notna(),ST.xg+ST.xa,ST.g+ST.a)
ST.loc[ST.gk==True,'pos']='GK'
ST['pa']=np.nan; ST['pdf']=np.nan; ST['pgk']=np.nan
# team-adjusted defensive involvement (defender rework): player's d90 relative to the team's rate per outfield minute
ng=ST[(ST.pos!='GK')&ST.d90.notna()&(ST['min']>0)]
tg=ng.groupby(['src','yr','league','team']).apply(lambda g:(g.tk+g.ic+g.cl).sum()/(g['min'].sum()/90)).rename('team_d90')
ST=ST.merge(tg.reset_index(),on=['src','yr','league','team'],how='left')
def team_rate(col):
    x=ST[(ST.pos!='GK')&ST[col].notna()&(ST['min']>0)]
    return x.groupby(['src','yr','league','team']).apply(lambda g:g[col].sum()/(g['min'].sum()/90)).rename('team_'+col)
for col in ['pc','oph','rec']:
    ST=ST.merge(team_rate(col).reset_index(),on=['src','yr','league','team'],how='left')
_o=ST[(ST.pos!='GK')&ST.xnum.notna()&(ST['min']>0)]
_t=_o.groupby(['src','yr','league','team']).apply(lambda g:g.xnum.sum()/(g['min'].sum()/90)).rename('team_x90')
ST=ST.merge(_t.reset_index(),on=['src','yr','league','team'],how='left')
ST['xrel']=ST.x90/ST.team_x90
ST['inv']=ST.d90/ST.team_d90
ST['ppc']=(ST.pc/(ST['min']/90))/ST.team_pc; ST['pacc']=ST.pc/ST.pt; ST['poph']=(ST.oph/(ST['min']/90))/ST.team_oph; ST['prec']=(ST.rec/(ST['min']/90))/ST.team_rec
ST['bon']=np.minimum(10,25*(ST.g+ST.a)/(ST['min']/90)).where(ST.g.notna()&ST.a.notna()&(ST['min']>0))
ST['dq']=ST.duw/(ST.duw+ST.dl); ST['aq']=ST.aer/(ST.aer+ST.aerl); ST['oph90']=ST.oph/(ST['min']/90)
for c in ['pinv','pdq','paq','pph','qpc','qacc','qoph','qrec','pta']: ST[c]=np.nan
for k,g in ST[(ST['min']>=450)&ST.pos.isin(['FW','AM','CM','DM','DF','FB'])].groupby(['src','yr','pos']):
    a=g[g.x90.notna()]; ST.loc[a.index,'pa']=a.x90.rank(pct=True)*100
    xr=g[g.xrel.notna()&np.isfinite(g.xrel)]
    if len(xr)>=15: ST.loc[xr.index,'pta']=xr.xrel.rank(pct=True)*100
    d=g[g.d90.notna()]; ST.loc[d.index,'pdf']=d.d90.rank(pct=True)*100
    if k[2] in('CM',):
        for col,out in [('ppc','qpc'),('pacc','qacc'),('poph','qoph'),('prec','qrec'),('dq','pdq')]:
            v=g[g[col].notna()&np.isfinite(g[col])]
            if len(v)>=15: ST.loc[v.index,out]=v[col].rank(pct=True)*100
    if k[2] in('DF','DM','FB'):
        for col,out in [('inv','pinv'),('dq','pdq'),('aq','paq'),('oph90','pph')]:
            v=g[g[col].notna()&np.isfinite(g[col])]
            if len(v)>=15: ST.loc[v.index,out]=v[col].rank(pct=True)*100
for k,g in ST[(ST['min']>=450)&(ST.pos=='GK')&ST.gp90.notna()].groupby(['src','yr']):
    ST.loc[g.index,'pgk']=g.gp90.rank(pct=True)*100
def comp(r):
    if r.pos=='GK': return (r.pgk,'GK saves above average' if r.gk_basic==1 else 'GK goals prevented') if r.pgk==r.pgk else (np.nan,'')
    a,d=r.pa,r.pdf
    if r.pos in('FW','AM'):
        if a!=a: return (np.nan,'')
        t=r.pta
        v=0.5*a+0.5*t if t==t else a
        suf=' + ' if False else ''
        if r.ga_only: return (v,'attack (goals + assists, team-adjusted)' if t==t else 'attack (goals + assists)')
        return (v,'attack (team-adjusted)' if t==t else 'attack')
    if r.pos=='FB':
        if r.pinv==r.pinv:
            parts=[(0.5,r.pinv),(0.25,r.pdq),(0.25,r.paq)]
            parts=[(w,x) for w,x in parts if x==x]
            base=sum(w*x for w,x in parts)/sum(w for w,x in parts)
            if a==a: return (0.6*base+0.4*a,'full-back: defence (team-adjusted) + attacking output')
            return (base,'full-back: defence (team-adjusted) + attacking output')
        return (a,'attack only') if a==a else (np.nan,'')
    if r.pos=='CM':
        if r.qpc==r.qpc:
            parts=[(0.30,r.qpc),(0.20,r.qacc),(0.20,r.qoph),(0.15,r.qrec),(0.15,r.pdq)]
            parts=[(w,x) for w,x in parts if x==x]
            base=sum(w*x for w,x in parts)/sum(w for w,x in parts)
            bon=r.bon if r.bon==r.bon else 0.0
            return (min(100.0,base+bon),'midfield control (team-adjusted) + goal/assist bonus')
        return (a,'attack only') if a==a else (np.nan,'')
    if d==d and r.pinv==r.pinv:
        parts=[(0.5,r.pinv),(0.25,r.pdq),(0.25,r.paq)]
        parts=[(w,x) for w,x in parts if x==x]
        base=sum(w*x for w,x in parts)/sum(w for w,x in parts)
        bon=r.bon if r.bon==r.bon else 0.0
        return (min(100.0,base+bon),'defence (team-adjusted) + goal/assist bonus')
    if a==a and d==d: return (0.25*a+0.75*d,'defence+attack')
    return (a,'attack only') if a==a else (np.nan,'')
cc=ST.apply(comp,axis=1,result_type='expand'); ST['pct']=cc[0]; ST['basis']=cc[1]
ST['pbase']=np.where(ST.basis.str.contains('bonus',na=False),ST.pct-ST.bon.fillna(0),np.nan)
ST.to_pickle('stats_scored.pkl')
# ---- attach to signings: per counted season percentile for the signing at the club
rows=[]
cl_by_name={v[2]:k for k,v in CL.items()}
for _,r in sig.iterrows():
    if r.retired_flag==r.retired_flag and r.retired_flag=='retired': continue
    cid=next((k for k,v in CL.items() if v[0]==r.league and v[1]==r.to_club),None)
    nn=' '.join(norm(r.player).split())
    out=[]
    for s in str(r.seasons).split(';'):
        if not s or s=='nan': continue
        yr,st,m=s.split(':'); yr=int(yr)
        g=ST[(ST.league==r.league)&(ST.yr==yr)&(ST.nn==nn)&ST.cands.map(lambda c:cid in c)]
        if g.empty: continue
        row=g.sort_values('min',ascending=False).iloc[0]
        out.append((yr,row['min'],row.x90,row.pct,row.src,row.basis))
    ok=[o for o in out if o[3]==o[3]]
    d=r.to_dict(); d['n_scored']=len(ok)
    sh=lambda o:50+(o[1]/(o[1]+300.0))*(o[3]-50) if o[1]==o[1] else o[3]
    d['first_pct']=sh(ok[0]) if ok else np.nan
    d['mean_pct']=np.mean([sh(o) for o in ok]) if ok else np.nan
    d['raw_mean_pct']=np.mean([o[3] for o in ok]) if ok else np.nan
    if ok:
        vs=[(o[1]/(o[1]+300.0))**2*(170.0+334.8*1000.0/max(o[1],450.0)) for o in ok]
        d['mean_se']=float(np.sqrt(sum(vs))/len(ok))
    else: d['mean_se']=np.nan
    d['first_x90']=ok[0][2] if ok else np.nan
    d['src']=ok[0][4] if ok else ''
    d['basis']=ok[0][5] if ok else ''
    rows.append(d)
R=pd.DataFrame(rows)
R.to_csv('signings_scored.csv',index=False)
print(len(R),R.first_pct.notna().sum()); print(R.groupby(['pos','basis']).size())
