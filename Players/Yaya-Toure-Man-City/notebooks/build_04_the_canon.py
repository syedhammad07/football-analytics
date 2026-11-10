"""Builds notebooks/04_the_canon.ipynb. Run from the project folder: python notebooks/build_04_the_canon.py"""
from pathlib import Path
import sys

import nbformat as nbf

sys.path.insert(0, str(Path(__file__).parent))
from setup_cell import SETUP

cells = []
md = lambda s: cells.append(nbf.v4.new_markdown_cell(s.strip()))
code = lambda s: cells.append(nbf.v4.new_code_cell(s.strip()))

md("""
# Touré and the "greatest midfielders" conversation

Career Premier League totals (appearances, goals, assists) for the midfielders who usually make the all-time lists,
from the public stats API behind premierleague.com, saved in `data/external/pl_career_midfield_greats.csv` with each
player's league titles and Premier League Hall of Fame year (Wikipedia).

Roy Keane isn't included: the API has no career record for players who retired before 2010.

**Read with care.** Goals and assists per appearance favour attacking midfielders. They say nothing about what Vieira,
Carrick or Kanté were in the team to do, so this is a check on one claim (that Touré's output doesn't belong in the
conversation), not a ranking.
""")

code(SETUP)

code(r'''
G = pd.read_csv(EXT / "pl_career_midfield_greats.csv")
G["ga"] = G.goals + G.assists
G["ga_per_app"] = G.ga / G.appearances
G.sort_values("ga_per_app", ascending=False).round(2)
''')

code(r'''
# Figure 11: goal involvement per appearance, with titles and Hall of Fame status
g = G.sort_values("ga_per_app")
fig, ax = plt.subplots(figsize=(10, 5.6))
yy = np.arange(len(g))
hof = g.hall_of_fame != "no"
cols = [NAVY if n == YAYA else GOLD if h else GREY for n, h in zip(g.name, hof)]
ax.barh(yy, g.ga_per_app, color=cols, height=0.62)
for yi, r in zip(yy, g.itertuples()):
    ax.text(r.ga_per_app + 0.01, yi, f"{r.ga_per_app:.2f}   ({r.ga} in {r.appearances} games, {r.pl_titles} title{'s' if r.pl_titles != 1 else ''})",
            va="center", fontsize=9.5, color=NAVY if r.name == YAYA else DARK, fontweight="bold" if r.name == YAYA else "normal")
ax.set_yticks(yy, g.name, fontsize=10)
ax.set_xlim(0, g.ga_per_app.max() * 1.75); ax.set_xticks([]); ax.spines["bottom"].set_visible(False); ax.tick_params(axis="y", length=0)
from matplotlib.patches import Patch
ax.legend(handles=[Patch(color=GOLD, label="In the Premier League Hall of Fame"), Patch(color=GREY, label="Not in the Hall of Fame")], frameon=False, loc="lower right")
y = G[G.name == YAYA].iloc[0]
above = G[(G.hall_of_fame != "no") & (G.ga_per_app < y.ga_per_app)].name.str.split().str[-1].tolist()
titles(fig, f"Touré was involved in more goals per game than {' and '.join(above)}, who are both in the Hall of Fame",
       "Premier League goals + assists per appearance, whole Premier League career. Favours attacking midfielders: it can't measure what Vieira or Kanté did",
       "Data: Premier League official stats, premierleague.com. Hall of Fame: Wikipedia (inductees up to 2025). Retired players only are eligible")
fig.savefig(FIGS / "11_the_canon.png")
''')

nb = nbf.v4.new_notebook(); nb["cells"] = cells
nb.metadata["kernelspec"] = {"name": "python3", "display_name": "Python 3", "language": "python"}
nbf.write(nb, Path(__file__).parent / "04_the_canon.ipynb")
print("wrote 04_the_canon.ipynb")
