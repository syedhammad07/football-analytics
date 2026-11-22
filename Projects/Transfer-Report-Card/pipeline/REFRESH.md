# Yearly refresh of the Transfer Report Card

Do this once a season ends (late May / June). The page then picks up the new season automatically: new signings
enter the list, and earlier signings gain another counted season.

## 1. Update the inputs
| Input | Where it comes from | What to add |
|---|---|---|
| Premier League player stats | Opta CSV per season (same format as 2019–2025 files) | the new season's file |
| Other four leagues, advanced stats | FBref via `worldfootballR_data` rds (`load_fb_advanced_season_stats`) | new season rows |
| Goalkeeper save data | SofaScore export (as used for 2024/25) | new season |
| Transfers and fees | Transfermarkt files (Kaggle dump) | new transfer window(s) |
| Premier League stats 2017/18 and 2018/19 | from FBref; no change | – |

## 2. Run
```
bash scripts/run_all.sh
```
The scripts were written with working paths under `/home/claude/work` and `/home/claude/trc`; set those
two folders to wherever you keep the data and the pipeline (search the scripts for `/home/claude`).

## 3. Change the season constants
- Last counted season: `seasons past 2025 not counted` appears in `build5b.py`; raise it by one.
- The footer line "Covers seasons through 2025/26" in `trc/template.html`.
- Re-run `scripts/backtest.py` and update `backtest/BACKTEST.md` (the headline correlation should stay near 0.50).

## 4. Check before publishing
- Page row count rose (about 600–700 new signings per year across the five leagues).
- Spot-check three well-known signings from the new window.
- Open both sections and all five tabs; no console errors.
- The Premier League site's 2009–2018 stats were removed from the project (its terms bar building a database from them without written approval). Do not add them back. Also check the terms of the source of the 2019+ Premier League Opta CSVs before publishing.
