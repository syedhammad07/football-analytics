"""Builds notebooks/02_underrated_model.ipynb. Run from the project folder: python notebooks/build_02_underrated_model.py"""
from pathlib import Path
import sys

import nbformat as nbf

sys.path.insert(0, str(Path(__file__).parent))
from setup_cell import SETUP

cells = []
md = lambda s: cells.append(nbf.v4.new_markdown_cell(s.strip()))
code = lambda s: cells.append(nbf.v4.new_code_cell(s.strip()))

md("""
# Who gets under-rated? A simple model of the PFA Team of the Year

**The idea.** Every year, the players vote for a PFA Team of the Year. If we learn what the voters usually reward,
we can ask, for any midfielder's season: *how likely was a player with these numbers to be picked?*
Add those probabilities up over a career and you get **expected selections**. Compare them with the **actual**
selections:
- more actual than expected = recognised **more** than his numbers suggest;
- fewer actual than expected = **under-rated** by the voters' own standards.

**The model.** A logistic regression on the six per-90 dimensions from notebook 01 (as percentiles within each
season) plus minutes played. Each season's probabilities come from a model trained on the *other* seven seasons,
so no player is judged by a model that has already seen his own selection.

**Data.** Opta, 2010/11 to 2017/18, midfielders with 1,800+ minutes (617 seasons, 30 selections).
Checked against Understat (xG-based numbers), 2014/15 to 2020/21.
""")

code(SETUP)

code(r'''
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import GroupKFold, cross_val_predict

M = load_opta(min_minutes=1800)
for c in DIMS:
    M["p_" + c] = M.groupby("season")[c].rank(pct=True)
M["p_minutes"] = M.groupby("season").timePlayed.rank(pct=True)
T = pd.read_csv(EXT / "pfa_team_of_the_year.csv")
T["start"] = T.season.str[:4].astype(int)
picked = set(zip(T.start, T.player))
M["toty"] = [(s, n) in picked for s, n in zip(M.season, M.name)]
FEATS = ["p_" + c for c in DIMS] + ["p_minutes"]
model = LogisticRegression(max_iter=2000)
M["prob"] = cross_val_predict(model, M[FEATS], M.toty, groups=M.season, cv=GroupKFold(8), method="predict_proba")[:, 1]
model.fit(M[FEATS], M.toty)
COEF = pd.Series(model.coef_[0], index=FEATS)
print(f"{len(M)} seasons, {M.toty.sum()} selections; held-out AUC {roc_auc_score(M.toty, M.prob):.2f}")
COEF.round(2)
''')

code(r'''
CAREER = M.groupby("id").agg(name=("name", "last"), seasons=("season", "size"), expected=("prob", "sum"), actual=("toty", "sum"))
CAREER["gap"] = CAREER.actual - CAREER.expected
CAREER.sort_values("gap").head(10).round(2)
''')

code(r'''
CAREER.sort_values("gap", ascending=False).head(8).round(2)
''')

code(r'''
M[M.name == YAYA][["season", "prob", "toty"] + ["p_" + c for c in DIMS]].round(2)
''')

md("## Charts")

code(r'''
# Figure 6: what the voters reward
lab = {"p_scoring": "Scoring", "p_assisting": "Assisting", "p_creating": "Creating chances", "p_passing": "Passing in the opposition half",
       "p_carrying": "Carrying (dribbles)", "p_defending": "Defending (tackles + interceptions)", "p_minutes": "Minutes played"}
c = COEF.sort_values()
fig, ax = plt.subplots(figsize=(9.5, 4.6))
ax.barh(range(len(c)), c.values, color=[NAVY if v >= 1 else SKY if v >= 0.3 else GREY for v in c.values], height=0.62)
for i, v in enumerate(c.values):
    ax.text(v + 0.04, i, f"{v:.2f}", va="center", fontsize=10, color=DARK)
ax.set_yticks(range(len(c)), [lab[k] for k in c.index], fontsize=10)
ax.set_xticks([]); ax.spines["bottom"].set_visible(False); ax.tick_params(axis="y", length=0)
ax.set_xlim(0, c.max() * 1.18)
titles(fig, "What gets a midfielder into the PFA Team of the Year: playing, scoring, carrying, passing. Not defending",
       "Weight of each number in a model of who was picked, 2010/11 to 2017/18 (logistic regression on percentiles; bigger = matters more)",
       SRC_PL + ". Team of the Year: Wikipedia")
fig.savefig(FIGS / "06_what_voters_reward.png")
''')

