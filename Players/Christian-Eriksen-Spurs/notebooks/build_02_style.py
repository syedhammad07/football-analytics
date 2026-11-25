"""Builds notebooks/02_style.ipynb. Run from the project folder: python notebooks/build_02_style.py"""
from pathlib import Path
import sys

import nbformat as nbf

sys.path.insert(0, str(Path(__file__).parent))
from setup_cell import SETUP

cells = []
md = lambda s: cells.append(nbf.v4.new_markdown_cell(s.strip()))
code = lambda s: cells.append(nbf.v4.new_code_cell(s.strip()))

md("""
# Christian Eriksen: beyond goals and assists

Expected goals and assists, shooting, ball security and a full percentile profile, for every Premier League
midfielder with 6,000+ minutes over Eriksen's six full Spurs seasons (2013/14 to 2018/19). Opta's expected goals (xG)
and expected assists (xA) as published by the Premier League's stats API.

Charts 5, 6, 8 and 9 of the report.
""")

code(SETUP)

code(r'''
D = load_opta()
E = D[(D.name == ERIKSEN) & D.season.isin(SPURS)].sort_values("season")
W = D[D.season.isin(SPURS)]
T = W.groupby("name").agg(g=("goals", "sum"), pen=("penaltyGoals", "sum"), xg=("expectedGoals", "sum"), a=("goalAssists", "sum"),
                          xa=("expectedAssists", "sum"), sh=("totalShots", "sum"), m=("timePlayed", "sum"),
                          loss=("totalLossesOfPossession", "sum"), cc=("keyPassesAttemptAssists", "sum"), thr=("throughBalls", "sum"),
                          pas=("totalPasses", "sum"), unp=("totalUnsuccessfulPassesExclCrossesAndCorners", "sum"),
                          lp=("successfulLongPasses", "sum"), opp=("successfulPassesOppositionHalf", "sum"),
                          drb=("successfulDribbles", "sum"), rec=("recoveries", "sum"), tk=("tacklesWon", "sum"), it=("interceptions", "sum"))
T = T[T.m >= 6000].copy()
p90 = lambda c: T[c] / T.m * 90
T["npg90"] = (T.g - T.pen) / T.m * 90; T["sh90"] = p90("sh"); T["xgps"] = T.xg / T.sh; T["a90"] = p90("a"); T["xa90"] = p90("xa")
T["cc90"] = p90("cc"); T["thr90"] = p90("thr"); T["opp90"] = p90("opp"); T["lp90"] = p90("lp"); T["pct"] = 1 - T.unp / T.pas
T["drb90"] = p90("drb"); T["rec90"] = p90("rec"); T["def90"] = (T.tk + T.it) / T.m * 90; T["loss90"] = p90("loss")
T["over_g"] = T.g - T.xg; T["over_a"] = T.a - T.xa
for c in ["over_a", "over_g", "sh90", "loss90"]:
    print(c, T[c].sort_values(ascending=False).head(4).round(2).to_dict())
T.loc[[ERIKSEN, SILVA], ["g", "xg", "a", "xa", "sh", "sh90", "xgps", "loss90", "pct"]].round(3)
''')

md("## Charts")

