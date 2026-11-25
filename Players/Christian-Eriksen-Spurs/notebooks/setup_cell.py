"""The first code cell shared by every notebook in this project (imported by the build_*.py scripts)."""

SETUP = r'''
import os
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib import font_manager

ROOT = Path.cwd().parent if Path.cwd().name == "notebooks" else Path.cwd()  # project folder
EXT = ROOT / "data" / "external"
DARK_THEME = os.environ.get("REPORT_THEME") == "dark"  # dark = black-background charts for the PDF; the README uses the light ones
FIGS = ROOT / "reports" / ("figures_dark" if DARK_THEME else "figures")
FIGS.mkdir(parents=True, exist_ok=True)

# Spurs navy for Eriksen, a lighter navy for secondary series
SKY, NAVY, GREY, DARK, MUTED, LIGHT, GOLD = "#7A8BB8", "#132257", "#B4B2A9", "#2B2B2A", "#6B6A64", "#F4F2EE", "#C9A227"
BG, GRID, SPAN, HEAT, HEAT_HI = "white", "#ECEAE4", "#FBF3DC", [NAVY, SKY, "#E8F1FA", "#FFFFFF"], "white"
if DARK_THEME:  # Spurs navy page: Eriksen in white, others in muted navy
    SKY, NAVY, GREY, DARK, MUTED = "#8C9CC8", "#FFFFFF", "#4A5888", "#FFFFFF", "#B8C0D9"
    BG, GRID, SPAN, HEAT, HEAT_HI = "#132257", "#25356F", "#2A2F5A", ["#FFFFFF", "#8C9CC8", "#2A3B78", "#0D1840"], "#000000"
SRC_PL = "Data: Premier League official stats (Opta), premierleague.com. Midfielders as listed in each club's squad, 2010/11 to 2019/20"
for _f in (ROOT / "assets" / "fonts").glob("*.ttf"):  # Anton (headlines) and Lato (text), bundled with the project (SIL Open Font License)
    font_manager.fontManager.addfont(str(_f))
plt.rcParams.update({
    "font.family": "Lato", "figure.dpi": 110, "savefig.dpi": 200, "savefig.bbox": "tight", "font.size": 10,
    "axes.spines.top": False, "axes.spines.right": False, "axes.edgecolor": GREY,
    "axes.labelcolor": DARK, "xtick.color": DARK, "ytick.color": DARK,
    "figure.facecolor": BG, "axes.facecolor": BG, "savefig.facecolor": BG, "text.color": DARK, "legend.labelcolor": DARK,
})


def fs(light, pdf):
    """Figure size: the README (light) size, or a narrower one for the PDF so the text prints larger on the page."""
    return pdf if DARK_THEME else light


def titles(fig, title, subtitle, source, y=1.06):
    fig.suptitle(title, x=0.01, y=y, ha="left", va="bottom", fontsize=18, color=DARK, family="Anton")
    fig.text(0.01, y - 0.005, subtitle, ha="left", va="top", fontsize=10.5, color=MUTED)
    fig.text(0.01, -0.03, source, ha="left", va="top", fontsize=8, color=MUTED)


def season_label(s):
    """2011 -> '2011/12'"""
    return f"{s}/{str(s + 1)[-2:]}"


def load_opta(min_minutes=0):
    """Every Premier League midfielder, 2010/11 to 2019/20 (official Opta stats). Season = starting year."""
    d = pd.concat([pd.read_csv(EXT / "pl_midfielders_2010-2018.csv"), pd.read_csv(EXT / "pl_midfielders_2018-2020.csv")])
    d = d.drop_duplicates(["season", "id"])
    d = d[d.timePlayed >= min_minutes].copy()
    p90 = lambda s: s / d.timePlayed * 90
    d["npg"] = d.goals - d.penaltyGoals
    d["scoring"] = p90(d.npg)                                   # non-penalty goals per 90
    d["assisting"] = p90(d.goalAssists)                         # assists per 90
    d["creating"] = p90(d.keyPassesAttemptAssists)              # chances created per 90
    d["passing"] = p90(d.successfulPassesOppositionHalf)        # completed passes in the opposition half per 90
    d["carrying"] = p90(d.successfulDribbles)                   # successful dribbles per 90
    d["defending"] = p90(d.tacklesWon + d.interceptions)        # tackles won + interceptions per 90
    d["through"] = p90(d.throughBalls)                          # through balls per 90
    d["box"] = p90(d.totalTouchesInOppositionBox)               # touches in the opposition box per 90
    d["dribbles"] = d.successfulDribbles + d.unsuccessfulDribbles
    d["dribble_pct"] = d.successfulDribbles / d.dribbles.where(d.dribbles > 0)
    return d


DIMS = ["scoring", "assisting", "creating", "passing", "carrying", "defending"]
DIM_LABELS = {"scoring": "Scoring\n(non-penalty goals)", "assisting": "Assisting\n(assists)", "creating": "Creating\n(chances created)",
              "passing": "Passing\n(passes in opp. half)", "carrying": "Carrying\n(successful dribbles)",
              "defending": "Defending\n(tackles won + interceptions)"}
ERIKSEN, SILVA = "Christian Eriksen", "David Silva"
SPURS = range(2013, 2019)   # his six full Spurs seasons, 2013/14 to 2018/19 (he left in January 2020)
FINISH = {2013: "6th", 2014: "5th", 2015: "3rd", 2016: "2nd", 2017: "3rd", 2018: "4th", 2019: "6th"}  # Spurs league finish
'''
