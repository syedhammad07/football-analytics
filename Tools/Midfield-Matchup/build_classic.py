"""Builds the classic-era table (1992/93 to 2007/08) for Midfield Matchup.

Detailed Opta stats are only published from 2008/09, so this era has scoring output only:
- minutes, appearances, starts and penalties: pssguy/epldata (every Premier League appearance with time on and off)
- goals and assists: the official Premier League figures (premierleague.com), matched to epldata by name and date of birth

Input:  data/raw/epldata/ (a clone of github.com/pssguy/epldata) and data/external/pl_classic_goals_assists.csv
Output: Players/Yaya-Toure-Man-City/data/external/pl_midfielders_classic_1992-2008.csv
Run from the repo root:  python Tools/Midfield-Matchup/build_classic.py
"""
import unicodedata
from pathlib import Path

import pandas as pd
import pyreadr

REPO = Path(__file__).resolve().parents[2]
EPL = REPO / "data" / "raw" / "epldata" / "data"
EXT = REPO / "Players" / "Yaya-Toure-Man-City" / "data" / "external"

TEAMS = {"Birmingham C": "Birmingham", "Bradford C": "Bradford", "Coventry C": "Coventry", "Crystal P": "C Palace",
         "Derby Co.": "Derby", "Ipswich T": "Ipswich", "Leeds U": "Leeds", "Leicester C": "Leicester", "Man. City": "Man City",
         "Man. Utd.": "Man Utd", "Middlesbro": "Middlesbrough", "Newcastle U": "Newcastle", "Norwich C": "Norwich",
         "Nottm Forest": "Nott'm Forest", "Sheff. Utd.": "Sheffield Utd", "Sheff. Wed.": "Sheffield Wed", "Swindon T": "Swindon",
         "Tottenham H": "Spurs", "West Ham U": "West Ham", "Wigan Ath.": "Wigan"}


def plain(s):
    s = unicodedata.normalize("NFD", str(s)).encode("ascii", "ignore").decode().lower()
    return "".join(ch for ch in s if ch.isalpha())


def minutes():
    R = lambda f: next(iter(pyreadr.read_r(str(EPL / f"{f}.rda")).values()))
    g, gt, pg, pt, pl, go = R("games"), R("game_team"), R("player_game"), R("player_team"), R("players"), R("goals")
    x = (pg.merge(gt[["team_game_id", "game_id", "team"]], on="team_game_id").merge(g[["game_id", "game_date"]], on="game_id")
           .merge(pt[["player_team_id", "player_id"]], on="player_team_id"))
    x["season"] = x.game_date.dt.year.where(x.game_date.dt.month >= 7, x.game_date.dt.year - 1)
    off = x.time_off.where(x.time_off > 0, 90).clip(upper=90)            # time_off 0 = played to the end
    x["mins"] = (off - x.time_on.clip(0, 90)).clip(lower=0)
    x["app"] = (x.start | (x.time_on > 0)).astype(int)
    x["start"] = x.start.astype(int)
    pens = go[go.play == "P"].groupby("player_game_id").size().rename("pens")
    x = x.merge(pens, left_on="player_game_id", right_index=True, how="left").fillna({"pens": 0})
    x = x[x.season <= 2007]
    games = x.groupby(["season", "team"]).game_id.nunique().groupby("season").max().rename("games")   # 42 until 1994/95, then 38
    a = (x.groupby(["season", "player_id"]).agg(team=("team", lambda s: s.value_counts().index[0]), mins=("mins", "sum"),
                                                 apps=("app", "sum"), starts=("start", "sum"), pens=("pens", "sum"))
          .reset_index().merge(pl, on="player_id").merge(games, left_on="season", right_index=True))
    a["team"] = a.team.replace(TEAMS)
    a["key"] = a.last_name.map(plain) + "|" + a.birth_date.dt.strftime("%Y-%m-%d")
    a["key2"] = (a.first_name.fillna("") + a.last_name).map(plain) + "|" + a.season.astype(str)
    return a


def main():
    m = minutes()
    o = pd.read_csv(EXT / "pl_classic_goals_assists.csv")          # official goals, assists, appearances by season
    o["birth"] = pd.to_datetime(o.birth, format="%d %B %Y", errors="coerce")
    o["key"] = o["last"].map(plain) + "|" + o.birth.dt.strftime("%Y-%m-%d")
    o["key2"] = (o["first"].fillna("") + o["last"]).map(plain) + "|" + o.season.astype(str)
    cols = ["pl_id", "name", "goals", "assists", "pos"]
    o["lastp"], o["byear"] = o["last"].map(plain), o.birth.dt.year
    m["lastp"], m["byear"] = m.last_name.map(plain), m.birth_date.dt.year
    passes = [  # most reliable first: surname + birth date, full name, surname + birth year, surname alone in that season
        ("birth date", ["season", "key"]), ("full name", ["key2"]), ("birth year", ["season", "lastp", "byear"]), ("surname", ["season", "lastp"])]
    j = m.copy()
    for c in cols:
        j[c] = None
    stats = {}
    for label, on in passes:
        todo = j[c].isna() if False else j.goals.isna()
        cand = o.dropna(subset=[k for k in on if k in o]).copy()
        cand = cand[~cand.duplicated(on, keep=False)]                 # only unambiguous matches
        hit = j.loc[todo, on].reset_index().merge(cand[on + cols], on=on, how="inner").set_index("index")
        j.loc[hit.index, cols] = hit[cols].values
        stats[label] = len(hit)
    unmatched = j.goals.isna()
    print("matched to official figures:", stats, "| unmatched (dropped):", int(unmatched.sum()),
          "e.g.", ", ".join(j[unmatched & (j.mins >= 900) & j.position.isin(["M", "Midfielder"])].apply(lambda r: f"{r.first_name} {r.last_name} {r.season}", axis=1).head(8)))
    j = j[~unmatched].copy()
    j = j[j.position.isin(["M", "Midfielder"]) | (j.pos == "M")]     # a midfielder in either source
    out = j.rename(columns={"mins": "timePlayed", "apps": "appearances", "pens": "penaltyGoals", "assists": "goalAssists"})
    out = out[["season", "pl_id", "player_id", "name", "team", "games", "appearances", "starts", "timePlayed", "goals", "penaltyGoals", "goalAssists"]]
    out.to_csv(EXT / "pl_midfielders_classic_1992-2008.csv", index=False)
    print(f"{len(out)} midfielder-seasons, {(out.timePlayed >= 900).sum()} with 900+ minutes")


if __name__ == "__main__":
    main()
