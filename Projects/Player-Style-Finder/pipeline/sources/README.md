# Sources: Premier League season stats, 2014/15 to 2024/25

`cross_season.py` uses two files for the "Find in" Premier League seasons. **They are not included in this repository**:
the Premier League's terms of use don't allow redistributing its statistics, so only the derived results (in
`../../data/`) are published.

| File (put it in this folder) | What it holds |
| --- | --- |
| `pl_players_2014-2024.csv` | One row per outfield player-season, 2014/15 to 2024/25: Premier League id, name, club, position, birth date and 20 season totals (minutes, goals, penalty goals, xG, shots, key passes, through balls, dribbles, touches, passes, forward and long passes, tackles, interceptions, recoveries, aerial duels won) |
| `pl_team_possession_2014-2024.csv` | Each club's average possession per season, for the possession-adjusted tackles and interceptions |

`season` is the starting year: 2014 means 2014/15. The 2025/26 and 2026/27 files come from `Projects/Scout-Finder/data/` instead.

To rebuild the "Find in" seasons you need to supply these two files yourself, from the Premier League's Opta statistics
and with whatever permission its terms require. The site (`../../index.html`) and its data files work without them.

**Check.** 2015/16 is in both these files and StatsBomb's event data. For the 289 Premier League outfield players with
900+ minutes found in both, the StatsBomb profile picks out the same player's Opta profile first 90.7% of the time
(see `check` in `../../data/now.json`).
