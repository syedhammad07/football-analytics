"""Season profiles -> ../data/seasons.json

Two kinds of extra profile, both measured in the SAME style space as the 2015/16 players
(the scaler, PCA and role centres are fitted on 2015/16 only and then applied unchanged):
  club   every season of a single-club StatsBomb dataset (club_seasons.py): 900+ minutes
  half   2015/16 split by date, August-December and January-May: 600+ minutes (450 for keepers)
So any season can be matched against the 2015/16 pool: "who in 2015/16 played like Xavi in 2008/09?"

Also reports two checks: re-identification between the two date halves of 2015/16, and how often a
Barcelona player's 2014/15 or 2016/17 profile finds his own 2015/16 profile.
"""
import os, json, urllib.request
from concurrent.futures import ThreadPoolExecutor
import numpy as np, pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from make_features import build
from roles import prep, META, FAMILY
from site_data_roles import ROLE_ID, POS
import gk_model_space as gms

H = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(H, "data")
OUT = os.path.join(os.path.dirname(H), "data")
BASE = "https://raw.githubusercontent.com/statsbomb/open-data/master/data"
sig = lambda v: float(f"{v:.4g}")

# ---------- outfield style space, exactly as validate.py / roles.py fit it ----------
full = pd.read_csv(os.path.join(D, "roles.csv"))
FEATS = [c for c in full.columns if c not in META + ["family", "role_id", "role_fit"]]
sc = StandardScaler().fit(prep(full, FEATS))
Zf = sc.transform(prep(full, FEATS))
p0 = PCA(random_state=0).fit(Zf)
pca = PCA(int(np.searchsorted(p0.explained_variance_ratio_.cumsum(), 0.85) + 1), random_state=0).fit(Zf)
emb = lambda df: pca.transform(sc.transform(prep(df, FEATS)))
E_saved = np.load(os.path.join(D, "embedding.npy"))
assert np.allclose(emb(full), E_saved, atol=1e-6), "style space does not reproduce embedding.npy"

# role centres per family (family PCA, as in validate.py)
FAM_SPACE = {}
for fam, g in full.groupby("family"):
    s2 = StandardScaler().fit(prep(g, FEATS)); Z = s2.transform(prep(g, FEATS))
    pp = PCA(random_state=0).fit(Z)
    pp = PCA(int(np.searchsorted(pp.explained_variance_ratio_.cumsum(), 0.8) + 1), random_state=0).fit(Z)
    P = pp.transform(Z); labs = g.role_id.values
    names = sorted(np.unique(labs), key=lambda r: int(r.split(":")[1]))
    FAM_SPACE[fam] = (s2, pp, names, np.stack([P[labs == r].mean(0) for r in names]))


def assign_roles(df):
    df = df.copy(); df["family"] = df.pos_group.map(FAMILY)
    df["role_id"], df["role_fit"] = "", np.nan
    for fam, idx in df.groupby("family").groups.items():
        s2, pp, names, C = FAM_SPACE[fam]
        d = np.linalg.norm(pp.transform(s2.transform(prep(df.loc[idx], FEATS)))[:, None] - C[None], axis=2)
        ds = np.sort(d, axis=1)
        df.loc[idx, "role_id"] = [names[k] for k in d.argmin(1)]
        df.loc[idx, "role_fit"] = 1 - ds[:, 0] / ds[:, 1]
    return df


# ---------- inputs ----------
pm = pd.read_csv(os.path.join(D, "player_match.csv"))
sm = pd.read_csv(os.path.join(D, "season_match.csv"))
dates = {}
for c in (2, 11, 12, 7):
    p = os.path.join(D, f"matches_{c}.json")
    if not os.path.exists(p):
        urllib.request.urlretrieve(f"{BASE}/matches/{c}/27.json", p)
    dates.update({m["match_id"]: m["match_date"] for m in json.load(open(p))})
pm["half"] = np.where(pm.match_id.map(dates) < "2016-01-01", "2015/16 Aug–Dec", "2015/16 Jan–May")

# ---------- outfield profiles ----------
parts = []
for s, g in sm.groupby("season"):
    f = build(g, 900); f["season"] = s; f["kind"] = "club"; parts.append(f)
key = ["player_id", "team"]
for s, g in pm.groupby("half"):
    f = build(g, 600).merge(full[key], on=key); f["season"] = s; f["kind"] = "half"; parts.append(f)
O = assign_roles(pd.concat(parts, ignore_index=True))
O["E"] = list(emb(O))
O["ri"] = O.role_id.map(ROLE_ID.index)

# ---------- goalkeeper profiles ----------
gsm = pd.read_csv(os.path.join(D, "season_gk_match.csv"))
gm = pd.read_csv(os.path.join(D, "gk_match.csv"))
gm["half"] = np.where(gm.match_id.map(dates) < "2016-01-01", "2015/16 Aug–Dec", "2015/16 Jan–May")
gparts = []
for s, g in gsm.groupby("season"):
    a = gms.features_from(g.drop(columns=["season"]), 900)
    a = a.merge(g.groupby(["player_id", "team"]).agg(player=("player", "first"), league=("league", "first"), minutes=("minutes", "sum"),
                matches=("match_id", "nunique")).reset_index(), on=["player_id", "team"])
    a["season"] = s; a["kind"] = "club"; gparts.append(a)
