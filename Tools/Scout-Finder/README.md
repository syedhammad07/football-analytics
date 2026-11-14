# Scout Finder

**Find Premier League players who play like someone else, for less.**

Ask for "a cheaper Rodri under 25" and Scout Finder ranks every Premier League midfielder from 2025/26 by how closely his numbers match Rodri's, then shows his age, his Transfermarkt value and what the two have in common.

```
$ python -m scout_finder find "Rodri" --max-age 25 --max-value 40 --top 5

Players most like Rodri (Man City, midfielder, 30, €50m, 1,513 mins)
2025/26 Premier League · age ≤ 25, value ≤ €40m, midfielders only · 900+ minutes
Values: Transfermarkt, June 2026

    Player                   Club            Age   Value  Match
  1 Nico González            Man City         25    €40m    79%
      also strong at: Passes completed in the opposition half, Passes, Ball recoveries
      biggest difference: fewer through balls (-56 pts)
  2 Lewis Miley              Newcastle        20    €25m    72%
      also strong at: Duels won %, Aerial duels won %, Aerial duels won
      biggest difference: fewer fouls won (-84 pts)
  3 Andrey Santos            Chelsea          22    €40m    70%
      also strong at: Duels won %, Pass completion %, Tackles won
      biggest difference: fewer long passes completed (-80 pts)
  4 Freddie Potts            West Ham         23    €10m    70%
      also strong at: Duels won %, Aerial duels won %, Long passes completed
      biggest difference: fewer ball recoveries (-98 pts)
  5 Soungoutou Magassa       West Ham         23    €17m    67%
      also strong at: Duels won %, Tackles won, Fouls won
      biggest difference: lower pass completion % (-75 pts)

Best cheaper option: Lewis Miley (Newcastle),
a 72% match for €25m, €25m less than Rodri.
```

Built as a small Python package with a command-line interface and tests, not a notebook.

## What it does

- **`find`**: the players most like a given player, with filters for age, value, position and club.
- **`profile`**: one player's percentiles in 27 stats across scoring, creating, passing, carrying and defending.
- **`fetch`**: downloads fresh data and matches Transfermarkt values to players.

A few more searches:

| Search | Top answer |
| --- | --- |
| `find "Saka" --max-value 50 --other-clubs` | Kevin (Fulham), 80% match, €25m |
| `find "van Dijk" --max-age 26` | Jaydee Canvot (Crystal Palace), 81% match, €28m |
| `find "Palmer" --max-value 40 --other-clubs` | Harvey Barnes (Newcastle), 81% match, €32m |

## How it works

| Step | Detail |
| --- | --- |
| **Data** | Official Premier League stats (Opta) for every outfield player in 2025/26: 491 players across all 20 clubs, 45 season totals each, from the Premier League's stats API. Goalkeepers are left out. |
| **Values** | Transfermarkt market values from [dcaribou/transfermarkt-datasets](https://github.com/dcaribou/transfermarkt-datasets), current to June 2026, so prices are as of the summer 2026 transfer window. |
| **Matching** | Each Premier League player is found in the Transfermarkt data by date of birth plus name, never name alone. Most shared name words win, so twins with the same birthday (Jurriën and Quinten Timber) aren't swapped. Two careful fallbacks handle different spellings ("Yarmoliuk" / "Yarmolyuk") and birth dates a day apart. 490 of 491 players are matched; the one missing played 25 minutes. |
| **Per 90** | Totals become per-90-minute rates or success percentages. Success rates need a minimum number of attempts (15 dribbles, 30 duels, 15 aerial duels). |
| **Possession** | Players at teams with more of the ball make more passes and fewer tackles. On-ball volume is scaled by 50 ÷ team possession, defending by 50 ÷ opponents' possession, so a Man City midfielder (60% possession) and a West Ham one (43%) are compared fairly. |
| **Percentiles** | Every stat becomes a percentile (0 to 100) within the player's position, against players with 900+ minutes, so a defender's tackles are compared with other defenders'. |
| **Match %** | 100 minus the average gap between two players' percentiles across all 27 stats. It measures how alike two players' numbers are, which includes their level as well as their style. |

## Run it

Python 3.10+. Part of [football-analytics](../../README.md): run everything from this folder.

```bash
cd Tools/Scout-Finder
pip install -e ".[dev]"                      # install the package and pytest

python -m scout_finder profile "Rodri"
python -m scout_finder find "Rodri" --max-age 25 --max-value 40
python -m scout_finder find "Saka" --other-clubs --top 5
python -m scout_finder find "Gvardiol" --any-position      # compare with every outfield player

python -m pytest                              # 20 tests
```

Options for `find`: `--max-age`, `--max-value` (millions of euros), `--other-clubs`, `--any-position`, `--min-minutes` (default 900), `--top` (default 10).

To rebuild the data:

```bash
python -m scout_finder fetch --stats          # Premier League stats (a few minutes)
python -m scout_finder fetch --values         # Transfermarkt file (about 4 MB), then match it
```

## Project structure

```
scout-finder/
  src/scout_finder/
    config.py       the 27 stats, the minutes bar and file paths
    features.py     per-90 numbers, possession adjustment, percentiles by position
    similarity.py   finding a player by name, match %, shared strengths, biggest difference
    data.py         loading, Transfermarkt matching, downloads
    cli.py          the find / profile / fetch commands
  tests/            pytest tests for the maths, the matching and the search
  data/
    pl_players_2025-26.csv          Premier League stats
    pl_team_possession_2025-26.csv  team possession, for the adjustment
    pl_values_2025-26.csv           Transfermarkt value for each player
```

## Limitations

- Premier League only, 2025/26 only. Opta's advanced stats for other leagues were removed from FBref in January 2026, and Understat (attacking stats only) was offline when this was built.
- "Midfielder", "Defender" and "Forward" are the positions in the club's squad list, so wingers can be listed as midfielders or forwards. Use `--any-position` to look across them.
- Transfermarkt values are estimates, not fees, and they're from June 2026. Contracts, wages and fees aren't included.
- A match % describes the numbers, not the player: it can't see tactics, injuries, personality or how a player would fit a new team.
- Goals and assists are noisy over one season, so a big gap in them matters less than a big gap in, say, passes or tackles.

## Sources

- Premier League official stats (Opta), premierleague.com
- Transfermarkt values via [dcaribou/transfermarkt-datasets](https://github.com/dcaribou/transfermarkt-datasets)

Built by Syed Hammad Ovais · [LinkedIn](https://www.linkedin.com/in/syedhammadovais)
