import pandas as pd,numpy as np
exec(open('/home/claude/work/build3b.py').read().split("# ---- stats sources")[0])
ST=pd.read_pickle('stats_scored.pkl'); R=pd.read_csv('signings_model.csv')
R=R[R.resid.notna()&(R.window=='S')|R.resid.notna()&(R.window=='W')].copy()
key={}
for (lg,yr,nn),g in ST.groupby(['league','yr','nn']): key[(lg,yr,nn)]=g
rows=[];allr=[]
for r in R.itertuples():
    cid=next((k for k,v in CL.items() if v[0]==r.league and v[1]==r.to_club),None)
    nn=' '.join(norm(r.player).split()); ps=[]
    for s in str(r.seasons).split(';'):
        if not s: continue
        y=int(s.split(':')[0]); g=key.get((r.league,y,nn))
        if g is None: continue
        g=g[g.cands.map(lambda c:cid in c)]
        if g.empty: continue
        x=g.sort_values('min',ascending=False).iloc[0]
        if x.pct==x.pct and x['min']>=450: ps.append((y,x.pct,x['min']))
    if len(ps)>=1: allr.append(dict(first=ps[0][1],exp=r.mean_pct-r.resid,fee_adj=r.fee_adj,stay=len(ps)>=2,k=len(str(r.seasons).split(';'))))
    if len(ps)>=2:
        exp=r.mean_pct-r.resid
        rows.append(dict(player=r.player,club=r.to_club,year=r.year,pos=r.pos,fee=r.fee_m_eur,fee_adj=r.fee_adj,exp=exp,first=ps[0][1],later=np.mean([p[1] for p in ps[1:]]),n_later=len(ps)-1,y1=ps[0][0],yl=ps[-1][0]))
B=pd.DataFrame(rows); B['r1']=B['first']-B.exp; B['rl']=B.later-B.exp
def tier(r):
    v=r.r1
    if r.fee_adj<=5 and v>=15: return '1 Bargain'
    if v>=30: return '2 Great value'
    if v>=15: return '3 Good value'
    if v>-15: return '4 About fair'
    return '5 Overpriced' if r['first']>=25 else '6 Poor signing'
B['tier']=B.apply(tier,axis=1)
B.to_csv('backtest.csv',index=False)
print('signings with 2+ graded seasons',len(B))
print('corr first-season value vs later value',round(B.r1.corr(B.rl),3),'| first score vs later score',round(B['first'].corr(B.later),3),'| fee-predicted vs later score',round(B.exp.corr(B.later),3))
t=B.groupby('tier').agg(n=('r1','size'),first_value=('r1','mean'),later_value=('rl','mean'),later_score=('later','mean'),beat_fee_later=('rl',lambda s:(s>0).mean())).round(2); print(t.to_string())
import statsmodels.formula.api as smf
for f in ['later ~ exp','later ~ first','later ~ first + exp']:
    m=smf.ols(f,data=B).fit(); print(f,'R2',round(m.rsquared,3),{k:round(v,2) for k,v in m.params.items()})
print('by position corr r1~rl'); print(B.groupby('pos').apply(lambda g:pd.Series({'n':len(g),'corr':g.r1.corr(g.rl)})).round(2).to_string())
# top vs bottom
q=B.r1.quantile([.2,.8]); print('top20% later value',round(B[B.r1>=q[.8]].rl.mean(),1),'bottom20%',round(B[B.r1<=q[.2]].rl.mean(),1))
# bootstrap CI for tier gap
rng=np.random.default_rng(1); a=B[B.tier.isin(['1 Bargain','2 Great value','3 Good value'])].rl.values; b=B[B.tier.isin(['5 Overpriced','6 Poor signing'])].rl.values
d=[rng.choice(a,len(a)).mean()-rng.choice(b,len(b)).mean() for _ in range(2000)]; print('good-minus-poor later value gap',round(a.mean()-b.mean(),1),'95% CI',np.percentile(d,[2.5,97.5]).round(1))

A=pd.DataFrame(allr); A=A[A.k>=2]; A['r1']=A['first']-A.exp
A['tier']=A.apply(lambda r:'1 Bargain' if r.fee_adj<=5 and r.r1>=15 else '2 Great' if r.r1>=30 else '3 Good' if r.r1>=15 else '4 Fair' if r.r1>-15 else '5 Over' if r['first']>=25 else '6 Poor',axis=1)
print('RETENTION (had 2+ counted seasons available): share with a 2nd graded season'); print(A.groupby('tier').agg(n=('stay','size'),stayed_and_played=('stay','mean')).round(2).to_string())
