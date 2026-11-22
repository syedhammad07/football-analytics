import pandas as pd,numpy as np
D='/mnt/user-data/uploads/football-analytics/Projects/Scout-Finder/data/'
o=pd.read_csv('top5_signings_2019_2025.csv')
n=pd.read_pickle('signings_2010_2025.pkl'); n=n[n.year>=2019]
e=pd.read_pickle('signings_ew_2010_2022.pkl')
import unicodedata as _u,re as _r
_k=lambda x:' '.join(_r.sub(r'[^a-z0-9 ]',' ',_u.normalize('NFKD',str(x)).encode('ascii','ignore').decode().lower()).split())
have={(_k(a),b_,c) for a,b_,c in zip(n.player,n.to_club,n.year)}
e=e[(e.year<2019)|~pd.Series([(_k(a),b_,c) in have for a,b_,c in zip(e.player,e.to_club,e.year)],index=e.index)]
n=pd.concat([n,e.drop(columns=['sub'])],ignore_index=True); n['window']='S'
w=pd.read_pickle('signings_winter.pkl'); sk={(_k(a),b_,c) for a,b_,c in zip(n.player,n.to_club,n.year)}
w=w[[(_k(a),b_,c) not in sk for a,b_,c in zip(w.player,w.to_club,w.year)]]
n=pd.concat([n,w],ignore_index=True)
tp=pd.read_csv(D+'tm_players.csv.gz',usecols=['player_id','position','current_club_name','last_season']).set_index('player_id')
n['position_tm']=n.player_id.map(tp.position).fillna(n.position_tm); n['fee_m_eur']=(n.fee_eur/1e6).round(2)
tpn=pd.read_csv(D+'tm_players.csv.gz',usecols=['player_id','name','current_club_name','last_season','position','sub_position'])
import unicodedata,re
nr=lambda x:' '.join(re.sub(r'[^a-z0-9 ]',' ',unicodedata.normalize('NFKD',str(x)).encode('ascii','ignore').decode().lower()).split())
tpn['nn']=tpn.name.map(nr); tpu=tpn.drop_duplicates('nn',keep=False).set_index('nn')
nn_=n.player.map(nr)
def _role(p,sb):
    if p=='Midfield': return {'Defensive Midfield':'DM','Central Midfield':'CM','Attacking Midfield':'AM','Left Midfield':'AM','Right Midfield':'AM'}.get(sb,'CM')
    if p=='Defender': return 'FB' if sb in('Left-Back','Right-Back') else 'DF'
    return {'Attack':'FW','Goalkeeper':'GK'}.get(p)
trole=pd.Series([_role(a_,b_) for a_,b_ in zip(tpu.position,tpu.sub_position)],index=tpu.index)
neg=n.player_id<0; fix=nn_.map(trole).where(nn_.str.contains(' '))
chg=(neg&fix.notna()&(fix!=n.pos_text)).sum(); print('ew rows whose role was replaced by the Transfermarkt role:',chg)
n.loc[neg&fix.notna(),'pos_text']=fix[neg&fix.notna()]
key=['player_id','to_club','year']
old=o[key+['fee_m_eur','current_club','current_status','retired_flag']].rename(columns={'fee_m_eur':'fee_old'}).drop_duplicates(key)
n=n.merge(old,on=key,how='left')
n['fee_m_eur']=n.fee_old.fillna(n.fee_m_eur); 
ls=n.player_id.map(tp.last_season).fillna(nn_.map(tpu.last_season)); cc=n.player_id.map(tp.current_club_name).fillna(nn_.map(tpu.current_club_name)).where((ls>=2024)|ls.isna(),'Retired')
n['current_club']=n.current_club.fillna(cc.where(cc!='Retired','Retired').fillna(''))
n['current_status']=n.current_status.fillna(pd.Series(np.where(n.current_club=='Retired','retired',np.where(n.current_club=='','unknown',np.where(n.current_club.astype(str).str[:6]==n.to_club.astype(str).str[:6],'at signing club','elsewhere'))),index=n.index))
cols=['window','pos_text','player','player_id','position_tm','gk','from_club','to_club','league','date','year','fee_m_eur','status','n_whole','left_early','seasons','current_club','current_status','retired_flag']
n=n[n.year>=2017]  # scope: all five leagues from 2017/18
n[cols].to_csv('top5_signings_2010_2025.csv',index=False); print(len(n),n.year.min(),n.current_status.value_counts().to_dict(),n.fee_m_eur.isna().sum())
