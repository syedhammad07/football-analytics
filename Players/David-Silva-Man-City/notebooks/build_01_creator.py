"""Builds notebooks/01_creator.ipynb. Run from the project folder: python notebooks/build_01_creator.py"""
from pathlib import Path
import sys

import nbformat as nbf

sys.path.insert(0, str(Path(__file__).parent))
from setup_cell import SETUP

cells = []
md = lambda s: cells.append(nbf.v4.new_markdown_cell(s.strip()))
code = lambda s: cells.append(nbf.v4.new_code_cell(s.strip()))

md("""
# David Silva: the creator, in numbers

Ten Premier League seasons at Manchester City (2010/11 to 2019/20), compared with every midfielder in the league over
the same decade. Official Opta season stats from the Premier League's stats API; "regular" = 1,800+ minutes in the
season (757 midfield seasons).

Charts 1 to 6 of the report: the career, the decade's assist leaders, his rank in every season, his best season as
percentiles, the rare creator-and-passer profile, and a test of how much of a dribbler he really was.
""")

code(SETUP)

code(r'''
D = load_opta()
S = D[D.name == SILVA].sort_values("season")
R = load_opta(min_minutes=1800)
print(f"{len(R)} regular midfield seasons; Silva: {S.appearances.sum()} games, {S.goals.sum()} goals, {S.goalAssists.sum()} assists")
S[["season", "appearances", "timePlayed", "goals", "goalAssists", "keyPassesAttemptAssists", "throughBalls", "successfulDribbles", "dribbles"]]
''')

code(r'''
# The decade's leaders, every Premier League midfielder 2010/11 to 2019/20
DEC = D.groupby("name").agg(assists=("goalAssists", "sum"), chances=("keyPassesAttemptAssists", "sum"),
                            through=("throughBalls", "sum"), minutes=("timePlayed", "sum"))
for c in ["assists", "chances", "through"]:
    print(c, DEC[c].sort_values(ascending=False).head(4).to_dict())
''')

code(r'''
# Rank in each season among regular midfielders (1 = best)
RANKS = {"creating": "Chances created", "through": "Through balls", "passing": "Passes in the opposition half",
         "assisting": "Assists", "box": "Touches in the opposition box", "carrying": "Successful dribbles"}
for c in RANKS:
    R["r_" + c] = R.groupby("season")[c].rank(ascending=False, method="min")
R["n"] = R.groupby("season").id.transform("size")
RS = R[R.name == SILVA].set_index("season")
RS[["n"] + ["r_" + c for c in RANKS]]
''')

code(r'''
# The rare profile: top 5 in the league in one season for BOTH chances created and passes in the opposition half (per 90)
R["top5_both"] = (R.r_creating <= 5) & (R.r_passing <= 5)
BOTH = R[R.top5_both]
print(len(BOTH), "of", len(R), "regular midfield seasons")
BOTH.groupby("name").size().sort_values(ascending=False)
''')

code(r'''
# Dribbling: volume and success, midfielders with 1,800+ minutes and 40+ attempted dribbles
DR = R[R.dribbles >= 40].copy()
DR["r_pct"] = DR.groupby("season").dribble_pct.rank(ascending=False, method="min")
DR["n_pct"] = DR.groupby("season").id.transform("size")
print("Silva, successful dribbles per 90 rank by season:", RS.r_carrying.astype(int).tolist(), "of", RS.n.tolist())
DR[DR.name == SILVA][["season", "dribbles", "dribble_pct", "r_pct", "n_pct"]].round(2)
''')

md("## Charts")

code(r'''
# Figure 1: ten seasons
fig, ax = plt.subplots(figsize=(11, 5))
x = np.arange(len(S)); w = 0.38
ax.bar(x - w / 2, S.goals, w, color=SKY, label="Goals")
ax.bar(x + w / 2, S.goalAssists, w, color=NAVY, label="Assists")
for xi, r in zip(x, S.itertuples()):
    ax.text(xi - w / 2, r.goals + 0.3, r.goals, ha="center", fontsize=9, color=DARK)
    ax.text(xi + w / 2, r.goalAssists + 0.3, r.goalAssists, ha="center", fontsize=9, color=NAVY, fontweight="bold")
    if r.season in TITLES:
        ax.text(xi, 17.3, "Champions", ha="center", fontsize=8.5, color=GOLD, fontweight="bold")
ax2 = ax.twinx(); ax2.plot(x, S.timePlayed, color=GREY, lw=2, marker="o", ms=4, label="Minutes"); ax2.set_ylim(0, 3200)
ax2.set_ylabel("Minutes played", color=MUTED); ax2.spines["right"].set_visible(True); ax2.tick_params(colors=MUTED)
ax.set_xticks(x, [season_label(s) for s in S.season]); ax.set_ylim(0, 18); ax.set_ylabel("Premier League goals / assists")
h1, l1 = ax.get_legend_handles_labels(); h2, l2 = ax2.get_legend_handles_labels()
ax.legend(h1 + h2, l1 + l2, frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.1), ncol=3)
titles(fig, "Ten seasons, four titles: 60 goals and 93 assists",
       "David Silva's Premier League seasons at Manchester City. Gold labels = title-winning seasons", SRC_PL)
fig.savefig(FIGS / "01_career_by_season.png")
''')

