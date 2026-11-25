"""Builds notebooks/03_recognition.ipynb. Run from the project folder: python notebooks/build_03_recognition.py"""
from pathlib import Path
import sys

import nbformat as nbf

sys.path.insert(0, str(Path(__file__).parent))
from setup_cell import SETUP

cells = []
md = lambda s: cells.append(nbf.v4.new_markdown_cell(s.strip()))
code = lambda s: cells.append(nbf.v4.new_code_cell(s.strip()))

md("""
# Was he recognised? The PFA Team of the Year model

The same model as the David Silva and Yaya Touré reports: a logistic regression that predicts PFA Team of the Year
selection for midfielders from six per-90 numbers (as percentiles within each season) plus minutes, 2010/11 to
2019/20. Each season is predicted by a model trained on the other nine. Expected selections = the sum of a player's
predicted chances.

Charts 10 and 11 of the report: what the voters reward, and Eriksen's chance of selection each season next to the
midfielders who were picked.
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
print(CAREER.loc[ERIKSEN].round(2).to_dict())
M[M.name == ERIKSEN][["season", "prob", "toty"] + FEATS].round(2)
''')

code(r'''
# Each season: Eriksen's predicted chance, his rank in that season's prediction, and the midfielders who were picked
SEAS = []
for s in SPURS:
    m = M[M.season == s].sort_values("prob", ascending=False).reset_index(drop=True)
    e = m[m.name == ERIKSEN].iloc[0]
    SEAS.append({"season": s, "prob": e.prob, "rank": int(m.index[m.name == ERIKSEN][0]) + 1, "picked": e.toty,
                 "chosen": ", ".join(m[m.toty].name)})
SEAS = pd.DataFrame(SEAS); SEAS
''')

md("## Charts")

code(r'''
# Figure 10: what the voters reward
lab = {"p_scoring": "Scoring", "p_assisting": "Assisting", "p_creating": "Creating chances", "p_passing": "Passing in the opposition half",
       "p_carrying": "Carrying (dribbles)", "p_defending": "Defending (tackles + interceptions)", "p_minutes": "Minutes played"}
c = COEF.sort_values()
fig, ax = plt.subplots(figsize=(9.5, 4.6))
ax.barh(range(len(c)), c.values, color=[GOLD if k == "p_creating" else NAVY if v >= 1 else GREY for k, v in c.items()], height=0.62)
for i, v in enumerate(c.values):
    ax.text(max(v, 0) + 0.04, i, f"{v:.2f}", va="center", fontsize=10, color=DARK)
ax.set_yticks(range(len(c)), [lab[k] for k in c.index], fontsize=10)
ax.set_xticks([]); ax.spines["bottom"].set_visible(False); ax.tick_params(axis="y", length=0); ax.set_xlim(min(0, c.min()) - 0.1, c.max() * 1.18)
titles(fig, "Eriksen's best number, chances created, counts for almost nothing with the voters",
       "Weight of each number in a model of PFA Team of the Year midfielders, 2010/11 to 2019/20 (logistic regression on percentiles)",
       SRC_PL + ". Team of the Year: Wikipedia")
fig.savefig(FIGS / "10_what_voters_reward.png")
''')

code(r'''
# Figure 11: his chance each season, and who was picked
fig, ax = plt.subplots(figsize=fs((10.5, 5), (9.4, 4.8)))
x = np.arange(len(SEAS))
ax.bar(x, SEAS.prob * 100, color=[GOLD if p else NAVY for p in SEAS.picked], width=0.58)
for xi, r in zip(x, SEAS.itertuples()):
    ax.text(xi, r.prob * 100 + 1, f"{r.prob * 100:.0f}%\n({r.rank}{'st' if r.rank == 1 else 'nd' if r.rank == 2 else 'rd' if r.rank == 3 else 'th'} most likely)",
            ha="center", va="bottom", fontsize=9, color=DARK)
    ax.text(xi, -4, r.chosen.replace(", ", "\n"), ha="center", va="top", fontsize=7.8, color=GOLD if r.picked else MUTED)
ax.set_xticks(x, [season_label(s) for s in SEAS.season], fontsize=10); ax.tick_params(axis="x", pad=2, length=0)
ax.xaxis.set_ticks_position("top"); ax.spines["bottom"].set_visible(False); ax.spines["top"].set_visible(False)
ax.set_ylim(-17, 33); ax.set_yticks([0, 10, 20, 30]); ax.spines["left"].set_bounds(0, 30); ax.set_ylabel("Predicted chance of selection (%)")
ax.axhline(0, color=GREY, lw=0.8)
r = CAREER.loc[ERIKSEN]
titles(fig, f"Picked once in six seasons: about what the voters' formula gives a creator ({r.expected:.1f} expected)",
       "Eriksen's predicted chance of a PFA Team of the Year place each season (gold = picked). Below: the midfielders who were picked",
       SRC_PL + ". Team of the Year: Wikipedia")
fig.savefig(FIGS / "11_selection_by_season.png")
''')

nb = nbf.v4.new_notebook(); nb["cells"] = cells
nb.metadata["kernelspec"] = {"name": "python3", "display_name": "Python 3", "language": "python"}
nbf.write(nb, Path(__file__).parent / "03_recognition.ipynb")
print("wrote 03_recognition.ipynb")
