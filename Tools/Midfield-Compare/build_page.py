"""Builds index.html for Midfield Compare from the Premier League midfielder data.

Run from the repo root:  python Tools/Midfield-Compare/build_page.py
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).parent
EXT = HERE.parents[1] / "Players" / "Yaya-Toure-Man-City" / "data" / "external"
MIN_MINUTES = 900          # about ten full games
POSSESSION = EXT / "pl_team_possession.csv"   # season, team, possession (%): official Premier League team stats

# Possession adjustment: a team that has the ball more gives its players more passes and touches, and fewer
# chances to tackle or intercept. On-ball volume is scaled to what it would be at 50% possession (x 50 / team
# possession) and defending to what it would be against 50% opposition possession (x 50 / opponents' possession).
# A 66% possession side's passes are scaled by 0.76 and its tackles by 1.47. Percentages are left as they are.
ON_BALL = ["passes", "opp", "long", "fwd", "touches", "loss"]
OFF_BALL = ["tklw", "int", "rec"]
ADJUSTED = ON_BALL + OFF_BALL


def padj(poss, defending):
    """Multiplier for a stat, given the team's possession in %. 1.0 at 50% possession."""
    return 50 / (100 - poss) if defending else 50 / poss
START = ["14664-2013", "61366-2019"]   # opens on Yaya Touré 2013/14 vs Kevin De Bruyne 2019/20

# Each stat: key, label, group, unit ("90" = per 90 minutes, "%" = percentage), higher_is_better
METRICS = [
    ("ga", "Goals + assists", "Output", "90", True),
    ("minshare", "Share of league minutes played", "Output", "%", True),
    ("npg", "Non-penalty goals", "Scoring", "90", True),
    ("shots", "Shots", "Scoring", "90", True),
    ("xg", "Expected goals", "Scoring", "90", True),
    ("boxtouch", "Touches in the opposition box", "Scoring", "90", True),
    ("ast", "Assists", "Creating", "90", True),
    ("kp", "Chances created", "Creating", "90", True),
    ("xa", "Expected assists", "Creating", "90", True),
    ("tb", "Through balls", "Creating", "90", True),
    ("passes", "Passes", "Passing", "90", True),
    ("passpct", "Pass completion", "Passing", "%", True),
    ("opp", "Passes completed in the opposition half", "Passing", "90", True),
    ("long", "Long passes completed", "Passing", "90", True),
    ("fwd", "Forward passes", "Passing", "90", True),
    ("drib", "Successful dribbles", "Carrying", "90", True),
    ("dribpct", "Dribble success", "Carrying", "%", True),
    ("touches", "Touches", "Carrying", "90", True),
    ("loss", "Possession lost", "Carrying", "90", False),
    ("tklw", "Tackles won", "Defending", "90", True),
    ("int", "Interceptions", "Defending", "90", True),
    ("rec", "Ball recoveries", "Defending", "90", True),
    ("duelpct", "Duels won", "Defending", "%", True),
    ("aer", "Aerial duels won", "Defending", "90", True),
]
GROUPS = ["Output", "Scoring", "Creating", "Passing", "Carrying", "Defending"]
CLASSIC = {"ga", "minshare", "npg", "ast"}
NOT_STYLE = {"xg", "xa"}   # expected goals/assists only exist from 2013/14 and repeat shots and chances created, so style ignores them

