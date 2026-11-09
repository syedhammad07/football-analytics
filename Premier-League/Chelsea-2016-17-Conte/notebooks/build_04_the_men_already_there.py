"""Builds notebooks/04_the_men_already_there.ipynb. Run from the project folder: python notebooks/build_04_the_men_already_there.py"""
from pathlib import Path
import sys

import nbformat as nbf

sys.path.insert(0, str(Path(__file__).parent))
from setup_cell import SETUP

cells = []
md = lambda s: cells.append(nbf.v4.new_markdown_cell(s.strip()))
code = lambda s: cells.append(nbf.v4.new_code_cell(s.strip()))

md("""
# The men who were already there

Nine players were at Chelsea for the 10th-place season and the title season. This notebook compares each one's
2015/16 and 2016/17, using official Premier League (Opta) player stats and Understat shot locations.

1. **Player cards.** Two numbers per player that show what changed in his game.
2. **Hazard and Costa shot maps.** Where the two main scorers shot from, in each season.
""")

code(SETUP)

code(r'''
import re

def parse_raw(path):
    """Read premierleague.com stat pages saved as 'key#label|value|label|value...' (English or German number format)."""
    rows = {}
    for line in open(path, encoding="utf-8"):
        key, body = line.strip().split("#", 1)
        parts = body.split("|")
        rec = {}
        for i in range(len(parts) - 1):
            lab, val = parts[i], parts[i + 1]
            if not re.match(r"^[\d.,]+( \(\d+%\))?$", val) or re.match(r"^[\d.,]+( \(\d+%\))?$", lab):
                continue
            num = val.split(" ")[0]
            num = num.replace(".", "").replace(",", "") if re.match(r"^\d{1,3}([.,]\d{3})+$", num) else num.replace(",", ".")
            rec.setdefault(lab, float(num))
            m = re.search(r"\((\d+)%\)", val)
            if m:
                rec.setdefault(lab + " %", float(m.group(1)))
        rows[key] = rec
    return pd.DataFrame(rows).T

P = parse_raw(EXT / "pl_player_raw.txt")
P = P.drop(index=["kante@2015", "kante@2016"])
P["Appearances"] = P.get("Appearances", np.nan).fillna(P.get("Appearances (Sub)"))
P[["Minutes Played", "Goals", "Assists", "XG", "XA", "Passes (Completed %)", "Total Tackles", "Clean Sheets"]].round(2)
''')

md("## 1. Player cards")

code(r'''
def p90(key, col):
    return P.loc[key, col] / P.loc[key, "Minutes Played"] * 90

def two(name, season):
    return f"{name}@{2015 if season == 15 else 2016}"

# (player, title, [(label, function returning the value for a season key, format)])
CARDS = [
    ("courtois", "Courtois · goalkeeper",
     [("Clean sheets", lambda k: P.loc[k, "Clean Sheets"], "{:.0f}"),
      ("Goals conceded per game", lambda k: P.loc[k, "Goals Conceded"] / P.loc[k, "Appearances"], "{:.2f}")]),
    ("azpilicueta", "Azpilicueta · full-back → right of a back three",
     [("Passes per 90", lambda k: p90(k, "Passes (Completed %)"), "{:.0f}"),
      ("Aerial duels won per 90", lambda k: p90(k, "Aerial Duels Won"), "{:.1f}")]),
    ("cahill", "Cahill · centre-back → left of a back three",
     [("Passes per 90", lambda k: p90(k, "Passes (Completed %)"), "{:.0f}"),
      ("Long-pass completion %", lambda k: P.loc[k, "Long Passes (Completed %) %"], "{:.0f}%")]),
    ("matic", "Matić · midfield two, beside Kanté",
     [("Assists", lambda k: P.loc[k, "Assists"], "{:.0f}"),
      ("Long passes per 90", lambda k: p90(k, "Long Passes (Completed %)"), "{:.1f}")]),
    ("fabregas", "Fàbregas · regular → super-sub",
     [("League minutes", lambda k: P.loc[k, "Minutes Played"], "{:,.0f}"),
      ("Assists per 90", lambda k: p90(k, "Assists"), "{:.2f}")]),
    ("pedro", "Pedro · right of the front three",
     [("Assists", lambda k: P.loc[k, "Assists"], "{:.0f}"),
      ("Tackles per 90", lambda k: p90(k, "Total Tackles"), "{:.1f}")]),
    ("willian", "Willian · starter → impact sub",
     [("Goals per 90", lambda k: p90(k, "Goals"), "{:.2f}"),
      ("Goals minus xG", lambda k: P.loc[k, "Goals"] - P.loc[k, "XG"], "{:+.1f}")]),
    ("hazard", "Hazard · left inside forward",
     [("Goals per 90", lambda k: p90(k, "Goals"), "{:.2f}"),
      ("Dribble success %", lambda k: P.loc[k, "Dribbles (Completed %) %"], "{:.0f}%")]),
    ("costa", "Costa · centre-forward",
     [("Goals", lambda k: P.loc[k, "Goals"], "{:.0f}"),
      ("Shots on target in the box", lambda k: P.loc[k, "Shots On Target Inside the Box"], "{:.0f}")]),
]

fig, axes = plt.subplots(3, 3, figsize=(14, 11))
fig.subplots_adjust(hspace=0.55, wspace=0.25, top=0.95, bottom=0.04, left=0.02, right=0.98)
for ax, (key, title, stats) in zip(axes.flat, CARDS):
    xs, labels = [], []
    for j, (lab, fn, fmt) in enumerate(stats):
        a, b = fn(f"{key}@2015"), fn(f"{key}@2016")
        top = max(a, b) * 1.25
        # each stat gets its own scale: normalise to its own max so both fit one panel
        x0 = j * 2.6
        ax.bar(x0, a / top, width=0.9, color=GREY)
        ax.bar(x0 + 1, b / top, width=0.9, color=BLUE)
        ax.text(x0, a / top + 0.02, fmt.format(a), ha="center", va="bottom", fontsize=10, color=MUTED)
        ax.text(x0 + 1, b / top + 0.02, fmt.format(b), ha="center", va="bottom", fontsize=10, color=BLUE, fontweight="bold")
        ax.text(x0 + 0.5, -0.1, lab, ha="center", va="top", fontsize=9, color=DARK)
    ax.set_xlim(-0.8, 4.4)
    ax.set_ylim(0, 1.05)
    ax.axis("off")
    ax.axhline(0, color=GREY, lw=0.8)
    ax.set_title(title, fontsize=11, loc="left")
fig.text(0.98, 1.0, "■ 2015/16", ha="right", color=GREY, fontsize=10, fontweight="bold")
fig.text(0.91, 1.0, "■ 2016/17", ha="right", color=BLUE, fontsize=10, fontweight="bold")
titles(fig, "Nine players from the 10th-place squad, two numbers each: almost all of them went up a level",
       "Grey = 2015/16, blue = 2016/17. Each pair of bars has its own scale. Players ordered from goalkeeper to striker",
       SRC_PL)
fig.savefig(FIGS / "20_returning_player_cards.png")
''')

