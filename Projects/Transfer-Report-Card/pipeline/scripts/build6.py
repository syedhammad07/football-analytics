import pandas as pd,numpy as np
exec(open('build3b.py').read().split("# ---- stats sources")[0])
ST=pd.read_pickle('stats_scored.pkl')
R=pd.read_csv('signings_model.csv'); R=R[R.window=='S']
tp=pd.read_csv(D+'tm_players.csv.gz',usecols=['player_id','position','sub_position','name']).set_index('player_id')
def role(position,sub):
    if position=='Midfield':
        return {'Defensive Midfield':'DM','Central Midfield':'CM','Attacking Midfield':'AM','Left Midfield':'AM','Right Midfield':'AM'}.get(sub,'CM')
    if position=='Defender': return 'FB' if sub in('Left-Back','Right-Back') else 'DF'
    return {'Attack':'FW','Goalkeeper':'GK'}.get(position)
tp['role']=[role(a,b_) for a,b_ in zip(tp.position,tp.sub_position)]
dep=tm[(tm.d>='2010-01-01')&(tm.d<='2026-01-01')&tm.from_club_id.isin(CL)].copy()
dep=dep[~dep.to_club_name.fillna('').str.contains(yth)&~dep.to_club_name.isin(['Retired','Career break'])]
dep['pos']=dep.player_id.map(tp.role); dep['nn']=dep.player_id.map(tp.name).map(lambda x:' '.join(norm(x).split()))
out=[]
for _,r in R.iterrows():
    cid=next((k for k,v in CL.items() if v[0]==r.league and v[1]==r.to_club),None)
    d0=pd.Timestamp(r.date)
    c=dep[(dep.from_club_id==cid)&(dep.pos==r.pos)&(dep.d>=d0-pd.Timedelta(days=200))&(dep.d<=d0+pd.Timedelta(days=100))&(dep.player_id!=r.player_id)]
    best=None
    for _,x in c.iterrows():
        g=ST[(ST.league==r.league)&(ST.yr==r.year-1)&(ST.nn==x.nn)&ST.cands.map(lambda cc:cid in cc)]
        if g.empty or not (g['min'].iloc[0]>=900): continue
        if best is None or g['min'].iloc[0]>best[1]: best=(x.player_name,g['min'].iloc[0],g.pct.iloc[0],x.d.date(),x.to_club_name)
    if best is None or best[2]!=best[2] or r.first_pct!=r.first_pct: continue
    out.append(dict(signing=r.player,club=r.to_club,league=r.league,year=r.year,pos=r.pos,fee_m_eur=r.fee_m_eur,signing_first_pct=round(r.first_pct,1),
      replaced=best[0],replaced_min_prev=int(best[1]),replaced_pct_prev=round(best[2],1),replaced_left_on=best[3],replaced_went_to=best[4],change=round(r.first_pct-best[2],1)))
O=pd.DataFrame(out); O.to_csv('replacements_2010_2025.csv',index=False)
print(len(O)); print(O.change.describe().round(1)); print((O.change>0).mean().round(3))
print(O.groupby(pd.cut(O.fee_m_eur,[0,5,15,40,300])).change.agg(['count','mean']).round(1))
print(O.sort_values('change',ascending=False).head(5).to_string()); 
