# Findings log

Every verified finding from the project, numbered, with the chart or table that proves it and a confidence rating.
For the narrative version, read the [full report](REPORT.md).

| Section | Findings | Notebook |
| --- | --- | --- |
| [How Leicester won](#how-leicester-won-the-201516-premier-league) | 1–9 | 02 |
| [Leicester players vs the league](#leicester-players-vs-the-league) | 10–14 | 03 |
| [Signings, spending and 2014/15](#signings-spending-and-the-jump-from-201415) | 15–21 | 04 |
| [Returning players and signings](#returning-players-and-signings-player-by-player) | 22–29 | 05 |
| [Tactics: Pearson → Ranieri](#tactics-pearson-201415--ranieri-201516) | 30–33 | 06 |
| [League top-10 context](#league-top-10-context-for-every-headline-stat) | 34–38 | 07 |

**Confidence:** *High* = computed directly from the data in this repo; *Medium* = relies on an external or partial source.

## How Leicester won the 2015/16 Premier League

Notebook: [`notebooks/02_leicester_title.ipynb`](../notebooks/02_leicester_title.ipynb)

| # | Finding | Evidence | Confidence |
| --- | --- | --- | --- |
| 1 | Leicester's chances were worth **66 expected points (4th)**, but they took **81**. At +15, that's the biggest overperformance in the league. | Section 2 table; `reports/figures/01_points_vs_expected_points.png` | High: model is simple and transparent; exact xPts varies ±0.2 with the random seed |
| 2 | **Defence was the outlier.** They conceded 36 goals from 46.1 xG against, **10.1 fewer than expected**, the most in the league (next: Man United, 3.5). | Section 5 table | High |
| 3 | The defensive overperformance came **entirely after mid-season**. Matches 1–19: 25 conceded from 25.9 xG against. Matches 20–38: 11 conceded from 20.2, with 11 clean sheets. | Section 4, `halves` table | High |
| 4 | **Attack beat its xG in the first half of the season** (37 goals from 31.0 xG). Over the season, non-penalty finishing was on par (57 goals from 56.1 npxG). | Section 4 and 5 tables | High |
| 5 | They won **14 games by one goal** (Arsenal 7, Spurs 6) and lost only 3. They won the **most penalties in the league (13, 10 scored)**. | Section 2 tables | High |
| 6 | **Most direct attack in the league.** Their median shot came after 3 passes, 67% of shots came within 15 s of winning the ball, and possession was 3rd-lowest at 42.6%. Their non-penalty xG per shot was the best in the league (0.110). | Section 3 table; `03_possession_vs_directness.png` | High (possession is approximated by pass share) |
| 7 | **Vardy** (24 goals, 5 assists) and **Mahrez** (17 goals, 10 assists) were 1st and 2nd in the league for goals plus assists. Mahrez and Drinkwater each assisted 5 of Vardy's goals. | Section 6 tables | High (StatsBomb counts Mahrez 10 assists; official stats say 11) |
| 8 | **Kanté** made **274 tackles plus interceptions**, the most in the league (next: Idrissa Gueye, 233), at 7.8 per 90. | Section 6 table; `04_kante_ball_winning.png` | High |
| 9 | **Most stable squad.** Leicester used 23 players (fewest) and made 33 changes to the starting XI all season, against 56 for Spurs, the next fewest. Their best 11 played 86% of minutes. | Section 7 table; `05_squad_stability.png` | High |

## Leicester players vs the league

Notebook: [`notebooks/03_leicester_players.ipynb`](../notebooks/03_leicester_players.ipynb). Rankings use outfield players; per-90 rankings include only players with 900+ minutes.

| # | Finding | Evidence | Confidence |
| --- | --- | --- | --- |
| 10 | **Distance:** Leicester covered 110.4 km per 90, 6th of the 10 teams Sky listed and 6.8 km less than Bournemouth (117.2). They didn't outrun opponents. | `06_distance_covered.png`. Source: [Sky Sports / EA Sports PPI, 8 March 2016](https://www.skysports.com/football/news/10196163/tireless-tottenham-running-further-in-2016-than-any-other-premier-league-team) | Medium: external data, season to 8 March only, top-10 teams only |
| 11 | Leicester players ranked **1st in the league in 10 season-total metrics**. Vardy led xG, counter-attack goals and attacking-third pressures. Mahrez led completed dribbles. Kanté led tackles, tackles won, interceptions, tackles plus interceptions and ball recoveries. Fuchs led blocks. | Section 3 table; `07_leicester_league_leaders.png` | High |
| 12 | **Vardy:** 22.3 xG, the most in the league (Kane 21.6). He scored 19 non-penalty goals from 17.6 npxG, plus 5 of 6 penalties. His 0.157 xG per non-penalty shot compares with 0.111 for forwards overall. He made 271 attacking-third pressures, the most of any player. | Section 4; `08_vardy_shot_map.png` | High |
| 13 | **Mahrez:** 123 completed dribbles from 218 attempts (56%), the most in the league (Zaha 119). He was 2nd for non-penalty goals above xG (+5.5, behind Agüero) and 2nd for fouls won (92). | Section 5; `09_mahrez_dribbles.png` | High |
| 14 | **Team totals:** Leicester ranked 1st of 20 for xG (66.3), blocks (961), and tackles plus interceptions (1,364). | Section 6 table | High |

## Signings, spending and the jump from 2014/15

Notebook: [`notebooks/04_signings_and_progression.ipynb`](../notebooks/04_signings_and_progression.ipynb). Fees, spending and all 2014/15 figures are **external** (sources listed in the notebook).

| # | Finding | Evidence | Confidence |
| --- | --- | --- | --- |
| 15 | Leicester's gross summer 2015 spend was about **£27m, 12th of 20**. Man City spent £154m and finished 15 points behind. | `10_spend_vs_points.png`. Source: Sportskeeda | Medium: secondary source, some fees undisclosed |
| 16 | **Four signings became regulars** (Kanté, Huth, Fuchs, Okazaki) for about **£15.6m combined**. The other signings (İnler, Benalouane, Gray, Amartey, Dyer) played under 300 minutes each. | Section 2 table. Fees: Wikipedia | High |
| 17 | They were specialists in their position: Kanté 100th percentile of midfielders for tackles, interceptions and recoveries per 90; Fuchs 100th of defenders for blocks and 98th for chances created; Huth 97th for clearances (2nd-most in the league, 312); Okazaki 91st–92nd of forwards for pressing. | Section 2 percentile tables | High (percentiles depend on position grouping) |
| 18 | Against the summer's big-money buys: Okazaki (£7m) pressed at the 91st percentile vs Benteke (£32.5m) at the 6th; Kanté (£5.6m) beat Schneiderlin (£25m) on tackles, recoveries and pressures. The big-money players were better at scoring and passing. The 4 Leicester regulars made **579 tackles plus interceptions; the 9 top-10 summer deals (£308m) made 639**. | `11_signings_vs_big_money.png`; Section 2 comparison table | High for metrics; fees external |
| 19 | **2014/15 → 2015/16:** 14th → 1st, 41 → 81 points, 46 → 68 goals for, 55 → 36 against, 19 → 3 losses. | Section 3 table. 2014/15: Wikipedia | High |
| 20 | **Vardy 5 → 24 league goals** (0.15 → 0.67 per appearance); **Mahrez 4 → 17**. Ulloa, 2014/15's top scorer, went 11 → 6. | `12_goals_2014_15_vs_2015_16.png`. 2014/15: Wikipedia | High (goals and appearances only; no 2014/15 event data) |
| 21 | **The run started in spring 2015:** 7 wins in the last 9 matches of 2014/15 plus 2015/16 = 103 points from 47 matches (2.19 per match). | Section 3. Source: Wikipedia | High |

## Returning players and signings, player by player

Notebook: [`notebooks/05_returning_players_and_signings.ipynb`](../notebooks/05_returning_players_and_signings.ipynb). Season-on-season and Leicester-vs-Leicester comparisons use **Premier League official stats (Opta)** from premierleague.com (raw copy in `data/external/pl_raw.txt`); league percentiles use StatsBomb. The two are never mixed in one chart.

| # | Finding | Evidence | Confidence |
| --- | --- | --- | --- |
| 22 | **Vardy:** goals per 90 went from 0.20 to 0.69 and xG per 90 from 0.30 to 0.66. In 2014/15 he scored 5 from 7.6 xG; in 2015/16, 24 from 23.1. The jump came from better chances, not lucky finishing. His assists fell from 8 to 6. | `13_returning_players_per90_change.png`, `14_vardy_mahrez_2014_15_vs_2015_16.png` | High |
| 23 | **Mahrez:** goals per 90 went from 0.17 to 0.50 and assists from 0.13 to 0.32. He scored 17 from 12.7 xG (+4.3), after 4 from 5.0 the year before. | Same figures | High |
| 24 | **Bigger roles:** Albrighton (1,027 → 2,765 minutes), Drinkwater (1,488 → 3,038) and Simpson (1,253 → 2,613) roughly doubled their minutes. Drinkwater went from 0 to 7 assists and made the most passes in the squad. Ulloa lost his place (2,407 → 968 minutes) but produced more per 90 off the bench. | Part 1 tables | High |
| 25 | **Schmeichel:** 1.54 goals conceded per game in 2014/15 → 0.95 in 2015/16; clean sheets in 25% of games → 39%. | Part 1 table | High |
| 26 | **Kanté vs Cambiasso**, whom he replaced: tackles 5.2 vs 2.6 per 90 and interceptions 4.7 vs 2.5. He was 1st in the league for tackles, interceptions and ball recoveries (StatsBomb). | `15_signings_vs_leicester_teammates.png`, `16_signings_league_percentiles.png` | High |
| 27 | **Fuchs vs Schlupp:** more tackles (3.3 vs 2.8), interceptions (3.3 vs 2.1), passes and xA per 90; Schlupp won more duels. Fuchs led all defenders for blocks per 90 and was 98th percentile for chances created. | Same | High |
| 28 | **Okazaki vs Ulloa (2014/15):** Okazaki won fewer duels (6.6 vs 8.3 per 90) and made fewer tackles (1.6 vs 1.9), with similar xG. His value only shows in StatsBomb's pressing data: 91st–92nd percentile among forwards. | Same | Medium: no 2014/15 pressing data to compare |
| 29 | **Huth** was already at Leicester on loan from February 2015 and played 14 matches of the escape. In 2015/16 he won more aerial duels per 90 than Morgan (3.3 vs 2.5) and made the 2nd-most clearances in the league, with weak passing (2nd percentile for progressive passes). | Same | High |

## Tactics: Pearson 2014/15 → Ranieri 2015/16

Notebook: [`notebooks/06_tactics_pearson_to_ranieri.ipynb`](../notebooks/06_tactics_pearson_to_ranieri.ipynb). Write-up with sources: [`docs/tactics_pearson_to_ranieri.md`](tactics_pearson_to_ranieri.md).

| # | Finding | Evidence | Confidence |
| --- | --- | --- | --- |
| 30 | **Same passing volume, much more danger:** passes 13,343 → 13,370 and long passes 2,706 → 2,695, but xG 46.9 → 69.3 and penalties won 4 → 13. Crosses fell 15% and aerial duels won fell 20%. | `17_team_2014_15_vs_2015_16.png` (Opta) | High |
| 31 | 4-4-2 starting shape in 33 of 38 matches. Leicester were 3rd-lowest for possession, 4th-highest for long-pass share, joint-1st for counter-attack shots and 3rd for pressures per game, but mid-table for PPDA and defensive action height: a hard-working mid-block, not a high press. | `18_leicester_tactical_profile.png` | High (metric definitions in notebook) |
| 32 | Leicester conceded an average number of shots (13.6 per game, 9th-most) but low-quality ones (5th-lowest xG per shot). | Same | High |
| 33 | **Matches 20–38 vs 1–19:** PPDA 18.4 → 14.5, pressures per game 153 → 175, xG per shot conceded 0.104 → 0.076. The "pragmatic" turn was harder pressing, not a deeper line. | `19_mid_season_change.png` | High |

## League top-10 context for every headline stat

Notebook: [`notebooks/07_league_leaderboards.ipynb`](../notebooks/07_league_leaderboards.ipynb). Figures `20`–`23`. Pitch maps `04`, `08` and `09` now also show the league top 10 beside them.

| # | Finding | Evidence | Confidence |
| --- | --- | --- | --- |
| 34 | **Goals:** Kane 25; Agüero and Vardy joint-2nd on 24; Lukaku 18; Mahrez 5th on 17. **Goals + assists:** Vardy 1st (29), Mahrez 2nd (27), ahead of Kane and Agüero (26). | `20_leaderboards_attack.png` | High (StatsBomb assists can differ by 1–2 from official) |
| 35 | **Mahrez** was 1st for completed dribbles (123, Zaha 119), 2nd for fouls won (92, Zaha 102), 2nd for non-penalty goals above xG (+5.5, Agüero +6.2), 6th for assists and 9th for chances created. | `20_…`, `21_leaderboards_dribbling_pressing.png` | High |
| 36 | **Pressing volume:** Kanté (906) and Drinkwater (779) were 2nd and 3rd in the league for total pressures, behind Idrissa Gueye (1,001). Vardy led attacking-third pressures (271). | `21_…` | High |
| 37 | **Defending:** Kanté 1st for tackles, interceptions, tackles + interceptions and ball recoveries, and 2nd for blocks. Fuchs 1st for blocks and 6th for interceptions. Huth 2nd for clearances. Drinkwater 4th for ball recoveries and joint-8th for tackles. | `22_leaderboards_defending.png` | High |
| 38 | **Distance:** no Leicester player was in the league's top 10 for distance covered (EA Sports PPI after 25 rounds). Albrighton was their furthest runner, 19th on total distance. Kanté's numbers come from winning the ball, not from out-running people. | `23_distance_covered_players.png`. Source: [Sky Sports, 9 Feb 2016](https://www.skysports.com/football/news/11661/10161166/which-premier-league-players-have-run-the-furthest-this-season) | Medium: external, partial season |

## Limitations

- xG and expected points treat shots as independent and ignore game state. Part of the defensive "overperformance" is likely skill (blocks, positioning, Schmeichel) and part luck, and this data cannot separate them.
- No post-shot xG or tracking data, so goalkeeping, off-ball pressing and running distance can't be measured from StatsBomb data. Distance comes from a separate, partial source.
- Possession is approximated by each team's share of passes in a match.
- This covers one historical season (2015/16).

## What I learned

- _Write 2–3 lines in your own words: e.g. what surprised you, what you'd test next._
