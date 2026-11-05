"""Builds notebooks/02_leicester_title.ipynb (run once; the notebook is the deliverable)."""
import nbformat as nbf

cells = []
md = lambda s: cells.append(nbf.v4.new_markdown_cell(s.strip()))
code = lambda s: cells.append(nbf.v4.new_code_cell(s.strip()))

md("""
# How did Leicester win the 2015/16 Premier League?

Leicester City started the season as **5000–1 outsiders** and finished it as champions, 10 points clear.
This notebook uses StatsBomb event data for all 380 matches to break the title down into five questions:

1. **Were they really the best team, or lucky?** Points vs expected points (xPts) from shot quality
2. **How did they attack?** Possession, directness and counter-attacks
3. **How did they defend?** Shots and chance quality conceded, and how it changed over the season
4. **Who made it work?** Vardy, Mahrez, Kanté and the supporting cast
5. **Did squad stability matter?** Players used and line-up changes

Data: `data/processed/2_27/` built by `python -m football_analytics.data 2 27` and `python -m football_analytics.clean`.
""")

code("""
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from mplsoccer import Pitch

ROOT = Path.cwd().parent if Path.cwd().name == "notebooks" else Path.cwd()
DATA = ROOT / "data" / "processed" / "2_27"
FIGS = ROOT / "reports" / "figures"
FIGS.mkdir(parents=True, exist_ok=True)

events = pd.read_parquet(DATA / "events.parquet")
player_match = pd.read_parquet(DATA / "player_match.parquet")
players = pd.read_parquet(DATA / "player_season.parquet")
matches = pd.read_parquet(ROOT / "data" / "raw" / "2_27" / "matches.parquet")

LEI = "Leicester City"
RIVALS = ["Arsenal", "Tottenham Hotspur", "Manchester City"]

# Chart style: every team grey, Leicester in one blue accent
BLUE, GREY, DARK = "#1F5FAD", "#B4B2A9", "#3D3D3A"
plt.rcParams.update({
    "figure.dpi": 110, "savefig.dpi": 200, "savefig.bbox": "tight",
    "font.size": 10, "axes.titlesize": 13, "axes.titleweight": "bold", "axes.titlelocation": "left",
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.edgecolor": GREY, "axes.labelcolor": DARK, "xtick.color": DARK, "ytick.color": DARK,
    "axes.grid": True, "grid.color": "#ECEAE4", "grid.linewidth": 0.8, "axes.axisbelow": True,
})
SOURCE = "Data: StatsBomb Open Data, Premier League 2015/16"

def finish(fig, name, subtitle=None):
    if subtitle:
        fig.axes[0].annotate(subtitle, xy=(0, 1.01), xycoords="axes fraction", fontsize=9.5, color="#6B6A64")
    fig.text(0.01, -0.02, SOURCE, fontsize=8, color="#8A8880")
    fig.savefig(FIGS / f"{name}.png")
    plt.show()

shots = events[events["type"] == "Shot"].copy()
shots["xg"] = shots["shot_statsbomb_xg"].astype(float)
shots["goal"] = shots["shot_outcome"] == "Goal"
print(f"{len(matches)} matches, {len(events):,} player actions, {len(shots):,} shots")
""")

md("""
## 1. Team-match table

One row per team per match: goals, xG for and against, and a possession proxy (share of the match's passes).
""")

