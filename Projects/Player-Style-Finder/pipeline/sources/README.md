# Sources: Premier League season stats, 2014/15 to 2024/25

Used by `cross_season.py` for the "Find in" Premier League seasons. The 2025/26 and 2026/27 files come from
`Projects/Scout-Finder/data/` instead.

| File | What it holds |
| --- | --- |
| `pl_players_2014-2024.csv` | Every outfield player with minutes, 11 seasons (5,413 player-seasons): Premier League id, name, club, position, birth date and 20 season totals (minutes, goals, penalty goals, xG, shots, key passes, through balls, dribbles, touches, passes, forward and long passes, tackles, interceptions, recoveries, aerial duels won) |
| `pl_team_possession_2014-2024.csv` | Each club's average possession per season (220 club-seasons), for the possession-adjusted tackles and interceptions |

`season` is the starting year: 2014 means 2014/15.

**How it was collected (22 November 2026).** From the Premier League's own stats service (Opta data), the same
one `Projects/Midfield-Matchup/fetch_current_season.py` uses:

- `v1/competitions/8/seasons/{season}/teams` for the clubs
- `v2/competitions/8/seasons/{season}/teams/{team}/stats` for possession
- `v1/competitions/8/seasons/{season}/teams/{team}/squad` for the players
- `v2/competitions/8/seasons/{season}/players/{player}/stats` for each player's season totals

The service doesn't answer requests from servers (GitHub Actions or this project's cloud workspace), so it was read
from a normal browser, in three passes because it rate-limits. Every club-season and every player with minutes was
collected; the only requests that never succeeded were for players with no minutes.

**Check.** 2015/16 is in both this file and StatsBomb's event data. For the 289 Premier League outfield players with
900+ minutes found in both, the StatsBomb profile picks out the same player's Opta profile first 90.7% of the time
(see `check` in `../../data/now.json`).
