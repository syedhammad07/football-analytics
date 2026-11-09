"""Builds notebooks/03_managers_and_signings.ipynb. Run from the project folder: python notebooks/build_03_managers_and_signings.py"""
from pathlib import Path
import sys

import nbformat as nbf

sys.path.insert(0, str(Path(__file__).parent))
from setup_cell import SETUP

cells = []
md = lambda s: cells.append(nbf.v4.new_markdown_cell(s.strip()))
code = lambda s: cells.append(nbf.v4.new_code_cell(s.strip()))

md("""
# The managers before Conte, and the players he brought in

1. **Five spells, one club.** Mourinho's 2014/15 champions, Mourinho's 2015/16 collapse, Hiddink's interim spell,
   Conte's first six games with a back four, and Conte's 3-4-3. Per-match numbers from every shot (Understat).
2. **The signings before and after.** Each newcomer's 2015/16 season at his old club against his 2016/17 season at Chelsea, per 90 minutes.
3. **Newcomer vs predecessor.** Each newcomer against the Chelsea player who did that job in 2015/16.

Note on part 2: Alonso (Serie A) and Luiz (Ligue 1) played in different leagues the season before. Understat uses the same
xG model across leagues, but the opposition and the team around them were different, so read those rows as a change of
role, not a like-for-like test.
""")

code(SETUP)

code("""
def spell_rows(season, spells):
    s = load_shots(season)
    m = matches(s)
    m = m[m.team == CHE].copy()
    c = s[s.team == CHE]
    np_c = c[c.situation != "Penalty"]
    m["npg"] = m.match_id.map(np_c[np_c.goal].groupby("match_id").size()).fillna(0)
    m["npxg"] = m.match_id.map(np_c.groupby("match_id").xG.sum()).fillna(0)
    m["sf"] = m.match_id.map(c.groupby("match_id").size()).fillna(0)
    opp = s[(s.team != CHE) & ((s.h_team == CHE) | (s.a_team == CHE))]
    m["sa"] = m.match_id.map(opp.groupby("match_id").size()).fillna(0)
    out = []
    for name, lo, hi in spells:
        d = m[(m.n >= lo) & (m.n <= hi)]
        out.append(dict(spell=name, games=len(d), ppg=d.pts.mean(), gf=d.gf.mean(), ga=d.ga.mean(),
                        xgf=d.xgf.mean(), xga=d.xga.mean(), sf=d.sf.mean(), sa=d.sa.mean(),
                        fin=(d.npg - d.npxg).sum(), fin_pm=(d.npg - d.npxg).mean()))
    return out

rows = (spell_rows("14-15", [("Mourinho 2014/15\\n(champions)", 1, 38)])
        + spell_rows("15-16", [("Mourinho 2015/16\\n(games 1-16)", 1, 16), ("Hiddink 2015/16\\n(games 17-38)", 17, 38)])
        + spell_rows("16-17", [("Conte, back four\\n(games 1-6)", 1, 6), ("Conte, 3-4-3\\n(games 7-38)", 7, 38)]))
SP = pd.DataFrame(rows)
SP.round(2)
""")

md("## 1. Five spells, one club")

code("""
panels = [("ppg", "Points per game", "{:.2f}"), ("xgf", "xG created per game", "{:.2f}"),
          ("xga", "xG conceded per game", "{:.2f}"), ("sa", "Shots conceded per game", "{:.1f}"),
          ("fin_pm", "Finishing: non-penalty goals\\nminus xG, per game", "{:+.2f}")]
fig, axes = plt.subplots(1, 5, figsize=(16, 4.8), sharey=True)
y = np.arange(len(SP))[::-1]
cols = [GREY, GREY, GREY, GREY, BLUE]
for ax, (col, lab, fmt) in zip(axes, panels):
    v = SP[col].values
    ax.barh(y, v, color=cols, height=0.62)
    span = max(abs(v).max(), 1e-9)
    for yi, vi in zip(y, v):
        ax.text(vi + (0.03 * span if vi >= 0 else -0.03 * span), yi, fmt.format(vi), va="center",
                ha="left" if vi >= 0 else "right", fontsize=9, color=DARK)
    ax.set_title(lab, fontsize=10.5)
    ax.grid(axis="y", visible=False)
    ax.set_xticks([])
    ax.spines["bottom"].set_visible(False)
    if col == "fin_pm":
        ax.axvline(0, color=DARK, lw=0.8)
        ax.set_xlim(-0.55, 1.0)
    else:
        ax.set_xlim(0, v.max() * 1.3)
axes[0].set_yticks(y)
axes[0].set_yticklabels(SP.spell)
axes[0].tick_params(axis="y", length=0)
fig.subplots_adjust(wspace=0.12)
titles(fig, "Conte's 3-4-3 conceded less than any Chelsea side of the three seasons, even Mourinho's champions",
       "Chelsea per league game in five spells, 2014/15 to 2016/17. Conte's 3-4-3 in blue",
       SRC_U + ". Hiddink's spell includes the 19 Dec 2015 game, when Steve Holland was in charge")
fig.savefig(FIGS / "17_manager_spells.png")
""")