code("""
m = matches.assign(hs=matches["home_score"].astype(int), aw=matches["away_score"].astype(int))
rows = []
for r in m.itertuples():
    rows.append(dict(match_id=r.match_id, date=r.match_date, team=r.home_team, opp=r.away_team, gf=r.hs, ga=r.aw, home=True))
    rows.append(dict(match_id=r.match_id, date=r.match_date, team=r.away_team, opp=r.home_team, gf=r.aw, ga=r.hs, home=False))
tm = pd.DataFrame(rows)
tm["pts"] = np.select([tm.gf > tm.ga, tm.gf == tm.ga], [3, 1], 0)

xg_for = shots.groupby(["match_id", "team"])["xg"].sum().rename("xgf")
tm = tm.join(xg_for, on=["match_id", "team"]).fillna({"xgf": 0})
tm["xga"] = tm.groupby("match_id")["xgf"].transform("sum") - tm["xgf"]

passes = events[events["type"] == "Pass"].groupby(["match_id", "team"]).size().rename("passes")
tm = tm.join(passes, on=["match_id", "team"])
tm["possession"] = tm["passes"] / tm.groupby("match_id")["passes"].transform("sum")

tm = tm.sort_values(["team", "date"])
tm["game"] = tm.groupby("team").cumcount() + 1
tm.head()
""")

md("""
## 2. Expected points: were Leicester the best team?

For every match, each shot is simulated 10,000 times as a goal with probability equal to its xG.
The share of simulations a team wins or draws gives its **expected points (xPts)**: the points its chances deserved on average.
""")

code("""
rng = np.random.default_rng(42)
N_SIMS = 10_000
xpts = {}
for match_id, g in shots.groupby("match_id"):
    home, away = tm.loc[tm.match_id == match_id, "team"].tolist()
    sims = {}
    for team in (home, away):
        p = g.loc[g.team == team, "xg"].to_numpy()
        sims[team] = (rng.random((N_SIMS, len(p))) < p).sum(axis=1)
    for a, b in ((home, away), (away, home)):
        xpts[(match_id, a)] = (3 * (sims[a] > sims[b]) + (sims[a] == sims[b])).mean()
tm["xpts"] = [xpts[(r.match_id, r.team)] for r in tm.itertuples()]

table = (tm.groupby("team")
           .agg(Pts=("pts", "sum"), xPts=("xpts", "sum"), GF=("gf", "sum"), GA=("ga", "sum"),
                xGF=("xgf", "sum"), xGA=("xga", "sum"), possession=("possession", "mean"))
           .assign(GD=lambda d: d.GF - d.GA, overperformance=lambda d: d.Pts - d.xPts))
table = table.sort_values(["Pts", "GD"], ascending=False)
table["rank"] = range(1, 21)
table["xPts_rank"] = table["xPts"].rank(ascending=False).astype(int)
table.round(1)
""")

code("""
t = table.sort_values("Pts")
fig, ax = plt.subplots(figsize=(8, 7))
for i, (team, r) in enumerate(t.iterrows()):
    c = BLUE if team == LEI else GREY
    ax.plot([r.xPts, r.Pts], [i, i], color=c, lw=2, solid_capstyle="round", zorder=1)
    ax.scatter(r.xPts, i, s=45, facecolor="white", edgecolor=c, lw=1.6, zorder=2)
    ax.scatter(r.Pts, i, s=45, color=c, zorder=3)
ax.set_yticks(range(len(t)), t.index)
for lbl in ax.get_yticklabels():
    if lbl.get_text() == LEI:
        lbl.set_color(BLUE); lbl.set_fontweight("bold")
lei = table.loc[LEI]
ax.annotate(f"+{lei.overperformance:.0f} points above what\\ntheir chances earned",
            xy=(lei.xPts + (lei.Pts - lei.xPts) / 2, len(t) - 1), xytext=(36, len(t) - 2.2),
            fontsize=9, color=BLUE, va="center", arrowprops=dict(arrowstyle="-", color=BLUE, lw=0.8))
ax.set_xlabel("Points")
ax.grid(axis="y", visible=False)
ax.scatter([], [], s=45, facecolor="white", edgecolor=DARK, label="Expected points (from shot xG)")
ax.scatter([], [], s=45, color=DARK, label="Actual points")
ax.legend(loc="lower right", frameon=False)
ax.set_title(f"Leicester's chances were worth {lei.xPts:.0f} points, 4th best. They took {lei.Pts:.0f}.", pad=22)
finish(fig, "01_points_vs_expected_points", "Each shot simulated 10,000 times as a goal with probability = its xG")
""")

