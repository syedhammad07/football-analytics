"""Export everything the website needs as compact JSON (site/data/*.json).

players.json  - per player: names, club, league, position, role, minutes, map x/y, 8-D style vector, 42 raw stats
teams.json    - per team: results-based table, team style stats + league percentiles, role mix, squad
roles.json    - per role: defining stats, typical players, extremes, league usage
extras.json   - out-of-position list, most/least unique players, validation numbers
"""
import os, json
from collections import defaultdict
import numpy as np, pandas as pd
from roles import prep, META
from explain import LABEL
from site_data_roles import POS
import urllib.request


def matches(cid, season=27):
    """StatsBomb match list for one competition, cached in data/."""
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", f"matches_{cid}.json")
    if not os.path.exists(p):
        url = f"https://raw.githubusercontent.com/statsbomb/open-data/master/data/matches/{cid}/{season}.json"
        urllib.request.urlretrieve(url, p)
    return json.load(open(p))

H = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(H, "data")
OUT = os.path.join(os.path.dirname(H), "data")  # Tools/Player-Style-Finder/data
os.makedirs(OUT, exist_ok=True)

ROLE_ID = ["Attackers:0", "Attackers:1", "Attackers:2", "Attackers:3", "Attackers:4", "Centre-backs:0", "Centre-backs:1",
           "Full-backs:0", "Full-backs:1", "Midfielders:0", "Midfielders:1"]
ROLES = [("Creative playmaker", "#2DD4BF", "Attackers"), ("Touchline winger", "#22D3EE", "Attackers"), ("Target striker", "#F87171", "Attackers"),
         ("Mobile forward", "#FB923C", "Attackers"), ("Deep wide midfielder", "#A3E635", "Attackers"), ("Stopper", "#3B82F6", "Centre-backs"),
         ("Ball-playing centre-back", "#93C5FD", "Centre-backs"), ("Defensive full-back", "#8B5CF6", "Full-backs"),
         ("Attacking full-back", "#E879F9", "Full-backs"), ("Box-to-box midfielder", "#FACC15", "Midfielders"), ("Holding midfielder", "#D97706", "Midfielders"),
         ("Ball-playing keeper", "#F472B6", "Goalkeepers"), ("Long-ball keeper", "#94A3B8", "Goalkeepers")]

r = pd.read_csv(os.path.join(D, "roles.csv"))
nick = dict(pd.read_csv(os.path.join(D, "nicknames.csv")).values)
E = np.load(os.path.join(D, "embedding.npy"))
mp = json.load(open(os.path.join(H, "data", "map.json")))
sim = pd.read_csv(os.path.join(D, "similar.csv"))
ctx = json.load(open(os.path.join(D, "match_context.json")))
feats = [c for c in r.columns if c not in META + ["family", "role_id", "role_fit"]]
r["ri"] = r.role_id.map(ROLE_ID.index)
r["short"] = [nick.get(i, n) for i, n in zip(r.player_id, r.player)]
# disambiguate duplicate short names
dup = r.short.duplicated(keep=False)
r.loc[dup, "short"] = r.loc[dup, "short"] + " (" + r.loc[dup, "team"] + ")"

# similarity scale used in similar.csv (validate.py): median of top-5 neighbour distances
Dm = np.linalg.norm(E[:, None] - E[None], axis=2)
np.fill_diagonal(Dm, np.inf)
scale = float(np.median(np.sort(Dm, axis=1)[:, :5]))

def sig(v, n=4):
    return float(f"{v:.{n}g}")

players = []
for i, p in r.iterrows():
    players.append(dict(id=int(p.player_id), n=p.short, f=p.player, t=p.team, l=p.league, p=POS.get(p.position, p.position), fam=p.family,
                        r=int(p.ri), fit=round(float(p.role_fit), 2), min=int(p.minutes), mp=int(p.matches),
                        x=mp["pts"][i][0], y=mp["pts"][i][1], e=[round(float(v), 4) for v in E[i]], v=[sig(p[c]) for c in feats]))
