"""Explain each similar-player match and say how close it is.

For every player and each of his top-10 matches (data/similar.csv) this adds:
  - alike_1..3: stats where the two are most alike (and at least one of them stands out)
  - differ_1..3: stats where they differ most, with both values and who is higher
  - overlap_pct: share of the 42 stats where they are within 0.5 standard deviations
  - vs_typical: this match's similarity relative to the median best-match similarity
Output: data/similar_explained.csv, data/match_context.json
"""
import os, json
import numpy as np, pandas as pd
from roles import prep, META

D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

LABEL = {
    "touches_p90": ("Touches", "per 90", 0), "passes_p90": ("Passes", "per 90", 1), "pass_cmp_pct": ("Pass completion", "%", 0),
    "avg_pass_len": ("Average pass length", "m", 1), "long_pass_share": ("Share of long passes", "%", 0),
    "short_pass_share": ("Share of short passes", "%", 0), "fwd_pass_share": ("Share of forward passes", "%", 0),
    "high_pass_share": ("Share of lofted passes", "%", 0), "prog_passes_p90": ("Progressive passes", "per 90", 2),
    "final3_passes_p90": ("Passes into final third", "per 90", 2), "box_passes_p90": ("Passes into the box", "per 90", 2),
    "crosses_p90": ("Crosses", "per 90", 2), "through_balls_p90": ("Through balls", "per 90", 2), "switches_p90": ("Switches of play", "per 90", 2),
    "key_passes_p90": ("Key passes", "per 90", 2), "carries_p90": ("Carries", "per 90", 1), "carry_dist_p90": ("Carry distance", "m per 90", 0),
    "prog_carries_p90": ("Progressive carries", "per 90", 2), "dribbles_p90": ("Dribbles", "per 90", 2), "dribble_success": ("Dribble success", "%", 0),
    "turnovers_p90": ("Ball losses", "per 90", 2), "fouls_won_p90": ("Fouls won", "per 90", 2), "shots_p90": ("Shots", "per 90", 2),
    "npxg_p90": ("Non-penalty xG", "per 90", 2), "npxg_per_shot": ("xG per shot", "", 2), "header_shot_share": ("Share of headed shots", "%", 0),
    "pressures_p90": ("Pressures (poss. adj.)", "per 90", 1), "high_press_share": ("Share of pressures in final third", "%", 0),
    "tackles_p90": ("Tackles (poss. adj.)", "per 90", 2), "interceptions_p90": ("Interceptions (poss. adj.)", "per 90", 2),
    "blocks_p90": ("Blocks (poss. adj.)", "per 90", 2), "clearances_p90": ("Clearances (poss. adj.)", "per 90", 2),
    "recoveries_p90": ("Ball recoveries (poss. adj.)", "per 90", 2), "aerials_p90": ("Aerial duels", "per 90", 2),
    "aerial_win_pct": ("Aerial duels won", "%", 0), "fouls_p90": ("Fouls committed", "per 90", 2), "avg_x": ("Average position up the pitch", "m", 0),
    "avg_width": ("Distance from centre line", "m", 1), "def3_share": ("Touches in own third", "%", 0), "att3_share": ("Touches in final third", "%", 0),
    "box_touch_share": ("Touches in the box", "%", 1), "wide_share": ("Touches out wide", "%", 0),
    # goalkeepers
    "sot_faced_p90": ("Shots on target faced", "per 90", 2), "save_pct": ("Save percentage", "%", 1),
    "goals_prevented_p90": ("Goals prevented vs xG", "per 90", 2), "xg_per_shot_faced": ("xG per shot faced", "", 3),
    "gk_passes_p90": ("Passes", "per 90", 1), "gk_pass_cmp": ("Pass completion", "%", 0), "op_pass_len": ("Open-play pass length", "m", 0),
    "launch_share": ("Share of long launches", "%", 0), "goal_kick_len": ("Goal-kick length", "m", 0), "short_goal_kicks": ("Short goal kicks", "%", 0),
    "sweeper_p90": ("Sweeper actions", "per 90", 2), "sweeper_dist": ("Sweeper action distance from goal", "m", 1),
    "gk_avg_x": ("Average position of keeper actions", "m", 1), "claims_p90": ("High balls caught", "per 90", 2),
    "punches_p90": ("Punches", "per 90", 2), "catch_share": ("High balls caught, not punched", "%", 0),
}


def fmt(c, v):
    name, unit, dp = LABEL[c]
    if unit == "%":
        return f"{v * 100:.{dp}f}%"
    if c in ("avg_x",):
        return f"{v * 105 / 120:.0f} m"  # StatsBomb x is 0-120 yards-ish units; show metres on a 105 m pitch
    return f"{v:.{dp}f}"


def main():
    r = pd.read_csv(os.path.join(D, "roles.csv"))
    s = pd.read_csv(os.path.join(D, "similar.csv"))
    feats = [c for c in r.columns if c not in META + ["family", "role_id", "role_fit"]]
    X = prep(r, feats)
    Z = ((X - X.mean()) / X.std()).values
    idx = {pid_team: i for i, pid_team in enumerate(zip(r.player_id, r.team))}

    best = s[s["rank"] == 1].similarity
    typical = float(best.median())

    rows = []
    for _, m in s.iterrows():
        i = idx[(m.player_id, m.team)]
        j = int(np.where((r.player_id == m.similar_id) & (r.team == m.similar_team))[0][0])
        diff = np.abs(Z[i] - Z[j])
        # "alike" only counts if at least one of the two is clearly not average on that stat
        # "alike" = among the player's 12 signature stats (where he is highest vs the average player), the ones they share
        sig = np.argsort(-Z[i])[:12]
        alike = [feats[k] for k in sorted(sig, key=lambda k: diff[k])][:3]
        differ = [feats[k] for k in np.argsort(-diff)][:3]
        out = dict(m)
        out["overlap_pct"] = round(100 * float((diff <= 0.5).mean()), 0)
        out["vs_typical"] = round(m.similarity - typical, 1)
        for n, c in enumerate(alike, 1):
            out[f"alike_{n}"] = f"{LABEL[c][0]}: {fmt(c, r.at[i, c])} vs {fmt(c, r.at[j, c])}"
        for n, c in enumerate(differ, 1):
            hi = m.player if r.at[i, c] > r.at[j, c] else m.similar
            out[f"differ_{n}"] = f"{LABEL[c][0]}: {fmt(c, r.at[i, c])} vs {fmt(c, r.at[j, c])} (higher: {hi})"
        rows.append(out)
    pd.DataFrame(rows).to_csv(os.path.join(D, "similar_explained.csv"), index=False)
    ctx = dict(typical_best_similarity=typical,
               best_similarity_p10=float(best.quantile(.1)), best_similarity_p90=float(best.quantile(.9)),
               n_players=len(r))
    json.dump(ctx, open(os.path.join(D, "match_context.json"), "w"), indent=1)
    print(ctx)


if __name__ == "__main__":
    main()
