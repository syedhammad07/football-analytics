"""Builds notebooks/03_leicester_players.ipynb."""
import nbformat as nbf

cells = []
md = lambda s: cells.append(nbf.v4.new_markdown_cell(s.strip()))
code = lambda s: cells.append(nbf.v4.new_code_cell(s.strip()))

md("""
# Leicester 2015/16: where their players led the league

Follow-up to `02_leicester_title.ipynb`. This notebook:

1. Compares **distance covered** by team (external data, because event data has no running distances)
2. Builds **32 player metrics** for every outfield player and finds where Leicester players ranked in the league's top 3
3. Looks closer at **Vardy's xG**, **Mahrez's dribbling** and **Kanté's** ball-winning

**Rankings:** season totals compare all outfield players. Per-90 rankings only include players with 900+ minutes (327 players).
""")

code("""
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from mplsoccer import Pitch, VerticalPitch

ROOT = Path.cwd().parent if Path.cwd().name == "notebooks" else Path.cwd()  # project folder
REPO = next(p for p in [ROOT, *ROOT.parents] if (p / "src" / "football_analytics").exists())  # repo root: shared code and downloaded data
DATA = REPO / "data" / "processed" / "2_27"
FIGS = ROOT / "reports" / "figures"

events = pd.read_parquet(DATA / "events.parquet").sort_values(["match_id", "index"])
players = pd.read_parquet(DATA / "player_season.parquet").set_index("player_id")
LEI = "Leicester City"

BLUE, GREY, DARK, MUTED = "#1F5FAD", "#B4B2A9", "#3D3D3A", "#6B6A64"
plt.rcParams.update({
    "figure.dpi": 110, "savefig.dpi": 200, "savefig.bbox": "tight",
    "font.size": 10, "axes.titlesize": 13, "axes.titleweight": "bold", "axes.titlelocation": "left",
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.edgecolor": GREY, "axes.labelcolor": DARK, "xtick.color": DARK, "ytick.color": DARK,
    "axes.grid": True, "grid.color": "#ECEAE4", "grid.linewidth": 0.8, "axes.axisbelow": True,
})
SOURCE = "Data: StatsBomb Open Data, Premier League 2015/16"

def subtitle(ax, text):
    ax.annotate(text, xy=(0, 1.01), xycoords="axes fraction", fontsize=9.5, color=MUTED)

def source(fig, text=SOURCE):
    fig.text(0.01, -0.02, text, fontsize=8, color="#8A8880")
""")

md("""
## 1. Distance covered

StatsBomb event data records on-ball actions only, with no player tracking, so running distance can't be computed from it.
The figures below were published by Sky Sports from the **EA Sports Player Performance Index**, the league's official rating system at the time ([Sky Sports, 8 March 2016](https://www.skysports.com/football/news/10196163/tireless-tottenham-running-further-in-2016-than-any-other-premier-league-team)).

**Caveat:** they cover the season only up to 8 March 2016 (about 29 matches), and Sky listed only the 10 teams that ran furthest. Teams outside this list, including Manchester City, Liverpool and Chelsea, ran less than 109.8 km per 90 minutes.
""")

code("""
distance = pd.DataFrame([
    ("AFC Bournemouth", 3398.9, 117.2), ("Tottenham Hotspur", 3360.5, 115.9),
    ("West Bromwich Albion", 3254.2, 112.2), ("Manchester United", 3229.3, 111.4),
    ("West Ham United", 3215.3, 110.9), ("Leicester City", 3202.9, 110.4),
    ("Arsenal", 3199.6, 110.3), ("Crystal Palace", 3191.7, 110.1),
    ("Sunderland", 3184.5, 109.8), ("Southampton", 3184.0, 109.8),
], columns=["team", "km_total_to_8_march", "km_per_90"])
distance
""")

code("""
d = distance.sort_values("km_per_90")
fig, ax = plt.subplots(figsize=(8, 5))
ax.scatter(d.km_per_90, d.team, s=70, color=[BLUE if t == LEI else GREY for t in d.team], zorder=3)
for i, (t, v) in enumerate(zip(d.team, d.km_per_90)):
    ax.annotate(f"{v:.1f}", (v + 0.25, i), va="center", fontsize=9, color=BLUE if t == LEI else MUTED)
for lbl in ax.get_yticklabels():
    if lbl.get_text() == LEI:
        lbl.set_color(BLUE); lbl.set_fontweight("bold")
ax.set_xlim(108.5, 118.5)
ax.grid(axis="x", visible=False)
ax.set_xlabel("Team distance covered per 90 minutes (km)")
gap = distance.km_per_90.max() - distance.set_index("team").km_per_90[LEI]
ax.set_title(f"Leicester didn't outrun the league: {gap:.1f} km per match less than Bournemouth", pad=22)
subtitle(ax, "The 10 teams that ran furthest, season to 8 March 2016")
source(fig, "Data: EA Sports Player Performance Index via Sky Sports, 8 March 2016")
fig.savefig(FIGS / "06_distance_covered.png"); plt.show()
""")

