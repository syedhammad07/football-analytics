# From relegation candidates to champions: Pearson's 2014/15 and Ranieri's 2015/16

> Note on the premise: Claudio Ranieri did **not** manage Leicester in 2014/15. Nigel Pearson did, including the escape from relegation. Pearson was sacked at the end of June 2015 and Ranieri appointed in July. This document compares the two seasons and what Ranieri kept, changed and added.

Data checks are in [`notebooks/06_tactics_pearson_to_ranieri.ipynb`](../notebooks/06_tactics_pearson_to_ranieri.ipynb). Every tactical claim below is either cited to a published source or marked **[data]** when it comes from this repo.

---

## 1. Pearson's 2014/15: what Ranieri inherited

**Where they were.** Leicester were 20th from 29 November 2014 to 11 April 2015 ([Wikipedia](https://en.wikipedia.org/wiki/2014%E2%80%9315_Leicester_City_F.C._season)), with 19 points from 29 games on 3 April ([theScore](https://www.thescore.com/epl/news/1017760)).

**A side still searching for a shape.** Leicester used 11 different formations that season ([Premier League, PL30](https://www.premierleague.com/en/news/2748139)), including 4-4-2, 4-3-3 and 4-2-3-1 ([The Set Pieces](https://thesetpieces.com/?p=5394)). [Coaches' Voice](https://learning.coachesvoice.com/coach-watch-nigel-pearson/) explains why the 4-4-2 was struggling: opposing full-backs' diagonal passes kept breaking through the midfield, and the back four was exposed.

**The switch to three at the back.** In April 2015 Pearson moved to a 3-5-2 ([Sky Sports](https://www.skysports.com/amp/football/news/30385/10083402/claudio-ranieri-five-ways-hes-changed-things-at-leicester-city) dates it to the win over Swansea; [AP via Dawn](https://dawn.com/news/1256467) calls it a 3-4-1-2). According to [Coaches' Voice](https://learning.coachesvoice.com/coach-watch-nigel-pearson/):
- **Wing-backs** (Konchesky, Schlupp, Albrighton) gave width, crossed early and covered the spaces beside the two central midfielders.
- **Three aerially strong centre-backs** forced opponents to cross into a crowded box. Robert Huth, on loan from Stoke from 2 February 2015, was part of this.
- **Mahrez as a number 10**, running beyond the front two.
- **Ulloa as the aerial target, Vardy as the runner.** Vardy also played on the left in some April wins ([Sky Sports](https://www.skysports.com/amp/football/news/30385/10083402/claudio-ranieri-five-ways-hes-changed-things-at-leicester-city)).
- Esteban Cambiasso was the experienced holding midfielder and captain-figure ([theScore](https://www.thescore.com/epl/news/1017760)).

**The result:** 7 wins, 1 draw and 1 loss in the last 9 games (22 points), finishing 14th on 41 points.

**What Pearson left behind besides the results:**
- A sports-science and analysis department set up under him ([Computer Weekly](https://www.computerweekly.com/news/450296302/Foxy-Leicester-City-FC-won-Premiership-with-data-analytics)).
- Steve Walsh's recruitment, which brought in Vardy, Mahrez and Kanté ([The42](https://the42.ie/7-key-factors-inspired-leicesters-title-triumph-2748883-May2016)).
- A squad hardened by a relegation fight. The42 argues the 2015 run-in was more pressured than the 2016 title race.

---

## 2. What Ranieri changed

### 2.1 Back to a back four, and one system all season
- Ranieri dropped the back three in pre-season. His reasoning: against the many 4-3-3 sides, three centre-backs leave you "three against one" in the wide areas ([AP via Dawn](https://dawn.com/news/1256467)). He also said the team struggled against lower-division sides in friendlies, so he switched immediately ([Football Italia interview](https://www.football-italia.net/84100/ranieri-my-tactics-explained)).
- He used a 4-4-2 (a 4-4-1-1 without the ball) in 35 of 38 games ([Premier League, PL30](https://www.premierleague.com/en/news/2748139)).
  - **[data]** StatsBomb starting positions show a 4-4-2 in 33 of 38 matches, and a five-man midfield in the other 5.
- He made only 33 starting-XI changes all season ([PL30](https://www.premierleague.com/en/news/2748139)).
  - **[data]** That was the fewest in the league (notebook 02, `05_squad_stability.png`).

### 2.2 Vardy moved into the middle, with Okazaki beside him
- Under Pearson, Vardy sometimes played on the left. Ranieri made him the central striker, and he started every match ([Sky Sports](https://www.skysports.com/amp/football/news/30385/10083402/claudio-ranieri-five-ways-hes-changed-things-at-leicester-city)).
- Ranieri originally planned to build the attack around Ulloa, but Ulloa struggled with fitness. Ranieri paired Okazaki with Vardy instead and told them to attack like "jet fighters" ([Football Italia](https://www.football-italia.net/84100/ranieri-my-tactics-explained)).
- Okazaki played as a second striker who dropped deep, combined with Vardy and pressed hard ([Spielverlagerung](https://spielverlagerung.com/?p=3393)).
  - **[data]** He ranked 91st–92nd percentile among forwards for pressures (notebook 05).
- Crosses fell 15% and aerial duels won fell 20% from 2014/15 (Opta). Leicester stopped aiming for a target man and played to Vardy's pace on the ground.

### 2.3 Inverted wide players
- Mahrez (left-footed) moved to the right and Albrighton (right-footed) to the left, so both could cut inside ([AP via Dawn](https://dawn.com/news/1256467); [Sky Sports](https://www.skysports.com/amp/football/news/30385/10083402/claudio-ranieri-five-ways-hes-changed-things-at-leicester-city)).
- The two wide players had different jobs. Mahrez was the one-on-one threat, Albrighton the team-oriented player who supported the forwards ([Spielverlagerung](https://spielverlagerung.com/?p=3393)).
- In possession, the 4-4-2 often became something close to a 4-2-4 ([The Set Pieces](https://thesetpieces.com/?p=5394)).

### 2.4 Energy instead of a like-for-like Cambiasso replacement
- When Cambiasso left, Ranieri didn't sign another veteran playmaker. He used two energetic central midfielders: Kanté and Drinkwater ([Sky Sports](https://www.skysports.com/amp/football/news/30385/10083402/claudio-ranieri-five-ways-hes-changed-things-at-leicester-city)).
- Kanté was the defensive engine and Drinkwater the box-to-box link who passed forward ([Spielverlagerung](https://spielverlagerung.com/?p=3393)).
  - **[data]** Per 90 minutes, Kanté made twice as many tackles and interceptions as Cambiasso had in 2014/15 (notebook 05).
  - **[data]** Drinkwater made the most passes in the squad and had 7 assists, after 0 in 2014/15.

### 2.5 Defensive full-backs, a deep and central centre-back pair
- Fuchs and Simpson replaced Schlupp and De Laet ([Wikipedia, Christian Fuchs](https://en.wikipedia.org/wiki/Christian_Fuchs)).
- The full-backs stayed narrow and close to Huth and Morgan, who are strong in the air but slow. So the back four defended deep and central rather than being pulled wide ([Spielverlagerung](https://spielverlagerung.com/?p=3393)).

### 2.6 Out of possession: a compact zonal block, pressing to force play wide
[Spielverlagerung](https://spielverlagerung.com/?p=3393) gives the most detailed account, and compares the setup to Arrigo Sacchi's AC Milan:
- **The forwards:** the two strikers shuffle across to mark opponents within a zonal structure. Then they press from behind on a diagonal, cutting off passing lanes back into the middle.
- **The midfield:** only the ball-side winger steps out. The central midfielders follow opponents who drop deep.
- **The effect:** play is pushed to one touchline and isolated there.

[TBR Football](https://tbrfootball.com/analysis-the-tactics-behind-leicesters-premier-league-success/) describes the same thing: a compact central block that channels play wide, where Leicester either outnumber the ball carrier or face a cross into an aerially strong back line.

**[data]** Against the other 19 teams in 2015/16:
- Leicester were **3rd for pressures per game**.
- Their **PPDA** (opponent passes per defensive action) and **defensive action height** were mid-table, so this was a hard-working mid-block, not a high press.
- They conceded an average number of shots (13.6 a game) but **low-quality ones** (5th-lowest xG per shot).

### 2.7 In possession: direct, fast and early
- Ranieri said his team "play at the speed of light". They accepted losing the ball often because they created chances ([Football Italia](https://www.football-italia.net/84100/ranieri-my-tactics-explained)).
- Forwards started their runs *before* the ball was won, so the first pass could go straight into space behind the defence ([Spielverlagerung](https://spielverlagerung.com/?p=3393)).
- Vardy's typical run was a diagonal from the centre into the channel. The most common attack was a ball over a high line for him ([The Hard Tackle](https://thehardtackle.com/blogs/2016/02/14/leicester-city-the-sum-of-all-parts-killing-premier-giants-one-game-at-a-time/amp/)).
- Leicester averaged 42.4% possession, the lowest for any Premier League champion since 2003/04 ([PL30](https://www.premierleague.com/en/news/2748139)).
- **[data]** They were 3rd-lowest for possession, 4th-highest for long-pass share and **joint-1st for counter-attack shots**. Two-thirds of their shots came within 15 seconds of winning the ball (notebook 02).
- **The weakness:** slow, static build-up. The full-backs stayed deep and the forwards left early, which left a gap, so Leicester relied on long diagonal balls ([Spielverlagerung](https://spielverlagerung.com/?p=3393)).

### 2.8 Set pieces and penalties
- Huth and Morgan were aerial threats at set pieces, and Fuchs delivered corners and free kicks ([The Hard Tackle](https://thehardtackle.com/blogs/2016/02/14/leicester-city-the-sum-of-all-parts-killing-premier-giants-one-game-at-a-time/amp/)). Fuchs's long throws were used as a deliberate weapon ([Spielverlagerung](https://spielverlagerung.com/?p=3393)).
- **[data]** Penalties won rose from 4 in 2014/15 to 13, the most in the league. That's what you'd expect from fast players running at retreating defenders.

### 2.9 The mid-season tightening
- Early in the season Leicester attacked freely and leaked goals. They went 9 games without a clean sheet before Ranieri promised the players pizza for one. After that the team became more pragmatic and kept 11 clean sheets in their last 16 games ([Jonathan Wilson, New Statesman](https://www.newstatesman.com/culture/sport/2016/04/trust-tinkerman-fall-and-rise-claudio-ranieri)).
- [The42](https://the42.ie/7-key-factors-inspired-leicesters-title-triumph-2748883-May2016) gives the same split in goals conceded: 26 in the first 19 games, 8 in the last 17 (their count).
- **[data]** Matches 20–38 compared with 1–19:
  - Leicester pressed harder: PPDA fell from 18.4 to 14.5 and pressures per game rose from 153 to 175.
  - The chances they allowed got worse: xG per shot conceded fell from 0.104 to 0.076.
  - Goals conceded fell from 25 to 11, and clean sheets rose from 4 to 11.
  - "Pragmatic" didn't mean sitting deeper. Defensive action height barely moved. It meant a tighter, harder-pressing block.

### 2.10 Management, rest and recovery
- **A light touch at first.** Ranieri told the players he'd keep Pearson's style and change things "slowly" ([AP via Dawn](https://dawn.com/news/1256467)). Captain Wes Morgan said he "tinkered a bit in terms of tactical positioning" ([New Statesman](https://www.newstatesman.com/culture/sport/2016/04/trust-tinkerman-fall-and-rise-claudio-ranieri)).
- **Keeping it calm.** He played down title talk, kept calm on the touchline, rewarded clean sheets with pizza, and gave the squad a break in Dubai in February ([The42](https://the42.ie/7-key-factors-inspired-leicesters-title-triumph-2748883-May2016); [AP via Dawn](https://dawn.com/news/1256467)).
- **Fewest injuries in the league.** Leicester had 20 injuries and lost 275 days, against 1,137 for Arsenal, who were second-best ([Sportskeeda](https://www.sportskeeda.com/football/secret-leicesters-success-sports-science), citing injury-tracking data; treat it as secondary).
- **Recovery work.** Players got 48 hours to recover after matches and a midweek day off. Staff monitored them with GPS (Catapult), and the club used Prozone tracking data, Opta reports and cryotherapy ([Sportskeeda](https://www.sportskeeda.com/football/secret-leicesters-success-sports-science); [Computer Weekly](https://www.computerweekly.com/news/450296302/Foxy-Leicester-City-FC-won-Premiership-with-data-analytics)).
- **A light schedule.** Leicester had no European football and went out of both domestic cups early, which left fewer matches ([The42](https://the42.ie/7-key-factors-inspired-leicesters-title-triumph-2748883-May2016)).

---

## 3. What did *not* change

**[data]** These are Opta team totals from premierleague.com:

| | 2014/15 (Pearson) | 2015/16 (Ranieri) |
| --- | --- | --- |
| Passes | 13,343 | 13,370 |
| Long passes | 2,706 | 2,695 |
| Possession | 42.9% | 42.4% |
| Shots per 90 ([PL30](https://www.premierleague.com/en/news/2748139)) | 12.0 | 13.7 |
| Shots faced per 90 ([PL30](https://www.premierleague.com/en/news/2748139)) | 14.6 | 13.6 |
| xG | 46.9 | 69.3 |
| Goals for / against | 46 / 55 | 68 / 36 |

**The style was already Pearson's: low possession and direct.** Ranieri didn't make Leicester pass more. He made the same amount of passing far more dangerous:
- A better structure: one settled 4-4-2 instead of 11 formations.
- Players in better positions: Vardy central, two inverted wide players, Okazaki pressing.
- One big signing in the key role: Kanté.
- From January, a defence that pressed harder and gave up only poor chances.

---

## 4. Limitations

- There's no 2014/15 event data in this repo. The Pearson-era tactics come from published analysis, and the season comparison uses Opta totals only.
- The tactical articles are a mix of professional analysis (Spielverlagerung, Coaches' Voice, the Premier League) and opinion pieces (TBR Football, The Hard Tackle). Where they disagree, this document follows the more detailed source.
- Some figures (the injury numbers, the clean-sheet and goals-conceded splits) come from secondary reporting. The repo's own counts are in the notebooks.

## Sources

- Adrian Clarke, [PL30: How Ranieri masterminded Leicester's title victory](https://www.premierleague.com/en/news/2748139), Premier League, 2022
- CE, [Leicester City: Smart as eleven foxes](https://spielverlagerung.com/?p=3393), Spielverlagerung, 16 April 2016
- Tony Hodson, [Coach watch: Nigel Pearson](https://learning.coachesvoice.com/coach-watch-nigel-pearson/), Coaches' Voice, 2021
- Adam Bate, [Claudio Ranieri: five ways he's changed things at Leicester City](https://www.skysports.com/amp/football/news/30385/10083402/claudio-ranieri-five-ways-hes-changed-things-at-leicester-city), Sky Sports, 28 November 2015
- [Ranieri: my tactics explained](https://www.football-italia.net/84100/ranieri-my-tactics-explained), Football Italia, 10 May 2016
- Associated Press, [Methodology behind Leicester: Ranieri's winning blueprint](https://dawn.com/news/1256467), Dawn, 5 May 2016
- Jonathan Wilson, [Trust the tinkerman: the fall and rise of Claudio Ranieri](https://www.newstatesman.com/culture/sport/2016/04/trust-tinkerman-fall-and-rise-claudio-ranieri), New Statesman, 23 April 2016
- Phil Costa, [Focus: Leicester City](https://thesetpieces.com/?p=5394), The Set Pieces, September 2015
- Soumo Ghosh, [Leicester City's multidimensional gameplay](https://thehardtackle.com/blogs/2016/02/14/leicester-city-the-sum-of-all-parts-killing-premier-giants-one-game-at-a-time/amp/), The Hard Tackle, February 2016
- Mihail Vladimirov, [Leicester 2 Liverpool 0: in-depth tactical analysis](https://tomkinstimes.com/?p=57636), The Tomkins Times, February 2016 (partly paywalled)
- [Analysis: the tactics behind Leicester's Premier League success](https://tbrfootball.com/analysis-the-tactics-behind-leicesters-premier-league-success/), TBR Football
- Paul Fennessy, [7 key factors that inspired Leicester's title triumph](https://the42.ie/7-key-factors-inspired-leicesters-title-triumph-2748883-May2016), The42, 4 May 2016
- [Foxy Leicester City won Premiership with data analytics](https://www.computerweekly.com/news/450296302/Foxy-Leicester-City-FC-won-Premiership-with-data-analytics), Computer Weekly, 2016
- [Secret to Leicester's success: sports science](https://www.sportskeeda.com/football/secret-leicesters-success-sports-science), Sportskeeda
- Daniel Rouse, [Flashback: Leicester City's great escape from relegation](https://www.thescore.com/epl/news/1017760), theScore
- [2014–15 Leicester City F.C. season](https://en.wikipedia.org/wiki/2014%E2%80%9315_Leicester_City_F.C._season), Wikipedia
- Premier League official club stats (Opta), [Leicester City 2014/15](https://www.premierleague.com/en/clubs/13/leicester-city/stats?season=2014) and [2015/16](https://www.premierleague.com/en/clubs/13/leicester-city/stats?season=2015)
- StatsBomb Open Data
