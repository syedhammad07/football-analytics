"""Finds the players whose statistical profile is closest to a target player."""
import unicodedata

import numpy as np
import pandas as pd

from .config import METRIC_BY_KEY, METRICS, MIN_MINUTES

PCT_COLS = ["p_" + m.key for m in METRICS]


def normalise(text: str) -> str:
    """Lower case, accents removed: 'Ødegaard' and 'odegaard' match."""
    text = text.replace("ø", "o").replace("Ø", "O").replace("ß", "ss")
    return "".join(c for c in unicodedata.normalize("NFKD", text) if not unicodedata.combining(c)).lower().strip()


def find_player(players: pd.DataFrame, query: str) -> pd.Series:
    """The player whose name best matches `query`. Raises LookupError with suggestions when unclear."""
    q = normalise(query)
    names = players["name"].map(normalise)
    exact = players[names == q]
    if len(exact) == 1:
        return exact.iloc[0]
    words = q.split()
    whole = players[names.map(lambda n: all(w in n.replace("-", " ").split() for w in words))]
    if len(whole) == 1:                       # "Saka" is a whole word in "Bukayo Saka", only part of "Wan-Bissaka"
        return whole.iloc[0]
    hits = players[names.map(lambda n: all(w in n for w in words))]
    if len(hits) == 1:
        return hits.iloc[0]
    if len(hits) > 1:
        options = ", ".join(f"{r['name']} ({r.team})" for _, r in hits.sort_values("timePlayed", ascending=False).head(6).iterrows())
        raise LookupError(f"'{query}' matches several players: {options}. Use more of the name.")
    raise LookupError(f"No Premier League player in the data matches '{query}'.")


def similarity(a: pd.Series, b: pd.Series) -> float:
    """100 minus the average percentile gap across every metric both players have. 100 = identical."""
    pa = a[PCT_COLS].to_numpy(dtype=float)
    pb = b[PCT_COLS].to_numpy(dtype=float)
    ok = ~np.isnan(pa) & ~np.isnan(pb)
    if not ok.any():
        return float("nan")
    return float(100 - np.abs(pa[ok] - pb[ok]).mean())


def similarity_to_all(target: pd.Series, players: pd.DataFrame) -> pd.Series:
    """Similarity of every row in `players` to `target` (vectorised version of `similarity`)."""
    t = target[PCT_COLS].to_numpy(dtype=float)
    p = players[PCT_COLS].to_numpy(dtype=float)
    gaps = np.abs(p - t)
    return pd.Series(100 - np.nanmean(gaps, axis=1), index=players.index)


def shared_strengths(target: pd.Series, other: pd.Series, n: int = 3, floor: float = 75) -> list[str]:
    """Metrics where both players are in the top quarter of their position, strongest first."""
    out = []
    for col in PCT_COLS:
        t, o = target[col], other[col]
        if pd.notna(t) and pd.notna(o) and t >= floor and o >= floor:
            out.append((min(t, o), METRIC_BY_KEY[col[2:]].label))
    return [label for _, label in sorted(out, reverse=True)[:n]]


def biggest_gap(target: pd.Series, other: pd.Series) -> str:
    """The metric where the two players differ most, in words."""
    best = None
    for col in PCT_COLS:
        t, o = target[col], other[col]
        if pd.notna(t) and pd.notna(o) and (best is None or abs(o - t) > abs(best[1])):
            best = (col, o - t)
    if best is None:
        return ""
    metric = METRIC_BY_KEY[best[0][2:]]
    label = metric.label.lower()
    if label.endswith("%"):
        word = "higher" if best[1] > 0 else "lower"
    else:
        word = "more" if best[1] > 0 else "fewer"
    if metric.key == "losses":               # percentile is reversed: higher = loses the ball less
        word, label = ("loses the ball less" if best[1] > 0 else "loses the ball more"), ""
    return f"{word}{' ' + label if label else ''} ({best[1]:+.0f} pts)"


def find_similar(players: pd.DataFrame, target: pd.Series, *, same_position: bool = True,
                 max_age: float | None = None, max_value_m: float | None = None,
                 min_minutes: int = MIN_MINUTES, exclude_team: bool = False, in_pl_only: bool = False,
                 top: int = 10) -> pd.DataFrame:
    """Rank everyone else by how closely their profile matches `target`, after applying the filters.

    `max_value_m` is in millions of euros and drops players with no known value.
    `exclude_team` leaves out the target's current club; `in_pl_only` keeps players still in the league now.
    """
    pool = players[(players.pl_id != target.pl_id) & (players.timePlayed >= min_minutes)]
    if in_pl_only and "in_pl_now" in pool:
        pool = pool[pool.in_pl_now.fillna(False).astype(bool)]
    if same_position:
        pool = pool[pool.position == target.position]
    if exclude_team:
        club = target.get("club_now", target.team)
        pool = pool[pool.get("club_now", pool.team) != club]
    if max_age is not None:
        pool = pool[pool.age <= max_age]
    if max_value_m is not None:
        pool = pool[pool.market_value_eur.notna() & (pool.market_value_eur <= max_value_m * 1e6)]
    if pool.empty:
        return pool.assign(match=[], shared=[], gap=[])
    pool = pool.assign(match=similarity_to_all(target, pool)).sort_values("match", ascending=False).head(top)
    pool["shared"] = [", ".join(shared_strengths(target, r)) for _, r in pool.iterrows()]
    pool["gap"] = [biggest_gap(target, r) for _, r in pool.iterrows()]
    return pool
