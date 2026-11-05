"""Shared chart helpers."""
import numpy as np

BLUE, GREY, DARK = "#1F5FAD", "#C9C7BF", "#3D3D3A"
ABBR = {"AFC Bournemouth": "BOU", "Arsenal": "ARS", "Aston Villa": "AVL", "Chelsea": "CHE", "Crystal Palace": "CRY",
        "Everton": "EVE", "Leicester City": "LEI", "Liverpool": "LIV", "Manchester City": "MCI", "Manchester United": "MUN",
        "Newcastle United": "NEW", "Norwich City": "NOR", "Southampton": "SOU", "Stoke City": "STK", "Sunderland": "SUN",
        "Swansea City": "SWA", "Tottenham Hotspur": "TOT", "Watford": "WAT", "West Bromwich Albion": "WBA",
        "West Ham United": "WHU"}


def leaderboard(ax, values, names, teams, highlight_team="Leicester City", n=10, fmt="{:.0f}", title=None):
    """Horizontal top-n bar chart. values/names/teams are aligned pandas Series (same index).

    Players from `highlight_team` are blue. If none is in the top n, the best one is appended below a dashed line.
    """
    order = values.sort_values(ascending=False)
    rank = order.rank(ascending=False, method="min").astype(int)
    rows = list(order.index[:n])
    extra = None
    if not any(teams[i] == highlight_team for i in rows):
        extra = next(i for i in order.index if teams[i] == highlight_team)
        rows.append(extra)
    y = np.arange(len(rows))[::-1].astype(float)
    if extra is not None:
        y[-1] -= 0.6
    vals = order.loc[rows].values
    hi = [teams[i] == highlight_team for i in rows]
    ax.barh(y, vals, color=[BLUE if h else GREY for h in hi], height=0.72)
    vmax = order.iloc[0]
    for yi, v, h in zip(y, vals, hi):
        ax.text(v + vmax * 0.015, yi, fmt.format(v), va="center", fontsize=8.5,
                color=BLUE if h else DARK, fontweight="bold" if h else "normal")
    ax.set_yticks(y, [f"{rank[i]}. {names[i]} ({ABBR.get(teams[i], teams[i])})" for i in rows], fontsize=8.5)
    for t, h in zip(ax.get_yticklabels(), hi):
        if h:
            t.set_color(BLUE)
            t.set_fontweight("bold")
    if extra is not None:
        ax.axhline(y[-1] + 0.8, color=GREY, lw=0.8, ls="--")
    ax.set_xlim(0, vmax * 1.2)
    ax.set_xticks([])
    ax.grid(False)
    for s in ["top", "right", "left"]:
        ax.spines[s].set_visible(False)
    ax.tick_params(axis="y", length=0)
    if title:
        ax.set_title(title, loc="left", fontsize=10.5, fontweight="bold", pad=6)