md("""
## 2. Player metrics

Definitions (StatsBomb pitch is 120 × 80 yards, attacking left to right):

- **Progressive pass / carry:** moves the ball at least 10 yards towards goal (passes must end in the opponent's 2/3 of the pitch)
- **Box:** x ≥ 102 and 18 ≤ y ≤ 62. "Into the box" means starting outside it and ending inside it.
- **xA (expected assists):** xG of the shot that a key pass led to
- **Big chance:** a non-penalty shot worth at least 0.3 xG
- **Dribble success %:** only for players with 30+ attempts
""")

code("""
f = lambda mask: events[mask].groupby("player_id").size()
box = lambda x, y: (x >= 102) & (y >= 18) & (y <= 62)

shots = events[events.type == "Shot"].assign(xg=lambda d: d.shot_statsbomb_xg.astype(float),
                                              goal=lambda d: d.shot_outcome == "Goal")
np_shots = shots[shots.shot_type != "Penalty"]

key = events[events.pass_shot_assist | events.pass_goal_assist][["match_id", "possession", "index", "player_id"]]
nxt = shots[["match_id", "possession", "index", "xg"]].rename(columns={"index": "shot_index"})
xa = (key.merge(nxt, on=["match_id", "possession"]).query("shot_index > index")
         .sort_values("shot_index").drop_duplicates(["match_id", "index"]).groupby("player_id").xg.sum())

P = events[events.type == "Pass"]
done = P.pass_outcome.isna()
open_play = ~P.pass_type.isin(["Corner", "Throw-in", "Kick Off", "Free Kick", "Goal Kick"])
C = events[events.type == "Carry"]
D = events[events.type == "Dribble"]
T = events[(events.type == "Duel") & (events.duel_type == "Tackle")]
Pr = events[events.type == "Pressure"]
g = lambda df: df.groupby("player_id").size()

metrics = {
    "Goals": shots.groupby("player_id").goal.sum(),
    "Non-penalty goals": np_shots.groupby("player_id").goal.sum(),
    "xG": shots.groupby("player_id").xg.sum(),
    "Non-penalty xG": np_shots.groupby("player_id").xg.sum(),
    "Non-penalty goals minus xG": np_shots.groupby("player_id").goal.sum() - np_shots.groupby("player_id").xg.sum(),
    "Shots": g(shots),
    "Shots on target": g(shots[shots.shot_outcome.isin(["Goal", "Saved", "Saved To Post"])]),
    "Big chances": g(np_shots[np_shots.xg >= 0.3]),
    "Counter-attack goals": g(shots[shots.goal & (shots.play_pattern == "From Counter")]),
    "Assists": f(events.pass_goal_assist),
    "Chances created": f(events.pass_shot_assist | events.pass_goal_assist),
    "Expected assists (xA)": xa,
    "Through balls completed": g(P[done & P.pass_through_ball]),
    "Progressive passes": g(P[done & open_play & ((P.pass_end_x - P.start_x) >= 10) & (P.pass_end_x >= 40)]),
    "Passes into the box": g(P[done & open_play & box(P.pass_end_x, P.pass_end_y) & ~box(P.start_x, P.start_y)]),
    "Crosses completed": g(P[done & P.pass_cross]),
    "Long passes completed": g(P[done & (P.pass_length.astype(float) >= 32)]),
    "Dribbles completed": g(D[D.dribble_outcome == "Complete"]),
    "Dribbles attempted": g(D),
    "Progressive carries": g(C[(C.carry_end_x - C.start_x) >= 10]),
    "Carries into the box": g(C[box(C.carry_end_x, C.carry_end_y) & ~box(C.start_x, C.start_y)]),
    "Fouls won": f(events.type == "Foul Won"),
    "Tackles": g(T),
    "Tackles won": g(T[T.duel_outcome.isin(["Won", "Success In Play", "Success Out"])]),
    "Interceptions": f(events.type == "Interception"),
    "Tackles + interceptions": g(T).add(f(events.type == "Interception"), fill_value=0),
    "Ball recoveries": f(events.type == "Ball Recovery"),
    "Pressures": g(Pr),
    "Pressures in attacking third": g(Pr[Pr.start_x >= 80]),
    "Blocks": f(events.type == "Block"),
    "Clearances": f(events.type == "Clearance"),
}
stats = players.join(pd.DataFrame(metrics)).fillna(0)
stats["Dribble success %"] = np.where(stats["Dribbles attempted"] >= 30,
                                      stats["Dribbles completed"] / stats["Dribbles attempted"].replace(0, np.nan) * 100, np.nan)
outfield = stats[stats.position_group != "Goalkeeper"]
print(f"{len(metrics) + 1} metrics for {len(outfield)} outfield players")
""")