md("""
## 2. The signings, before and after

Per 90 minutes, 2015/16 at the old club vs 2016/17 at Chelsea. Batshuayi is left out of the chart: he played
221 league minutes for Chelsea, too few for per-90 numbers (he scored 5 goals in them).
""")

code("""
def load_other(league):
    p = pd.read_csv(U / "other" / f"players_{league}_15-16.csv")
    p["player_name"] = p.player_name.map(html.unescape)
    return p

prev = pd.concat([load_players("15-16"), load_other("serie_a"), load_other("ligue_1")])
now = load_players("16-17")
SIGN = [("N'Golo Kanté", "Leicester (PL)"), ("Marcos Alonso", "Fiorentina (Serie A)"),
        ("David Luiz", "PSG (Ligue 1)"), ("Victor Moses", "West Ham (PL)"), ("Michy Batshuayi", "Marseille (Ligue 1)")]
METRICS = [("xGChain", "xGChain\\n(involved in attacks)"), ("xGBuildup", "xGBuildup\\n(build-up, no shot or key pass)"),
           ("npxG_xA", "npxG + xA\\n(goal threat)"), ("key_passes", "Key passes")]

def per90(r):
    return {"xGChain": r.xGChain / r.time * 90, "xGBuildup": r.xGBuildup / r.time * 90,
            "npxG_xA": (r.npxG + r.xA) / r.time * 90, "key_passes": r.key_passes / r.time * 90}

tab = []
for name, club in SIGN:
    a = prev[prev.player_name == name].iloc[0]; b = now[now.player_name == name].iloc[0]
    tab.append(dict(player=name, old_club=club, old_min=a.time, che_min=b.time,
                    **{f"old_{k}": v for k, v in per90(a).items()}, **{f"che_{k}": v for k, v in per90(b).items()}))
SG = pd.DataFrame(tab)
SG.round(2)
""")

code("""
d = SG[SG.che_min >= 900].reset_index(drop=True)
fig, axes = plt.subplots(1, 4, figsize=(15, 4.6), sharey=True)
y = np.arange(len(d))[::-1]
for ax, (k, lab) in zip(axes, METRICS):
    o, c = d[f"old_{k}"].values, d[f"che_{k}"].values
    for yi, oi, ci in zip(y, o, c):
        ax.plot([oi, ci], [yi, yi], color=GREY, lw=2, zorder=1)
    ax.scatter(o, y, s=70, color="white", edgecolor=MUTED, lw=1.6, zorder=2, label="2015/16, old club")
    ax.scatter(c, y, s=70, color=BLUE, zorder=3, label="2016/17, Chelsea")
    for yi, oi, ci in zip(y, o, c):
        ax.text(ci, yi + 0.28, f"{ci:.2f}", ha="center", fontsize=8.5, color=BLUE)
    ax.set_title(lab, fontsize=10.5)
    ax.set_xlim(0, max(o.max(), c.max()) * 1.25)
    ax.grid(axis="y", visible=False)
    ax.set_ylim(-0.6, len(d) - 0.3)
axes[0].set_yticks(y)
axes[0].set_yticklabels([f"{r.player}\\n{r.old_club}" for r in d.itertuples()])
axes[0].tick_params(axis="y", length=0)
h, l = axes[0].get_legend_handles_labels()
fig.legend(h[:2], l[:2], loc="lower right", bbox_to_anchor=(0.99, 0.93), fontsize=9, frameon=False, ncol=2)
fig.subplots_adjust(wspace=0.1)
titles(fig, "Kanté and Alonso got more involved at Chelsea; Moses and Luiz did less on the ball in more defensive jobs",
       "Per 90 minutes: hollow = 2015/16 at the old club, blue = 2016/17 at Chelsea. Players with 900+ Chelsea minutes",
       SRC_U + ". Serie A and Ligue 1 numbers come from different leagues: read them as a change of role, not a like-for-like test")
fig.savefig(FIGS / "18_signings_before_after.png")
""")

