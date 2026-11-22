import pandas as pd,numpy as np,warnings; warnings.filterwarnings('ignore')
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import cross_val_predict,GroupKFold
ST=pd.read_pickle('stats_scored.pkl'); S=pd.read_csv('signings_model.csv')
print('fpos values',ST.fpos.value_counts(dropna=False).to_dict())
# (a) broad group mismatch between the signing role and FBref's own position
grp={'FW':'FW','AM':'MF','CM':'MF','DM':'MF','DF':'DF','FB':'DF','GK':'GK'}
x=ST[(ST['min']>=450)&ST.pos.notna()&ST.fpos.notna()].copy(); x['g']=x.pos.map(grp)
x['f']=x.fpos.astype(str).str[:2]
print('TM vs FBref broad position agreement',(x.g.str[:2]==x.f.str[:2]).mean().round(3), len(x))
# (b) centre-back vs full-back from stats
d=ST[(ST['min']>=900)&ST.pos.isin(['DF','FB'])&ST.src.isin(['Opta','FBref'])&(ST.yr>=2016)].copy()
m=d['min']/90
for c in ['cl','aer','ic','tk','kp','dr','sh','pc','pt','oph','fl','duw','dl','aerl','rec']: d[c+'90']=d[c]/m
d['aerp']=d.aer/(d.aer+d.aerl); d['accu']=d.pc/d.pt; d['ophs']=d.oph/d.pc
feat=['cl90','aer90','ic90','tk90','kp90','dr90','sh90','pc90','fl90','aerp','accu','ophs']
d=d.dropna(subset=feat+['x90']); d['x90f']=d.x90
feat+=['x90f']
# standardise within source+year so Opta/FBref scales don't mix
for c in feat: d[c]=d.groupby(['src','yr'])[c].transform(lambda s:(s-s.mean())/s.std())
y=(d.pos=='FB').astype(int).values
d['pid']=d.nn
p=cross_val_predict(LogisticRegression(C=1.0,max_iter=500),d[feat].values,y,cv=GroupKFold(5),groups=d.pid.values,method='predict_proba')[:,1]
d['pfb']=p; print('CB/FB season-level accuracy',((p>.5)==y).mean().round(3),'FB share',y.mean().round(2),'n',len(d))
pl=d.groupby('nn').agg(pfb=('pfb','mean'),n=('pfb','size'),lab=('pos','first')).reset_index()
pl['flag']=np.where((pl.lab=='DF')&(pl.pfb>=.8),'to FB',np.where((pl.lab=='FB')&(pl.pfb<=.2),'to CB',''))
print(pl.flag.value_counts().to_dict(),'of',len(pl))
pl.to_csv('rolecheck_players.csv',index=False)
S['nn']=S.player.map(lambda v:' '.join(__import__('unicodedata').normalize('NFKD',str(v)).encode('ascii','ignore').decode().lower().replace('-',' ').replace("'",' ').split()))
f=S.merge(pl[pl.flag!=''][['nn','pfb','flag','n']],on='nn')
f=f[f.pos.isin(['DF','FB'])]
print('graded signings flagged:',len(f),'of',(S.pos.isin(['DF','FB'])).sum()); print(f[['player','to_club','year','pos','pfb','flag','n']].head(25).to_string())
f.to_csv('role_flags.csv',index=False)
