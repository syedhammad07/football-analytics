# Dataset documentation

## Source

- **Provider:** StatsBomb Open Data ([github.com/statsbomb/open-data](https://github.com/statsbomb/open-data)), free for non-commercial use with attribution
- **Competition / season:** Premier League 2015/16 (`competition_id = 2`, `season_id = 27`)
- **Coverage:** all 380 matches, 20 teams, 8 Aug 2015 – 17 May 2016
- **Downloaded on:** 2026-11-05
- **Access:** `python -m football_analytics.data 2 27`, then `python -m football_analytics.clean`

Why this season: see [0002-premier-league-2015-16.md](../Leicester-City-2015-16-Miracle/docs/decisions/0002-premier-league-2015-16.md).

## Raw tables (`data/raw/2_27/`, not committed)

| Table | Rows | Grain | Notes |
| --- | ---: | --- | --- |
| `matches.parquet` | 380 | one match | teams, score, date, referee, stadium |
| `lineups.parquet` | 12,717 | one player × one position spell | on/off clock times; unused subs excluded |
| `events.parquet` | 1,313,773 | one event | 46 of StatsBomb's 100+ event columns kept |

## Processed tables (`data/processed/2_27/`, not committed)

### `events.parquet` — 1,305,608 player actions

Match-admin events (Starting XI, Half Start/End, substitutions, tactical shifts, injury stoppages, referee drop-balls) and events without a player are removed.

| Field | Type | Meaning |
| --- | --- | --- |
| `match_id`, `period`, `minute`, `second` | int | When it happened. `clock` = minute + second / 60 |
| `type` | text | Pass, Carry, Ball Receipt*, Pressure, Shot, Duel, Dribble, … (33 types) |
| `team`, `player`, `player_id`, `position` | text / int | Who did it, and the position they were playing |
| `possession`, `possession_team`, `play_pattern` | | Possession sequence and how it started (Regular Play, From Corner, …) |
| `start_x`, `start_y` | float | Pitch location. StatsBomb pitch is 120 × 80, attacking left → right |
| `pass_end_x/y`, `carry_end_x/y`, `shot_end_x/y` | float | End location for passes, carries and shots |
| `under_pressure` | bool | An opponent was pressing the player |
| `pass_*` | | Outcome (empty = completed), length, type, cross, through ball, cut-back, switch, `pass_shot_assist`, `pass_goal_assist`, recipient |
| `shot_statsbomb_xg` | float | Expected goals of the shot (0–1) |
| `shot_outcome`, `shot_type`, `shot_body_part` | text | Goal / Saved / Off T / Blocked …; Open Play / Penalty / Free Kick; foot or head |
| `dribble_outcome`, `duel_type`, `duel_outcome`, `interception_outcome` | text | Defensive and 1v1 outcomes |
| `foul_committed_card`, `bad_behaviour_card` | text | Yellow Card / Second Yellow / Red Card |

### `player_match.parquet` — 10,469 rows (one player in one match)

| Field | Meaning |
| --- | --- |
| `match_id`, `team`, `player_id`, `player` | Keys |
| `minutes` | Minutes on the pitch (see method below) |
| `started` | On the pitch at kick-off |
| `sent_off` | Received a red card or second yellow |
| `position` | Position played for the most minutes in that match |

### `player_season.parquet` — 550 players

| Field | Meaning |
| --- | --- |
| `player_id`, `player`, `display_name` | `display_name` is the common name (e.g. "N'Golo Kanté") |
| `main_team`, `teams` | Team with the most minutes, and all teams (for mid-season transfers) |
| `main_position`, `position_group` | Detailed position with the most minutes, grouped into Goalkeeper / Defender / Midfielder / Forward |
| `country` | Nationality |
| `minutes`, `appearances`, `starts`, `red_cards` | Season totals |

Players by group: Defenders 178, Midfielders 176, Forwards 149, Goalkeepers 47.
With **900+ minutes** (the threshold for per-90 comparisons): 327 players, made up of 119 defenders, 102 midfielders, 79 forwards and 27 goalkeepers.

## How minutes are calculated

1. Each lineup spell has an on time and an off time on the match clock (`from`, `to`).
2. Spells still open at the final whistle end at the match's last event (average match length: **94.1 minutes**, including stoppage time).
3. StatsBomb's lineups keep sent-off players on until the final whistle, which happened in 58 of 59 red cards here. So a red card or second yellow ends the player's time at the moment of the card.
4. A player's match minutes are the sum of their spells; season minutes are the sum over matches.

## Cleaning log

| Date | Step | Rows before → after | Reason |
| --- | --- | --- | --- |
| 2026-11-05 | Keep 46 relevant event columns | 100+ → 46 columns | Smaller files; the rest are rarely used (e.g. goalkeeper detail, 360 freeze frames) |
| 2026-11-05 | Store mixed-type columns as text | — | Some columns mix numbers and text (e.g. `"4711, 3626"`), which parquet rejects |
| 2026-11-05 | Remove match-admin events and events without a player | 1,313,773 → 1,305,608 | Only player actions are analysed |
| 2026-11-05 | Split `[x, y]` lists into numeric columns | — | Easier filtering and plotting |
| 2026-11-05 | Normalise doubled apostrophes in names (`N''Golo` → `N'Golo`) | 555 → 550 players | Same player was split across two spellings |
| 2026-11-05 | Define "started" as on the pitch at 00:00 of the first half | — | One Swansea match labels its kick-off spells "Tactical Shift" instead of "Starting XI" |
| 2026-11-05 | End sent-off players' minutes at the card | 59 players-matches adjusted | Lineup data does not end their time |

## Validation checks

| Check | Result |
| --- | --- |
| Goals from shots + own goals = season total | 988 + 38 = 1,026, which matches the official 2015/16 Premier League total |
| Starters per team per match | 11 in all 760 team-matches |
| Team minutes ÷ match length | 10.97 on average, between 10.8 and 11.5 without red cards, as low as 9.6 with them |
| Spot checks against public season stats | Kane 38 appearances, Mahrez 37, Vardy 36, Kanté 37, all consistent |

## Known limitations

- **One season, 2015/16.** Findings describe that season; players and tactics have changed since.
- **Minutes include stoppage time** (about 94 per full match), so per-90 numbers come out about 4% lower than sites that count 90 minutes per match. Comparisons within this dataset are unaffected.
- **xG is StatsBomb's model**, and other providers' xG values differ.
- **No tracking data**: only on-ball events, so off-ball movement and positioning are invisible.
