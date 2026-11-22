exec(open('build3b.py').read().split("# ---- stats sources")[0])
import re
ST=pd.read_pickle('stats_all.pkl')
LG={'Premier League':'ENG','1 Bundesliga':'GER','Serie A':'ITA','Primera Division':'ESP','Ligue 1':'FRA'}
E=pd.concat([pd.read_csv(f'ew/{f}.csv') for f in ['premier-league','1-bundesliga','serie-a','primera-division','ligue-1']],ignore_index=True)
E['lg']=E.league_name.map(LG)
GEN={'fc','afc','cf','sc','ac','as','ssc','sv','vfl','vfb','fsv','tsg','1','04','05','ud','cd','rc','us','ogc','rcd','calcio','ss','sd','de','le','the','1899','1846','1860','1907','1909','1913','1893','1900','1910','1919','1948','1901','fk','sk','bsc','ca','cfc','spvgg','sg','bv','sas','cds'}
def sig_t(s): return {w for w in toks(s) if w not in GEN}
CS={k:sig_t(v[3]) for k,v in CL.items()}
cache={}
OV={'RCD Espanyol Barcelona':714,'Athlétic Club Arlésien':11300,'1.FC Kaiserslautern':900001}
def cid_of(lg,name):
    if name in OV: return OV[name]
    if (lg,name) in cache: return cache[(lg,name)]
    t=sig_t(name); c=[k for k,v in CL.items() if v[0]==lg and t and t<=CS[k]]
    if len(c)!=1:
        c2=[k for k,v in CL.items() if v[0]==lg and t and (CS[k]<=t or len(t&CS[k])>=1 and len(CS[k])>0 and t&CS[k]==t&CS[k] and len(t&CS[k])>=max(1,len(t)-1))]
        c=c if len(c)>1 else c2
    cache[(lg,name)]=c[0] if len(c)>=1 else None
    if len(c)>1: cache[(lg,name)]=sorted(c,key=lambda k:len(CS[k]))[0]
    return cache[(lg,name)]
E['cid']=[cid_of(l,n) for l,n in zip(E.lg,E.club_name)]
un=E[(E.transfer_movement=='in')&E.cid.isna()&E.year.between(2009,2022)]
print('unresolved clubs',un.groupby(['lg','club_name']).size().to_dict())
PM={'Centre-Forward':'FW','Second Striker':'FW','Left Winger':'FW','Right Winger':'FW','attack':'FW','Centre-Back':'DF','Left-Back':'FB','Right-Back':'FB','Sweeper':'DF','defence':'DF','Goalkeeper':'GK','Defensive Midfield':'DM','Central Midfield':'CM','Attacking Midfield':'AM','Left Midfield':'AM','Right Midfield':'AM','midfield':'CM'}
I=E[(E.transfer_movement=='in')&(E.transfer_period=='Summer')&E.year.between(2009,2022)&(E.fee_cleaned>0)&E.cid.notna()].copy()
I=I[~I.club_involved_name.fillna('').str.contains(yth)]
I=I.drop_duplicates(['lg','club_name','player_name','year'])
O=E[(E.transfer_movement=='out')&~E.fee.fillna('').str.contains('End of loan',case=False)]
outs={}
for r in O.itertuples(): outs.setdefault((r.cid,r.player_name),[]).append((r.year,r.transfer_period))
idx={}
for (lg,yr),g in ST.groupby(['league','yr']): idx[(lg,yr)]=g
def find(lg,cid,name,yr):
    g=idx.get((lg,yr))
    if g is None: return 'data gap',None,None,False,'no source'
    club_rows=g[g.cands.map(lambda c:cid in c)]
    if club_rows.empty: return 'club not in league',None,None,False,''
    nn=' '.join(norm(name).split())
    h=club_rows[club_rows.nn==nn]
    if h.empty: h=club_rows[club_rows.name.map(lambda n:_names_match(n,name))]
    if h.empty: return 'no appearances',0,0,False,''
    m=h['min'].sum(min_count=1); gk=bool(h.gk.any()); src=h.src.iloc[0]
    if pd.isna(m): return 'data gap',None,int(h.mp.sum()),gk,src+' no minutes'
    return ('usable' if m>=450 else 'low minutes'),int(m),int(h.mp.sum()),gk,src