# Roles are learned from well-known seasons: each role's "shape" is the average percentile profile of its examples,
# centred on each player's own average so that how good a player was doesn't decide what kind of player he was.
ROLE_INFO = [
    ("6", "holding 6", "a 6", "6s", "screens the defence, recycles the ball and wins it back"),
    ("8", "box-to-box 8", "an 8", "8s", "links defence and attack: passes a lot, presses and gets forward"),
    ("10", "creative 10", "a 10", "10s", "creates and scores chances in the final third"),
    ("w", "wide attacker", "a wide attacker", "wide attackers", "takes players on and attacks the box"),
]
ROLE_EXAMPLES = {
    "6": [("Rodri", 2019), ("Rodri", 2022), ("Rodri", 2023), ("Fernandinho", 2017), ("Nemanja Matic", 2014), ("Michael Carrick", 2012),
          ("Casemiro", 2022), ("Fabinho", 2019), ("Thomas Partey", 2021), ("Jorginho", 2018), ("Declan Rice", 2021), ("Idrissa Gueye", 2018),
          ("Javier Mascherano", 2009), ("N'Golo Kanté", 2016), ("Moisés Caicedo", 2024), ("Lucas Leiva", 2011), ("John Obi Mikel", 2012),
          ("Victor Wanyama", 2016), ("Wilfred Ndidi", 2018)],
    "8": [("Yaya Touré", 2013), ("Jordan Henderson", 2019), ("Georginio Wijnaldum", 2018), ("Ilkay Gündogan", 2020), ("Aaron Ramsey", 2013),
          ("Declan Rice", 2025), ("N'Golo Kanté", 2018), ("Paul Pogba", 2018), ("Mousa Dembélé", 2016), ("Alexis Mac Allister", 2024),
          ("Steven Gerrard", 2013), ("James Milner", 2015), ("Frank Lampard", 2009), ("Bruno Guimarães", 2022), ("Conor Gallagher", 2023),
          ("Mateo Kovacic", 2019), ("Douglas Luiz", 2023)],
    "10": [("Kevin De Bruyne", 2019), ("David Silva", 2011), ("Mesut Özil", 2015), ("Bruno Fernandes", 2020), ("Martin Ødegaard", 2022),
           ("James Maddison", 2022), ("Christian Eriksen", 2017), ("Philippe Coutinho", 2016), ("Cesc Fàbregas", 2014), ("Juan Mata", 2012),
           ("Cole Palmer", 2023), ("Adam Lallana", 2016), ("Gylfi Sigurdsson", 2017), ("Morgan Gibbs-White", 2023)],
    "w": [("Eden Hazard", 2014), ("Riyad Mahrez", 2015), ("Bernardo Silva", 2018), ("Jack Grealish", 2019), ("Aaron Lennon", 2010),
          ("Charles N'Zogbia", 2010), ("Bukayo Saka", 2022), ("Bryan Mbeumo", 2023), ("Mohammed Kudus", 2024), ("Ashley Young", 2010)],
}          # the only stats recorded before 2008/09


def load():
    d = pd.concat([pd.read_csv(EXT / f) for f in ("pl_midfielders_2008-2010.csv", "pl_midfielders_2010-2018.csv", "pl_midfielders_2018-2026.csv")])
    d = d.drop_duplicates(["season", "id"])
    d["name"] = d.id.map(d.sort_values("season").groupby("id").name.last())   # one spelling per player (latest)
    d = d.query("timePlayed >= @MIN_MINUTES").copy()
    p90 = lambda s: s / d.timePlayed * 90
    d["npg"] = p90(d.goals - d.penaltyGoals)
    d["shots"] = p90(d.totalShots)
    d["boxtouch"] = p90(d.totalTouchesInOppositionBox)
    d["ast"] = p90(d.goalAssists)
    d["kp"] = p90(d.keyPassesAttemptAssists)
    XG_FROM = 2013     # Opta expected goals and assists on premierleague.com are complete from 2013/14
    d["xgt"] = d.expectedGoals.where((d.season >= XG_FROM) & ~((d.expectedGoals == 0) & (d.totalShots > 5)))   # 0.0 xG with shots = not recorded
    d["xg"] = p90(d.xgt)
    d["xa"] = p90(d.expectedAssists.where((d.season >= XG_FROM) & d.xgt.notna()))
    d["tb"] = p90(d.throughBalls)
    d["passes"] = p90(d.totalPasses)
    d["passpct"] = 100 * (1 - d.totalUnsuccessfulPassesExclCrossesAndCorners / d.totalPasses)
    d["opp"] = p90(d.successfulPassesOppositionHalf)
    d["long"] = p90(d.successfulLongPasses)
    d["fwd"] = p90(d.forwardPasses)
    d["drib"] = p90(d.successfulDribbles)
    att = d.successfulDribbles + d.unsuccessfulDribbles
    d["dribpct"] = np.where(att >= 15, 100 * d.successfulDribbles / att.where(att > 0), np.nan)   # too few attempts = no percentage
    d["touches"] = p90(d.touches)
    d["loss"] = p90(d.totalLossesOfPossession)
    d["tklw"] = p90(d.tacklesWon)
    d["int"] = p90(d.interceptions)
    d["rec"] = p90(d.recoveries)
    duels = d.duelsWon + d.duelsLost
    d["duelpct"] = 100 * d.duelsWon / duels.where(duels > 0)
    d["aer"] = p90(d.aerialDuelsWon)
    d["ga"] = p90(d.goals + d.goalAssists)
    d["minshare"] = 100 * d.timePlayed / (38 * 90)
    d["era"] = 1
    if POSSESSION.exists():
        poss = pd.read_csv(POSSESSION)
        d = d.merge(poss[["season", "team", "possession"]], on=["season", "team"], how="left")
        missing = d[d.possession.isna()][["season", "team"]].drop_duplicates()
        if len(missing):
            print("no possession for:", missing.values.tolist()[:10], "...")
        for k in ADJUSTED:
            d[k + "_a"] = d[k] * padj(d.possession, k in OFF_BALL)
    return d