md("""
## 3. Where Leicester players ranked in the league's top 3

For each metric, the table shows the Leicester player's rank and value, the league leader, and the best player from another club.
""")

code("""
rows = []
for metric in list(metrics) + ["Dribble success %"]:
    bases = [("Season total", outfield[metric])]
    if metric != "Dribble success %":
        reg = outfield[outfield.minutes >= 900]
        bases.append(("Per 90", reg[metric] / reg.minutes * 90))
    for basis, values in bases:
        ranked = values.dropna().sort_values(ascending=False)
        team = outfield.loc[ranked.index, "main_team"]
        best_other = ranked[team != LEI]
        for rank, (pid, v) in enumerate(ranked.head(3).items(), start=1):
            if team[pid] == LEI:
                rows.append({
                    "Metric": metric, "Basis": basis, "Rank": rank,
                    "Leicester player": outfield.loc[pid, "display_name"], "Value": round(v, 2),
                    "Best from another club": f"{outfield.loc[best_other.index[0], 'display_name']} ({best_other.iloc[0]:.2f})",
                    "_other": best_other.iloc[0],
                })
leaders = pd.DataFrame(rows).sort_values(["Rank", "Leicester player", "Basis"]).reset_index(drop=True)
leaders.drop(columns="_other")
""")

code("""
firsts = leaders[(leaders.Rank == 1) & (leaders.Basis == "Season total")
                 & (leaders.Metric != "Dribbles attempted")].copy()
firsts["margin_pct"] = (firsts.Value / firsts._other - 1) * 100
firsts = firsts.sort_values("margin_pct")

fig, ax = plt.subplots(figsize=(9, 5.8))
y = np.arange(len(firsts))
ax.barh(y, firsts.margin_pct, color=BLUE, height=0.6)
labels = [f"{m}  ·  {p}" for m, p in zip(firsts.Metric, firsts["Leicester player"])]
ax.set_yticks(y, labels)
for i, (_, r) in enumerate(firsts.iterrows()):
    digits = 1 if r["Value"] % 1 else 0
    other_name = r["Best from another club"].rsplit(" (", 1)[0]
    ax.annotate(f"{r['Value']:.{digits}f} vs {r['_other']:.{digits}f} ({other_name})", (r["margin_pct"] + 0.5, i),
                va="center", fontsize=8.5, color=MUTED)
ax.grid(axis="y", visible=False)
ax.set_xlim(0, firsts.margin_pct.max() * 1.9)
ax.set_xlabel("Lead over the best player from another club (%)")
ax.set_title(f"Leicester players led the whole league in {len(firsts)} metrics", pad=22)
subtitle(ax, "Season totals, outfield players · value vs the best player from another club")
source(fig); fig.savefig(FIGS / "07_leicester_league_leaders.png"); plt.show()
""")

md("""
## 4. Jamie Vardy: shot locations and xG
""")

code("""
vardy_id = stats.index[stats.display_name == "Jamie Vardy"][0]
v = shots[shots.player_id == vardy_id]
v_np = v[v.shot_type != "Penalty"]
print(f"Shots {len(v)}, goals {v.goal.sum()} ({(v.shot_type == 'Penalty').sum()} penalties, "
      f"{v[v.shot_type == 'Penalty'].goal.sum()} scored)")
print(f"xG {v.xg.sum():.1f} (most in the league), non-penalty xG {v_np.xg.sum():.1f}, non-penalty goals {v_np.goal.sum()}")
print(f"xG per non-penalty shot {v_np.xg.mean():.3f}; league average for forwards "
      f"{np_shots[np_shots.player_id.isin(outfield[outfield.position_group == 'Forward'].index)].xg.mean():.3f}")
print("Goals by play pattern:", v[v.goal].play_pattern.value_counts().to_dict())
""")