code(r'''
# Figure 7: expected vs actual selections
sub = CAREER[CAREER.seasons >= 3]
show = pd.concat([sub.sort_values("gap").head(7), sub.sort_values("gap", ascending=False).head(5)]).drop_duplicates()
if YAYA not in show.name.values:
    show = pd.concat([show, sub[sub.name == YAYA]])
show = show.sort_values("gap")
fig, ax = plt.subplots(figsize=(10, 6))
yy = np.arange(len(show))
for yi, r in zip(yy, show.itertuples()):
    ax.plot([r.expected, r.actual], [yi, yi], color=GREY, lw=2.2, zorder=1)
ax.scatter(show.expected, yy, s=80, color="white", edgecolors=MUTED, lw=1.8, zorder=2, label="Expected selections (from his numbers)")
ax.scatter(show.actual, yy, s=80, color=[NAVY if n == YAYA else SKY for n in show.name], zorder=3, label="Actual selections")
for yi, r in zip(yy, show.itertuples()):
    ax.text(max(r.expected, r.actual) + 0.12, yi, f"{r.gap:+.1f}", va="center", fontsize=9.5,
            color=NAVY if r.name == YAYA else DARK, fontweight="bold" if r.name == YAYA else "normal")
ax.set_yticks(yy, [f"{r.name} ({r.seasons} seasons)" for r in show.itertuples()], fontsize=10)
ax.set_xlabel("PFA Team of the Year selections, 2010/11 to 2017/18"); ax.grid(axis="x", color="#ECEAE4"); ax.set_axisbelow(True)
ax.tick_params(axis="y", length=0); ax.legend(frameon=False, loc="lower right")
ax.axhspan(-0.5, (show.gap < 0).sum() - 0.5, color="#FBF3DC", zorder=0)
ax.text(ax.get_xlim()[1], (show.gap < 0).sum() - 0.7, "Under-rated: picked less than their numbers predict", ha="right", va="top", fontsize=9, color=GOLD, fontweight="bold")
titles(fig, "Özil and Cazorla were the under-rated ones. Yaya was picked more often than his numbers predict",
       "Expected selections = sum of each season's predicted chance of being picked. Midfielders with 3+ seasons of 1,800+ minutes",
       SRC_PL + ". Team of the Year: Wikipedia")
fig.savefig(FIGS / "07_expected_vs_actual_selections.png")
''')

code(r'''
# Figure 8: Understat check — the build-up work voters don't see (2014/15)
UP = pd.concat([pd.read_csv(U / f"players_epl_{y}-{y + 1}.csv").assign(start=2000 + y) for y in range(14, 21)])
UP["player_name"] = UP.player_name.map(html.unescape)
UM = UP[UP.position.str.contains("M") & (UP.time >= 1800)].copy()
for c in ["npxG", "xA", "xGBuildup", "npg", "assists"]:
    UM[c + "90"] = UM[c] / UM.time * 90
UM["ga90"] = UM.npg90 + UM.assists90
s14 = UM[UM.start == 2014]
fig, ax = plt.subplots(figsize=(10.5, 6.2))
ax.scatter(s14.xGBuildup90, s14.ga90, s=30, color=GREY, alpha=0.7, edgecolors="none")
yr = s14[s14.player_name == YAYA].iloc[0]
ax.scatter(yr.xGBuildup90, yr.ga90, s=120, color=NAVY, edgecolors="white", lw=1.2, zorder=3)
ax.annotate("Yaya Touré", (yr.xGBuildup90, yr.ga90), xytext=(-10, 10), textcoords="offset points", ha="right", fontsize=11, color=NAVY, fontweight="bold")
for r in s14.sort_values("ga90", ascending=False).head(4).itertuples():
    ax.annotate(r.player_name, (r.xGBuildup90, r.ga90), xytext=(6, 2), textcoords="offset points", fontsize=9, color=MUTED)
rank = int(s14.xGBuildup90.rank(ascending=False)[s14.player_name == YAYA].iloc[0])
ax.set_xlabel("xG build-up per 90: involvement in moves that ended in a shot, excluding the shot and the final pass")
ax.set_ylabel("Non-penalty goals + assists per 90"); ax.grid(color="#ECEAE4", lw=0.8); ax.set_axisbelow(True)
titles(fig, f"2014/15: no midfielder did more build-up work than Yaya Touré (rank {rank} of {len(s14)})",
       "Premier League midfielders with 1,800+ minutes, 2014/15. Build-up work is mostly invisible in goals and assists",
       SRC_U)
fig.savefig(FIGS / "08_buildup_2014_15.png")
''')

code(r'''
# The same model on Understat numbers, 2014/15 to 2020/21 (a check, not a chart)
UDIMS = ["npg90", "assists90", "npxG90", "xA90", "xGBuildup90"]
for c in UDIMS:
    UM["p_" + c] = UM.groupby("start")[c].rank(pct=True)
UM["p_min"] = UM.groupby("start").time.rank(pct=True)
alias = {"İlkay Gündoğan": "Ilkay Gündogan", "Thiago": "Thiago Alcántara"}
upicked = {(s, alias.get(n, n)) for s, n in picked}
UM["toty"] = [(s, n) in upicked for s, n in zip(UM.start, UM.player_name)]
UF = ["p_" + c for c in UDIMS] + ["p_min"]
UM["prob"] = cross_val_predict(LogisticRegression(max_iter=2000), UM[UF], UM.toty, groups=UM.start, cv=GroupKFold(7), method="predict_proba")[:, 1]
UC = UM.groupby("player_name").agg(seasons=("start", "size"), expected=("prob", "sum"), actual=("toty", "sum"))
UC["gap"] = UC.actual - UC.expected
print(f"Understat check: {len(UM)} seasons, {UM.toty.sum()} selections, held-out AUC {roc_auc_score(UM.toty, UM.prob):.2f}")
UC.sort_values("gap").head(8).round(2)
''')

nb = nbf.v4.new_notebook(); nb["cells"] = cells
nb.metadata["kernelspec"] = {"name": "python3", "display_name": "Python 3", "language": "python"}
nbf.write(nb, Path(__file__).parent / "02_underrated_model.ipynb")
print("wrote 02_underrated_model.ipynb")
