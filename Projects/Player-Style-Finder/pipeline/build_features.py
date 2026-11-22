"""Build per-player-season style features from StatsBomb open data (2015/16).

Downloads each match's events, aggregates per player per match, then sums to
player-season and converts to per-90 rates and shares. Raw events are not kept.
Output: data/player_match.csv (derived counts), data/features.csv (per-90 style features).
"""
import json, os, sys, math, urllib.request
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
import pandas as pd

BASE = "https://raw.githubusercontent.com/statsbomb/open-data/master/data"
LEAGUES = {2: "Premier League", 11: "La Liga", 12: "Serie A", 7: "Ligue 1"}
SEASON = 27
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
os.makedirs(OUT, exist_ok=True)


def get(url):
    for _ in range(4):
        try:
            with urllib.request.urlopen(url, timeout=60) as r:
                return json.loads(r.read())
        except Exception as e:
            err = e
    raise err


def dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


GOAL = (120, 40)
# the open data uses two names for a few clubs; use the name from the match files
ALIAS = {"Marseille": "Olympique de Marseille", "Caen": "Stade Malherbe Caen"}


def progressive(start, end):
    # move at least 25% closer to goal centre, and ends in opponent half or >10m gain
    d0, d1 = dist(start, GOAL), dist(end, GOAL)
    return d1 <= 0.75 * d0 and end[0] > 60


