"""Turns season totals into per-90 numbers, adjusts them for team possession and ranks them as percentiles."""
import numpy as np
import pandas as pd

from .config import METRICS, MIN_MINUTES


def per90(total: pd.Series, minutes: pd.Series) -> pd.Series:
    """A season total expressed per 90 minutes played."""
    return total / minutes * 90


def share(made: pd.Series, attempted: pd.Series, min_attempts: int = 0) -> pd.Series:
    """Success rate in %, blank (NaN) when there are too few attempts to mean anything."""
    attempted = attempted.astype(float)
    return (100 * made / attempted).where(attempted >= max(min_attempts, 1))


def possession_factor(possession: pd.Series, kind: str) -> pd.Series:
    """Scale to a neutral 50% possession.

    A team with 65% of the ball gives its players more passes and touches, and fewer chances to tackle.
    On-ball volume is scaled by 50 / possession; defending by 50 / opponents' possession.
    """
    if kind == "on_ball":
        return 50 / possession
    if kind == "off_ball":
        return 50 / (100 - possession)
    raise ValueError(f"unknown adjustment: {kind}")


def build_metrics(raw: pd.DataFrame) -> pd.DataFrame:
    """One row per player with every metric in config.METRICS (raw, before possession adjustment)."""
    d = raw.copy()
    m = d.timePlayed
    d["npg"] = per90(d.goals - d.penaltyGoals, m)
    d["xg"] = per90(d.expectedGoals, m)
    d["shots"] = per90(d.totalShots, m)
    d["box_touches"] = per90(d.totalTouchesInOppositionBox, m)
    d["assists"] = per90(d.goalAssists, m)
    d["xa"] = per90(d.expectedAssists, m)
    d["chances"] = per90(d.keyPassesAttemptAssists, m)
    d["through_balls"] = per90(d.throughBalls, m)
    d["crosses"] = per90(d.successfulCrossesOpenPlay, m)
    d["passes"] = per90(d.totalPasses, m)
    d["pass_pct"] = share(d.totalPasses - d.totalUnsuccessfulPassesExclCrossesAndCorners, d.totalPasses, 100)
    d["opp_half_passes"] = per90(d.successfulPassesOppositionHalf, m)
    d["long_passes"] = per90(d.successfulLongPasses, m)
    d["forward_passes"] = per90(d.forwardPasses, m)
    d["dribbles"] = per90(d.successfulDribbles, m)
    d["dribble_pct"] = share(d.successfulDribbles, d.successfulDribbles + d.unsuccessfulDribbles, 15)
    d["touches"] = per90(d.touches, m)
    d["losses"] = per90(d.totalLossesOfPossession, m)
    d["fouls_won"] = per90(d.totalFoulsWon, m)
    d["tackles_won"] = per90(d.tacklesWon, m)
    d["interceptions"] = per90(d.interceptions, m)
    d["recoveries"] = per90(d.recoveries, m)
    d["blocks"] = per90(d.blocks, m)
    d["clearances"] = per90(d.totalClearances, m)
    d["duel_pct"] = share(d.duelsWon, d.duelsWon + d.duelsLost, 30)
    d["aerials_won"] = per90(d.aerialDuelsWon, m)
    d["aerial_pct"] = share(d.aerialDuelsWon, d.aerialDuelsWon + d.aerialDuelsLost, 15)
    return d


def adjust_for_possession(d: pd.DataFrame, possession: pd.DataFrame) -> pd.DataFrame:
    """Add each team's possession and scale the metrics that depend on it."""
    d = d.merge(possession[["team", "possession"]], on="team", how="left")
    if d.possession.isna().any():
        missing = sorted(d.loc[d.possession.isna(), "team"].unique())
        raise ValueError(f"no possession figure for: {missing}")
    for metric in METRICS:
        if metric.adjust:
            d[metric.key] = d[metric.key] * possession_factor(d.possession, metric.adjust)
    return d


def add_percentiles(d: pd.DataFrame, min_minutes: int = MIN_MINUTES) -> pd.DataFrame:
    """Percentile (0-100) of every metric, ranked within the player's position.

    Only players with `min_minutes` set the scale, so a defender's 2 tackles per 90 is compared with other
    regular defenders. Players below the minutes bar still get a percentile, placed on that same scale.
    """
    d = d.copy()
    pool = d.timePlayed >= min_minutes
    for metric in METRICS:
        col = np.full(len(d), np.nan)
        for pos, idx in d.groupby("position").groups.items():
            group = d.loc[idx]
            ref = group.loc[pool.loc[idx], metric.key].dropna().to_numpy()
            if len(ref) == 0:
                continue
            values = group[metric.key].to_numpy()
            below = (ref[None, :] < values[:, None]).sum(axis=1)
            equal = (ref[None, :] == values[:, None]).sum(axis=1)
            pct = 100 * (below + 0.5 * equal) / len(ref)        # midpoint rank: ties share a percentile
            if not metric.higher_is_better:
                pct = 100 - pct
            pct[np.isnan(values)] = np.nan
            col[d.index.get_indexer(idx)] = pct
        d["p_" + metric.key] = np.round(col)
    return d