# ---- goalkeepers: own feature set and own style space
gkdf = pd.read_csv(os.path.join(D, "gk_roles.csv")); GE = np.load(os.path.join(D, "gk_embedding.npy"))
gfeats = [c for c in gkdf.columns if c not in ("player_id", "player", "team", "league", "minutes", "matches", "cluster", "role_fit")]
GD = np.linalg.norm(GE[:, None] - GE[None], axis=2); np.fill_diagonal(GD, np.inf)
gscale = float(np.median(np.sort(GD, axis=1)[:, :5]))
g_best = 100 * np.exp(-np.sort(GD, axis=1)[:, 0] / (2 * gscale))
gkdf["short"] = [nick.get(i, n) for i, n in zip(gkdf.player_id, gkdf.player)]
NGK0 = len(players)
for i, p in gkdf.iterrows():
    players.append(dict(id=int(p.player_id), n=p.short, f=p.player, t=p.team, l=p.league, p="Goalkeeper", fam="Goalkeepers",
                        r=11 + int(p.cluster), fit=round(float(p.role_fit), 2), min=int(p.minutes), mp=int(p.matches), x=None, y=None,
                        e=[round(float(v), 4) for v in GE[i]], v=[sig(p[c]) for c in gfeats]))
names = [p["n"] for p in players]
for k, p in enumerate(players):
    if names.count(p["n"]) > 1 and "(" not in p["n"]:
        p["n"] = f'{p["n"]} ({p["t"]})'
gkchk = json.load(open(os.path.join(D, "gk_check.json")))
json.dump(dict(feats=feats, labels=[LABEL[c] for c in feats], roles=[dict(name=a, color=b, family=c) for a, b, c in ROLES],
               scale=round(scale, 4), typical_best=ctx["typical_best_similarity"],
               gk=dict(feats=gfeats, labels=[LABEL[c] for c in gfeats], scale=round(gscale, 4), typical_best=round(float(np.median(g_best)), 1), check=gkchk),
               players=players),
          open(os.path.join(OUT, "players.json"), "w"), separators=(",", ":"), ensure_ascii=False)

# ---------------- teams
pm = pd.read_csv(os.path.join(D, "player_match.csv"))
tm = pm.groupby(["match_id", "team", "league"]).agg(
    passes=("passes", "sum"), passes_ok=("passes_ok", "sum"), long=("long_passes", "sum"), crosses=("crosses", "sum"),
    pressures=("pressures", "sum"), press_att=("pressures_att3", "sum"), shots=("shots", "sum"), npxg=("npxg", "sum"),
    tackles=("tackles", "sum"), interceptions=("interceptions", "sum"), prog=("prog_passes", "sum"), dribbles=("dribbles", "sum"),
    poss=("team_poss", "first")).reset_index()
opp = tm[["match_id", "team", "npxg", "shots", "passes"]].rename(columns={"team": "opp", "npxg": "npxg_against", "shots": "shots_against", "passes": "opp_passes"})
tm = tm.merge(opp, on="match_id")
tm = tm[tm.team != tm.opp]
# defensive line: average x of centre-back touches
cb = pm[pm.top_position.str.contains("Center Back", na=False)]
cbx = (cb.groupby("team").x_sum.sum() / cb.groupby("team").touches.sum())
# results from match files
pts, gf, ga, w, d, l_ = defaultdict(int), defaultdict(int), defaultdict(int), defaultdict(int), defaultdict(int), defaultdict(int)
for c in (2, 11, 12, 7):
    for m in matches(c):
        h, a, hs, as_ = m["home_team"]["home_team_name"], m["away_team"]["away_team_name"], m["home_score"], m["away_score"]
        for t, f_, g_ in ((h, hs, as_), (a, as_, hs)):
            gf[t] += f_; ga[t] += g_
            if f_ > g_: pts[t] += 3; w[t] += 1
            elif f_ == g_: pts[t] += 1; d[t] += 1
            else: l_[t] += 1
