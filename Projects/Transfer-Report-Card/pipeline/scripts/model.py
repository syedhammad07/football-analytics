import pandas as pd,numpy as np
import statsmodels.formula.api as smf
R=pd.read_csv('signings_scored.csv'); R['window']=R.window.fillna('S')
R['full_basis']=R.basis.isin(['attack','attack (goals + assists)','attack+defence','defence+attack','defence (team-adjusted) + goal/assist bonus','midfield control (team-adjusted) + goal/assist bonus','GK goals prevented','GK saves above average','attack (team-adjusted)','attack (goals + assists, team-adjusted)','full-back: defence (team-adjusted) + attacking output'])
import numpy as _np
R['sec']=_np.where(R.league=='ENG','PL','REST')
_lg=R[R.fee_m_eur>0].groupby(['sec','year']).fee_m_eur.apply(lambda s:_np.log(s).mean())   # log geometric-mean fee per section and year
_parts=[]
for _s,_g in _lg.groupby(level=0):
    _g=_g.droplevel(0); _parts.append(_g.rolling(3,center=True,min_periods=2).mean().rename(_s))
_sm=pd.concat(_parts,axis=1)   # columns PL / REST
print('geo-mean fee by section and year',_np.exp(_sm).round(1).to_dict())
R['fee_adj']=(R.fee_m_eur*_np.exp(_np.array([_sm.loc[2025,s]-_sm.loc[y,s] for s,y in zip(R.sec,R.year)]))).round(2)
A=R[R.mean_pct.notna()&(R.fee_m_eur>0)].copy(); A['lf']=np.log2(A.fee_adj)
A['sec']=np.where(A.league=='ENG','PL','REST')
F=A[A.full_basis].copy(); F['rest']=(F.sec=='REST').astype(int)
# separate fee slope for the Premier League section and the other four leagues (slopes differ, p=0.03; CV error is no worse than pooled)
m=smf.ols('mean_pct ~ lf + lf:rest + C(pos) + C(year) + C(league) + C(window)',data=F).fit()
print('N',len(F),'R2',round(m.rsquared,3),'lf (PL)',round(m.params.lf,2),'lf (rest)',round(m.params.lf+m.params['lf:rest'],2))
for p,g in F.groupby('pos'):
    mm=smf.ols('mean_pct ~ lf + C(league)',data=g).fit(); print(p,len(g),round(mm.params['lf'],2),'se',round(mm.bse['lf'],2),'R2',round(mm.rsquared,3))
F['resid']=m.resid
F['exp_se']=m.get_prediction(F).se_mean
A=A.merge(F[['player_id','to_club','year','resid','exp_se']],on=['player_id','to_club','year'],how='left')
A.to_csv('signings_model.csv',index=False)
cols=['player','to_club','year','pos','fee_m_eur','mean_pct','resid']
print(F[F.pos=='DF'].sort_values('resid').head(8)[cols].round(1).to_string()); print(F[F.pos=='DF'].sort_values('resid',ascending=False).head(8)[cols].round(1).to_string())
print(A[A.player.str.contains('Dias|Caicedo|Rice')&(A.pos!='')][cols].round(1).to_string())