code("""
import sys; sys.path.insert(0, str(REPO / "src"))
from football_analytics.viz import leaderboard
fig = plt.figure(figsize=(13, 5.6))
gs = fig.add_gridspec(1, 2, width_ratios=[1.5, 1], wspace=0.45)
ax, ax2 = fig.add_subplot(gs[0]), fig.add_subplot(gs[1])
pitch = VerticalPitch(pitch_type="statsbomb", half=True, line_color=GREY, linewidth=1, pad_bottom=-22)
pitch.draw(ax=ax)
leaderboard(ax2, outfield["xG"], outfield.display_name, outfield.main_team, fmt="{:.1f}",
            title="Total xG: league top 10")
miss, goal = v_np[~v_np.goal], v_np[v_np.goal]
pitch.scatter(miss.start_x, miss.start_y, s=miss.xg * 900 + 20, ax=ax, facecolor="white", edgecolor=GREY, lw=1.2, zorder=2)
pitch.scatter(goal.start_x, goal.start_y, s=goal.xg * 900 + 20, ax=ax, color=BLUE, alpha=0.85, edgecolor="white", lw=0.8, zorder=3)
for size, lab in [(0.05, "0.05 xG"), (0.3, "0.3"), (0.6, "0.6")]:
    ax.scatter([], [], s=size * 900 + 20, facecolor="white", edgecolor=DARK, label=lab)
ax.scatter([], [], s=80, color=BLUE, label="Goal")
ax.legend(loc="upper center", ncol=4, frameon=False, fontsize=9, bbox_to_anchor=(0.5, 0.0), labelspacing=1.4)
ax.set_title(f"Vardy: {v_np.goal.sum()} non-penalty goals from {v_np.xg.sum():.1f} xG", loc="left",
             fontsize=13, fontweight="bold", pad=24)
ax.annotate(f"{len(v_np)} non-penalty shots; dot size = xG\\nplus {v[v.shot_type == 'Penalty'].goal.sum()} penalty goals", xy=(0, 1.015), xycoords="axes fraction", fontsize=9, color=MUTED)
ax.annotate(SOURCE, xy=(1, -0.2), xycoords="axes fraction", ha="right", fontsize=8, color="#8A8880")
fig.savefig(FIGS / "08_vardy_shot_map.png"); plt.show()
""")

md("""
## 5. Riyad Mahrez: dribbling
""")

code("""
mahrez_id = stats.index[stats.display_name == "Riyad Mahrez"][0]
mz = events[(events.player_id == mahrez_id) & (events.type == "Dribble")]
ok = mz[mz.dribble_outcome == "Complete"]
attempts = outfield["Dribbles attempted"]
q = outfield[attempts >= 100].assign(success=lambda d: d["Dribbles completed"] / d["Dribbles attempted"] * 100)
print(f"Mahrez: {len(ok)} completed of {len(mz)} ({len(ok) / len(mz):.0%}); "
      f"{(ok.start_x >= 80).mean():.0%} of completed dribbles in the attacking third")
q.sort_values("Dribbles completed", ascending=False)[["display_name", "main_team", "Dribbles completed",
                                                       "Dribbles attempted", "success"]].head(6).round(1)
""")

code("""
import sys; sys.path.insert(0, str(REPO / "src"))
from football_analytics.viz import ABBR

def dribble_bars(df, col, label_fn, title, subtitle, xlabel, fname, median=None, fmt="{:.0f}"):
    top = df.sort_values(col, ascending=False).head(10)
    y = np.arange(len(top))[::-1]
    lei = (top.main_team == "Leicester City").values
    fig, ax = plt.subplots(figsize=(10, 5.6))
    ax.barh(y, top[col], color=np.where(lei, BLUE, GREY), height=0.68)
    vmax = top[col].max()
    for yi, (_, r), h in zip(y, top.iterrows(), lei):
        ax.text(r[col] + vmax * 0.012, yi, fmt.format(r[col]), va="center", fontsize=10,
                fontweight="bold", color=BLUE if h else DARK)
        ax.text(r[col] + vmax * 0.012 + vmax * 0.075, yi, label_fn(r), va="center", fontsize=8.5,
                color=BLUE if h else MUTED)
    names = [f"{i}. {r.display_name} ({ABBR[r.main_team]})" for i, (_, r) in enumerate(top.iterrows(), 1)]
    ax.set_yticks(y, names, fontsize=10)
    for t, h in zip(ax.get_yticklabels(), lei):
        if h:
            t.set_color(BLUE); t.set_fontweight("bold")
    if median is not None:
        ax.axvline(median, color=DARK, lw=1, ls="--")
        ax.text(median, -0.95, f" league median {median:.2f}", fontsize=8.5, color=DARK, va="center")
    ax.set_xlim(0, vmax * 1.42)
    ax.set_ylim(-1.3, len(top) - 0.4)
    ax.set_xlabel(xlabel)
    ax.grid(axis="y", visible=False)
    ax.tick_params(axis="y", length=0)
    ax.set_title(title, loc="left", fontsize=13.5, fontweight="bold", pad=24)
    ax.annotate(subtitle, xy=(0, 1.015), xycoords="axes fraction", fontsize=9.5, color=MUTED)
    ax.annotate(SOURCE, xy=(0, -0.155), xycoords="axes fraction", fontsize=8, color="#8A8880")
    fig.savefig(FIGS / fname); plt.show()

d = outfield.assign(success=lambda x: x["Dribbles completed"] / x["Dribbles attempted"] * 100)
dribble_bars(d, "Dribbles completed",
             lambda r: f"of {r['Dribbles attempted']:.0f} attempts",
             "Mahrez completed more dribbles than any player in the league",
             "Completed dribbles, season total, Premier League 2015/16 top 10. Leicester in blue",
             "Completed dribbles", "09_mahrez_dribbles.png")
""")