g = tm.groupby(["team", "league"])
T = pd.DataFrame(dict(
    matches=g.size(), possession=g.poss.mean() * 100, passes=g.passes.mean(), pass_cmp=g.passes_ok.sum() / g.passes.sum() * 100,
    long_share=g.long.sum() / g.passes.sum() * 100, prog=g.prog.mean(), crosses=g.crosses.mean(), dribbles=g.dribbles.mean(),
    pressures=g.pressures.sum() / g.opp_passes.sum() * 100, high_press=g.press_att.sum() / g.pressures.sum() * 100, def_actions=(g.tackles.mean() + g.interceptions.mean()),
    shots=g.shots.mean(), npxg=g.npxg.mean(), shots_against=g.shots_against.mean(), npxg_against=g.npxg_against.mean())).reset_index()
T["line"] = T.team.map(cbx) * 105 / 120
TS = [("possession", "Possession", "%", 1), ("passes", "Passes per match", "", 0), ("pass_cmp", "Pass completion", "%", 1),
      ("long_share", "Share of long passes", "%", 1), ("prog", "Progressive passes per match", "", 1), ("crosses", "Crosses per match", "", 1),
      ("dribbles", "Dribbles per match", "", 1), ("pressures", "Pressures per 100 opponent passes", "", 1), ("high_press", "Pressures in final third", "%", 1),
      ("def_actions", "Tackles + interceptions per match", "", 1), ("line", "Centre-back average position", "m", 1),
      ("shots", "Shots per match", "", 1), ("npxg", "Non-penalty xG per match", "", 2), ("shots_against", "Shots conceded per match", "", 1),
      ("npxg_against", "Non-penalty xG conceded per match", "", 2)]
for k, *_ in TS:
    T[k + "_pct"] = T.groupby("league")[k].rank(pct=True) * 100
T["pts"] = T.team.map(pts); T["w"] = T.team.map(w); T["d"] = T.team.map(d); T["l"] = T.team.map(l_); T["gf"] = T.team.map(gf); T["ga"] = T.team.map(ga)
T["pos"] = T.groupby("league").apply(lambda x: (-(x.pts * 1000 + (x.gf - x.ga))).rank(method="first")).reset_index(level=0, drop=True)
teams = []
for _, t in T.sort_values(["league", "pos"]).iterrows():
    sq = r[r.team == t.team].sort_values("minutes", ascending=False)
    mix = sq.groupby("ri").minutes.sum()
    gq = gkdf[gkdf.team == t.team]
    for _, kp in gq.iterrows():
        mix.loc[11 + int(kp.cluster)] = mix.get(11 + int(kp.cluster), 0) + kp.minutes
    gk_idx = [NGK0 + int(j) for j in gq.sort_values("minutes", ascending=False).index]
    teams.append(dict(t=t.team, l=t.league, pos=int(t.pos), pts=int(t.pts), w=int(t.w), d=int(t.d), lo=int(t.l), gf=int(t.gf), ga=int(t.ga),
                      s={k: [round(float(t[k]), dp), int(round(t[k + "_pct"]))] for k, _, _, dp in TS},
                      mix={int(k): int(v) for k, v in mix.items()}, squad=gk_idx + [int(i) for i in sq.index]))
json.dump(dict(stats=[dict(k=k, name=n, unit=u) for k, n, u, _ in TS], teams=teams), open(os.path.join(OUT, "teams.json"), "w"),
          separators=(",", ":"), ensure_ascii=False)

# ---------------- roles
X = prep(r, feats); Z = (X - X.mean()) / X.std()
ex = json.load(open(os.path.join(H, "data", "extremes.json")))
leagues = ["Premier League", "La Liga", "Serie A", "Ligue 1"]
roles = []
for k, (name, color, fam) in enumerate(ROLES[:11]):
    m = r.ri == k; fm = r.family == fam
    diff = (Z[m].mean() - Z[fm].mean()).sort_values()
    hi = [(c, round(float(v), 2)) for c, v in diff[::-1][:5].items()]
    lo = [(c, round(float(v), 2)) for c, v in diff[:3].items()]
    idx = np.where(m)[0]; cen = E[idx].mean(0); dd = np.linalg.norm(E[idx] - cen, axis=1)
    typical = [int(idx[j]) for j in np.argsort(dd) if r.minutes[idx[j]] >= 1500][:6]
    use = {lg: round(100 * float((r[(r.league == lg) & fm].ri == k).mean()), 1) for lg in leagues}
    med = {c: sig(float(r[m][c].median())) for c, _ in hi + lo}
    famed = {c: sig(float(r[fm][c].median())) for c, _ in hi + lo}
    roles.append(dict(name=name, color=color, family=fam, n=int(m.sum()), hi=hi, lo=lo, med=med, famed=famed, typical=typical,
                      extremes=[dict(i=e["i"], pct=e["pct8"]) for e in ex if e["role"] == k], use=use))
