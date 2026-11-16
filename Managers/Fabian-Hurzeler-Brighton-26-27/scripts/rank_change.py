import pandas as pd, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

def team_table(s, yr):
    d = pd.read_csv(f'data/pl_players_{s}.csv')
    g = d.groupby('team').sum(numeric_only=True); n = g.timePlayed / 990
    p = pd.read_csv('data/pl_team_possession.csv'); p = p[p.season == yr].set_index('team').possession
    return pd.DataFrame({
        'poss': p, 'pass90': g.totalPasses / n,
        'fwd': g.forwardPasses / g.totalPasses,
        'opp': g.successfulPassesOppositionHalf / g.totalPasses,
        'shots': g.totalShots / n, 'xg': g.expectedGoals / n, 'xgs': g.expectedGoals / g.totalShots,
        'drib': g.successfulDribbles / n, 'tkl': g.totalTackles / n, 'rec': g.recoveries / n,
    }).dropna()

A, B = team_table('2025-26', 2025), team_table('2026-27', 2026)
rA, rB = A.rank(ascending=False).astype(int), B.rank(ascending=False).astype(int)
T = 'Brighton'

groups = [
 ("POSSESSION & BUILD-UP", [('poss', 'Possession', '{:.1f}%', ''),
      ('pass90', 'Passes per 90', '{:.0f}', ''),
      ('fwd', 'Forward passes', '{:.1%}', 'share of all passes'),
      ('opp', 'Passes completed in opposition half', '{:.1%}', 'share of all passes')]),
 ("ATTACK", [('shots', 'Shots per 90', '{:.1f}', ''),
      ('xg', 'Expected goals per 90', '{:.2f}', ''),
      ('xgs', 'Chance quality (xG per shot)', '{:.3f}', ''),
      ('drib', 'Successful dribbles per 90', '{:.1f}', '')]),
 ("WINNING THE BALL", [('tkl', 'Tackles per 90', '{:.1f}', 'raw counts, not adjusted for possession'),
      ('rec', 'Ball recoveries per 90', '{:.0f}', 'raw counts, not adjusted for possession')]),
]
BG, FG, MUTED, TRACK, BLUE = '#0A1628', '#EAF1FB', '#8FA3BF', '#1F3354', '#5AB0FF'
H = 12.6
fig = plt.figure(figsize=(8, H), dpi=200, facecolor=BG)
ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, 8); ax.set_ylim(0, H); ax.axis('off')
ordn = lambda n: f"{n}{'th' if 10 <= n % 100 <= 20 else {1:'st',2:'nd',3:'rd'}.get(n % 10,'th')}"

ax.text(0.45, H-0.62, "Hürzeler's Brighton: 2025/26 vs 2026/27", color=FG, fontsize=20, fontweight='bold', va='center')
ax.text(0.45, H-1.02, "More of the ball, far more shots", color=BLUE, fontsize=13.5, fontweight='bold', va='center')
ax.text(0.45, H-1.36, "Rank among the 20 Premier League teams in each season (right = highest value).",
        color=MUTED, fontsize=9, va='center')
# legend
ax.scatter([0.55], [H-1.78], s=70, facecolor='none', edgecolor=FG, lw=1.6)
ax.text(0.72, H-1.78, "2025/26, 38 games", color=FG, fontsize=8.8, va='center')
ax.scatter([2.75], [H-1.78], s=95, color=BLUE, edgecolor=BG, lw=1.2)
ax.text(2.92, H-1.78, "2026/27, first 9 to 10 games", color=FG, fontsize=8.8, va='center')

x0, x1 = 3.55, 6.45
pos = lambda rk: x0 + (20 - rk) / 19 * (x1 - x0)
y = H - 2.55
for gname, rows in groups:
    ax.text(0.45, y, gname, color=MUTED, fontsize=8.5, fontweight='bold', va='center')
    ax.plot([0.45, 7.55], [y-0.17, y-0.17], color='#1B2D4A', lw=0.8)
    y -= 0.58
    for key, label, fmt, note in rows:
        a_rk, b_rk = rA.loc[T, key], rB.loc[T, key]
        ax.text(0.45, y + (0.07 if note else 0), label, color=FG, fontsize=9.6, va='center')
        if note: ax.text(0.45, y - 0.17, note, color=MUTED, fontsize=7.4, va='center')
        ax.plot([x0, x1], [y, y], color=TRACK, lw=1.2, zorder=1)
        ax.scatter([pos(r) for r in range(1, 21)], [y] * 20, s=7, color=TRACK, zorder=1, lw=0)
        ax.plot([pos(10.5)] * 2, [y-0.12, y+0.12], color=MUTED, lw=1.1, zorder=2)
        if a_rk != b_rk:
            ax.annotate("", xy=(pos(b_rk), y), xytext=(pos(a_rk), y), zorder=3,
                        arrowprops=dict(arrowstyle="-|>", color=BLUE, lw=1.6, shrinkA=6, shrinkB=7, alpha=.9))
        ax.scatter([pos(a_rk)], [y], s=85, facecolor=BG, edgecolor=FG, lw=1.7, zorder=4)
        ax.scatter([pos(b_rk)], [y], s=120, color=BLUE, edgecolor=BG, lw=1.3, zorder=5)
        ax.text(7.55, y + 0.07, f"{ordn(a_rk)} → {ordn(b_rk)}", color=BLUE, fontsize=9.6, fontweight='bold', va='center', ha='right')
        ax.text(7.55, y - 0.17, f"{fmt.format(A.loc[T, key])} → {fmt.format(B.loc[T, key])}",
                color=MUTED, fontsize=7.8, va='center', ha='right')
        y -= 0.62
    y -= 0.18

ax.text(0.45, 1.18, "Tick = league middle. Dribbles, tackles and recoveries fall partly because Brighton have the ball more, so read them with care.",
        color=MUTED, fontsize=7.2, va='center')
ax.text(0.45, 0.88, "This season is a short run of games, so ranks can swing. Each rank compares Brighton with the other teams in that same season.",
        color=MUTED, fontsize=7.2, va='center')
ax.text(0.45, 0.58, "Data: Premier League official stats (Opta), summed per team; possession from the Premier League site.",
        color=MUTED, fontsize=7.2, va='center')
ax.text(0.45, 0.32, "Built with Scout Finder.", color=MUTED, fontsize=7.2, va='center')
out = f'assets/brighton_2025-26_vs_2026-27.png'
fig.savefig(out, facecolor=BG); print(out)
print(pd.DataFrame({'A':A.loc[T],'rA':rA.loc[T],'B':B.loc[T],'rB':rB.loc[T]}).round(3).to_string())
