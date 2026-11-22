# Player Style Finder

Groups football players by **how** they play, not where they are listed, and finds the most similar players to anyone in the dataset.

Data: StatsBomb open data, 2015/16 full seasons of the Premier League, La Liga, Serie A and Ligue 1 (1,517 matches). 1,247 outfield player-seasons with at least 900 minutes.

## Method

1. **Features (42 per player).** Built from raw event data: passing style (volume, length, direction, progressive passes, crosses, through balls), carrying and dribbling, shooting (non-penalty xG, shot distance, headers), defending (pressures, tackles, interceptions, aerials), and where the player touches the ball (average height up the pitch, width, share in each third and in the box). Counts are per 90 minutes and log-transformed. Defensive actions are adjusted for possession so that players in low-possession teams aren't overrated.
2. **Embedding.** Standardise, then PCA keeping 85% of variance (8 components).
3. **Similar players.** Nearest neighbours in that space, shown as a 0–100 similarity.
4. **Explaining each match.** For every match the app lists the 3 stats where the two players are most alike (picked from the player's 12 highest stats, so they're stats that define him) and the 3 with the biggest differences, with both players' real values. It also shows three closeness measures:
   - **Style match (0–100):** distance in the 8-dimension style space. This is what ranks the list.
   - **% of stats alike:** share of the 42 stats where the two are within half a standard deviation. It counts every stat equally, so it can disagree with the score. The score gives more weight to the stats that best separate styles.
   - **Typical best match (66):** the median best-match score across all players. A best match well below 66 means the player's style is unusual (Messi's best is 28).
5. **Roles.** k-means within four position families. The number of roles per family is the largest k whose bootstrap stability (adjusted Rand index) stays at or above 0.7. That gives 2 roles each for centre-backs, full-backs and midfielders, and 5 for attackers.

| Family | Roles |
|---|---|
| Centre-backs | Stopper · Ball-playing |
| Full-backs | Defensive · Attacking |
| Midfielders | Holding · Box-to-box |
| Attackers | Creative playmaker · Touchline winger · Target striker · Mobile forward · Deep-lying wide midfielder |

## Checks

- **Split-half re-identification.** Each player's features are rebuilt from odd and even matches separately (982 players with ≥600 minutes in each half). From one half, the search ranks the same player's other half **first 36.9%** of the time and **in the top 5 65.6%** of the time, against 0.1% and 0.5% by chance. The median rank is 3 of 982. So the features capture a stable individual style rather than noise.
- **Role stability.** The two halves land in the same role 86.3% of the time (chance: 20–50%).
- **Team leakage.** 2.6% of top-5 neighbours are team-mates (random ≈ 1.2%), so similarity is not mainly driven by team.
- **How many roles?** Within positions, style is mostly a continuum. More than 2 roles per family (5 for attackers) were unstable, which is why the similarity search is the main tool and roles are a summary.

## Limits

- One season (2015/16). The players are now mostly retired or in different roles.
- Style is partly shaped by the team's system (for example, ball-playing centre-backs cluster in possession teams). Only defensive actions are possession-adjusted.
- Positions come from StatsBomb's per-event position labels (the most frequent label is used).
- Bundesliga is left out: only 34 matches are open.

## Run

```
pip install pandas numpy scikit-learn
./run_all.sh
```

## Data licence

StatsBomb open data, used under the StatsBomb Public Data User Agreement. The raw data and derived data files are **not** redistributed (the `data/` folder is gitignored); the pipeline downloads them. Any published analysis must credit StatsBomb with their logo. Users should register at statsbomb.com/resource-centre.
