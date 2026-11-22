import pandas as pd,numpy as np,re,sys,json,unicodedata
sys.path.insert(0,'/home/claude/scout-finder/src')
from scout_finder.transfers import _names_match
D='/mnt/user-data/uploads/football-analytics/Projects/Scout-Finder/data/'
def norm(s):
    s=unicodedata.normalize('NFKD',str(s)).encode('ascii','ignore').decode().lower()
    return re.sub(r'[^a-z0-9 ]',' ',s)
def toks(s): return set(norm(s).split())
CL={int(k):v for k,v in json.load(open('club_ids.json')).items()}
EXTRA={'Inter':'Internacional Internazionale Inter Milan','Leverkusen':'Bayer Leverkusen','Gladbach':"Monchengladbach Borussia M'gladbach",'Leipzig':'RB Leipzig','Verona':'Hellas Verona',
'Paris':'Paris Saint Germain PSG Paris SG','Atletico':'Atletico Madrid Atletico de Madrid','Athletic':'Athletic Club Bilbao','Furth':'Greuther Furth Fürth','Eintracht':'Eintracht Frankfurt Frankfurt',
'Union':'Union Berlin','Marseille':'Olympique de Marseille','Lyon':'Olympique Lyonnais Olympique Lyon','Nottingham Forest':"Nottingham Forest Nott'm Forest Nottm Forest",'Spurs':'Tottenham Hotspur','Wolves':'Wolverhampton Wanderers',
'Man City':'Manchester City Manchester','Man Utd':'Manchester United Manchester','Aston Villa':'A Villa Aston','Crystal Palace':'C Palace Crystal','West Ham':'West Ham United West','West Brom':'West Bromwich Albion West',
'Sheffield Utd':'Sheffield United Sheffield','Saint-Etienne':'Saint Etienne Saint','Real Madrid':'Real Madrid Real','Real Betis':'Real Betis Betis Real','Real Sociedad':'Real Sociedad Real','Valladolid':'Real Valladolid Valladolid Real',
'Oviedo':'Real Oviedo Real','Koln':'Koln Cologne 1 FC Koln','Milan':'AC Milan Milan','Newcastle':'Newcastle United','Brighton':'Brighton Hove Albion','Hamburg':'Hamburger SV Hamburg','Heidenheim':'Heidenheim 1 Heidenheim',
'Mainz':'Mainz 05 1 FSV Mainz','Dortmund':'Borussia Dortmund Dortmund','Bayern':'Bayern Munchen Bayern Munich','Stuttgart':'VfB Stuttgart Stuttgart','Barcelona':'FC Barcelona Barcelona','Nurnberg':'Nurnberg Nuremberg',
'Celta':'Celta Vigo Celta de Vigo','Rayo':'Rayo Vallecano','Alaves':'Alaves Deportivo Alaves','Almeria':'Almeria UD Almeria','Cadiz':'Cadiz','Leganes':'Leganes','Rennes':'Stade Rennais Rennes','Nimes':'Nimes','Lille':'Lille LOSC','Brest':'Brest Stade Brestois','Lens':'Lens RC Lens','Reims':'Reims Stade de Reims','Hoffenheim':'TSG Hoffenheim Hoffenheim','Werder':'Werder Bremen','Dusseldorf':'Dusseldorf Fortuna Dusseldorf','Salernitana':'Salernitana','Torino':'Torino','Roma':'Roma AS Roma'}
for k,v in CL.items(): v.append(' '.join([v[1],v[2],EXTRA.get(v[1],'')]))
CT={k:toks(v[3]) for k,v in CL.items()}
def club_ok(cid,team):
    t=toks(team); return bool(t) and t<=CT[cid]