code(r'''
# Figure 2: the decade's assist leaders
top = DEC.sort_values("assists", ascending=False).head(10)[::-1]
fig, ax = plt.subplots(figsize=(10, 5.2))
ax.barh(range(len(top)), top.assists, color=[NAVY if n == SILVA else GREY for n in top.index], height=0.65)
for i, (n, r) in enumerate(top.iterrows()):
    ax.text(r.assists + 1, i, f"{r.assists}   ·   {r.chances} chances created", va="center", fontsize=9.5,
            color=NAVY if n == SILVA else DARK, fontweight="bold" if n == SILVA else "normal")
ax.set_yticks(range(len(top)), top.index, fontsize=10); ax.set_xticks([]); ax.spines["bottom"].set_visible(False)
ax.tick_params(axis="y", length=0); ax.set_xlim(0, top.assists.max() * 1.55)
gap = int(top.assists.iloc[-1] - top.assists.iloc[-2])
titles(fig, f"The decade's creator: 93 assists, {gap} more than any other Premier League midfielder",
       "Most Premier League assists by a midfielder, 2010/11 to 2019/20, with chances created (passes leading to a shot)", SRC_PL)
fig.savefig(FIGS / "02_decade_assists.png")
''')

code(r'''
# Figure 3: rank in every season
M = RS[["r_" + c for c in RANKS]].T
fig, ax = plt.subplots(figsize=(11.5, 4.4))
cmap = plt.matplotlib.colors.LinearSegmentedColormap.from_list("rk", HEAT)
ax.imshow(np.clip(M.values, 1, 40), cmap=cmap, vmin=1, vmax=40, aspect="auto")
for i in range(M.shape[0]):
    for j in range(M.shape[1]):
        v = int(M.values[i, j]); ax.text(j, i, v, ha="center", va="center", fontsize=10.5, fontweight="bold", color=HEAT_HI if v <= 6 else DARK)
ax.set_yticks(range(len(RANKS)), [RANKS[c[2:]] + " per 90" for c in M.index], fontsize=10)
ax.set_xticks(range(M.shape[1]), [f"{season_label(s)}\n(of {int(n)})" for s, n in zip(RS.index, RS.n)], fontsize=8.5)
ax.tick_params(length=0); [s.set_visible(False) for s in ax.spines.values()]
titles(fig, "Near the top of the league for creating, every season for ten years",
       f"David Silva's rank among Premier League midfielders with 1,800+ minutes in each season (1 = best; {'brighter' if DARK_THEME else 'darker'} = higher)", SRC_PL)
fig.savefig(FIGS / "03_rank_every_season.png")
''')

code(r'''
# Figure 4: the 2011/12 profile
best = R[R.season == 2011].copy()
for c in DIMS:
    best["p_" + c] = best[c].rank(pct=True) * 100
row = best[best.name == SILVA].iloc[0]
fig, ax = plt.subplots(figsize=(10, 4.6))
vals = [row["p_" + c] for c in DIMS]
ax.barh(range(len(DIMS)), vals, color=[NAVY if v >= 90 else SKY if v >= 60 else GREY for v in vals], height=0.6)
for i, v in enumerate(vals):
    ax.text(v + 1, i, f"{v:.0f}th", va="center", fontsize=10.5, color=DARK)
ax.set_yticks(range(len(DIMS)), [DIM_LABELS[c] for c in DIMS], fontsize=9.5); ax.invert_yaxis()
ax.set_xlim(0, 110); ax.set_xticks([0, 25, 50, 75, 100]); ax.axvline(50, color=GREY, lw=0.8, ls="--")
ax.set_xlabel("Percentile among Premier League midfielders with 1,800+ minutes, 2011/12")
titles(fig, f"2011/12: the league's best assister ({int(row.goalAssists)} assists), and a passer and creator at the very top",
       f"David Silva's numbers per 90 as a percentile of the {len(best)} regular midfielders that season. City won the title", SRC_PL)
fig.savefig(FIGS / "04_profile_2011_12.png")
''')