IW=E[(E.transfer_movement=='in')&(E.transfer_period=='Winter')&E.year.between(2009,2022)&(E.fee_cleaned>0)&E.cid.notna()].copy()
IW=IW[~IW.club_involved_name.fillna('').str.contains(yth)].drop_duplicates(['lg','club_name','player_name','year'])
rows=[]
def mk(pid,name,frm,cid,lg,yr,fee,seas,left,gkpos,pos_text,position_tm,date):
    seas=[x for x in seas if x[1]!='club not in league']
    gk=any(x[4] for x in seas) or gkpos
    st=[x[1] for x in seas]
    overall=('usable' if 'usable' in st else 'low minutes' if 'low minutes' in st else 'no appearances' if 'no appearances' in st else 'data gap' if 'data gap' in st else ('left early' if left or not seas else '?'))
    return dict(player_id=pid,player=name,from_club=frm,to_club=CL[cid][1],league=lg,date=date,year=yr,fee_eur=fee,status=overall,n_whole=len(seas),left_early=left and not seas,gk=gk,
      seasons=';'.join(f"{x[0]}:{x[1]}:{x[2]}" for x in seas),pos_text=pos_text,position_tm=position_tm,sub='',window='W')
for i,r in enumerate(IW.itertuples()):
    ol=outs.get((r.cid,r.player_name),[]); yr=r.year; left=False; seas=[]
    if any((y==yr and p=='Winter') or (y==yr+1 and p=='Summer') for y,p in ol): left=True
    else:
        for s in range(yr+1,2026):
            if any(y==s and p=='Winter' for y,p in ol): left=True;break
            seas.append((s,)+find(r.lg,r.cid,r.player_name,s))
            if any(y==s+1 and p=='Summer' for y,p in ol): break
    pt=PM.get(r.position)
    rows.append(mk(-(100000+i),r.player_name,r.club_involved_name,r.cid,r.lg,yr,r.fee_cleaned*1e6,seas,left,r.position=='Goalkeeper',pt,{'FW':'Attack','DF':'Defender','FB':'Defender','GK':'Goalkeeper'}.get(pt,'Midfield'),f'{yr+1}-01-15'))
# TM-based winters, seasons 2023 and 2024 (Jan 2024, Jan 2025)
x=tm[(tm.d>='2024-01-01')&(tm.d<'2025-03-01')&tm.to_club_id.isin(CL)&(tm.transfer_fee>0)&tm.d.dt.month.isin([1,2])].copy()
x=x[~x.from_club_name.fillna('').str.contains(yth)]
tp=pd.read_csv(D+'tm_players.csv.gz',usecols=['player_id','position']).set_index('player_id')
dep=tm[['player_id','from_club_id','d']]
for r in x.itertuples():
    yr=r.d.year-1; cid=r.to_club_id; lg=CL[cid][0]; seas=[]; left=False
    for s in range(yr+1,2026):
        end=pd.Timestamp(f'{s+1}-06-01')
        if ((dep.player_id==r.player_id)&(dep.from_club_id==cid)&(dep.d>r.d)&(dep.d<end)).any(): left=True;break
        seas.append((s,)+find(lg,cid,r.player_name,s))
    rows.append(mk(r.player_id,r.player_name,r.from_club_name,cid,lg,yr,r.transfer_fee,seas,left,tp.position.get(r.player_id)=='Goalkeeper',None,tp.position.get(r.player_id),f'{r.d.date()}'))
o=pd.DataFrame(rows).drop(columns='sub'); o.to_pickle('signings_winter.pkl')
print(len(o)); print(o.status.value_counts().to_dict()); print(o.groupby('year').size().to_dict())