code(r'''
# Figure 5: goals and assists against expected, season by season
fig, axes = plt.subplots(1, 2, figsize=fs((11, 4.6), (9.6, 4.4)), sharey=True)
y = np.arange(len(E))[::-1]
for ax, (act, exp, lab) in zip(axes, [("goals", "expectedGoals", "Goals vs expected goals (xG)"), ("goalAssists", "expectedAssists", "Assists vs expected assists (xA)")]):
    for yi, r in zip(y, E.itertuples()):
        a, x = getattr(r, act), getattr(r, exp)
        ax.plot([x, a], [yi, yi], color=SKY if a >= x else GREY, lw=3, zorder=1, solid_capstyle="round")
        ax.text(max(a, x) + 0.5, yi, f"{a - x:+.1f}", va="center", fontsize=9.5, color=NAVY if a >= x else MUTED, fontweight="bold")
    ax.scatter(E[exp], y, s=70, color=BG, edgecolors=MUTED, lw=1.6, zorder=2, label="Expected")
    ax.scatter(E[act], y, s=80, color=NAVY, zorder=3, label="Actual")
    tot_a, tot_x = E[act].sum(), E[exp].sum()
    ax.set_title(f"{lab}\nTotal {tot_a} vs {tot_x:.1f} ({tot_a - tot_x:+.1f})", loc="left", fontsize=10.5, color=DARK)
    ax.set_xlim(0, 18.5); ax.grid(axis="x", color=GRID, lw=0.7); ax.set_axisbelow(True)
axes[0].set_yticks(y, [season_label(s) for s in E.season]); axes[0].legend(frameon=False, loc="upper right")
r = T.loc[ERIKSEN]
titles(fig, f"Better than expected: {r.over_a:+.0f} assists above xA, the most of any midfielder",
       "Eriksen's goals and assists against Opta's expected goals and assists, Premier League, 2013/14 to 2018/19", SRC_PL + ". xG and xA: Opta", y=1.1)
fig.savefig(FIGS / "05_beating_expected.png")
''')

code(r'''
# Figure 6: the shooter
fig, ax = plt.subplots(figsize=fs((10.5, 6), (9, 5.8)))
o = T.drop([ERIKSEN]); ax.scatter(o.sh90, o.xgps, s=24, color=GREY, alpha=0.85, edgecolors="none")
ax.scatter(r.sh90, r.xgps, s=170, color=NAVY, edgecolors=BG, lw=1.5, zorder=3)
ax.annotate("Eriksen", (r.sh90, r.xgps), xytext=(10, 8), textcoords="offset points", color=NAVY, fontsize=12, fontweight="bold")
for n, (dx, dy) in {"David Silva": (8, 2), "Mesut Özil": (8, -4), "Philippe Coutinho": (-8, 8), "Paul Pogba": (-6, -14), "Eden Hazard": (8, -2),
                    "Kevin De Bruyne": (8, -10), "Dele Alli": (8, -2), "Yaya Touré": (8, -2)}.items():
    if n in T.index:
        ax.annotate(n, (T.loc[n].sh90, T.loc[n].xgps), xytext=(dx, dy), textcoords="offset points", fontsize=9, color=MUTED,
                    ha="right" if dx < 0 else "left")
ax.set_xlabel("Shots per 90"); ax.set_ylabel("Expected goals per shot (lower = from further out)")
ax.grid(color=GRID, lw=0.6); ax.set_axisbelow(True)
s = T.loc[SILVA]
titles(fig, "The shooter: half as many shots again as Silva, from further out, and more goals than expected",
       f"Midfielders with 6,000+ minutes, 2013/14 to 2018/19. Eriksen: {int(r.sh)} shots, {r.xgps:.2f} xG per shot, {int(r.g)} goals from {r.xg:.1f} xG. Silva: {int(s.sh)} shots, {s.xgps:.2f} xG per shot",
       SRC_PL + ". xG: Opta")
fig.savefig(FIGS / "06_shooting.png")
''')

