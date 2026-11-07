# 0002 — Analyse the Premier League 2015/16 season

- **Date:** 2026-11-05
- **Status:** Accepted

## Context

The project compares players per 90 minutes and looks for under-rated players. That needs a **full league season**: every team, every match, so each player's numbers are complete and comparable.

## Options considered

StatsBomb's open data (80 competition-seasons in November 2026) includes only a few full league seasons:

| Option | Matches | Verdict |
| --- | ---: | --- |
| Bundesliga 2023/24 | 34 | Only Bayer Leverkusen's matches, so not a full league |
| World Cup 2022 / Euro 2024 | 64 / 51 | Tournaments: at most 7 matches per player, too few minutes |
| La Liga 2015/16 | 380 | Full season, but the open La Liga data focuses on Messi's era |
| **Premier League 2015/16** | **380** | Full season with all 20 teams |

## Decision

Use **Premier League 2015/16**.

- It's complete: all 380 matches and 550 players, 327 of them with 900+ minutes.
- It's a strong story for a scouting project. Leicester won the league at 5000–1 odds, built on bargain signings such as N'Golo Kanté and Riyad Mahrez. "Could data have spotted them?" is exactly the question this project asks.
- It's widely known, so readers can sanity-check the results.

## Consequences

- The findings are historical (2015/16) and must be presented that way.
- The same pipeline works for other full seasons later (for example La Liga 2015/16) by changing the competition and season IDs.