def match_rows(match, league):
    mid = match["match_id"]
    ev = get(f"{BASE}/events/{mid}.json")
    # match length per period
    period_end = defaultdict(float)
    for e in ev:
        t = e["minute"] + e["second"] / 60
        period_end[e["period"]] = max(period_end[e["period"]], t)
    # StatsBomb minutes are cumulative across periods, so match length = last minute
    total = max(v for p, v in period_end.items() if p <= 4)
    on, off, info = {}, {}, {}
    team_passes = defaultdict(int)
    S = defaultdict(lambda: defaultdict(float))
    pos_count = defaultdict(lambda: defaultdict(int))

    def abs_min(e):
        # minutes elapsed in match terms
        m = e["minute"] + e["second"] / 60
        return min(m, total)

    for e in ev:
        typ = e["type"]["name"]
        team = e.get("team", {}).get("name")
        team = ALIAS.get(team, team)
        if typ == "Starting XI":
            for p in e["tactics"]["lineup"]:
                pid = p["player"]["id"]
                on[pid] = 0.0
                info[pid] = (p["player"]["name"], team)
            continue
        if typ == "Substitution":
            off[e["player"]["id"]] = abs_min(e)
            r = e["substitution"]["replacement"]
            on[r["id"]] = abs_min(e)
            info[r["id"]] = (r["name"], team)
        card = (e.get("foul_committed", {}) or {}).get("card", {}).get("name") or \
               (e.get("bad_behaviour", {}) or {}).get("card", {}).get("name")
        if card in ("Red Card", "Second Yellow") and "player" in e:
            off[e["player"]["id"]] = abs_min(e)
        if typ == "Pass":
            team_passes[team] += 1
        if "player" not in e:
            continue
        pid = e["player"]["id"]
        s = S[pid]
        if "position" in e:
            pos_count[pid][e["position"]["name"]] += 1
        loc = e.get("location")
        if loc and typ in ("Pass", "Carry", "Shot", "Dribble", "Ball Receipt*", "Duel",
                           "Interception", "Clearance", "Ball Recovery", "Block", "Pressure",
                           "Miscontrol", "Dispossessed", "Foul Won"):
            if typ != "Pressure":
                s["touches"] += 1
                s["x_sum"] += loc[0]
                s["absy_sum"] += abs(loc[1] - 40)
                if loc[0] < 40: s["t_def3"] += 1
                elif loc[0] < 80: s["t_mid3"] += 1
                else: s["t_att3"] += 1
                if loc[0] >= 102 and 18 <= loc[1] <= 62: s["t_box"] += 1
                if loc[1] < 18 or loc[1] > 62: s["t_wide"] += 1
        if typ == "Pass":
            p = e["pass"]
            if p.get("type", {}).get("name") in ("Corner", "Free Kick", "Throw-in", "Kick Off", "Goal Kick"):
                s["set_piece_passes"] += 1
                continue
            s["passes"] += 1
            ok = "outcome" not in p
            s["passes_ok"] += ok
            end = p["end_location"]
            L = p.get("length", dist(loc, end))
            s["pass_len_sum"] += L
            if L >= 32: s["long_passes"] += 1
            if L < 15: s["short_passes"] += 1
            if end[0] - loc[0] > 0: s["fwd_passes"] += 1
            if ok and progressive(loc, end): s["prog_passes"] += 1
            if ok and loc[0] < 80 <= end[0]: s["final3_passes"] += 1
            if ok and end[0] >= 102 and 18 <= end[1] <= 62 and not (loc[0] >= 102 and 18 <= loc[1] <= 62):
                s["box_passes"] += 1
            if p.get("cross"): s["crosses"] += 1
            if p.get("through_ball") or p.get("technique", {}).get("name") == "Through Ball":
                s["through_balls"] += 1
            if p.get("switch"): s["switches"] += 1
            if p.get("shot_assist") or p.get("goal_assist"): s["key_passes"] += 1
            if p.get("height", {}).get("name") == "High Pass": s["high_passes"] += 1
            if p.get("body_part", {}).get("name") == "Head": s["headed_passes"] += 1
            if p.get("aerial_won"): s["aerials_won"] += 1
        elif typ == "Carry":
            end = e["carry"]["end_location"]
            s["carries"] += 1
            s["carry_dist"] += dist(loc, end)
            if progressive(loc, end) and dist(loc, end) >= 5: s["prog_carries"] += 1
        elif typ == "Dribble":
            s["dribbles"] += 1
            if e["dribble"].get("outcome", {}).get("name") == "Complete": s["dribbles_ok"] += 1
        elif typ == "Shot":
            sh = e["shot"]
            if sh.get("type", {}).get("name") == "Penalty":
                continue
            s["shots"] += 1
            s["npxg"] += sh.get("statsbomb_xg", 0)
            s["shot_dist_sum"] += dist(loc, GOAL)
            if sh.get("body_part", {}).get("name") == "Head": s["headers"] += 1
            if sh.get("outcome", {}).get("name") == "Goal": s["np_goals"] += 1
            if sh.get("aerial_won"): s["aerials_won"] += 1
        elif typ == "Pressure":
            s["pressures"] += 1
            if loc and loc[0] >= 80: s["pressures_att3"] += 1
        elif typ == "Duel":
            d = e["duel"]
            dt = d.get("type", {}).get("name")
            if dt == "Tackle":
                s["tackles"] += 1
                if d.get("outcome", {}).get("name") in ("Won", "Success", "Success In Play", "Success Out"):
                    s["tackles_won"] += 1
            elif dt == "Aerial Lost":
                s["aerials_lost"] += 1
        elif typ == "Interception":
            s["interceptions"] += 1
        elif typ == "Block":
            s["blocks"] += 1
        elif typ == "Clearance":
            s["clearances"] += 1
            if e.get("clearance", {}).get("aerial_won"): s["aerials_won"] += 1
        elif typ == "Ball Recovery":
            s["recoveries"] += 1
        elif typ == "Foul Committed":
            s["fouls"] += 1
        elif typ == "Foul Won":
            s["fouls_won"] += 1
        elif typ in ("Miscontrol", "Dispossessed"):
            s["turnovers"] += 1
        elif typ == "Goal Keeper":
            s["gk_actions"] += 1

    teams = list(team_passes)
    rows = []
    for pid, (name, team) in info.items():
        mins = max(0.0, off.get(pid, total) - on.get(pid, 0.0))
        if mins <= 0:
            continue
        opp = [t for t in teams if t != team]
        tp, op = team_passes.get(team, 0), (team_passes.get(opp[0], 0) if opp else 0)
        poss = tp / (tp + op) if tp + op else 0.5
        pos = max(pos_count[pid].items(), key=lambda kv: kv[1])[0] if pos_count[pid] else None
        r = dict(match_id=mid, league=league, player_id=pid, player=name, team=team,
                 minutes=mins, team_poss=poss, top_position=pos,
                 pos_events=json.dumps(pos_count[pid]))
        r.update(S[pid])
        rows.append(r)
    return rows


def main():
    jobs = []
    for cid, lg in LEAGUES.items():
        for m in get(f"{BASE}/matches/{cid}/{SEASON}.json"):
            jobs.append((m, lg))
    print(len(jobs), "matches", flush=True)
    rows, done = [], 0
    with ThreadPoolExecutor(16) as ex:
        for res in ex.map(lambda j: match_rows(*j), jobs):
            rows.extend(res)
            done += 1
            if done % 100 == 0:
                print(done, flush=True)
    df = pd.DataFrame(rows).fillna(0)
    df.to_csv(os.path.join(OUT, "player_match.csv"), index=False)
    print("rows", len(df))


if __name__ == "__main__":
    main()