yth=re.compile(r'(U\d\d|Yth|Youth|\bII\b|\bB$|\bC$|Res\.|Jgd|Jugend)',re.I)
tm=pd.read_csv(D+'tm_transfers.csv.gz'); tm['d']=pd.to_datetime(tm.transfer_date,errors='coerce')
# ---- stats sources: unified frame league,yr,team,name,min,mp,gk
fr=[]
for yr in range(2019,2026):
    f=(D if yr<2025 else '/home/claude/scout-finder/data/')+f'pl_players_{yr}-{str(yr+1)[2:]}.csv'
    o=pd.read_csv(f); fr.append(pd.DataFrame({'league':'ENG','yr':yr,'team':o.team,'name':o.name,'min':o.timePlayed,'mp':o.appearances,'gk':o.position.str.contains('Goalkeeper',na=False),'src':'Opta','g':o.goals,'a':o.goalAssists,'xg':o.expectedGoals,'xa':o.expectedAssists,'tk':o.totalTackles,'ic':o.interceptions,'cl':o.totalClearances,'dr':o.successfulDribbles,'kp':o.keyPassesAttemptAssists,'sh':o.totalShots,'tw':o.tacklesWon,'duw':o.duelsWon,'aer':o.aerialDuelsWon,'fl':o.totalFoulsConceded,'yc':o.yellowCards,'rc':np.nan,'rec':o.recoveries,'pc':o.successfulShortPasses+o.successfulLongPasses,'pt':o.successfulShortPasses+o.successfulLongPasses+o.totalUnsuccessfulPassesExclCrossesAndCorners,'dl':o.duelsLost,'aerl':o.aerialDuelsLost,'oph':o.successfulPassesOppositionHalf,'prgc':np.nan,'prgp':np.nan,'sv':np.nan}))
FB=pd.read_pickle('/home/claude/work/fb_all.pkl')
FB=FB[FB.yr>=2017].copy()  # Premier League site feed (2009-2018) removed: no permission to use it; all five leagues start 2017/18
TA={'Eint Frankfurt':'Eintracht Frankfurt','Paris S-G':'Paris Saint Germain PSG','Newcastle Utd':'Newcastle United Newcastle','Racing Sant':'Racing Santander','Gazélec Ajaccio':'Gazelec Ajaccio','Wigan Athletic':'Wigan','Blackburn':'Blackburn','QPR':'QPR Queens Park Rangers'}
FB['team']=FB.team.map(lambda t:TA.get(t,t)); fr.append(FB)
S=pd.read_csv('/tmp/s.csv',usecols=['league','season','team','player','minutesPlayed','appearances','saves','goals','assists','expectedGoals','expectedAssists','tackles','interceptions','clearances','goalsPrevented','successfulDribbles','keyPasses','totalShots','tacklesWon','totalDuelsWon','aerialDuelsWon','fouls','yellowCards','redCards','ballRecovery','duelLost','aerialLost','accurateOppositionHalfPasses','accuratePasses','totalPasses'])
S=S[(~S.league.str.startswith('ENG'))|(S.saves.fillna(0)>0)]
fr.append(pd.DataFrame({'league':S.league.str[:3].map({'ENG':'ENG','ESP':'ESP','ITA':'ITA','GER':'GER','FRA':'FRA'}),'yr':S.season.map({2425:2024,2526:2025}),'team':S.team,'name':S.player,'min':S.minutesPlayed,'mp':S.appearances,'gk':S.saves.fillna(0)>0,'src':'SofaScore','g':S.goals,'a':S.assists,'xg':S.expectedGoals,'xa':S.expectedAssists,'tk':S.tackles,'ic':S.interceptions,'cl':S.clearances,'gp':S.goalsPrevented,'dr':S.successfulDribbles,'kp':S.keyPasses,'sh':S.totalShots,'tw':S.tacklesWon,'duw':S.totalDuelsWon,'aer':S.aerialDuelsWon,'fl':S.fouls,'yc':S.yellowCards,'rc':S.redCards,'rec':S.ballRecovery,'pc':S.accuratePasses,'pt':S.totalPasses,'dl':S.duelLost,'aerl':S.aerialLost,'oph':S.accurateOppositionHalfPasses,'sv':S.saves}))
ST=pd.concat(fr,ignore_index=True); ST['nn']=ST.name.map(lambda x:' '.join(norm(x).split()))
ST.to_pickle('stats_all.pkl')
# club -> stat team resolution
ST['cid']=-1
teams=ST[['league','team']].drop_duplicates()
res={}
for _,r in teams.iterrows():
    c=[k for k,v in CL.items() if v[0]==r.league and club_ok(k,r.team)]
    if not c:
        gen={'fc','sc','vfl','vfb','sv','ssc','rc','as','ac','ud','cf','ca','afc','united','city','real','club','1','04','05'}
        t=[w for w in toks(r.team) if len(w)>3 and w not in gen]
        c=[k for k,v in CL.items() if v[0]==r.league and any(w in CT[k] for w in t)]
        if len(c)>1: c=[]
    res[(r.league,r.team)]=c
un=[k for k,v in res.items() if not v]; print('unresolved stat teams',un[:60],len(un))
ST['cands']=[tuple(res[(a,b)]) for a,b in zip(ST.league,ST.team)]
ST.to_pickle('stats_all.pkl')
