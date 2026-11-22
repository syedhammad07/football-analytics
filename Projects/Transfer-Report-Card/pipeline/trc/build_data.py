import pandas as pd,numpy as np,json
W='/home/claude/work/'
S=pd.read_csv(W+'top5_signings_2010_2025.csv')
M=pd.read_csv(W+'top5_signings_scored_2010_2025.csv')
RP=pd.read_csv(W+'replacements_2010_2025.csv')
key=['player_id','to_club','year']
M=M[key+['fee_adj','raw_mean_pct','mean_se','exp_se','pos','first_pct','mean_pct','basis','resid','full_basis','n_scored']]
import sys,unicodedata,re
def nrm(x): return ' '.join(re.sub(r'[^a-z0-9 ]',' ',unicodedata.normalize('NFKD',str(x)).encode('ascii','ignore').decode().lower()).split())
P=pd.read_csv('/home/claude/scout-finder/data/transfers_summer_2026.csv'); E=pd.read_csv('/home/claude/scout-finder/data/transfers_summer_2026_europe.csv')
P['dt']=pd.to_datetime(P.date,errors='coerce'); P=P[(P.dt>='2026-06-01')&P.to_club.notna()]
E=E[E.to_club.notna()]
mv=pd.concat([P[['player','from_club','to_club']],E[['player','from_club','to_club']]]).drop_duplicates()
mv['pn']=mv.player.map(nrm); mvd={}
for _,r in mv.iterrows(): mvd.setdefault(r.pn,[]).append(r)
def upd(r):
    c=r.current_club if isinstance(r.current_club,str) else ''
    for m in mvd.get(nrm(r.player),[]):
        ft=set(nrm(m.from_club).split())-{'fc','afc','cf','sc','ac','as','club','de','united','city'}
        if ft & set(nrm(c).split()) or ft & set(nrm(r.to_club).split()): return m.to_club
    return c
S['current_club']=S.apply(upd,axis=1)
S['current_status']=S.apply(lambda r:'retired' if r.current_status=='retired' else 'retired (excluded)' if r.retired_flag=='retired' else 'free agent' if r.current_club=='Without Club' else 'at signing club' if str(r.current_club)[:6]==str(r.to_club)[:6] else 'elsewhere',axis=1)
S.to_csv(W+'top5_signings_2010_2025.csv',index=False)
D=S.merge(M,on=key,how='left')
TP=pd.read_csv(W.replace('work/','')+'x' if False else '/mnt/user-data/uploads/football-analytics/Projects/Scout-Finder/data/tm_players.csv.gz',usecols=['player_id','position','sub_position']).set_index('player_id')
def role(p,sb):
    if p=='Midfield': return {'Defensive Midfield':'DM','Central Midfield':'CM','Attacking Midfield':'AM','Left Midfield':'AM','Right Midfield':'AM'}.get(sb,'CM')
    if p=='Defender': return 'FB' if sb in('Left-Back','Right-Back') else 'DF'
    return {'Attack':'FW','Goalkeeper':'GK'}.get(p)
TP['role']=[role(a,b) for a,b in zip(TP.position,TP.sub_position)]
D['pos']=D.pos.fillna(D.player_id.map(TP.role))
D.loc[D.gk==True,'pos']='GK'
D=D.merge(RP.rename(columns={'signing':'player','club':'to_club'})[['player','to_club','year','replaced','replaced_pct_prev','replaced_min_prev','replaced_went_to']],on=['player','to_club','year'],how='left')
def seas(s):
    out=[]
    for p in str(s).split(';'):
        if not p or p=='nan':continue
        y,st,m=p.split(':'); out.append([int(y),st,None if m in('None','nan') else int(float(m))])
    return out
rows=[]
for _,r in D.iterrows():
    exp=None if pd.isna(r.resid) else round(r.mean_pct-r.resid,1)
    rows.append([r.player,r.from_club,r.to_club,r.league,int(r.year),r.pos if isinstance(r.pos,str) else '',round(r.fee_m_eur,2),r.status,
      seas(r.seasons),None if pd.isna(r.mean_pct) else round(r.mean_pct,1),None if pd.isna(r.first_pct) else round(r.first_pct,1),
      r.basis if isinstance(r.basis,str) else '',exp,None if pd.isna(r.resid) else round(r.resid,1),
      r.current_club if isinstance(r.current_club,str) else '',r.current_status,
      r.replaced if isinstance(r.replaced,str) else '',None if pd.isna(r.replaced_pct_prev) else round(r.replaced_pct_prev,1),r.replaced_went_to if isinstance(r.replaced_went_to,str) else '',r.window if isinstance(r.window,str) else 'S',None if pd.isna(r.fee_adj) else round(float(r.fee_adj),1),None if pd.isna(r.raw_mean_pct) else round(float(r.raw_mean_pct),1),None if pd.isna(r.mean_se) else round(float(r.mean_se),1),None if pd.isna(r.exp_se) else round(float(r.exp_se),1)])
rows=[x for x in rows if x[7]!='left early' or True]
json.dump(rows,open('data.json','w'),ensure_ascii=False,separators=(',',':'))
print(len(rows),len(open('data.json').read())//1024,'KB'); print(D.status.value_counts().to_dict())
