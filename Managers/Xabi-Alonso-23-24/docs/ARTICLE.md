# Xabi Alonso's Leverkusen: the philosophy in the data

**How Bayer Leverkusen went a whole Bundesliga season unbeaten, told through seven ideas and nine charts.**

*By Hammad · Data: StatsBomb open data, all 34 of Leverkusen's 2023/24 Bundesliga matches · Each idea is described from published analysis, then tested against the data*

---

## The season in numbers

| | |
| --- | --- |
| **Record** | 28 wins, 6 draws, 0 defeats: the first unbeaten season in Bundesliga history |
| **Points** | 90 |
| **Goals** | 89 scored, 24 conceded |
| **Share of all passes** | 62% on average; more than half in 28 of 34 games |
| **Pass completion** | 88% (opponents 80%) |
| **Goals in stoppage time** | 8, worth 9 points |

> **The short version.** Alonso's Leverkusen controlled games with the ball, built patiently from the goalkeeper, attacked through the middle with two wing-backs pushed high, won the ball back in the opponent's half, and refused to lose: three of their six draws were rescued in stoppage time.

---

## The coach

Xabi Alonso played under some of the most influential coaches of his era: Rafael Benítez at Liverpool, José Mourinho and Carlo Ancelotti at Real Madrid, and Pep Guardiola at Bayern Munich. He has said he joined Bayern in 2014 partly to watch Guardiola's methods up close, and that Ancelotti's man-management had the biggest impact on him as a coach. His own summary: "You learn from that but you need to build your own personality."

Analysts describe his style as a mix of the two schools he played in: **Guardiola's possession play** and **Mourinho's defensive organisation and counter-attacking**. He is seen as a pragmatist who adapts the system rather than following one ideology.

His coaching path was short and fast:

| Years | Job |
| --- | --- |
| 2018–2019 | Real Madrid youth teams |
| 2019–2022 | Real Sociedad B (Segunda División B) |
| October 2022 | Bayer Leverkusen, his first senior job, replacing Gerardo Seoane |
| 2023/24 | Unbeaten Bundesliga champions; German Cup winners |

---

## Idea 1 · The shape: 3-4-2-1

In his first season Alonso mostly used a 3-4-3. In 2023/24 he settled on a **3-4-2-1**: three centre-backs, two wing-backs, a double pivot of Xhaka and Palacios, Wirtz and Hofmann as two number 10s behind Boniface. Without the ball, it became a back five.

![The shape](../reports/figures/04_shape_pass_network.png)

*Figure 4 · Average position of each regular starter when passing, all 34 matches. Lines join players who completed 120+ passes to each other.*

**What the data shows.** The shape is clear even averaged over a season. Tapsoba, Tah and Kossounou form the back three around the halfway line. Xhaka and Palacios sit together in the centre, and **Xhaka completed more passes than anyone (3,045)**. The wing-backs are the highest players on each side: Grimaldo on the left and Frimpong on the right are level with or ahead of the two 10s. The thickest lines run from the centre-backs into Xhaka and from Xhaka out to Grimaldo: the ball goes through the middle and then wide.

---

## Idea 2 · Control the ball, control the game

Alonso's teams dominate the ball in compact triangles. Published early-season figures put Leverkusen at 58% possession and a league-high 90% pass completion.

![Control by match](../reports/figures/05_control_by_match.png)

*Figure 5 · Each dot is one match: Leverkusen's share of all passes (across) and of passes into the final third (up).*

**What the data shows.** Leverkusen made **713 passes per match to their opponents' 440**, completed **88%** of them (opponents 80%), and had more of the ball in **28 of 34 games**. They had more of the passes into the final third in **30**.

The exceptions are the interesting part. Their **biggest win of the season, 3-0 at home to Bayern, came with only 39% of the passes**, their lowest share all season. Against the strongest teams, Alonso was happy to give up the ball and counter. This is the Mourinho half of the mix.

---

## Idea 3 · Build from the goalkeeper

This is the question answered in the [one-page report](../reports/Leverkusen_build_up_one_page.pdf).