code("""
lei_games = tm[tm.team == LEI]
summary = pd.DataFrame({
    team: {
        "Wins": (g.pts == 3).sum(), "Draws": (g.pts == 1).sum(), "Losses": (g.pts == 0).sum(),
        "One-goal wins": ((g.gf - g.ga) == 1).sum(), "1-0 wins": ((g.gf == 1) & (g.ga == 0)).sum(),
        "Clean sheets": (g.ga == 0).sum(),
    }
    for team, g in tm[tm.team.isin([LEI] + RIVALS)].groupby("team")
})[[LEI] + RIVALS]
summary
""")

code("""
pens = shots[shots.shot_type == "Penalty"].groupby("team").agg(penalties=("goal", "size"), scored=("goal", "sum"))
np_xg = shots[shots.shot_type != "Penalty"].groupby("team")["xg"].sum().rename("non_penalty_xG")
pens.join(np_xg).sort_values("penalties", ascending=False).head(6).round(1)
""")

code("""
fig, ax = plt.subplots(figsize=(9, 5.2))
for team, g in tm[tm.team.isin([LEI] + RIVALS)].groupby("team"):
    g = g.sort_values("game")
    lead = team == LEI
    ax.plot(g.game, g.pts.cumsum(), color=BLUE if lead else GREY, lw=2.4 if lead else 1.6, zorder=3 if lead else 2)
    ax.annotate(f"{team} {g.pts.sum()}", (38.5, {"Arsenal": 72.6, "Tottenham Hotspur": 69.4, "Manchester City": 66.4}.get(team, g.pts.sum())),
                va="center", fontsize=9, annotation_clip=False,
                color=BLUE if lead else "#6B6A64", fontweight="bold" if lead else "normal")
g = lei_games.sort_values("game")
ax.plot(g.game, g.xpts.cumsum(), color=BLUE, lw=1.3, ls=(0, (3, 2)), zorder=2)
ax.annotate(f"Leicester expected {g.xpts.sum():.0f}", (38.5, 63.2), va="center", fontsize=9,
            color=BLUE, annotation_clip=False)
ax.set_xlim(1, 38); ax.set_xticks([1, 10, 19, 28, 38])
ax.set_xlabel("Matches played"); ax.set_ylabel("Cumulative points")
ax.set_title(f"Leicester finished {g.pts.sum() - g.xpts.sum():.0f} points above their expected total, and 10 clear", pad=22)
finish(fig, "02_title_race", "Cumulative points of the top four; dashed line = Leicester's expected points")
""")

md("""
## 3. How Leicester attacked: few passes, fast shots

For each shot, count the passes in that possession before the shot and the seconds since the possession began.
""")

code("""
ev = events.assign(t=events.period * 10_000 + events.clock * 60)
poss_start = ev.groupby(["match_id", "possession"])["t"].min().rename("poss_start")
poss_passes = ev[ev.type == "Pass"].groupby(["match_id", "possession"]).size().rename("passes_before")

open_shots = shots[shots.shot_type != "Penalty"].join(poss_start, on=["match_id", "possession"])
open_shots = open_shots.join(passes_before := poss_passes, on=["match_id", "possession"]).fillna({"passes_before": 0})
open_shots["secs"] = open_shots.period * 10_000 + open_shots.clock * 60 - open_shots.poss_start

pass_events = events[(events.type == "Pass") & ~events.pass_type.isin(["Corner", "Throw-in", "Kick Off", "Free Kick", "Goal Kick"])]
style = pd.DataFrame({
    "possession": table.possession,
    "median_passes_before_shot": open_shots.groupby("team").passes_before.median(),
    "fast_shot_share": open_shots.groupby("team").secs.apply(lambda s: (s <= 15).mean()),
    "long_ball_share": pass_events.groupby("team").pass_length.apply(lambda s: (s.astype(float) >= 32).mean()),
    "pass_completion": pass_events.groupby("team").pass_outcome.apply(lambda s: s.isna().mean()),
    "counter_xg_share": open_shots.groupby("team").apply(lambda g: g.loc[g.play_pattern == "From Counter", "xg"].sum() / g.xg.sum(), include_groups=False),
    "np_xg_per_shot": open_shots.groupby("team").xg.mean(),
})
style.sort_values("fast_shot_share", ascending=False).round(3)
""")