code(r'''
# Figure 8: two pizzas, Eriksen and Silva (percentiles among midfielders with 6,000+ minutes)
MET = [("npg90", "Non-penalty\ngoals"), ("sh90", "Shots"), ("a90", "Assists"), ("xa90", "Expected\nassists"), ("cc90", "Chances\ncreated"),
       ("thr90", "Through\nballs"), ("opp90", "Passes in\nopp. half"), ("lp90", "Long\npasses"), ("pct", "Pass\naccuracy"),
       ("drb90", "Dribbles"), ("rec90", "Recoveries"), ("def90", "Tackles +\ninterceptions")]
PCT = T[[m for m, _ in MET]].rank(pct=True) * 100
GROUPS = [SKY] * 6 + [GOLD] * 3 + [MUTED if DARK_THEME else GREY] * 3        # attacking, passing, defending/carrying
fig, axes = plt.subplots(1, 2, figsize=(12, 6.2), subplot_kw={"projection": "polar"})
fig.subplots_adjust(wspace=0.45)
ang = np.linspace(0, 2 * np.pi, len(MET), endpoint=False); wdt = 2 * np.pi / len(MET) * 0.92
for ax, n in zip(axes, [ERIKSEN, SILVA]):
    v = PCT.loc[n].values
    ax.bar(ang, [100] * len(MET), width=wdt, color=GRID, edgecolor=BG, lw=1.5, zorder=1)
    ax.bar(ang, v, width=wdt, color=GROUPS, edgecolor=BG, lw=1.5, zorder=2)
    for a_, vi in zip(ang, v):   # value inside the end of long slices, just beyond the end of short ones
        inside = vi >= 45
        ax.text(a_, vi - 10 if inside else vi + 10, f"{vi:.0f}", ha="center", va="center", fontsize=9.5, fontweight="bold",
                color="#000000" if inside else DARK)
    ax.set_xticks(ang, [l for _, l in MET], fontsize=8.5, color=DARK); ax.tick_params(axis="x", pad=10)
    ax.set_yticks([]); ax.set_ylim(0, 100); ax.spines["polar"].set_visible(False); ax.grid(False)
    ax.set_theta_offset(np.pi / 2); ax.set_theta_direction(-1)
    ax.set_title(n, fontsize=15, family="Anton", color=DARK, pad=26)
fig.text(0.5, 0.02, "Blue = attacking   ·   Gold = passing   ·   Pale = carrying and defending", ha="center", fontsize=9.5, color=MUTED)
titles(fig, "Same engine, different style", "Per-90 percentiles among Premier League midfielders with 6,000+ minutes, 2013/14 to 2018/19 (100 = best)",
       SRC_PL + ". xA: Opta", y=1.02)
fig.savefig(FIGS / "08_pizzas.png")
''')

code(r'''
# Figure 9: risk and reward
fig, ax = plt.subplots(figsize=fs((10.5, 6), (9, 5.6)))
o = T.drop([ERIKSEN]); ax.scatter(o.loss90, o.cc90, s=24, color=GREY, alpha=0.85, edgecolors="none")
ax.scatter(r.loss90, r.cc90, s=170, color=NAVY, edgecolors=BG, lw=1.5, zorder=3)
ax.annotate("Eriksen", (r.loss90, r.cc90), xytext=(-8, 12), textcoords="offset points", ha="right", color=NAVY, fontsize=12, fontweight="bold")
for n, (dx, dy) in {"David Silva": (8, -4), "Mesut Özil": (8, 0), "Kevin De Bruyne": (8, -4), "Eden Hazard": (8, -4), "Cesc Fàbregas": (6, -14),
                    "Mousa Dembélé": (8, -4), "Dele Alli": (8, -4)}.items():
    if n in T.index:
        ax.annotate(n, (T.loc[n].loss90, T.loc[n].cc90), xytext=(dx, dy), textcoords="offset points", fontsize=9, color=MUTED)
ax.axvline(T.loss90.median(), color=GREY, lw=0.8, ls="--"); ax.axhline(T.cc90.median(), color=GREY, lw=0.8, ls="--")
ax.set_xlabel("Times losing the ball per 90 (passes, dribbles and touches that went wrong)"); ax.set_ylabel("Chances created per 90")
ax.grid(color=GRID, lw=0.6); ax.set_axisbelow(True)
rk = int(T.loss90.rank(ascending=False)[ERIKSEN])
titles(fig, "High risk, high reward: he gave the ball away a lot, and created even more",
       f"Midfielders with 6,000+ minutes, 2013/14 to 2018/19. Eriksen lost the ball {r.loss90:.1f} times per 90 ({rk}th most of {len(T)}); Silva {s.loss90:.1f}. Dashed = medians",
       SRC_PL)
fig.savefig(FIGS / "09_risk_and_reward.png")
''')

nb = nbf.v4.new_notebook(); nb["cells"] = cells
nb.metadata["kernelspec"] = {"name": "python3", "display_name": "Python 3", "language": "python"}
nbf.write(nb, Path(__file__).parent / "02_style.ipynb")
print("wrote 02_style.ipynb")
