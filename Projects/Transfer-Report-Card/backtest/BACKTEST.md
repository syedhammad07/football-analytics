# Backtest: do the verdicts predict later output?

**Question.** If a signing is graded on his *first* graded season only, does that verdict predict how he performs in his *later* seasons at the club (seasons 2+, excluded from the first-season grade)?

**Scope.** Paid signings into the Premier League, La Liga, Serie A, the Bundesliga and Ligue 1 from summer 2017 (the first season detailed stats exist for all five leagues). 1,810 signings have two or more graded seasons.

| First-season verdict | n | First-season value | Later value | Later score | Beat the fee later |
|---|---|---|---|---|---|
| Bargain | 164 | +26.9 | +15.7 | 64.0 | 85% |
| Great value | 113 | +36.8 | +19.6 | 72.9 | 85% |
| Good value | 244 | +22.2 | +11.3 | 64.9 | 78% |
| About fair | 853 | +0.3 | +1.2 | 53.5 | 52% |
| Overpriced | 232 | -20.6 | -11.0 | 42.5 | 29% |
| Poor signing | 204 | -35.5 | -14.7 | 36.3 | 25% |

**Headline.** First-season value correlates 0.50 with later value. The fee alone predicts later score far worse (R² 0.04 against 0.27 for the first-season value). The best fifth of signings later average +15.8 against -13.4 for the worst fifth; the good-minus-poor gap is 27.2 points (95% CI 24.9 to 29.5).

**By position** (correlation of first and later season): central midfield 0.63, defensive midfield 0.56, full-back 0.55, forward 0.50, centre-back 0.49, attacking midfield 0.51, goalkeeper 0.31 (weakest; goalkeeper grades should be read loosely).

**Change from the earlier version.** The Premier League seasons 2009/10 to 2016/17 were removed because the data source's terms do not allow reuse without written approval. Results are essentially unchanged (0.50 before and after).