md("## 2. Hazard and Costa: where they shot from")

code(r'''
from mplsoccer import VerticalPitch

pitch = VerticalPitch(pitch_type="opta", half=True, pitch_color="white", line_color="#C9C7BF", linewidth=1)
fig, axes = pitch.draw(nrows=2, ncols=2, figsize=(11, 6.6))
fig.subplots_adjust(top=0.95, bottom=0.03, left=0.02, right=0.98, hspace=0.3, wspace=0.06)
for r, name in enumerate(["Eden Hazard", "Diego Costa"]):
    for c, season in enumerate(["15-16", "16-17"]):
        ax = axes[r, c]
        s = load_shots(season)
        d = s[(s.player == name) & (s.team == CHE) & (s.situation != "Penalty")]
        miss, goal = d[~d.goal], d[d.goal]
        pitch.scatter(miss.X * 100, miss.Y * 100, s=miss.xG * 900 + 20, ax=ax, facecolor="none", edgecolor=MUTED, lw=1, alpha=0.8)
        pitch.scatter(goal.X * 100, goal.Y * 100, s=goal.xG * 900 + 20, ax=ax, color=BLUE if season == "16-17" else GREY,
                      edgecolor="white", lw=0.6, zorder=3)
        box = (d.X >= 0.83) & (d.Y.between(0.21, 0.79))
        yr = "2015/16" if season == "15-16" else "2016/17"
        ax.set_title(f"{name.split()[-1]} {yr}", fontsize=12, fontweight="bold", loc="left", color=DARK)
        ax.set_ylim(63, 101)
        ax.text(0.5, -0.02, f"{len(d)} shots · {box.mean():.0%} inside the box · {d.xG.mean():.2f} xG per shot · {len(goal)} goals",
                ha="center", va="top", fontsize=9.5, color=DARK, transform=ax.transAxes)
titles(fig, "Hazard shot twice as often, from better positions; Costa shot 60% more often and scored 8 more",
       "Every non-penalty league shot. Filled = goal, hollow = no goal. Circle size = xG",
       SRC_U)
fig.savefig(FIGS / "21_hazard_costa_shot_maps.png")
''')

nb = nbf.v4.new_notebook(); nb["cells"] = cells
nb.metadata["kernelspec"] = {"name": "python3", "display_name": "Python 3", "language": "python"}
nbf.write(nb, Path(__file__).parent / "04_the_men_already_there.ipynb")
print("wrote 04_the_men_already_there.ipynb")
