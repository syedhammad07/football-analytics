"""Settings shared by the whole package: where the data lives, who counts, and which stats describe a player."""
from dataclasses import dataclass
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_DIR / "data"

SEASON = 2025                       # 2025 = the 2025/26 Premier League season
PLAYERS_CSV = DATA_DIR / "pl_players_2025-26.csv"
POSSESSION_CSV = DATA_DIR / "pl_team_possession_2025-26.csv"
TRANSFERMARKT_GZ = DATA_DIR / "tm_players.csv.gz"          # downloaded by `scout-finder fetch`, not committed
VALUES_CSV = DATA_DIR / "pl_values_2025-26.csv"           # Transfermarkt value matched to each Premier League player

MIN_MINUTES = 900                   # about ten full games: enough to trust per-90 numbers
VALUE_DATE = "June 2026"            # when the Transfermarkt values were taken (end of the dataset)
AGE_ON = "2026-09-01"               # ages are given at the start of the 2026/27 season


@dataclass(frozen=True)
class Metric:
    key: str
    label: str
    group: str
    higher_is_better: bool = True
    adjust: str | None = None       # "on_ball" or "off_ball": scaled for team possession (see features.py)


# Every metric is per 90 minutes unless the label says %.
METRICS = [
    Metric("npg", "Non-penalty goals", "Scoring"),
    Metric("xg", "Expected goals", "Scoring"),
    Metric("shots", "Shots", "Scoring"),
    Metric("box_touches", "Touches in the opposition box", "Scoring"),
    Metric("assists", "Assists", "Creating"),
    Metric("xa", "Expected assists", "Creating"),
    Metric("chances", "Chances created", "Creating"),
    Metric("through_balls", "Through balls", "Creating"),
    Metric("crosses", "Successful open-play crosses", "Creating"),
    Metric("passes", "Passes", "Passing", adjust="on_ball"),
    Metric("pass_pct", "Pass completion %", "Passing"),
    Metric("opp_half_passes", "Passes completed in the opposition half", "Passing", adjust="on_ball"),
    Metric("long_passes", "Long passes completed", "Passing", adjust="on_ball"),
    Metric("forward_passes", "Forward passes", "Passing", adjust="on_ball"),
    Metric("dribbles", "Successful dribbles", "Carrying"),
    Metric("dribble_pct", "Dribble success %", "Carrying"),
    Metric("touches", "Touches", "Carrying", adjust="on_ball"),
    Metric("losses", "Possession lost", "Carrying", higher_is_better=False, adjust="on_ball"),
    Metric("fouls_won", "Fouls won", "Carrying"),
    Metric("tackles_won", "Tackles won", "Defending", adjust="off_ball"),
    Metric("interceptions", "Interceptions", "Defending", adjust="off_ball"),
    Metric("recoveries", "Ball recoveries", "Defending", adjust="off_ball"),
    Metric("blocks", "Blocks", "Defending", adjust="off_ball"),
    Metric("clearances", "Clearances", "Defending", adjust="off_ball"),
    Metric("duel_pct", "Duels won %", "Defending"),
    Metric("aerials_won", "Aerial duels won", "Defending"),
    Metric("aerial_pct", "Aerial duels won %", "Defending"),
]
METRIC_BY_KEY = {m.key: m for m in METRICS}
GROUPS = ["Scoring", "Creating", "Passing", "Carrying", "Defending"]
POSITIONS = ["Defender", "Midfielder", "Forward"]
