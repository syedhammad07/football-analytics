"""Goalkeeper style features from StatsBomb events -> data/gk_features.csv (900+ minutes).

Shot-stopping: on-target shots faced, save %, goals prevented vs xG, xG per shot faced
Distribution:  passes, completion, open-play pass length, share of long launches, goal-kick length, short goal kicks
Sweeping:      sweeper actions, how far from goal they happen, average position of all keeper actions
Crosses:       claims, punches, share of high balls caught rather than punched
Penalties are left out of shot-stopping. Minutes come from data/player_match.csv.
"""
import os, json, urllib.request
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
import numpy as np, pandas as pd

BASE = "https://raw.githubusercontent.com/statsbomb/open-data/master/data"
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
ALIAS = {"Marseille": "Olympique de Marseille", "Caen": "Stade Malherbe Caen"}
ON_TARGET = {"Goal", "Saved", "Saved to Post"}
SHOT_GK = {"Shot Faced", "Shot Saved", "Goal Conceded", "Shot Saved to Post", "Shot Saved Off Target", "Save", "Penalty Conceded", "Penalty Saved"}


def get(url):
    for _ in range(4):
        try:
            return json.loads(urllib.request.urlopen(url, timeout=60).read())
        except Exception as e:
            err = e
    raise err


def match_gk(m):
    ev = get(f"{BASE}/events/{m['match_id']}.json")
    byid = {e["id"]: e for e in ev}
    S = defaultdict(lambda: defaultdict(float)); seen = set()
    for e in ev:
        if "player" not in e:
            continue
        pid = e["player"]["id"]
        pos = e.get("position", {}).get("name")
        if e["type"]["name"] == "Goal Keeper":
            g = e["goalkeeper"]; gt = g["type"]["name"]; s = S[pid]
            s["gk_x_sum"] += e.get("location", [0])[0]; s["gk_n"] += 1
            if gt in SHOT_GK:
                for rid in e.get("related_events", []):
                    sh = byid.get(rid)
                    if not sh or sh["type"]["name"] != "Shot" or (pid, rid) in seen:
                        continue
                    seen.add((pid, rid))
                    if sh["shot"].get("type", {}).get("name") == "Penalty":
                        continue
                    xg = sh["shot"].get("statsbomb_xg", 0); out = sh["shot"]["outcome"]["name"]
                    s["shots_faced"] += 1; s["xg_faced"] += xg
                    if out in ON_TARGET:
                        s["sot_faced"] += 1; s["xg_on_target"] += xg
                    if out == "Goal":
                        s["goals_conceded"] += 1
            elif gt == "Collected":
                s["claims"] += 1
            elif gt == "Punch":
                s["punches"] += 1
            elif gt in ("Keeper Sweeper", "Smother"):
                s["sweeper"] += 1; s["sweeper_x"] += e.get("location", [0])[0]
        elif e["type"]["name"] == "Pass" and pos == "Goalkeeper":
            p = e["pass"]; s = S[pid]; L = p.get("length", 0); ok = "outcome" not in p
            kind = p.get("type", {}).get("name")
            if kind == "Goal Kick":
                s["goal_kicks"] += 1; s["gk_len"] += L; s["gk_short"] += L < 30
            else:
                s["op_passes"] += 1; s["op_len"] += L; s["launches"] += L >= 40; s["op_ok"] += ok
            s["passes"] += 1; s["passes_ok"] += ok
    return [dict(match_id=m["match_id"], player_id=pid, **v) for pid, v in S.items()]


def main():
    jobs = [m for c in (2, 11, 12, 7) for m in get(f"{BASE}/matches/{c}/27.json")]
    rows = []
    with ThreadPoolExecutor(16) as ex:
        for res in ex.map(match_gk, jobs):
            rows.extend(res)
    gk = pd.DataFrame(rows).fillna(0)
    pm = pd.read_csv(os.path.join(D, "player_match.csv"))
    pm["team"] = pm.team.replace(ALIAS)
    gk = gk.merge(pm[["match_id", "player_id", "player", "team", "league", "minutes", "top_position"]], on=["match_id", "player_id"])
    gk = gk[gk.top_position == "Goalkeeper"]
    num = [c for c in gk.columns if c not in ("match_id", "player_id", "player", "team", "league", "top_position")]
    gk.to_csv(os.path.join(D, "gk_match.csv"), index=False)
    a = gk.groupby(["player_id", "player", "team", "league"])[num].sum().reset_index()
    a["matches"] = gk.groupby(["player_id", "player", "team", "league"]).size().values
    a = a[a.minutes >= 900].copy()
    p90 = lambda c: a[c] / a.minutes * 90
    share = lambda x, y: np.where(a[y] > 0, a[x] / a[y].replace(0, np.nan), 0)
    F = pd.DataFrame(index=a.index)
    F["sot_faced_p90"] = p90("sot_faced")
    F["save_pct"] = 1 - share("goals_conceded", "sot_faced")
    F["goals_prevented_p90"] = (a.xg_faced - a.goals_conceded) / a.minutes * 90
    F["xg_per_shot_faced"] = share("xg_faced", "shots_faced")
    F["gk_passes_p90"] = p90("passes")
    F["gk_pass_cmp"] = share("passes_ok", "passes")
    F["op_pass_len"] = share("op_len", "op_passes")
    F["launch_share"] = share("launches", "op_passes")
    F["goal_kick_len"] = share("gk_len", "goal_kicks")
    F["short_goal_kicks"] = share("gk_short", "goal_kicks")
    F["sweeper_p90"] = p90("sweeper")
    F["sweeper_dist"] = np.where(a.sweeper > 0, a.sweeper_x / a.sweeper.replace(0, np.nan), np.nan)
    F["sweeper_dist"] = F.sweeper_dist.fillna(F.sweeper_dist.median())
    F["gk_avg_x"] = share("gk_x_sum", "gk_n")
    F["claims_p90"] = p90("claims")
    F["punches_p90"] = p90("punches")
    F["catch_share"] = share("claims", np.nan) if False else np.where(a.claims + a.punches > 0, a.claims / (a.claims + a.punches).replace(0, np.nan), 0)
    out = pd.concat([a[["player_id", "player", "team", "league", "minutes", "matches"]], F], axis=1).reset_index(drop=True)
    out.to_csv(os.path.join(D, "gk_features.csv"), index=False)
    print(len(out), "goalkeeper-seasons;", F.shape[1], "features")
    print(out.describe().T[["mean", "min", "max"]].round(3).to_string())


if __name__ == "__main__":
    main()