gk_full = gms.G
for s, g in gm.groupby("half"):
    a = gms.features_from(g.drop(columns=["half"]), 450).merge(gk_full[key], on=key)
    a = a.merge(g.groupby(["player_id", "team"]).agg(player=("player", "first"), league=("league", "first"), minutes=("minutes", "sum"),
                matches=("match_id", "nunique")).reset_index(), on=["player_id", "team"])
    a["season"] = s; a["kind"] = "half"; gparts.append(a)
G = pd.concat(gparts, ignore_index=True)
GE = gms.emb(G)
gd = np.linalg.norm(GE[:, None] - gms.CENT[None], axis=2); gds = np.sort(gd, axis=1)
G["E"] = list(GE); G["ri"] = 11 + gd.argmin(1); G["role_fit"] = 1 - gds[:, 0] / gds[:, 1]

# ---------- names: StatsBomb lineups for the club-season matches ----------
nick = dict(pd.read_csv(os.path.join(D, "nicknames.csv")).values)
cache = os.path.join(D, "season_nicknames.csv")
if os.path.exists(cache):
    nick.update(dict(pd.read_csv(cache).values))
else:
    import time

    def get(u):
        for t in range(6):
            try:
                return json.loads(urllib.request.urlopen(u, timeout=60).read())
            except Exception:
                time.sleep(5 * (t + 1))
        raise RuntimeError(u)
    new = {}
    with ThreadPoolExecutor(6) as ex:
        for lu in ex.map(lambda m: get(f"{BASE}/lineups/{m}.json"), sorted(sm.match_id.unique())):
            for team in lu:
                for p in team["lineup"]:
                    new[p["player_id"]] = p.get("player_nickname") or p["player_name"]
    pd.DataFrame(new.items(), columns=["player_id", "short_name"]).to_csv(cache, index=False)
    nick.update(new)

# ---------- export ----------
gfeats = gms.FEATS
prof = []
for _, p in O.iterrows():
    prof.append(dict(id=int(p.player_id), n=nick.get(p.player_id, p.player), f=p.player, t=p.team, l=p.league, s=p.season, k=p.kind,
                     p=POS.get(p.position, p.position), fam=p.family, r=int(p.ri), fit=round(float(p.role_fit), 2),
                     min=int(p.minutes), mp=int(p.matches), e=[round(float(v), 4) for v in p.E], v=[sig(p[c]) for c in FEATS]))
for _, p in G.iterrows():
    prof.append(dict(id=int(p.player_id), n=nick.get(p.player_id, p.player), f=p.player, t=p.team, l=p.league, s=p.season, k=p.kind,
                     p="Goalkeeper", fam="Goalkeepers", r=int(p.ri), fit=round(float(p.role_fit), 2),
                     min=int(p.minutes), mp=int(p.matches), e=[round(float(v), 4) for v in p.E], v=[sig(p[c]) for c in gfeats]))
order = lambda x: (x["s"][:7], x["k"] == "half", x["s"])
prof.sort(key=lambda x: (x["id"], order(x)))

# ---------- checks ----------
chk = {}
# 1. date halves: from Aug-Dec, find own Jan-May among everyone
h = O[O.kind == "half"]
A = h[h.season.str.endswith("Aug–Dec")].set_index(key); B = h[h.season.str.endswith("Jan–May")].set_index(key)
both = A.index.intersection(B.index)
EA, EB = np.stack(A.loc[both].E), np.stack(B.loc[both].E)
dd = np.linalg.norm(EA[:, None] - EB[None], axis=2); rank = (dd < np.diag(dd)[:, None]).sum(1)
chk["halves"] = dict(n=len(both), top1=round(100 * float(np.mean(rank < 1)), 1), top5=round(100 * float(np.mean(rank < 5)), 1),
                     median_rank=int(np.median(rank)) + 1, role_agree=round(100 * float(np.mean(A.loc[both].ri.values == B.loc[both].ri.values)), 1))
# 2. other seasons -> own 2015/16 profile, among all 2015/16 players
c = O[(O.kind == "club") & O.player_id.isin(full.player_id)]
ranks = []
for _, p in c.iterrows():
    d = np.linalg.norm(E_saved - p.E, axis=1)
    own = d[(full.player_id == p.player_id).values].min()
    ranks.append(dict(season=p.season, r=int((d < own).sum())))
rk = pd.DataFrame(ranks); adj = rk[rk.season.isin(["2014/15", "2016/17"])]
chk["other_seasons"] = dict(n=len(rk), top5=round(100 * float(np.mean(rk.r < 5)), 1), median_rank=int(rk.r.median()) + 1,
                            adjacent_n=len(adj), adjacent_top5=round(100 * float(np.mean(adj.r < 5)), 1),
                            adjacent_median_rank=int(adj.r.median()) + 1, pool=len(full))
seasons = sorted({(p["t"], p["s"], p["l"]) for p in prof if p["k"] == "club"}, key=lambda x: (x[0], x[1]))
json.dump(dict(profiles=prof, seasons=[dict(t=t, s=s, l=l) for t, s, l in seasons], check=chk),
          open(os.path.join(OUT, "seasons.json"), "w"), separators=(",", ":"), ensure_ascii=False)
print(len(prof), "profiles:", sum(p["k"] == "club" for p in prof), "club-season,", sum(p["k"] == "half" for p in prof), "half-season;",
      len({p["id"] for p in prof if p["k"] == "club"} - set(full.player_id) - set(gk_full.player_id)), "players with no 2015/16 profile")
print(json.dumps(chk, indent=1))
print(os.path.getsize(os.path.join(OUT, "seasons.json")) // 1024, "KB")
