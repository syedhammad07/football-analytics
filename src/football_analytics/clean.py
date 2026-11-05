"""Clean the raw StatsBomb data and compute minutes played.

Usage:
    python -m football_analytics.clean            # Premier League 2015/16 (2 27)
    python -m football_analytics.clean 2 27

Reads  data/raw/<comp>_<season>/{events,lineups,matches}.parquet
Writes data/processed/<comp>_<season>/
    events.parquet           on-ball events by players, with x/y columns
    player_match.parquet     one row per player per match: minutes, started, position
    player_season.parquet    one row per player: minutes, appearances, team, position group
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

# Event types that describe the match itself rather than a player's action.
NON_ACTION_TYPES = {
    "Starting XI", "Half Start", "Half End", "Tactical Shift", "Substitution",
    "Player On", "Player Off", "Injury Stoppage", "Referee Ball-Drop",
}

RED_CARDS = {"Red Card", "Second Yellow"}

# StatsBomb's 25 detailed positions grouped into the four used for comparisons.
POSITION_GROUPS = {
    "Goalkeeper": "Goalkeeper",
    "Right Back": "Defender", "Left Back": "Defender",
    "Right Center Back": "Defender", "Left Center Back": "Defender", "Center Back": "Defender",
    "Right Wing Back": "Defender", "Left Wing Back": "Defender",
    "Right Defensive Midfield": "Midfielder", "Left Defensive Midfield": "Midfielder",
    "Center Defensive Midfield": "Midfielder", "Right Center Midfield": "Midfielder",
    "Left Center Midfield": "Midfielder", "Center Midfield": "Midfielder",
    "Right Midfield": "Midfielder", "Left Midfield": "Midfielder",
    "Right Attacking Midfield": "Midfielder", "Left Attacking Midfield": "Midfielder",
    "Center Attacking Midfield": "Midfielder",
    "Right Wing": "Forward", "Left Wing": "Forward",
    "Right Center Forward": "Forward", "Left Center Forward": "Forward",
    "Center Forward": "Forward", "Secondary Striker": "Forward",
}


def _clock_to_minutes(clock: pd.Series) -> pd.Series:
    """'MM:SS' match clock -> minutes as a float. Missing stays NaN."""
    parts = clock.str.split(":", expand=True)
    return parts[0].astype(float) + parts[1].astype(float) / 60


def _split_xy(series: pd.Series, prefix: str) -> pd.DataFrame:
    """Turn a column of [x, y] (or [x, y, z]) lists into prefix_x and prefix_y floats."""
    def first_two(v):
        if isinstance(v, (list, tuple, np.ndarray)) and len(v) >= 2:
            return float(v[0]), float(v[1])
        return np.nan, np.nan

    xy = series.map(first_two)
    return pd.DataFrame(xy.tolist(), columns=[f"{prefix}_x", f"{prefix}_y"], index=series.index)


def clean_events(events: pd.DataFrame) -> pd.DataFrame:
    """Keep player actions only and add numeric coordinate columns."""
    ev = events[events["player_id"].notna() & ~events["type"].isin(NON_ACTION_TYPES)].copy()
    ev["player_id"] = ev["player_id"].astype(int)
    ev["clock"] = ev["minute"] + ev["second"] / 60

    coord_cols = {
        "location": "start",
        "pass_end_location": "pass_end",
        "carry_end_location": "carry_end",
        "shot_end_location": "shot_end",
    }
    for col, prefix in coord_cols.items():
        ev = ev.join(_split_xy(ev[col], prefix))
    ev = ev.drop(columns=list(coord_cols) + [
        "substitution_replacement", "substitution_replacement_id", "substitution_outcome",
    ])

    for col in ["under_pressure", "pass_shot_assist", "pass_goal_assist", "pass_cross",
                "pass_switch", "pass_through_ball", "pass_cut_back"]:
        ev[col] = ev[col].fillna("False").astype(str).str.lower().eq("true")

    return ev.reset_index(drop=True)


def player_match_minutes(lineups: pd.DataFrame, events: pd.DataFrame) -> pd.DataFrame:
    """Minutes each player was on the pitch in each match.

    Uses the lineup position spells (on/off times). Two corrections:
    * spells still open at the final whistle end at that match's last event;
    * lineups keep sent-off players on until the final whistle, so a red card
      or second yellow ends the player's time at the moment of the card.
    """
    sp = lineups.copy()
    sp["start"] = _clock_to_minutes(sp["from"])
    # "Started" = on the pitch at kick-off. (One Swansea match labels its
    # kick-off spells "Tactical Shift" instead of "Starting XI".)
    sp["at_kickoff"] = (sp["from"] == "00:00") & (sp["from_period"] == 1)
    sp["end"] = _clock_to_minutes(sp["to"])

    match_end = events.groupby("match_id").apply(
        lambda g: (g["minute"] + g["second"] / 60).max(), include_groups=False
    ).rename("match_end")
    sp = sp.join(match_end, on="match_id")
    sp["end"] = sp["end"].fillna(sp["match_end"])

    cards = events[
        events["foul_committed_card"].isin(RED_CARDS) | events["bad_behaviour_card"].isin(RED_CARDS)
    ]
    sent_off = (
        cards.assign(card_time=cards["minute"] + cards["second"] / 60)
        .groupby(["match_id", "player_id"])["card_time"].min()
    )
    sp = sp.join(sent_off, on=["match_id", "player_id"])
    sp["end"] = np.where(sp["card_time"].notna(), np.minimum(sp["end"], sp["card_time"]), sp["end"])
    sp["minutes"] = (sp["end"] - sp["start"]).clip(lower=0)

    # Position played for longest in each match
    main_pos = (
        sp.sort_values("minutes", ascending=False)
        .drop_duplicates(["match_id", "player_id"])[["match_id", "player_id", "position"]]
    )
    pm = (
        sp.groupby(["match_id", "team", "player_id"], as_index=False)
        .agg(minutes=("minutes", "sum"),
             started=("at_kickoff", "any"),
             sent_off=("card_time", lambda s: s.notna().any()))
        .merge(main_pos, on=["match_id", "player_id"])
    )
    names = lineups.drop_duplicates("player_id").set_index("player_id")["player"]
    pm.insert(3, "player", pm["player_id"].map(names))
    pm["minutes"] = pm["minutes"].round(1)
    return pm


def player_season(pm: pd.DataFrame, lineups: pd.DataFrame) -> pd.DataFrame:
    """Season totals per player, with the team and position they played most."""
    def most_minutes(col: str) -> pd.Series:
        return (pm.groupby(["player_id", col])["minutes"].sum()
                  .reset_index().sort_values("minutes", ascending=False)
                  .drop_duplicates("player_id").set_index("player_id")[col])

    season = pm.groupby(["player_id", "player"], as_index=False).agg(
        minutes=("minutes", "sum"),
        appearances=("match_id", "nunique"),
        starts=("started", "sum"),
        red_cards=("sent_off", "sum"),
        teams=("team", lambda s: ", ".join(sorted(s.unique()))),
    )
    season = season.join(most_minutes("team").rename("main_team"), on="player_id")
    season = season.join(most_minutes("position").rename("main_position"), on="player_id")
    season["position_group"] = season["main_position"].map(POSITION_GROUPS)

    nick = (lineups.dropna(subset=["player_nickname"])
                   .drop_duplicates("player_id").set_index("player_id")["player_nickname"])
    season["display_name"] = season["player_id"].map(nick).fillna(season["player"])
    country = lineups.drop_duplicates("player_id").set_index("player_id")["country"]
    season["country"] = season["player_id"].map(country)

    season["minutes"] = season["minutes"].round(0).astype(int)
    cols = ["player_id", "display_name", "player", "main_team", "teams", "position_group",
            "main_position", "country", "minutes", "appearances", "starts", "red_cards"]
    return season[cols].sort_values("minutes", ascending=False).reset_index(drop=True)


def _fix_names(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    """Some names come with a doubled apostrophe (N''Golo); make them consistent."""
    for col in cols:
        if col in df.columns:
            df[col] = df[col].str.replace("''", "'", regex=False)
    return df


def run(competition_id: int = 2, season_id: int = 27) -> Path:
    raw = RAW_DIR / f"{competition_id}_{season_id}"
    out = PROCESSED_DIR / f"{competition_id}_{season_id}"
    out.mkdir(parents=True, exist_ok=True)

    events = _fix_names(pd.read_parquet(raw / "events.parquet"), ["player", "pass_recipient"])
    lineups = _fix_names(pd.read_parquet(raw / "lineups.parquet"), ["player", "player_nickname"])

    ev = clean_events(events)
    pm = player_match_minutes(lineups, events)
    season = player_season(pm, lineups)

    ev.to_parquet(out / "events.parquet", index=False)
    pm.to_parquet(out / "player_match.parquet", index=False)
    season.to_parquet(out / "player_season.parquet", index=False)

    print(f"events:        {len(events):>9,} raw -> {len(ev):,} player actions")
    print(f"player_match:  {len(pm):>9,} rows")
    print(f"player_season: {len(season):>9,} players "
          f"({(season['minutes'] >= 900).sum()} with 900+ minutes)")
    print(f"Saved to {out}")
    return out


if __name__ == "__main__":
    args = [int(a) for a in sys.argv[1:3]]
    run(*args) if len(args) == 2 else run()