def load_classic():
    """1992/93 to 2007/08: minutes, goals and assists only (see build_classic.py)."""
    c = pd.read_csv(EXT / "pl_midfielders_classic_1992-2008.csv").rename(columns={"pl_id": "id"})
    c = c.query("timePlayed >= @MIN_MINUTES").copy()
    p90 = lambda s: s / c.timePlayed * 90
    c["npg"] = p90(c.goals - c.penaltyGoals)
    c["ast"] = p90(c.goalAssists)
    c["ga"] = p90(c.goals + c.goalAssists)
    c["minshare"] = 100 * c.timePlayed / (c.games * 90)
    c["era"] = 0
    return c


def learn_roles(d):
    """Average centred percentile profile of each role's example seasons, plus a leave-one-out check."""
    style = [m[0] for m in METRICS if m[2] != "Output" and m[0] not in NOT_STYLE]
    full = d[d.era == 1]
    pc = lambda k: ("pa_" + k) if ("pa_" + k) in full else ("p_" + k)    # style is judged with team possession taken out
    X = full[[pc(k) for k in style]].astype(float).fillna(50)
    X.columns = ["p_" + k for k in style]
    Xc = X.sub(X.mean(axis=1), axis=0)
    idx, lab = [], []
    for r, ex in ROLE_EXAMPLES.items():
        for name, season in ex:
            hit = full.index[(full.name == name) & (full.season == season)]
            if len(hit):
                idx.append(hit[0]); lab.append(r)
            else:
                print("role example not found:", name, season)
    lab = pd.Series(lab, index=idx)
    cent = lambda excl=None: {r: Xc.loc[[i for i in idx if lab[i] == r and i != excl]].mean() for r in ROLE_EXAMPLES}
    right = sum(min(cent(i).items(), key=lambda kv: ((Xc.loc[i] - kv[1]) ** 2).sum())[0] == lab[i] for i in idx)
    C = pd.DataFrame(cent()).rename(index=lambda x: x[2:])
    standout = C.sub(C.mean(axis=1), axis=0)      # what sets each role apart from the other three
    roles = []
    for key, n, t, ts, desc in ROLE_INFO:
        # The 8 is defined by balance rather than one standout area, so its key stats cover both boxes.
        k = ["passes", "opp", "rec", "tklw", "npg", "drib"] if key == "8" else list(standout[key].sort_values(ascending=False).index[:6])
        roles.append({"id": key, "n": n, "t": t, "ts": ts, "d": desc, "c": {s_: round(float(v), 1) for s_, v in C[key].items()}, "k": k})
    return roles, f"{right}/{len(idx)} example seasons put back in their own role when left out"


def blank_broken_seasons(d):
    """Some Opta fields are missing (all zero) for some seasons on premierleague.com. Blank them rather than rank zeros."""
    report = {}
    for k, *_ in METRICS:
        med = d.groupby("season")[k].median()
        overall = med[med > 0].median()
        bad = med[(med <= 0.15 * overall) | med.isna()].index.tolist()
        if bad:
            d.loc[d.season.isin(bad), k] = np.nan
            report[k] = bad
    return report


def season_label(s):
    return f"{s}/{str(s + 1)[-2:]}"


