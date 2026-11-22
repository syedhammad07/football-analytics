import pandas as pd,numpy as np,warnings; warnings.filterwarnings('ignore')
import statsmodels.formula.api as smf
from sklearn.model_selection import KFold
A=pd.read_csv('signings_model.csv'); F=A[A.resid.notna()].copy(); F['sec']=np.where(F.league=='ENG','PL','REST')
F['lf']=np.log2(F.fee_adj)
print(len(F),F.sec.value_counts().to_dict())
fp='mean_pct ~ lf + C(pos) + C(year) + C(league) + C(window)'
fi='mean_pct ~ lf*C(sec) + C(pos) + C(year) + C(league) + C(window)'
fs='mean_pct ~ lf + C(pos) + C(year) + C(window)'
kf=KFold(10,shuffle=True,random_state=1); res={k:np.zeros(len(F)) for k in ['pooled','interaction','split']}
F=F.reset_index(drop=True)
for tr,te in kf.split(F):
    T,V=F.iloc[tr],F.iloc[te]
    # year levels unseen in training are rare; clip
    res['pooled'][te]=smf.ols(fp,data=T).fit().predict(V)
    res['interaction'][te]=smf.ols(fi,data=T).fit().predict(V)
    for s in ['PL','REST']:
        t=T[T.sec==s]; v=V[V.sec==s]
        if len(v): res['split'][v.index]=smf.ols(fs+('' if s=='PL' else ' + C(league)'),data=t).fit().predict(v)
for k,p in res.items():
    e=F.mean_pct-p; print(k,'CV RMSE',round(np.sqrt((e**2).mean()),3),'CV R2',round(1-(e**2).sum()/((F.mean_pct-F.mean_pct.mean())**2).sum(),4))
m=smf.ols(fi,data=F).fit(); print(m.summary().tables[1].as_text().split('\n')[1:3]); print({k:round(v,2) for k,v in m.params.items() if 'lf' in k}, {k:round(v,3) for k,v in m.pvalues.items() if 'lf' in k})
for s,g in F.groupby('sec'):
    mm=smf.ols(fs+('' if s=='PL' else ' + C(league)'),data=g).fit(); print(s,len(g),'slope',round(mm.params.lf,2),'se',round(mm.bse.lf,2),'R2',round(mm.rsquared,3))