code("""
fig, ax = plt.subplots(figsize=(8, 5.5))
x, y = style.possession * 100, style.fast_shot_share * 100
others = style.index != LEI
ax.scatter(x[others], y[others], s=55, color=GREY, zorder=2)
ax.scatter(x[LEI], y[LEI], s=80, color=BLUE, zorder=3)
offsets = {LEI: (8, 4, "left"), "Arsenal": (-8, -3, "right"), "Tottenham Hotspur": (-8, -3, "right"),
           "Manchester City": (-8, -3, "right"), "West Bromwich Albion": (8, -3, "left"), "Sunderland": (8, -3, "left")}
for team, (dx, dy, ha) in offsets.items():
    ax.annotate(team, (x[team], y[team]), xytext=(dx, dy), textcoords="offset points", fontsize=9, ha=ha,
                color=BLUE if team == LEI else "#6B6A64", fontweight="bold" if team == LEI else "normal")
ax.set_xlabel("Average possession (% of the match's passes)")
ax.set_ylabel("Shots within 15 s of winning the ball (%)")
ax.set_title("Leicester had little of the ball and shot faster than anyone", pad=22)
finish(fig, "03_possession_vs_directness", "Excluding penalties; each dot is one team")
""")

md("""
## 4. How Leicester defended

They faced plenty of shots, but mostly poor ones, and the defence tightened sharply in the second half of the season.
""")

code("""
opp_of = tm.set_index(["match_id", "team"])["opp"]
shots_against = shots.assign(defending=[opp_of[(m_, t_)] for m_, t_ in zip(shots.match_id, shots.team)])
defence = shots_against.groupby("defending").agg(shots_against=("xg", "size"), xg_per_shot_against=("xg", "mean"))
defence = defence.join(table[["GA", "xGA"]])
defence.loc[[LEI] + RIVALS].round(3)
""")

code("""
lg = lei_games.sort_values("game")
halves = pd.DataFrame({
    half: {"Points": g.pts.sum(), "Expected points": round(g.xpts.sum(), 1),
           "Goals scored": g.gf.sum(), "xG for": round(g.xgf.sum(), 1),
           "Goals conceded": g.ga.sum(), "xG against": round(g.xga.sum(), 1),
           "Clean sheets": (g.ga == 0).sum()}
    for half, g in [("Matches 1-19", lg[lg.game <= 19]), ("Matches 20-38", lg[lg.game > 19])]
})
halves
""")

md("""
## 5. Where did the extra 15 points come from?

Compare goals with xG at both ends of the pitch. `goals_saved_vs_xG` = xG conceded − goals conceded (positive means fewer goals conceded than the chances allowed).
`np_finishing` = non-penalty goals − non-penalty xG.
""")

code("""
np_goals = shots[shots.shot_type != "Penalty"].groupby("team").agg(np_goals=("goal", "sum"), np_xG=("xg", "sum"))
ends = table[["Pts", "xPts", "GA", "xGA"]].join(np_goals)
ends["np_finishing"] = ends.np_goals - ends.np_xG
ends["goals_saved_vs_xG"] = ends.xGA - ends.GA
ends.sort_values("goals_saved_vs_xG", ascending=False).round(1).head(8)
""")

md("""
## 6. Who made it work

Season totals for Leicester's regulars, plus how N'Golo Kanté's ball-winning compares with the rest of the league.
""")