def player_facts(d):
    """One remarkable, checkable fact per player, found in the data: the most extreme thing about his seasons."""
    lab = {m[0]: m[1].lower() for m in METRICS}
    unit = {m[0]: m[3] for m in METRICS}
    hib = {m[0]: m[4] for m in METRICS}
    fmt = lambda k, v: f"{v:.0f}%" if unit[k] == "%" else (f"{v:.1f}" if v >= 10 else f"{v:.2f}")
    cands = {}                                   # name -> list of (score, text); higher score = more remarkable
    add = lambda n, sc, t: cands.setdefault(n, []).append((sc, t))

    # 1. A season that ranks near the top of the all-time list for one stat (raw per-90 values, every season with the stat)
    for k in [m[0] for m in METRICS if m[0] not in ("minshare", "ga")]:
        col = d[k]
        ok = col.notna()
        if ok.sum() < 200:
            continue
        rank = col[ok].rank(ascending=not hib[k], method="min")
        n, first = int(ok.sum()), int(d.season[ok].min())
        for i in rank[rank <= 25].index:
            r, rk = d.loc[i], int(rank[i])
            word = "lowest" if not hib[k] else "highest"
            val = f"{fmt(k, r[k])}{'' if unit[k] == '%' else ' per 90'}"
            pos = f"the {word}" if rk == 1 else f"the {ordinal(rk)}-{word}"
            text = (f"His {season_label(r.season)} figure for {lab[k]}, {val}, was {pos} by any Premier League midfielder "
                    f"in a season since {season_label(first)}, out of {n:,} seasons.")
            add(r["name"], 100 - rk * 2 + (5 if k in ("npg", "ast", "kp", "drib", "tklw", "int") else 0), text)

    # 2. Finishing far above or below expected goals (from 2013/14)
    g = d[d.xgt.notna() & (d.xgt > 0.5)].copy()     # a few seasons have no xG recorded (0.0); leave those out
    g["diff"] = g.goals - g.xgt
    top = list(g.nlargest(15, "diff").index)
    for i, r in g.loc[top].iterrows():
        add(r["name"], 97 - top.index(i) * 2, f"In {season_label(r.season)} he scored {int(r.goals)} league goals from chances worth just {r.xgt:.1f} expected goals, "
            f"the {'biggest' if top.index(i) == 0 else ordinal(top.index(i) + 1) + '-biggest'} overperformance by a midfielder since 2013/14 (+{r['diff']:.1f}).")
    for i, r in g.nsmallest(8, "diff").iterrows():
        add(r["name"], 70, f"In {season_label(r.season)} he scored only {int(r.goals)} from chances worth {r.xgt:.1f} expected goals, one of the unluckiest finishing seasons by a midfielder since 2013/14.")

    # 3. Every single minute of a season
    for i, r in d[d.minshare >= 99.9].iterrows():
        add(r["name"], 78, f"He played every minute of the {season_label(r.season)} Premier League season for {r.team}.")

    # 4. Longevity and clubs
    car = d.groupby("name").agg(n=("season", "size"), first=("season", "min"), last=("season", "max"), clubs=("team", "nunique"))
    long_rank = car.n.rank(ascending=False, method="min")
    for n_, r in car[car.n >= 12].iterrows():
        add(n_, 80 + r.n, f"He had {r.n} seasons of 900+ Premier League minutes in midfield, {season_label(r['first'])} to {season_label(r['last'])}. "
            f"Only {int(long_rank[n_]) - 1} midfielder{'s' if long_rank[n_] != 2 else ''} {'have' if long_rank[n_] != 2 else 'has'} more." if long_rank[n_] > 1 else
            f"He had {r.n} seasons of 900+ Premier League minutes in midfield, {season_label(r['first'])} to {season_label(r['last'])}: more than any other midfielder.")
    for n_, r in car[car.clubs >= 5].iterrows():
        clubs = ", ".join(d[d.name == n_].sort_values("season").team.drop_duplicates())
        add(n_, 60 + r.clubs, f"He was a regular for {r.clubs} different Premier League clubs: {clubs}.")

    # 5. Rare combination: top 10% for scoring and for defending in the same season (2008/09 onwards)
    full = d[d.era == 1]
    combo = full[(full.p_npg >= 90) & (full.p_tklw >= 90)]
    for i, r in combo.iterrows():
        add(r["name"], 88, f"In {season_label(r.season)} he was in the top 10% of midfielders for both non-penalty goals and tackles won. "
            f"Only {len(combo)} midfield seasons since 2008/09 have managed that.")

    # Fallback: his single best percentile in any season
    for n_, grp in d.groupby("name"):
        if n_ in cands:
            continue
        best = None
        for i, r in grp.iterrows():
            for k in [m[0] for m in METRICS if m[0] not in ("minshare", "ga")]:
                p = r.get("p_" + k)
                if pd.notna(p) and (best is None or p > best[0]):
                    best = (p, k, r)
        if best:
            p, k, r = best
            add(n_, 10, f"His best number: {lab[k]} in {season_label(r.season)} ({fmt(k, r[k])}{'' if unit[k] == '%' else ' per 90'}), "
                f"better than {int(p) - 1}% of Premier League midfielders that season.")
    out = {}
    for n_, lst in cands.items():
        seen, picks = set(), []
        for sc, t in sorted(lst, key=lambda x: -x[0]):
            if t not in seen:
                seen.add(t); picks.append(t)
        out[n_] = picks[:3]
    return out


