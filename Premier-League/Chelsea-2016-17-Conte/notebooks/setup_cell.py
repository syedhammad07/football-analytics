"""The first code cell shared by every notebook in this project (imported by the build_*.py scripts)."""

SETUP = r'''
from pathlib import Path
import html
import sys

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path.cwd().parent if Path.cwd().name == "notebooks" else Path.cwd()  # project folder
REPO = next(p for p in [ROOT, *ROOT.parents] if (p / "src" / "football_analytics").exists())  # repo root
sys.path.insert(0, str(REPO / "src"))
from football_analytics.viz import leaderboard

U = REPO / "data" / "raw" / "understat"
EXT = ROOT / "data" / "external"
FIGS = ROOT / "reports" / "figures"
FIGS.mkdir(parents=True, exist_ok=True)
CHE = "Chelsea"
BLUE, GREY, DARK, MUTED, GOLD = "#1F5FAD", "#B4B2A9", "#3D3D3A", "#6B6A64", "#FDBE11"
GOLD_TEXT = "#9A7200"  # darker gold for text on white
SRC_U = "Data: Understat (via douglasbc/scraping-understat-dataset)"
SRC_PL = "Data: Premier League official stats (Opta), premierleague.com"
plt.rcParams.update({
    "figure.dpi": 110, "savefig.dpi": 200, "savefig.bbox": "tight", "font.size": 10,
    "axes.titlesize": 13, "axes.titleweight": "bold", "axes.titlelocation": "left",
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.edgecolor": GREY, "axes.labelcolor": DARK, "xtick.color": DARK, "ytick.color": DARK,
    "axes.grid": True, "grid.color": "#ECEAE4", "grid.linewidth": 0.8, "axes.axisbelow": True,
})


def titles(fig, title, subtitle, source):
    """Title above the axes (va=bottom) and subtitle just under it (va=top) so they never overlap."""
    fig.suptitle(title, x=0.01, y=1.06, ha="left", va="bottom", fontsize=14, fontweight="bold", color=DARK)
    fig.text(0.01, 1.055, subtitle, ha="left", va="top", fontsize=10, color=MUTED)
    fig.text(0.01, -0.04, source, ha="left", va="top", fontsize=8, color=MUTED)


def load_shots(season):
    d = pd.read_csv(U / f"shots_epl_{season}.csv")
    d["team"] = np.where(d.h_a == "h", d.h_team, d.a_team)
    d["opp"] = np.where(d.h_a == "h", d.a_team, d.h_team)
    d["goal"] = d.result == "Goal"
    d["date"] = pd.to_datetime(d.date)
    d["player"] = d.player.map(html.unescape)
    return d


def load_players(season):
    p = pd.read_csv(U / f"players_epl_{season}.csv")
    p["player_name"] = p.player_name.map(html.unescape)
    p["team"] = p.team_title.str.split(",").str[-1]  # players who moved mid-season: last club
    return p


def matches(shots):
    """One row per team per match: goals, xG for and against, points."""
    g = shots.groupby("match_id").agg(date=("date", "first"), h=("h_team", "first"), a=("a_team", "first"),
                                      hg=("h_goals", "first"), ag=("a_goals", "first"))
    xg = shots.groupby(["match_id", "team"]).xG.sum()
    rows = []
    for mid, r in g.iterrows():
        for team, opp, gf, ga in [(r.h, r.a, r.hg, r.ag), (r.a, r.h, r.ag, r.hg)]:
            rows.append(dict(match_id=mid, date=r.date, team=team, opp=opp, home=team == r.h, gf=gf, ga=ga,
                             xgf=xg.get((mid, team), 0.0), xga=xg.get((mid, opp), 0.0),
                             pts=3 if gf > ga else 1 if gf == ga else 0))
    m = pd.DataFrame(rows).sort_values(["team", "date"])
    m["n"] = m.groupby("team").cumcount() + 1
    return m


def expected_points(shots, sims=10_000, seed=42):
    """Replay every match `sims` times: each shot is a goal with probability = its xG."""
    rng = np.random.default_rng(seed)
    out = {}
    for mid, g in shots.groupby("match_id"):
        h, a = g.h_team.iloc[0], g.a_team.iloc[0]
        hx, ax = g[g.team == h].xG.values, g[g.team == a].xG.values
        sh = (rng.random((sims, len(hx))) < hx).sum(1)
        sa = (rng.random((sims, len(ax))) < ax).sum(1)
        out[(mid, h)] = (3 * (sh > sa) + (sh == sa)).mean()
        out[(mid, a)] = (3 * (sa > sh) + (sa == sh)).mean()
    return pd.Series(out, name="xpts")
'''