code(r'''
# Figure 5: creator and passer at once
fig, ax = plt.subplots(figsize=(10.5, 6.4))
ax.scatter(R.passing, R.creating, s=14, color=GREY, alpha=0.55, edgecolors="none", label="A midfield season (1,800+ min)")
o = BOTH[BOTH.name != SILVA]
ax.scatter(o.passing, o.creating, s=46, color=SKY, edgecolors=BG, lw=0.8, zorder=3, label="Top 5 that season for both")
s = BOTH[BOTH.name == SILVA]
ax.scatter(s.passing, s.creating, s=95, color=NAVY, edgecolors=BG, lw=1.2, zorder=4, label="David Silva, top 5 for both")
for k, r in enumerate(s.sort_values("creating").itertuples()):
    ax.annotate(season_label(r.season), (r.passing, r.creating), xytext=(-8 if k % 2 else 8, -3), ha="right" if k % 2 else "left", textcoords="offset points", fontsize=8.5, color=NAVY)
ax.annotate(f"Others: {', '.join(f'{n} ({k})' for n, k in o.name.value_counts().items())}", xy=(0.99, 0.02), xycoords="axes fraction", ha="right", fontsize=8.5, color=MUTED)
ax.set_xlabel("Completed passes in the opposition half per 90"); ax.set_ylabel("Chances created per 90")
ax.grid(color=GRID, lw=0.8); ax.set_axisbelow(True); ax.legend(frameon=False, loc="upper left")
n_s = len(s)
titles(fig, f"Only {len(BOTH)} midfield seasons in ten years were top 5 for both creating and passing. {n_s} were Silva's",
       f"Every Premier League midfield season with 1,800+ minutes, 2010/11 to 2019/20 ({len(R)} seasons). Next most: Özil, {int((o.name == 'Mesut Özil').sum())}", SRC_PL)
fig.savefig(FIGS / "05_creator_and_passer.png")
''')

code(r'''
# Figure 6: the dribbling test
fig, ax = plt.subplots(figsize=(10.5, 6.2))
ax.scatter(DR.carrying, DR.dribble_pct * 100, s=16, color=GREY, alpha=0.55, edgecolors="none")
s = DR[DR.name == SILVA]
ax.scatter(s.carrying, s.dribble_pct * 100, s=90, color=NAVY, edgecolors=BG, lw=1.2, zorder=3)
for k, r in enumerate(s.sort_values("dribble_pct").itertuples()):
    ax.annotate(season_label(r.season), (r.carrying, r.dribble_pct * 100), xytext=(-8 if k % 2 else 8, -3), ha="right" if k % 2 else "left", textcoords="offset points", fontsize=8.5, color=NAVY)
for r in DR.sort_values("carrying", ascending=False).head(5).itertuples():
    ax.annotate(f"{r.name} {season_label(r.season)[2:]}", (r.carrying, r.dribble_pct * 100), xytext=(-6, 6), textcoords="offset points", ha="right", fontsize=8, color=MUTED)
ax.axvline(DR.carrying.median(), color=GREY, lw=0.8, ls="--"); ax.axhline(DR.dribble_pct.median() * 100, color=GREY, lw=0.8, ls="--")
ax.set_xlabel("Successful dribbles (take-ons) per 90"); ax.set_ylabel("Dribble success %")
ax.grid(color=GRID, lw=0.8); ax.set_axisbelow(True)
titles(fig, "A reliable dribbler, not a prolific one: Silva rarely lost a take-on, but didn't attempt many",
       "Premier League midfielders with 1,800+ minutes and 40+ attempted dribbles, 2010/11 to 2019/20. Dashed lines = medians", SRC_PL)
fig.savefig(FIGS / "06_dribbling.png")
''')

nb = nbf.v4.new_notebook(); nb["cells"] = cells
nb.metadata["kernelspec"] = {"name": "python3", "display_name": "Python 3", "language": "python"}
nbf.write(nb, Path(__file__).parent / "01_creator.ipynb")
print("wrote 01_creator.ipynb")
