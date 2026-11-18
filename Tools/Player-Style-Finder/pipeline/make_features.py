"""Player-match counts -> player-season per-90 style features (outfield, >= 900 min)."""
import os, json
from collections import Counter
import numpy as np
import pandas as pd

D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
MIN_MINUTES = 900

POS_GROUP = {
    "Goalkeeper": "GK",
    "Center Back": "CB", "Left Center Back": "CB", "Right Center Back": "CB",
    "Left Back": "FB", "Right Back": "FB", "Left Wing Back": "FB", "Right Wing Back": "FB",
    "Center Defensive Midfield": "DM", "Left Defensive Midfield": "DM", "Right Defensive Midfield": "DM",
    "Center Midfield": "CM", "Left Center Midfield": "CM", "Right Center Midfield": "CM",
    "Left Midfield": "W", "Right Midfield": "W", "Left Wing": "W", "Right Wing": "W",
    "Center Attacking Midfield": "AM", "Left Attacking Midfield": "AM", "Right Attacking Midfield": "AM",
    "Center Forward": "FW", "Left Center Forward": "FW", "Right Center Forward": "FW", "Secondary Striker": "FW",
}


def build(pm, min_minutes=MIN_MINUTES):
    pm = pm.copy()
    # possession-adjust defensive actions to a 50/50 match
    DEF = ["pressures", "pressures_att3", "tackles", "interceptions", "blocks", "clearances", "recoveries"]
    opp_poss = (1 - pm["team_poss"]).clip(0.25, 0.75)
    for c in DEF:
        pm[c + "_padj"] = pm[c] * 0.5 / opp_poss


    num = pm.select_dtypes("number").columns.drop(["match_id", "player_id", "team_poss"])
    g = pm.groupby(["player_id", "player", "team", "league"])
    agg = g[num].sum().reset_index()
    agg["matches"] = g.size().values
    agg["team_poss"] = g["team_poss"].mean().values
    pos = [sum((Counter(json.loads(x)) for x in grp["pos_events"]), Counter()) for _, grp in g]
    agg["position"] = [c.most_common(1)[0][0] if c else None for c in pos]
    agg["pos_group"] = agg["position"].map(POS_GROUP)

    agg = agg[(agg.minutes >= min_minutes) & (agg.pos_group != "GK") & agg.pos_group.notna()].copy()

    p90 = lambda c: agg[c] / agg.minutes * 90
    safe = lambda a, b: np.where(agg[b] > 0, agg[a] / agg[b].replace(0, np.nan), 0)

    F = pd.DataFrame(index=agg.index)
    # involvement & passing style
    F["touches_p90"] = p90("touches")
    F["passes_p90"] = p90("passes")
    F["pass_cmp_pct"] = safe("passes_ok", "passes")
    F["avg_pass_len"] = safe("pass_len_sum", "passes")
    F["long_pass_share"] = safe("long_passes", "passes")
    F["short_pass_share"] = safe("short_passes", "passes")
    F["fwd_pass_share"] = safe("fwd_passes", "passes")
    F["high_pass_share"] = safe("high_passes", "passes")
    F["prog_passes_p90"] = p90("prog_passes")
    F["final3_passes_p90"] = p90("final3_passes")
    F["box_passes_p90"] = p90("box_passes")
    F["crosses_p90"] = p90("crosses")
    F["through_balls_p90"] = p90("through_balls")
    F["switches_p90"] = p90("switches")
    F["key_passes_p90"] = p90("key_passes")
    # carrying & dribbling
    F["carries_p90"] = p90("carries")
    F["carry_dist_p90"] = p90("carry_dist")
    F["prog_carries_p90"] = p90("prog_carries")
    F["dribbles_p90"] = p90("dribbles")
    F["dribble_success"] = safe("dribbles_ok", "dribbles")
    F["turnovers_p90"] = p90("turnovers")
    F["fouls_won_p90"] = p90("fouls_won")
    # shooting
    F["shots_p90"] = p90("shots")
    F["npxg_p90"] = p90("npxg")
    F["npxg_per_shot"] = safe("npxg", "shots")
    F["header_shot_share"] = safe("headers", "shots")
    # defending (possession adjusted)
    F["pressures_p90"] = p90("pressures_padj")
    F["high_press_share"] = safe("pressures_att3", "pressures")
    F["tackles_p90"] = p90("tackles_padj")
    F["interceptions_p90"] = p90("interceptions_padj")
    F["blocks_p90"] = p90("blocks_padj")
    F["clearances_p90"] = p90("clearances_padj")
    F["recoveries_p90"] = p90("recoveries_padj")
    F["aerials_p90"] = (agg.aerials_won + agg.aerials_lost) / agg.minutes * 90
    F["aerial_win_pct"] = np.where(agg.aerials_won + agg.aerials_lost > 0,
                                   agg.aerials_won / (agg.aerials_won + agg.aerials_lost).replace(0, np.nan), 0)
    F["fouls_p90"] = p90("fouls")
    # where on the pitch
    F["avg_x"] = safe("x_sum", "touches")
    F["avg_width"] = safe("absy_sum", "touches")
    F["def3_share"] = safe("t_def3", "touches")
    F["att3_share"] = safe("t_att3", "touches")
    F["box_touch_share"] = safe("t_box", "touches")
    F["wide_share"] = safe("t_wide", "touches")

    meta = agg[["player_id", "player", "team", "league", "position", "pos_group", "minutes", "matches", "team_poss"]]
    out = pd.concat([meta, F], axis=1).reset_index(drop=True)
    return out


if __name__ == "__main__":
    out = build(pd.read_csv(os.path.join(D, "player_match.csv")))
    out.to_csv(os.path.join(D, "features.csv"), index=False)
    print(len(out), "player-seasons;", out.shape[1] - 9, "features")
    print(out.pos_group.value_counts().to_dict())
