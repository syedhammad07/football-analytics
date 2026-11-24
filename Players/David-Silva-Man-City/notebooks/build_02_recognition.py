"""Builds notebooks/02_recognition.ipynb. Run from the project folder: python notebooks/build_02_recognition.py"""
from pathlib import Path
import sys

import nbformat as nbf

sys.path.insert(0, str(Path(__file__).parent))
from setup_cell import SETUP

cells = []
md = lambda s: cells.append(nbf.v4.new_markdown_cell(s.strip()))
code = lambda s: cells.append(nbf.v4.new_code_cell(s.strip()))

md("""
# Was he recognised? The PFA Team of the Year model, and the all-time table

**The model** is the one from the Yaya Touré report, extended to ten seasons (2010/11 to 2019/20): a logistic
regression that predicts PFA Team of the Year selection from six per-90 numbers (as percentiles within each season)
plus minutes. Each season is predicted by a model trained on the other nine. Expected selections = the sum of a
player's predicted chances; compare with actual selections.

**The all-time table** compares Premier League career totals per appearance for the great midfielders, with Hall of
Fame status (Eden Hazard, inducted in 2025, added from his Premier League record: 245 games, 85 goals, 54 assists).

Charts 7 to 9 of the report.
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
M["prob"] = cross_val_predict(LogisticRegression(max_iter=2000), M[FEATS], M.toty, groups=M.season, cv=GroupKFold(10), method="predict_proba")[:, 1]
model = LogisticRegression(max_iter=2000).fit(M[FEATS], M.toty)
COEF = pd.Series(model.coef_[0], index=FEATS)
print(f"{len(M)} seasons, {M.toty.sum()} selections; held-out AUC {roc_auc_score(M.toty, M.prob):.2f}")
COEF.round(2)
''')

code(r'''
CAREER = M.groupby("name").agg(seasons=("season", "size"), expected=("prob", "sum"), actual=("toty", "sum"))
CAREER["gap"] = CAREER.actual - CAREER.expected
print(CAREER.loc[SILVA].round(2).to_dict())
CAREER[CAREER.seasons >= 3].sort_values("gap").head(6).round(2)
''')

code(r'''
M[M.name == SILVA][["season", "prob", "toty"] + FEATS].round(2)
''')

code(r'''
G = pd.read_csv(EXT / "pl_career_midfield_greats.csv")
G["a_pg"] = G.assists / G.appearances
G["ga_pg"] = (G.goals + G.assists) / G.appearances
G.sort_values("a_pg", ascending=False).round(2)
''')

md("## Charts")

code(r'''
# Figure 7: what the voters reward, with creating highlighted
lab = {"p_scoring": "Scoring", "p_assisting": "Assisting", "p_creating": "Creating chances", "p_passing": "Passing in the opposition half",
       "p_carrying": "Carrying (dribbles)", "p_defending": "Defending (tackles + interceptions)", "p_minutes": "Minutes played"}
c = COEF.sort_values()
fig, ax = plt.subplots(figsize=(9.5, 4.6))
ax.barh(range(len(c)), c.values, color=[GOLD if k == "p_creating" else NAVY if v >= 1 else GREY for k, v in c.items()], height=0.62)
for i, v in enumerate(c.values):
    ax.text(max(v, 0) + 0.04, i, f"{v:.2f}", va="center", fontsize=10, color=DARK)
ax.set_yticks(range(len(c)), [lab[k] for k in c.index], fontsize=10)
ax.set_xticks([]); ax.spines["bottom"].set_visible(False); ax.tick_params(axis="y", length=0); ax.set_xlim(0, c.max() * 1.18)
titles(fig, "Silva's best number, chances created, counts for almost nothing with the voters",
       "Weight of each number in a model of PFA Team of the Year midfielders, 2010/11 to 2019/20 (logistic regression on percentiles)",
       SRC_PL + ". Team of the Year: Wikipedia")
fig.savefig(FIGS / "07_what_voters_reward.png")
''')

code(r'''
# Figure 8: expected vs actual selections
sub = CAREER[CAREER.seasons >= 3]
show = pd.concat([sub.sort_values("gap").head(6), sub.sort_values("gap", ascending=False).head(5)]).drop_duplicates()
if SILVA not in show.index:
    show = pd.concat([show, sub.loc[[SILVA]]])
show = show.sort_values("gap")
fig, ax = plt.subplots(figsize=(10, 6))
yy = np.arange(len(show))
for yi, (n, r) in zip(yy, show.iterrows()):
    ax.plot([r.expected, r.actual], [yi, yi], color=GREY, lw=2.2, zorder=1)
ax.scatter(show.expected, yy, s=80, color=BG, edgecolors=MUTED, lw=1.8, zorder=2, label="Expected selections (from his numbers)")
ax.scatter(show.actual, yy, s=80, color=[NAVY if n == SILVA else SKY for n in show.index], zorder=3, label="Actual selections")
for yi, (n, r) in zip(yy, show.iterrows()):
    ax.text(max(r.expected, r.actual) + 0.12, yi, f"{r.gap:+.1f}", va="center", fontsize=9.5,
            color=NAVY if n == SILVA else DARK, fontweight="bold" if n == SILVA else "normal")
ax.set_yticks(yy, [f"{n} ({int(r.seasons)} seasons)" for n, r in show.iterrows()], fontsize=10)
ax.set_xlabel("PFA Team of the Year selections, 2010/11 to 2019/20"); ax.grid(axis="x", color=GRID); ax.set_axisbelow(True)
ax.tick_params(axis="y", length=0); ax.legend(frameon=False, loc="lower right")
ax.axhspan(-0.5, (show.gap < 0).sum() - 0.5, color=SPAN, zorder=0)
ax.text(ax.get_xlim()[1], (show.gap < 0).sum() - 0.7, "Under-rated: picked less than their numbers predict", ha="right", va="top", fontsize=9, color=GOLD, fontweight="bold")
r = CAREER.loc[SILVA]
titles(fig, f"The voters didn't miss him: picked {int(r.actual)} times when his numbers predicted {r.expected:.1f}",
       "Expected selections = sum of each season's predicted chance of being picked. Midfielders with 3+ seasons of 1,800+ minutes",
       SRC_PL + ". Team of the Year: Wikipedia")
fig.savefig(FIGS / "08_expected_vs_actual_selections.png")
''')

code(r'''
# Figure 9: against the all-time greats, per game
g = G.sort_values("a_pg")
fig, ax = plt.subplots(figsize=(10.5, 5.6))
y = np.arange(len(g))
ax.barh(y, g.a_pg, color=[NAVY if n == SILVA else SKY if h != "no" else GREY for n, h in zip(g.name, g.hall_of_fame)], height=0.62)
for yi, r in zip(y, g.itertuples()):
    hof = f"Hall of Fame {r.hall_of_fame}" if r.hall_of_fame != "no" else "not in the Hall of Fame"
    ax.text(r.a_pg + 0.006, yi, f"{r.a_pg:.2f}   ·   {r.assists} assists in {r.appearances} games · {r.pl_titles} titles · {hof}", va="center", fontsize=9,
            color=NAVY if r.name == SILVA else DARK, fontweight="bold" if r.name == SILVA else "normal")
ax.set_yticks(y, g.name, fontsize=10); ax.set_xticks([]); ax.spines["bottom"].set_visible(False); ax.tick_params(axis="y", length=0)
ax.set_xlim(0, g.a_pg.max() * 2.6)
titles(fig, "Assists per game: Silva is third among the great Premier League midfielders, and still outside the Hall of Fame",
       "Premier League career assists per appearance. Blue = in the Hall of Fame", SRC_PL.split(". Mid")[0] + ". Hall of Fame: premierleague.com")
fig.savefig(FIGS / "09_all_time_assists_per_game.png")
''')

nb = nbf.v4.new_notebook(); nb["cells"] = cells
nb.metadata["kernelspec"] = {"name": "python3", "display_name": "Python 3", "language": "python"}
nbf.write(nb, Path(__file__).parent / "02_recognition.ipynb")
print("wrote 02_recognition.ipynb")
