"""Download StatsBomb open data into data/raw/.

Usage:
    python -m football_analytics.data                 # list available competitions
    python -m football_analytics.data 2 27            # download Premier League 2015/16 (default choice)

Output (git-ignored):
    data/raw/<competition_id>_<season_id>/matches.parquet
    data/raw/<competition_id>_<season_id>/lineups.parquet   (position spells)
    data/raw/<competition_id>_<season_id>/events.parquet
"""
from __future__ import annotations

import sys
import warnings
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd
from statsbombpy import sb

warnings.filterwarnings("ignore", message="credentials were not supplied")

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = PROJECT_ROOT / "data" / "raw"

# Columns kept from the event data. The full table has 100+ columns; these
# cover shots, passes, carries, dribbles, defensive actions, cards and subs.
EVENT_COLUMNS = [
    "id", "match_id", "index", "period", "minute", "second", "timestamp",
    "type", "possession", "possession_team", "play_pattern",
    "team", "player", "player_id", "position", "location",
    "duration", "under_pressure",
    # passes
    "pass_end_location", "pass_outcome", "pass_length", "pass_type",
    "pass_shot_assist", "pass_goal_assist", "pass_cross", "pass_switch",
    "pass_through_ball", "pass_cut_back", "pass_recipient",
    # carries / dribbles
    "carry_end_location", "dribble_outcome",
    # shots
    "shot_statsbomb_xg", "shot_outcome", "shot_type", "shot_body_part",
    "shot_end_location",
    # defending
    "duel_type", "duel_outcome", "interception_outcome",
    # discipline and substitutions
    "foul_committed_card", "bad_behaviour_card",
    "substitution_replacement", "substitution_replacement_id",
    "substitution_outcome",
]


def _parquet_safe(df: pd.DataFrame) -> pd.DataFrame:
    """Make object columns writable to parquet.

    StatsBomb tables mix types in some columns (e.g. "4711, 3626" next to ints),
    which pyarrow rejects. Columns holding lists (coordinates) are kept as lists;
    every other object column is stored as text.
    """
    df = df.copy()
    for col in df.columns[df.dtypes == object]:
        non_null = df[col].dropna()
        if len(non_null) and isinstance(non_null.iloc[0], (list, tuple)):
            df[col] = df[col].apply(lambda v: list(v) if isinstance(v, (list, tuple)) else None)
        else:
            df[col] = df[col].astype("string")
    return df


def list_competitions() -> pd.DataFrame:
    comps = sb.competitions()
    return comps[["competition_id", "season_id", "competition_name", "season_name"]]


def _events(match_id: int) -> pd.DataFrame:
    ev = sb.events(match_id=match_id)
    for col in EVENT_COLUMNS:
        if col not in ev.columns:
            ev[col] = pd.NA
    return ev[EVENT_COLUMNS]


def _lineups(match_id: int) -> pd.DataFrame:
    """One row per player per position spell (who played where, from when to when).

    Unused substitutes have no spells and are left out.
    """
    rows = []
    for team, df in sb.lineups(match_id=match_id).items():
        for _, p in df.iterrows():
            for spell in p["positions"]:
                rows.append({
                    "match_id": match_id,
                    "team": team,
                    "player_id": p["player_id"],
                    "player": p["player_name"],
                    "player_nickname": p["player_nickname"],
                    "country": p["country"],
                    "position": spell["position"],
                    "from": spell["from"],
                    "to": spell["to"],
                    "from_period": spell["from_period"],
                    "to_period": spell["to_period"],
                    "start_reason": spell["start_reason"],
                    "end_reason": spell["end_reason"],
                })
    return pd.DataFrame(rows)


def download_season(competition_id: int, season_id: int, workers: int = 8) -> Path:
    out_dir = RAW_DIR / f"{competition_id}_{season_id}"
    out_dir.mkdir(parents=True, exist_ok=True)

    matches = sb.matches(competition_id=competition_id, season_id=season_id)
    _parquet_safe(matches).to_parquet(out_dir / "matches.parquet", index=False)
    ids = matches["match_id"].tolist()
    print(f"{len(ids)} matches found, downloading events and lineups...")

    with ThreadPoolExecutor(max_workers=workers) as pool:
        events = list(pool.map(_events, ids))
        lineups = list(pool.map(_lineups, ids))

    events_df = pd.concat(events, ignore_index=True)
    # Lists like [x, y] are stored as plain lists; parquet keeps them as arrays.
    _parquet_safe(events_df).to_parquet(out_dir / "events.parquet", index=False)
    _parquet_safe(pd.concat(lineups, ignore_index=True)).to_parquet(out_dir / "lineups.parquet", index=False)

    print(f"Saved {len(ids)} matches and {len(events_df):,} events to {out_dir}")
    return out_dir


if __name__ == "__main__":
    if len(sys.argv) == 3:
        download_season(int(sys.argv[1]), int(sys.argv[2]))
    else:
        print(list_competitions().to_string(index=False))
        print("\nThis project uses Premier League 2015/16:")
        print("    python -m football_analytics.data 2 27")
