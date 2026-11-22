exec(open('build3b.py').read().split("# ---- stats sources")[0])
ST=pd.read_pickle('stats_all.pkl')
tp=pd.read_csv(D+'tm_players.csv.gz',usecols=['player_id','position','last_season','current_club_name','current_club_id']).set_index('player_id')
GKS=set(tp.index[tp.position=='Goalkeeper'])
x=tm[(tm.d>='2010-06-01')&(tm.d<='2025-09-05')&tm.to_club_id.isin(CL)].copy()
x=x[~x.from_club_name.fillna('').str.contains(yth)]
x=x[x.transfer_fee>0].copy(); x['year']=x.d.dt.year
x['league']=x.to_club_id.map(lambda i:CL[i][0]); x['club']=x.to_club_id.map(lambda i:CL[i][1])
x=x[(x.d.dt.month>=6)&(x.d.dt.month<=9)]
dep=tm[['player_id','from_club_id','d']]
idx={}
for (lg,yr),g in ST.groupby(['league','yr']): idx[(lg,yr)]=g
def find(r,yr):
    g=idx.get((r.league,yr))
    if g is None: return 'data gap',None,None,False,'no source'
    club_rows=g[g.cands.map(lambda c:r.to_club_id in c)]
    if club_rows.empty: return 'club not in league',None,None,False,''
    nn=' '.join(norm(r.player_name).split())
    h=club_rows[club_rows.nn==nn]
    if h.empty:
        h=club_rows[club_rows.name.map(lambda n:_names_match(n,r.player_name))]
    other=g[(g.nn==nn)&~g.index.isin(club_rows.index)]
    if h.empty and r.league=='ENG' and 2019<=yr<2024 and r.player_id in GKS: return 'data gap',None,None,True,'no GK source'
    if h.empty:
        return ('no appearances',0,0,False,'also other club' if len(other) else '')
    m=h['min'].sum(min_count=1)
    gk=bool(h.gk.any()); src=h.src.iloc[0]
    if pd.isna(m): return 'data gap',None,int(h.mp.sum()),gk,src+' no minutes'
    return ('usable' if m>=450 else 'low minutes'),int(m),int(h.mp.sum()),gk,src
rows=[]
for _,r in x.iterrows():
    seas=[]; left=False
    for yr in range(r.year,2026):
        end=pd.Timestamp(f'{yr+1}-06-01')
        if ((dep.player_id==r.player_id)&(dep.from_club_id==r.to_club_id)&(dep.d>r.d)&(dep.d<end)).any():
            left=True; break
        seas.append((yr,)+find(r,yr))
    seas=[s for s in seas if s[1]!='club not in league']
    gk=any(s[4] for s in seas)
    st=[s[1] for s in seas]
    overall=('usable' if 'usable' in st else 'low minutes' if 'low minutes' in st else 'no appearances' if 'no appearances' in st else 'data gap' if 'data gap' in st else ('left early' if left or not seas else '?'))
    rows.append(dict(player_id=r.player_id,player=r.player_name,from_club=r.from_club_name,to_club=r.club,league=r.league,date=r.d.date(),year=r.year,fee_eur=r.transfer_fee,
        status=overall,n_whole=len(seas),left_early=left and not seas,gk=gk,
        seasons=';'.join(f"{s[0]}:{s[1]}:{s[2]}" for s in seas)))
o=pd.DataFrame(rows)
o.to_pickle('signings_2010_2025.pkl')
print(len(o)); print(o.groupby(['league','status']).size().unstack(fill_value=0).to_string())
print(o.groupby(['year','status']).size().unstack(fill_value=0).to_string())