code("""
def per_player(mask, name):
    return events[mask].groupby("player_id").size().rename(name)

stats = players.set_index("player_id").join([
    shots.groupby("player_id").agg(goals=("goal", "sum"), xG=("xg", "sum"),
                                   penalties=("shot_type", lambda s: (s == "Penalty").sum())),
    shots[shots.shot_type != "Penalty"].groupby("player_id").agg(np_goals=("goal", "sum"), np_xG=("xg", "sum")),
    per_player(events.pass_goal_assist, "assists"),
    per_player(events.pass_shot_assist | events.pass_goal_assist, "chances_created"),
    per_player((events.type == "Duel") & (events.duel_type == "Tackle"), "tackles"),
    per_player(events.type == "Interception", "interceptions"),
]).fillna(0)
stats["tackles_int_p90"] = (stats.tackles + stats.interceptions) / stats.minutes * 90

cols = ["display_name", "position_group", "minutes", "goals", "penalties", "np_goals", "np_xG",
        "assists", "chances_created", "tackles", "interceptions"]
stats[stats.main_team == LEI].sort_values("minutes", ascending=False)[cols].head(11).round(1)
""")

code("""
regulars = stats[(stats.minutes >= 1800) & (stats.position_group != "Goalkeeper")]
regulars.assign(tackles_plus_int=regulars.tackles + regulars.interceptions) \\
    .sort_values("tackles_plus_int", ascending=False)[["display_name", "main_team", "tackles_plus_int", "tackles_int_p90"]] \\
    .head(8).round(2)
""")

code("""
kante_id = stats.index[stats.display_name == "N'Golo Kanté"][0]
k = events[(events.player_id == kante_id) &
           (((events.type == "Duel") & (events.duel_type == "Tackle")) | (events.type == "Interception"))]
import sys; sys.path.insert(0, str(ROOT / "src"))
from football_analytics.viz import leaderboard
of = stats[stats.position_group != "Goalkeeper"]
fig = plt.figure(figsize=(14.5, 6.2))
gs = fig.add_gridspec(1, 2, width_ratios=[2.3, 1], wspace=0.32)
ax, ax2 = fig.add_subplot(gs[0]), fig.add_subplot(gs[1])
pitch = Pitch(pitch_type="statsbomb", line_color="#B4B2A9", linewidth=1, pitch_color="white")
pitch.draw(ax=ax)
leaderboard(ax2, of.tackles + of.interceptions, of.display_name, of.main_team,
            title="Tackles + interceptions: league top 10")
tack = k[k.type == "Duel"]; inter = k[k.type == "Interception"]
pitch.scatter(tack.start_x, tack.start_y, ax=ax, s=28, color=BLUE, alpha=0.75, label=f"Tackles ({len(tack)})")
pitch.scatter(inter.start_x, inter.start_y, ax=ax, s=28, facecolor="white", edgecolor=BLUE, lw=1.2,
              label=f"Interceptions ({len(inter)})")
ax.legend(loc="upper left", bbox_to_anchor=(0, 0.0), ncol=2, frameon=False, fontsize=9)
ax.set_title(f"N'Golo Kanté won the ball {len(k)} times, more than any player in the league", loc="left",
             fontsize=13, fontweight="bold", pad=24)
ax.annotate("Every tackle and interception, 2015/16 Premier League · Leicester attack left to right",
            xy=(0, 1.02), xycoords="axes fraction", fontsize=9.5, color="#6B6A64")
ax.annotate(SOURCE, xy=(1, -0.04), xycoords="axes fraction", ha="right", va="top", fontsize=8, color="#8A8880")
fig.savefig(FIGS / "04_kante_ball_winning.png"); plt.show()
""")

code("""
assists_to_vardy = events[events.pass_goal_assist & events.pass_recipient.str.contains("Vardy", na=False)]
assists_to_vardy.player.value_counts()
""")

md("""
## 7. Squad stability

`xi_changes` counts, across the season, how many players came into the starting XI compared with the previous match.
""")