GZ = (prep(gkdf, gfeats) - prep(gkdf, gfeats).mean()) / prep(gkdf, gfeats).std()
for k in (0, 1):
    m = (gkdf.cluster == k).values
    diff = (GZ[m].mean() - GZ.mean()).sort_values()
    hi = [(c, round(float(v), 2)) for c, v in diff[::-1][:5].items()]; lo = [(c, round(float(v), 2)) for c, v in diff[:3].items()]
    idx = np.where(m)[0]; dd = np.linalg.norm(GE[idx] - GE[idx].mean(0), axis=1)
    typical = [NGK0 + int(idx[j]) for j in np.argsort(dd) if gkdf.minutes[idx[j]] >= 1500][:6]
    ext = [dict(i=NGK0 + int(idx[j]), pct=int(100 * (dd < dd[j]).mean())) for j in np.argsort(-dd)[:2]]
    use = {lg: round(100 * float((gkdf[gkdf.league == lg].cluster == k).mean()), 1) for lg in leagues}
    roles.append(dict(name=ROLES[11 + k][0], color=ROLES[11 + k][1], family="Goalkeepers", n=int(m.sum()), hi=hi, lo=lo,
                      med={c: sig(float(gkdf[m][c].median())) for c, _ in hi + lo}, famed={c: sig(float(gkdf[c].median())) for c, _ in hi + lo},
                      typical=typical, extremes=ext, use=use))
json.dump(roles, open(os.path.join(OUT, "roles.json"), "w"), separators=(",", ":"), ensure_ascii=False)

# ---------------- extras
nn = np.argsort(Dm, axis=1)[:, :10]
fams = r.family.values
mis = []
for i in range(len(r)):
    other = [fams[j] for j in nn[i] if fams[j] != fams[i]]
    share = len(other) / 10
    if share >= 0.6:
        like = pd.Series(other).mode()[0]
        roles_nb = pd.Series([int(r.ri[j]) for j in nn[i] if fams[j] == like]).mode()[0]
        mis.append(dict(i=i, share=share, like=like, like_role=int(roles_nb)))
mis = sorted(mis, key=lambda x: (-x["share"], -r.minutes[x["i"]]))
best = sim[sim["rank"] == 1].set_index(["player_id", "team"]).similarity
bs = np.array([best[(a, b)] for a, b in zip(r.player_id, r.team)])
q = r.minutes >= 1500
uniq = [int(i) for i in np.argsort(bs) if q[i]][:12]
twins = sorted({tuple(sorted((i, int(nn[i][0])))) for i in range(len(r)) if nn[nn[i][0]][0] == i}, key=lambda p: Dm[p[0], p[1]])[:12]
json.dump(dict(misfits=mis, unique=[dict(i=i, best=round(float(bs[i]), 1)) for i in uniq],
               twins=[dict(a=int(a), b=int(b), s=round(float(100 * np.exp(-Dm[a, b] / (2 * scale))), 1)) for a, b in twins],
               validation=dict(top1=36.9, top5=65.6, top10=74.8, median_rank=3, pool=982, role_agree=86.3, team_leak=2.6, team_leak_random=1.2)),
          open(os.path.join(OUT, "extras.json"), "w"), separators=(",", ":"), ensure_ascii=False)
for f in os.listdir(OUT):
    print(f, os.path.getsize(os.path.join(OUT, f)) // 1024, "KB")
print("misfits", len(mis), "| unique", [r.short[i] for i in uniq[:5]], "| twins", [(r.short[a], r.short[b]) for a, b in twins[:4]])
print("scale", scale)
