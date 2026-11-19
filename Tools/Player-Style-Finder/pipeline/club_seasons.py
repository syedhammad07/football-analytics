"""Extra seasons: StatsBomb's free single-club seasons -> data/season_match.csv, data/season_gk_match.csv.

These seasons cover only one club's matches (every Barcelona La Liga season 2004/05 to 2020/21,
Arsenal 2003/04, PSG 2021/22 and 2022/23, Leverkusen 2023/24), so only that club's players are kept:
opponents play the club once or twice, far too little to describe them.
Each match's events are downloaded once and used for both outfield and goalkeeper stats.
"""
import os, threading
from concurrent.futures import ThreadPoolExecutor
import pandas as pd
import build_features as bf
import gk_features as gkf

D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
# (competition id, season id, league, club, season label)
SEASONS = [(11, s, "La Liga", "Barcelona", lab) for s, lab in [
    (37, "2004/05"), (38, "2005/06"), (39, "2006/07"), (40, "2007/08"), (41, "2008/09"), (21, "2009/10"),
    (22, "2010/11"), (23, "2011/12"), (24, "2012/13"), (25, "2013/14"), (26, "2014/15"),
    (2, "2016/17"), (1, "2017/18"), (4, "2018/19"), (42, "2019/20"), (90, "2020/21")]] + [
    (2, 44, "Premier League", "Arsenal", "2003/04"),
    (7, 108, "Ligue 1", "Paris Saint-Germain", "2021/22"),
    (7, 235, "Ligue 1", "Paris Saint-Germain", "2022/23"),
    (9, 281, "Bundesliga", "Bayer Leverkusen", "2023/24"),
]

# one events download per match, shared by the outfield and goalkeeper code
_local = threading.local()
_raw_get = bf.get


def cached_get(url):
    c = getattr(_local, "c", None)
    if c and c[0] == url:
        return c[1]
    v = _raw_get(url)
    if "/events/" in url:
        _local.c = (url, v)
    return v


bf.get = gkf.get = cached_get


def one(job):
    m, lg, club, lab = job
    rows = [r for r in bf.match_rows(m, lg) if r["team"] == club]
    gk = gkf.match_gk(m)
    for r in rows:
        r["season"] = lab
    for r in gk:
        r["season"] = lab
    return rows, gk


def main():
    jobs = []
    for cid, sid, lg, club, lab in SEASONS:
        for m in bf.get(f"{bf.BASE}/matches/{cid}/{sid}.json"):
            jobs.append((m, lg, club, lab))
    print(len(jobs), "matches", flush=True)
    rows, gks, done = [], [], 0
    with ThreadPoolExecutor(12) as ex:
        for r, g in ex.map(one, jobs):
            rows += r; gks += g; done += 1
            if done % 100 == 0:
                print(done, flush=True)
    pm = pd.DataFrame(rows).fillna(0)
    pm.to_csv(os.path.join(D, "season_match.csv"), index=False)
    gk = pd.DataFrame(gks).fillna(0)
    gk = gk.merge(pm[["match_id", "player_id", "player", "team", "league", "minutes", "top_position"]],
                  on=["match_id", "player_id"])
    gk = gk[gk.top_position == "Goalkeeper"]
    gk.to_csv(os.path.join(D, "season_gk_match.csv"), index=False)
    print("outfield rows", len(pm), "keeper rows", len(gk))


if __name__ == "__main__":
    main()