![Where the keeper's passes go](../reports/figures/02_where_the_keeper_passes_go.png)

*Figure 2 · Where each player received the goalkeeper's short passes, and who took the ball into midfield.*

**What the data shows.** Hrádecký went short 65% of the time (opponents 47%). Tapsoba and Tah split wide and Xhaka dropped between them. 72% of Leverkusen's goalkeeper possessions reached midfield before the opponent touched the ball (opponents 52%), and **85% did when the keeper went short**, against 47% when he went long. See figures 1–3.

---

## Idea 4 · Win the ball back high, but patiently

Alonso's Leverkusen were not a gegenpressing team. Coaches' Voice notes that in his first season they allowed more passes per defensive action than most of the league. The midfield delayed the ball so the wing-backs could recover, and the press steered opponents towards the touchline rather than charging at them.

![Where they win the ball](../reports/figures/06_where_they_win_the_ball.png)

*Figure 6 · Where each team's ball recoveries and pressures happened, by third.*

**What the data shows.** Leverkusen applied fewer pressures per match than their opponents (141 to 195), but that is mostly because the opponents had far less of the ball to press. **Where** they pressed is the point: **34% of their pressures and 31% of their ball recoveries came in the attacking third**, against 18% and 20% for their opponents. They didn't press more; they pressed higher, and they won the ball back more often (52 recoveries per match to 43).

---

## Idea 5 · Wing-backs as attackers

In a 3-4-2-1 the wing-backs provide all the width, so the 10s can play inside. Alonso picked two attacking full-backs for the job: Álex Grimaldo on the left and Jeremie Frimpong on the right.

![Wing-back goal contributions](../reports/figures/07_wingback_goal_contributions.png)

*Figure 7 · League goals and assists, 2023/24 (as recorded by StatsBomb).*

**What the data shows.** **Grimaldo had more goal contributions than anyone in the squad: 10 goals and 13 assists**, more than the striker Boniface (22) and Wirtz (21). Frimpong was fourth with 16 (9 goals, 7 assists). Two of Leverkusen's top four attackers were, on the team sheet, defenders.

---

## Idea 6 · Through the middle, not round the outside

Alonso's teams prefer to progress centrally. In his first season Leverkusen had the second-lowest number of crosses in the Bundesliga.

![Passes into the box](../reports/figures/08_passes_into_the_box.png)

*Figure 8 · Completed passes into the penalty area from outside it, per match, by where they were played from.*

**What the data shows.** Leverkusen completed **16.1 passes into the box per match, more than twice their opponents' 7.6**, and **half of them came through the middle** (8.1 per match). Only **16%** were crosses, against 23% for their opponents. Because they had so much more of the ball, they still crossed more often in total (12.9 crosses per match to 7.3), but crossing was the back-up plan, not the main one.

---

## Idea 7 · Never lose: "Xabi time"

Leverkusen's habit of scoring in the last minutes became a catchphrase in Germany. Across all competitions they scored 15 goals after the 90th minute that season.

![Goals by minute](../reports/figures/09_goals_by_minute.png)

*Figure 9 · League goals by 15-minute period. 45+ and 90+ = stoppage time.*

**What the data shows.** In the league alone they scored **8 stoppage-time goals and conceded none**. Those goals were worth **9 points**:

| Match | Score | Late goal changed |
| --- | --- | --- |
| Leverkusen vs Stuttgart | 2-2 | Defeat → draw |
| Bayern vs Leverkusen | 2-2 | Defeat → draw |
| Dortmund vs Leverkusen | 1-1 | Defeat → draw |
| Leverkusen vs Hoffenheim | 2-1 | Draw → win |
| Leipzig vs Leverkusen | 2-3 | Draw → win |
| Augsburg vs Leverkusen | 0-1 | Draw → win |

**Without stoppage time, the invincible season would have had three defeats.** Their second-half record was even stronger than their first: 52 of their 89 goals came after half-time, against 13 conceded.

---

## What clubs can learn

1. **One clear shape, with roles everyone understands.** Alonso stuck with the 3-4-2-1, and a whole season of averages in Figure 4 still looks like the team sheet.
2. **Build the attack around a deep passer.** Xhaka made the most passes and was the link from defence to attack, both from the goalkeeper and in open play.
3. **Use full-backs who can attack.** Grimaldo and Frimpong scored or assisted 39 goals between them.
4. **Possession is a tool, not a rule.** The best result of the season came with 39% of the ball.
5. **Fitness and belief at the end.** Nine points came after the 90th minute. That is depth, conditioning and mentality as much as tactics.

---

## Appendix

### Data and method

| Source | What it gives | Used for |
| --- | --- | --- |
| [StatsBomb open data](https://github.com/statsbomb/open-data), Bundesliga 2023/24 | Every event in Leverkusen's 34 league matches (137,765 events) | Every number and chart in this article |

- **Opponents** means the other team in Leverkusen's matches. The open data only covers Leverkusen's games, so it is not a league average.
- **Average positions** (Figure 4) are where each player made his passes, over the whole season. They show the shape on the ball, not without it.
- **Thirds** are measured from each team's own goal line (0–40, 40–80, 80–120 yards).
- **Passes into the box** are completed passes ending in the penalty area that started outside it; "left wing" and "right wing" are the 18 yards nearest each touchline.
- **Goals** include own goals scored by opponents (3). Assists are as recorded by StatsBomb.

### Limitations

- Event data records what happens on the ball. It can't show off-ball movement, so the press and the shape without the ball are inferred from where actions happened.
- Fewer pressures per match partly reflects how little of the ball opponents had; the useful comparison is where pressures happened, not how many.
- The descriptions of Alonso's ideas come from published analysis, not from the coach himself, except where quoted.

### Sources

- [Xabi Alonso at Bayer Leverkusen](https://learning.coachesvoice.com/cv/xabi-alonso-bayer-leverkusen-liverpool/), Coaches' Voice
- [Xabi Alonso: manager profile, style of play, formations, philosophy](https://www.goal.com/en-gb/news/xabi-alonso-manager-profile-style-of-play-formations-philosophy/bltfe8a9e2f46675370), Goal
- [Years of learning from the best to help Alonso at Real Madrid](https://www.thescore.com/news/3291075), theScore (AFP)
- [Xabi Alonso's Bayer Leverkusen tactics](https://www.bundesliga.com/en/bundesliga/news/xabi-alonso-bayer-leverkusen-tactics-25350), bundesliga.com
- [Leverkusen midfield analysis: Xhaka, Andrich, Palacios](https://www.bundesliga.com/en/bundesliga/news/bayer-leverkusen-midfield-tactical-analysis-xhaka-andrich-palacios-26871), bundesliga.com
- [The statistics behind Leverkusen's historic unbeaten Bundesliga title win](https://www.aljazeera.com/sports/2024/5/19/the-statistics-behind-leverkusens-historic-unbeaten-bundesliga-title-win), Al Jazeera