md("""
## 3. Newcomer vs predecessor

Each newcomer in 2016/17 against the player (or players, weighted by minutes) who did that job for Chelsea in 2015/16.
""")

code("""
old = load_players("15-16"); old = old[old.team == CHE]

def group90(df):
    t = df[["time", "npxG", "xA", "key_passes", "xGChain", "xGBuildup"]].sum()
    return per90(t)

PAIRS = [("Right side", "Victor Moses", ["Branislav Ivanovic"], "Ivanović"),
         ("Left side", "Marcos Alonso", ["César Azpilicueta", "Abdul Rahman Baba"], "Azpilicueta + Baba Rahman"),
         ("Centre of defence", "David Luiz", ["John Terry"], "Terry"),
         ("Holding midfield", "N'Golo Kanté", ["Nemanja Matic", "John Obi Mikel"], "Matić + Mikel")]
pr = []
for role, new, olds, olabel in PAIRS:
    n = per90(now[now.player_name == new].iloc[0])
    o = group90(old[old.player_name.isin(olds)])
    pr.append(dict(role=role, new=new, old=olabel, **{f"new_{k}": v for k, v in n.items()}, **{f"old_{k}": v for k, v in o.items()}))
PR = pd.DataFrame(pr)
PR.round(2)
""")

code("""
fig, axes = plt.subplots(1, 4, figsize=(15, 4.6), sharey=True)
y = np.arange(len(PR))[::-1]
for ax, (k, lab) in zip(axes, METRICS):
    o, c = PR[f"old_{k}"].values, PR[f"new_{k}"].values
    ax.barh(y + 0.18, o, height=0.34, color=GREY, label="2015/16 predecessor")
    ax.barh(y - 0.18, c, height=0.34, color=BLUE, label="2016/17 newcomer")
    for yi, oi, ci in zip(y, o, c):
        ax.text(oi, yi + 0.18, f" {oi:.2f}", va="center", fontsize=8, color=MUTED)
        ax.text(ci, yi - 0.18, f" {ci:.2f}", va="center", fontsize=8, color=BLUE)
    ax.set_title(lab, fontsize=10.5)
    ax.set_xlim(0, max(o.max(), c.max()) * 1.3)
    ax.grid(axis="y", visible=False)
    ax.set_xticks([])
    ax.spines["bottom"].set_visible(False)
axes[0].set_yticks(y)
axes[0].set_yticklabels([f"{r.role}\\n{r.new} vs {r.old}" for r in PR.itertuples()])
axes[0].tick_params(axis="y", length=0)
h, l = axes[0].get_legend_handles_labels()
fig.legend(h[:2], l[:2], loc="lower right", bbox_to_anchor=(0.99, 0.93), fontsize=9, frameon=False, ncol=2)
fig.subplots_adjust(wspace=0.1)
titles(fig, "The new wing-backs carried 2-3 times the goal threat of the old full-backs; Kanté matched Matić and Mikel on the ball",
       "Per 90 minutes. Grey = who did the job in 2015/16 (minutes-weighted if two players), blue = the 2016/17 newcomer",
       SRC_U + ". Understat has no defensive data, so this measures what each player added on the ball only")
fig.savefig(FIGS / "19_newcomers_vs_predecessors.png")
""")

nb = nbf.v4.new_notebook(); nb["cells"] = cells
nb.metadata["kernelspec"] = {"name": "python3", "display_name": "Python 3", "language": "python"}
nbf.write(nb, Path(__file__).parent / "03_managers_and_signings.ipynb")
print("wrote 03_managers_and_signings.ipynb")