md("""
### Completed dribbles per 90 minutes

Season totals reward players who play a lot. Per 90 minutes compares everyone on equal playing time (players with 900+ minutes).
""")

code("""
reg = d[d.minutes >= 900].assign(p90=lambda x: x["Dribbles completed"] / x.minutes * 90)
dribble_bars(reg, "p90",
             lambda r: f"{r['Dribbles completed']:.0f} in {r.minutes:,.0f} min ({r.success:.0f}% success)",
             "Per 90 minutes, Mahrez was 3rd, behind Zaha and Sánchez",
             f"Completed dribbles per 90 minutes, players with 900+ minutes (n={len(reg)}). Leicester in blue",
             "Completed dribbles per 90 minutes", "23_mahrez_dribbles_per90.png",
             median=reg.p90.median(), fmt="{:.2f}")
rank = reg.p90.rank(ascending=False, method="min")
print("Mahrez per 90:", round(reg.loc[mahrez_id, "p90"], 2), "rank", int(rank[mahrez_id]), "of", len(reg),
      "| league median", round(reg.p90.median(), 2))
""")

md("""
## 6. Leicester as a team: where they ranked

The same metrics summed by team (all 20 teams; 1 = highest).
""")

code("""
team_totals = stats.groupby("main_team")[list(metrics)].sum()
team_rank = team_totals.rank(ascending=False, method="min").astype(int)
team_view = pd.DataFrame({"Leicester": team_totals.loc[LEI].round(1), "Rank (of 20)": team_rank.loc[LEI],
                          "League leader": team_totals.idxmax(), "Leader value": team_totals.max().round(1)})
team_view.sort_values("Rank (of 20)").head(15)
""")

md("""
## Summary

- **Distance:** Leicester ran **110.4 km per 90 minutes**, about the same as Arsenal and 6.8 km less than Bournemouth (EA Sports PPI, season to 8 March 2016). They didn't win by outrunning teams.
- **Vardy:** the most xG in the league (22.3, including 6 penalties) and the most counter-attack goals (5). His chances were unusually good: 0.157 xG per non-penalty shot, against 0.111 for forwards in general. He also made the most pressures in the attacking third of any player (271), so the striker was the first line of the press.
- **Mahrez:** the most completed dribbles in the league (123 of 218, 56%). He beat his xG by +5.5 non-penalty goals, 2nd only to Agüero, and won the 2nd-most fouls.
- **Kanté:** 1st in tackles, tackles won, interceptions, tackles plus interceptions and ball recoveries. Also 2nd in pressures and blocks.
- **Fuchs:** the most blocks in the league (115), just ahead of Kanté (114). Huth made the 2nd-most clearances.

- **As a team:** Leicester ranked 1st of 20 in total xG (66.3), blocks (961), and tackles plus interceptions (1,364).

Leicester players led on effort and ball-winning metrics (pressing, tackles, interceptions, blocks) and on directness metrics (counter goals, dribbles). They didn't lead on possession metrics such as progressive passes.
""")

nb = nbf.v4.new_notebook(cells=cells, metadata={"kernelspec": {"name": "python3", "display_name": "Python 3"}})
nbf.write(nb, "notebooks/03_leicester_players.ipynb")
print("written")
