"""Find similar players in recent Premier League seasons -> ../data/now.json

StatsBomb has no free data for recent seasons, so this step uses the Premier League's own (Opta) season
stats that this repo already keeps for Scout Finder: 2025/26 (full season) and 2026/27 (so far).

The two providers count some things differently (what is a "long" pass, a "dribble", a "key pass"), and the
seasons are ten years apart, so raw numbers are not compared directly. Instead:
  1. 16 stats that both providers have are built the same way from each (per 90, shares, possession-adjusted
     defending: tackles and interceptions are scaled to a 50/50 share of the ball).
  2. Each stat becomes a percentile within its own season's pool of outfield players:
     StatsBomb profiles against the 1,251 outfield players of 2015/16; Premier League players against
     their own season (900+ minutes in 2025/26, 450+ in 2026/27 so far).
  3. Stat match = 100 - the average gap in percentile points across the stats.

Check: 2015/16 Premier League midfielders appear in BOTH sources (repo file pl_midfielders_2010-2018.csv
is Opta's 2015/16). If the method works, a player's StatsBomb profile should find his own Opta profile.
"""
import os, json, unicodedata, re
import numpy as np, pandas as pd

H = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(H, "data")
TOOL = os.path.dirname(H)
REPO = os.path.dirname(os.path.dirname(TOOL))
SF = os.path.join(REPO, "Tools", "Scout-Finder", "data")
EXT = os.path.join(REPO, "Players", "Yaya-Toure-Man-City", "data", "external")

# stat key, label, unit
STATS = [
    ("npg_p90", "Non-penalty goals per 90", ""), ("npxg_p90", "Non-penalty xG per 90", ""), ("shots_p90", "Shots per 90", ""),
    ("key_passes_p90", "Key passes per 90", ""),
    ("through_balls_p90", "Through balls per 90", ""),
    ("dribbles_p90", "Dribbles attempted per 90", ""), ("dribble_success", "Dribble success", "%"),
    ("touches_p90", "Touches per 90", ""), ("passes_p90", "Passes per 90", ""), ("pass_cmp", "Pass completion", "%"),
    ("fwd_share", "Share of passes forward", "%"), ("long_share", "Share of passes long", "%"),
    ("tackles_p90", "Tackles per 90 (poss. adj.)", ""), ("interceptions_p90", "Interceptions per 90 (poss. adj.)", ""),
    ("recoveries_p90", "Ball recoveries per 90", ""), ("aerials_won_p90", "Aerial duels won per 90", ""),
]
# Left out after the two-provider check below: touches in the box (StatsBomb and Opta disagree, rank
# correlation 0.14), and crosses and clearances (not in the 2015/16 Opta file, so they can't be checked).
KEYS = [k for k, _, _ in STATS]
ADJ = ["tackles", "interceptions"]


def stats_from(t):
    """t: one row per player with totals in the standard columns below; returns the 16 stats."""
    m = t.minutes / 90
    sh = lambda a, b: np.where(t[b] > 0, t[a] / t[b].replace(0, np.nan), np.nan)
    adj = 0.5 / (1 - t.team_poss).clip(0.25, 0.75)
    o = pd.DataFrame(index=t.index)
    o["npg_p90"] = t.np_goals / m; o["npxg_p90"] = t.npxg / m; o["shots_p90"] = t.shots / m
    o["key_passes_p90"] = t.key_passes / m; o["through_balls_p90"] = t.through_balls / m
    o["dribbles_p90"] = t.dribbles / m; o["dribble_success"] = sh("dribbles_ok", "dribbles")
    o["touches_p90"] = t.touches / m; o["passes_p90"] = t.passes / m; o["pass_cmp"] = sh("passes_ok", "passes")
    o["fwd_share"] = sh("fwd_passes", "passes"); o["long_share"] = sh("long_passes", "passes")
    for c in ADJ:
        o[c + "_p90"] = t[c] * adj / m
    o["recoveries_p90"] = t.recoveries / m; o["aerials_won_p90"] = t.aerials_won / m
    return o[KEYS]


def sb_totals(pm):
    """StatsBomb match rows -> season totals per player and team."""
    g = pm.groupby(["player_id", "team"])
    t = g[["minutes", "np_goals", "npxg", "shots", "t_box", "key_passes", "through_balls", "crosses", "dribbles", "dribbles_ok",
           "touches", "passes", "passes_ok", "fwd_passes", "long_passes", "tackles", "interceptions", "clearances",
           "recoveries", "aerials_won"]].sum()
    t["team_poss"] = g.team_poss.mean()
    return t.rename(columns={"t_box": "box_touches"}).reset_index()