def ordinal(n):
    return f"{n}{'th' if 11 <= n % 100 <= 13 else {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')}"


def main():
    d = load()
    broken = blank_broken_seasons(d)
    print("blanked (stat: seasons):", broken)
    d = pd.concat([load_classic(), d], ignore_index=True)
    d["goals"], d["goalAssists"] = d.goals.astype(int), d.goalAssists.astype(int)
    adj = [k for k in ADJUSTED if k + "_a" in d]
    for k, _, _, _, hib in METRICS:
        r = d.groupby("season")[k].rank(pct=True, ascending=hib)
        d["p_" + k] = (r * 100).round().astype("Int64")
        if k in adj:
            r = d.groupby("season")[k + "_a"].rank(pct=True, ascending=hib)
            d["pa_" + k] = (r * 100).round().astype("Int64")
    if "possession" not in d:
        d["possession"] = np.nan
    if "xgt" not in d:
        d["xgt"] = np.nan
    cols = (["id", "name", "team", "season", "era", "min", "goals", "assists", "possession", "xgt"] + [m[0] for m in METRICS] + ["p_" + m[0] for m in METRICS]
            + [k + "_a" for k in adj] + ["pa_" + k for k in adj])
    d = d.rename(columns={"timePlayed": "min", "goalAssists": "assists"})
    rows = []
    for r in d[cols].itertuples(index=False):
        out = []
        for c, v in zip(cols, r):
            if c in ("id", "season", "era", "min", "goals", "assists"):
                out.append(int(v))
            elif c in ("name", "team"):
                out.append(v)
            elif c.startswith("p_") or c.startswith("pa_"):
                out.append(None if pd.isna(v) else int(v))
            else:
                out.append(None if pd.isna(v) else round(float(v), 3 if c not in ("passpct", "dribpct", "duelpct", "minshare", "possession", "xgt") else 1))
        rows.append(out)
    facts = player_facts(d)
    print(f"facts: {len(facts)} players")
    roles, acc = learn_roles(d)
    print(f"roles: {acc}")
    data = {"facts": facts, "roles": roles, "cols": cols, "rows": rows, "groups": GROUPS, "start": START, "classic": sorted(CLASSIC), "notStyle": sorted(NOT_STYLE),
            "metrics": [{"k": k, "l": l, "g": g, "u": u} for k, l, g, u, _ in METRICS]}
    last, first = int(d.season.max()), int(d.season.min())
    html = (HERE / "template.html").read_text(encoding="utf-8")
    html = (html.replace("__DATA__", json.dumps(data, ensure_ascii=False, separators=(",", ":")))
                .replace("__LAST__", f"{last}/{str(last + 1)[-2:]}").replace("__FIRST__", f"{first}/{str(first + 1)[-2:]}")
                .replace("__NDETAIL__", f"{(d.era == 1).sum():,}").replace("__NCLASSIC__", f"{(d.era == 0).sum():,}")
                .replace("__MIN__", f"{MIN_MINUTES:,}")
                .replace("__NROWS__", f"{len(rows):,}"))
    (HERE / "page_body.html").write_text(html, encoding="utf-8")   # the page content (published as the shareable artifact)
    doc = ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
           '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
           '</head>\n<body>\n' + html + '\n</body>\n</html>\n')
    (HERE / "index.html").write_text(doc, encoding="utf-8")       # a full web page: open it in any browser, or serve it with GitHub Pages
    print(f"index.html: {len(rows)} player-seasons, {d.id.nunique()} players, seasons {d.season.min()}-{last}, {len(html) / 1e6:.2f} MB")


if __name__ == "__main__":
    main()
