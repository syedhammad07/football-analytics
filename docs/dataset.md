# Dataset documentation

## Source

- **Provider:** StatsBomb Open Data — https://github.com/statsbomb/open-data
- **Competition / season used:** _fill in (e.g. competition_id 9, season_id 281)_
- **Downloaded on:** _YYYY-MM-DD_
- **Access method:** `statsbombpy` (`python -m football_analytics.data`)

## Tables

| Table | Rows | Grain | Key columns |
| --- | --- | --- | --- |
| matches | | one row per match | match_id, home_team, away_team, match_date |
| events | | one row per on-ball event | id, match_id, type, player, team, location, shot_statsbomb_xg |

## Fields I use

| Field | Type | Meaning | Notes |
| --- | --- | --- | --- |
| `type` | string | Event type (Pass, Shot, Carry, ...) | |
| `shot_statsbomb_xg` | float | Expected goals for a shot | Only on Shot events |
| `location` | [x, y] | Pitch coordinates (120 × 80) | Split into x, y |
| `minute` | int | Match minute | |

## Cleaning log

| Date | Step | Rows before → after | Reason |
| --- | --- | --- | --- |
| | Drop events without a player | | Team-level events not needed |
| | Compute minutes played per player | | Needed for per-90 metrics |

## Known limitations

- Open data covers selected competitions only, so results may not generalise.
- _Add others as you find them._