code("""
starters = player_match[player_match.started].merge(tm[["match_id", "team", "game"]], on=["match_id", "team"])
xi = starters.sort_values("game").groupby(["team", "game"]).player_id.apply(frozenset)
stability = pd.DataFrame({
    "players_used": player_match.groupby("team").player_id.nunique(),
    "xi_changes": xi.groupby("team").apply(lambda s: sum(len(a - b) for a, b in zip(s.values[1:], s.values[:-1]))),
    "top11_minutes_share": player_match.groupby(["team", "player_id"]).minutes.sum()
                             .groupby("team").apply(lambda s: s.nlargest(11).sum() / s.sum()),
}).sort_values("xi_changes")
stability.round(3)
""")

code("""
s = stability.sort_values("xi_changes", ascending=False)
fig, ax = plt.subplots(figsize=(8, 6.5))
colors = [BLUE if t == LEI else GREY for t in s.index]
ax.barh(s.index, s.xi_changes, color=colors, height=0.7)
for i, (team, v) in enumerate(s.xi_changes.items()):
    if team in [LEI, "Sunderland"] + RIVALS:
        ax.annotate(str(v), (v + 2, i), va="center", fontsize=9, color=BLUE if team == LEI else "#6B6A64")
for lbl in ax.get_yticklabels():
    if lbl.get_text() == LEI:
        lbl.set_color(BLUE); lbl.set_fontweight("bold")
ax.grid(axis="y", visible=False)
ax.set_xlabel("Changes to the starting XI across 38 matches")
ax.set_title(f"Leicester changed their line-up least and used only {stability.loc[LEI, 'players_used']} players", pad=22)
finish(fig, "05_squad_stability", "Players brought into the starting XI compared with the previous match, summed over the season")
""")

md("""
## Summary

The numbers behind each statement are printed in the cells above; `docs/results.md` lists them with their evidence.

1. **A top-four team that took title-winning points.** Leicester's chances were worth about 66 expected points, 4th in the league. They took 81, the biggest overperformance in the league (+15).
2. **Attack carried the first half, defence the second.** In matches 1–19 they scored 37 goals from 31.0 xG (including penalties) while conceding in line with xG. In matches 20–38 the attack cooled (31 goals from 35.3 xG), but the defence conceded only **11 goals from 20.2 xG against**, with 11 clean sheets. Over the whole season, non-penalty finishing was on par with xG (57 from 56.1). The real outlier is defence: 10 goals fewer conceded than the chances allowed, the most in the league (next best: 3.5).
3. **They won tight games.** They had 14 one-goal wins (Arsenal had 7, Spurs 6) and only 3 defeats. They also won the most penalties in the league, 13.
4. **A counter-attacking side.** They had the 3rd-lowest possession and the fastest attack in the league. Their median shot came after 3 passes, and 67% of their shots came within 15 seconds of winning the ball. Their non-penalty xG per shot was the best in the league (0.110).
5. **Stars in the right roles.** Vardy (24 goals) and Mahrez (17) were 1st and 2nd in the league for goals plus assists. Mahrez and Drinkwater supplied 10 of Vardy's goals between them. Kanté made more tackles plus interceptions than any player in the league (274).
6. **The same XI every week.** Leicester used 23 players, the fewest in the league. They made 33 changes to the starting XI all season (Spurs, next fewest, made 56), and their best 11 played 86% of the minutes.

**Limitation:** xG treats every shot as independent and ignores game state. A team leading 1-0 that sits deep concedes many low-quality shots, and keeping them out is partly skill (blocks, goalkeeping) and partly luck. The data alone cannot separate the two, and goalkeeper-specific models (post-shot xG) aren't in this dataset.
""")

nb = nbf.v4.new_notebook(cells=cells, metadata={"kernelspec": {"name": "python3", "display_name": "Python 3"}})
nbf.write(nb, "notebooks/02_leicester_title.ipynb")
print("written")