def opta_totals(d, poss):
    """Premier League (Opta) season totals -> the same standard columns."""
    t = pd.DataFrame(dict(
        minutes=d.timePlayed, np_goals=d.goals - d.penaltyGoals, npxg=(d.expectedGoals - d.penaltyGoals).clip(lower=0),  # a penalty is worth ~0.78 xG and ~78% are scored, so pen xG ~ pen goals
        shots=d.totalShots, box_touches=d.totalTouchesInOppositionBox, key_passes=d.keyPassesAttemptAssists, through_balls=d.throughBalls,
        crosses=d.get("successfulCrossesOpenPlay", 0) + d.get("unsuccessfulCrossesOpenPlay", 0),
        dribbles=d.successfulDribbles + d.unsuccessfulDribbles, dribbles_ok=d.successfulDribbles, touches=d.touches,
        passes=d.totalPasses, passes_ok=d.totalPasses - d.totalUnsuccessfulPassesExclCrossesAndCorners, fwd_passes=d.forwardPasses,
        long_passes=d.successfulLongPasses + d.unsuccessfulLongPasses, tackles=d.totalTackles, interceptions=d.interceptions,
        clearances=d.get("totalClearances", 0), recoveries=d.recoveries, aerials_won=d.aerialDuelsWon), index=d.index)
    t["team_poss"] = d.team.map(poss).fillna(50) / 100
    return t


def pct_against(ref, x):
    """Percentile (1-99) of each value in x within ref, column by column (NaN -> 50)."""
    out = np.zeros(x.shape)
    for j in range(x.shape[1]):
        r = np.sort(ref[:, j][~np.isnan(ref[:, j])]); v = x[:, j]
        lo = np.searchsorted(r, v, "left"); hi = np.searchsorted(r, v, "right")
        p = 100 * (lo + (hi - lo) / 2) / len(r)
        out[:, j] = np.where(np.isnan(v), 50, p)
    return np.clip(np.round(out), 1, 99).astype(int)


norm = lambda s: re.sub(r"[^a-z ]", "", unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().lower()).strip()
TEAM_SB = {"AFC Bournemouth": "Bournemouth", "Aston Villa": "A Villa", "Crystal Palace": "C Palace", "Leicester City": "Leicester",
           "Manchester City": "Man City", "Manchester United": "Man Utd", "Newcastle United": "Newcastle", "Norwich City": "Norwich",
           "Stoke City": "Stoke", "Swansea City": "Swansea", "Tottenham Hotspur": "Spurs", "West Bromwich Albion": "West Brom",
           "West Ham United": "West Ham"}
TEAM_FULL = {"A Villa": "Aston Villa", "C Palace": "Crystal Palace", "Man City": "Manchester City", "Man Utd": "Manchester United",
             "Nott'm Forest": "Nottingham Forest", "Spurs": "Tottenham Hotspur", "Newcastle": "Newcastle United", "West Ham": "West Ham United",
             "Wolves": "Wolverhampton Wanderers", "Brighton": "Brighton & Hove Albion", "Leeds": "Leeds United", "Hull": "Hull City",
             "Ipswich": "Ipswich Town", "Coventry": "Coventry City"}


