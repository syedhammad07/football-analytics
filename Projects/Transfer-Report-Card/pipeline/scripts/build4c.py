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
rows=[]
for i,r in enumerate(I.itertuples()):
    seas=[];left=False
    ol=outs.get((r.cid,r.player_name),[])
    for yr in range(r.year,2026):
        if any((y==yr and p=='Winter') or (y==yr and p=='Summer' and yr==r.year) for y,p in ol): left=True;break
        seas.append((yr,)+find(r.lg,r.cid,r.player_name,yr))
        if any(y==yr+1 and p=='Summer' for y,p in ol): break   # left next summer after completing this season
    seas=[s for s in seas if s[1]!='club not in league']
    gk=any(s[4] for s in seas) or r.position=='Goalkeeper'
    st=[s[1] for s in seas]
    overall=('usable' if 'usable' in st else 'low minutes' if 'low minutes' in st else 'no appearances' if 'no appearances' in st else 'data gap' if 'data gap' in st else ('left early' if left or not seas else '?'))
    rows.append(dict(player_id=-(i+1),player=r.player_name,from_club=r.club_involved_name,to_club=CL[r.cid][1],league=r.lg,date=f'{r.year}-08-01',year=r.year,fee_eur=r.fee_cleaned*1e6,
      status=overall,n_whole=len(seas),left_early=left and not seas,gk=gk,seasons=';'.join(f"{s[0]}:{s[1]}:{s[2]}" for s in seas),pos_text=PM.get(r.position),position_tm={'FW':'Attack','DF':'Defender','FB':'Defender','GK':'Goalkeeper'}.get(PM.get(r.position),'Midfield'),sub=r.position))
o=pd.DataFrame(rows); o.to_pickle('signings_ew_2010_2022.pkl')
print(len(o)); print(o.groupby(['status']).size().to_dict()); print(o.groupby('year').size().to_dict())
