"""Fetches the current Premier League season's midfielder stats and team possession, so Midfield Matchup stays up to date.

Writes, in Players/Yaya-Toure-Man-City/data/external/:
  pl_midfielders_current.csv   every midfielder's season-so-far totals (same columns as the other pl_midfielders files)
  pl_team_possession.csv       this season's rows are replaced; earlier seasons are left alone

Run from the repo root:
  python Projects/Midfield-Matchup/fetch_current_season.py            # fetch from the Premier League stats API
  python Projects/Midfield-Matchup/fetch_current_season.py --season 2026
  python Projects/Midfield-Matchup/fetch_current_season.py --from-dump dump.txt   # rows already fetched in a browser

The GitHub Action in .github/workflows/update-midfield-matchup.yml runs this every week, then build_page.py.
"""
import argparse
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from pathlib import Path

import pandas as pd

HERE = Path(__file__).parent
EXT = HERE.parents[1] / "Players" / "Yaya-Toure-Man-City" / "data" / "external"
API = "https://sdp-prem-prod.premier-league-prod.pulselive.com/api/"
HEADERS = {"Origin": "https://www.premierleague.com", "Referer": "https://www.premierleague.com/",
           "User-Agent": "Mozilla/5.0 (Midfield Matchup weekly update)"}
FIELDS = ("appearances,starts,timePlayed,goals,penaltyGoals,goalAssists,expectedGoals,expectedAssists,totalShots,"
          "keyPassesAttemptAssists,throughBalls,totalPasses,totalUnsuccessfulPassesExclCrossesAndCorners,"
          "successfulPassesOppositionHalf,successfulLongPasses,unsuccessfulLongPasses,forwardPasses,touches,"
          "totalTouchesInOppositionBox,successfulDribbles,unsuccessfulDribbles,totalTackles,tacklesWon,interceptions,"
          "recoveries,duelsWon,duelsLost,aerialDuelsWon,totalLossesOfPossession,totalFoulsWon,setPiecesGoals").split(",")


def current_season():
    """The season that started most recently: 2026 means 2026/27 (seasons start in August)."""
    t = date.today()
    return t.year if t.month >= 8 else t.year - 1


def get(session, path):
    for attempt in range(5):
        try:
            r = session.get(API + path, headers=HEADERS, timeout=30)
            if r.status_code == 404:
                return None
            if r.ok:
                return r.json() if r.text else None
        except Exception:
            pass
        time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"could not fetch {path}")


def fetch(season):
    import requests
    s = requests.Session()
    teams = get(s, f"v1/competitions/8/seasons/{season}/teams?_limit=60")["data"]
    rows, poss = [], []
    for tm in teams:
        st = (get(s, f"v2/competitions/8/seasons/{season}/teams/{tm['id']}/stats") or {}).get("stats", {})
        poss.append({"season": season, "team_id": int(tm["id"]), "team": tm["shortName"], "possession": st.get("possessionPercentage"),
                     "team_passes": st.get("totalPasses"), "games": st.get("gamesPlayed")})
        squad = get(s, f"v1/competitions/8/seasons/{season}/teams/{tm['id']}/squad") or []
        mids = [p for p in squad if p.get("position") == "Midfielder"]

        def one(p):
            j = get(s, f"v2/competitions/8/seasons/{season}/players/{p['id']['playerId']}/stats") or {}
            stats = j.get("stats") or {}
            if not stats.get("timePlayed"):
                return None
            return {"season": season, "id": int(p["id"]["playerId"]), "name": p["name"]["display"], "team": tm["shortName"],
                    **{f: stats.get(f) or 0 for f in FIELDS}}

        with ThreadPoolExecutor(6) as ex:
            rows += [r for r in ex.map(one, mids) if r]
        print(f"  {tm['shortName']}: {len([r for r in rows if r['team'] == tm['shortName']])} midfielders")
    return rows, poss


def from_dump(path):
    """Rows fetched in a browser: 'season|id|name|team|v1,v2,...' lines, then POSS, then 'season|team_id|team|poss|passes|games'."""
    text = Path(path).read_text(encoding="utf-8")
    text = text[text.index("BEGINROWS"):text.index("ENDROWS")]
    players, teams = text.split("\nPOSS\n")
    rows = []
    for line in players.splitlines()[1:]:
        if line.strip():
            a = line.split("|")
            rows.append({"season": int(a[0]), "id": int(a[1]), "name": a[2], "team": a[3], **dict(zip(FIELDS, map(float, a[4].split(","))))})
    poss = []
    for line in teams.strip().splitlines():
        a = line.split("|")
        poss.append({"season": int(a[0]), "team_id": int(a[1]), "team": a[2], "possession": float(a[3]) if a[3] else None,
                     "team_passes": float(a[4]) if a[4] else None, "games": int(a[5]) if a[5] else None})
    return rows, poss


def save(rows, poss):
    season = rows[0]["season"]
    old_poss = pd.read_csv(EXT / "pl_team_possession.csv")
    # The site's short club names change over time ("A Villa" became "Villa"); keep the names the rest of the data uses.
    latest = old_poss.sort_values("season").groupby("team_id").team.last()
    rename = {p["team"]: latest.get(p["team_id"], p["team"]) for p in poss}
    p = pd.DataFrame(poss).assign(team=lambda x: x.team.map(rename))
    p = pd.concat([old_poss[old_poss.season != season], p[old_poss.columns].sort_values("team")])
    for c in ("team_passes", "games"):
        p[c] = p[c].round().astype("Int64")
    p.to_csv(EXT / "pl_team_possession.csv", index=False)

    d = pd.DataFrame(rows).assign(team=lambda x: x.team.map(rename).fillna(x.team))
    cols = pd.read_csv(EXT / "pl_midfielders_2018-2026.csv", nrows=1).columns
    for c in cols:
        if c not in ("name", "team", "expectedGoals", "expectedAssists"):
            d[c] = d[c].round().astype(int)
    d = d[cols].sort_values(["team", "name"])
    cur = EXT / "pl_midfielders_current.csv"
    if cur.exists():                       # a new season has started: keep last season's final numbers as their own file
        prev = pd.read_csv(cur)
        if len(prev) and int(prev.season.iloc[0]) != season:
            s0 = int(prev.season.iloc[0])
            prev.to_csv(EXT / f"pl_midfielders_{s0}-{str(s0 + 1)[-2:]}.csv", index=False)
            print(f"archived {s0}/{str(s0 + 1)[-2:]}")
    d.to_csv(cur, index=False)
    games = int(pd.Series([x["games"] for x in poss if x["games"]]).median())
    print(f"{season}/{str(season + 1)[-2:]}: {len(d)} midfielders, {len(poss)} clubs, about {games} games played")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--season", type=int, default=current_season())
    ap.add_argument("--from-dump")
    a = ap.parse_args()
    rows, poss = from_dump(a.from_dump) if a.from_dump else fetch(a.season)
    if not rows:
        sys.exit("no rows fetched")
    save(rows, poss)