def main():
    # ---------- StatsBomb side: 2015/16 pool, plus every season profile in seasons.json ----------
    pm = pd.read_csv(os.path.join(D, "player_match.csv"))
    players = json.load(open(os.path.join(TOOL, "data", "players.json")))["players"]
    S = json.load(open(os.path.join(TOOL, "data", "seasons.json")))["profiles"]
    base = stats_from(sb_totals(pm).set_index(["player_id", "team"]))
    outk = [(p["id"], p["t"]) for p in players if p["fam"] != "Goalkeepers"]
    REF = base.loc[outk].values                        # the 2015/16 reference pool: 1,251 outfield players
    sm = pd.read_csv(os.path.join(D, "season_match.csv"))
    club = {s: stats_from(sb_totals(g).set_index(["player_id", "team"])) for s, g in sm.groupby("season")}
    dates = {}
    for c in (2, 11, 12, 7):
        dates.update({m["match_id"]: m["match_date"] for m in json.load(open(os.path.join(D, f"matches_{c}.json")))})
    pm["half"] = np.where(pm.match_id.map(dates) < "2016-01-01", "2015/16 Aug–Dec", "2015/16 Jan–May")
    half = {s: stats_from(sb_totals(g).set_index(["player_id", "team"])) for s, g in pm.groupby("half")}
    rows_b = [base.loc[(p["id"], p["t"])].values if p["fam"] != "Goalkeepers" else None for p in players]
    rows_s = [(club[q["s"]] if q["k"] == "club" else half[q["s"]]).loc[(q["id"], q["t"])].values if q["fam"] != "Goalkeepers" else None for q in S]
    sbq = lambda rows: [None if r is None else pct_against(REF, r[None])[0].tolist() for r in rows]
    sbv = lambda rows: [None if r is None else [None if np.isnan(v) else float(f"{v:.3g}") for v in r] for r in rows]

    # ---------- Premier League (Opta) seasons ----------
    poss = pd.read_csv(os.path.join(SF, "pl_team_possession.csv"))
    pools = []
    for key, fn, yr, floor, label in [("2025/26", "2025-26", 2025, 900, "Premier League 2025/26"),
                                      ("2026/27", "2026-27", 2026, 450, "Premier League 2026/27, so far")]:
        d = pd.read_csv(os.path.join(SF, f"pl_players_{fn}.csv"))
        d = d[(d.position != "Goalkeeper") & (d.timePlayed >= floor)].reset_index(drop=True)
        X = stats_from(opta_totals(d, dict(poss[poss.season == yr][["team", "possession"]].values))).values
        q = pct_against(X, X)
        val = pd.read_csv(os.path.join(SF, f"pl_values_{fn}.csv")).drop_duplicates("pl_id").set_index("pl_id").market_value_eur
        asof = pd.Timestamp("2026-11-18") if yr == 2026 else None
        age = lambda b: None if pd.isna(b) else int(((asof or pd.Timestamp(f"{yr + 1}-05-31")) - pd.Timestamp(b)).days // 365.25)
        pls = []
        for i, r in d.iterrows():
            mv = val.get(r.pl_id)
            pls.append(dict(n=r["name"], t=TEAM_FULL.get(r.team, r.team), p=r.position, a=age(r.birth_date), min=int(r.timePlayed),
                            mp=int(r.appearances), mv=None if mv is None or pd.isna(mv) else int(mv), q=q[i].tolist(),
                            v=[None if np.isnan(v) else float(f"{v:.3g}") for v in X[i]]))
        pools.append(dict(key=key, label=label, floor=floor, rounds=int(d.timePlayed.max() // 90), players=pls))
        print(key, len(pls), "players")

    # ---------- check: the same 2015/16 Premier League midfielders in both sources ----------
    mid = pd.read_csv(os.path.join(EXT, "pl_midfielders_2010-2018.csv")); mid = mid[(mid.season == 2015) & (mid.timePlayed >= 900)].reset_index(drop=True)
    pposs = pd.read_csv(os.path.join(EXT, "pl_team_possession.csv")); pposs = dict(pposs[pposs.season == 2015][["team", "possession"]].values)
    nick = dict(pd.read_csv(os.path.join(D, "nicknames.csv")).values)
    sbpl = [p for p in players if p["l"] == "Premier League" and p["fam"] != "Goalkeepers"]
    idx = {}
    for p in sbpl:
        for nm in {norm(p["n"]), norm(p["f"]), norm(nick.get(p["id"], ""))}:
            idx.setdefault((nm, TEAM_SB.get(p["t"], p["t"])), p)
    pairs = []
    for i, r in mid.iterrows():
        p = idx.get((norm(r["name"]), r.team))
        if p is None:   # fall back to surname + team
            cand = [q for (nm, tm), q in idx.items() if tm == r.team and nm.split()[-1:] == norm(r["name"]).split()[-1:]]
            p = cand[0] if len({c["id"] for c in cand}) == 1 else None
        if p is not None:
            pairs.append((i, p))
    usable = KEYS
    cols = [KEYS.index(k) for k in usable]
    O = stats_from(opta_totals(mid, pposs)).values[:, cols]
    B = np.stack([base.loc[(p["id"], p["t"])].values[cols] for _, p in pairs]); Om = O[[i for i, _ in pairs]]
    # percentiles within the same matched group on each side, so only the provider differs
    qb, qo = pct_against(B, B), pct_against(Om, Om)
    rho = {k: round(float(pd.Series(B[:, j]).rank().corr(pd.Series(Om[:, j]).rank())), 2) for j, k in enumerate(usable)}
    # same players, same season: how the two providers' raw numbers compare (StatsBomb / Opta, median of the group)
    ratio = {k: round(float(np.nanmedian(B[:, j]) / np.nanmedian(Om[:, j])), 2) if np.nanmedian(Om[:, j]) else None for j, k in enumerate(usable)}
    gap = np.abs(qb[:, None, :] - qo[None, :, :]).mean(2)
    rank = (gap < np.diag(gap)[:, None]).sum(1)
    sim_self = 100 - np.diag(gap); sim_best_other = 100 - np.where(np.eye(len(gap), dtype=bool), 999, gap).min(1)
    chk = dict(n=len(pairs), of=len(mid), top1=round(100 * float(np.mean(rank < 1)), 1), top5=round(100 * float(np.mean(rank < 5)), 1),
               median_rank=int(np.median(rank)) + 1, chance_top5=round(100 * 5 / len(pairs), 1), self_match=round(float(np.median(sim_self)), 1),
               best_other=round(float(np.median(sim_best_other)), 1), rho=rho, ratio=ratio, stats=len(usable))
    print(json.dumps(chk, indent=1))
    weak = [k for k, r in rho.items() if r < 0.5]
    if weak:
        print("WARNING: stats that disagree between providers:", weak)

    # raw values are shown side by side only where both providers count on a similar scale (within 25%)
    same_scale = {k: r is not None and 0.8 <= r <= 1.25 for k, r in ratio.items()}
    json.dump(dict(stats=[dict(k=k, label=l, u=u, raw=same_scale[k]) for k, l, u in STATS], pools=pools, base=sbq(rows_b), seasons=sbq(rows_s),
                   base_v=sbv(rows_b), seasons_v=sbv(rows_s), check=chk),
              open(os.path.join(TOOL, "data", "now.json"), "w"), separators=(",", ":"), ensure_ascii=False)
    print(os.path.getsize(os.path.join(TOOL, "data", "now.json")) // 1024, "KB")


if __name__ == "__main__":
    main()
