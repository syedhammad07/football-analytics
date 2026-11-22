"""Settings shared by the whole package: where the data lives, who counts, and which stats describe a player."""
from dataclasses import dataclass
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_DIR / "data"

SEASON = 2025                       # default season to search: 2025 = 2025/26, the last complete one
CURRENT_SEASON = 2026               # 2026/27, being played now
SEASONS = {2025: "2025-26", 2026: "2026-27"}
POSSESSION_CSV = DATA_DIR / "pl_team_possession.csv"      # every team's possession, both seasons
SQUADS_CSV = DATA_DIR / "pl_squads_2026-27.csv"           # who is in each Premier League squad now
TRANSFERS_CSV = DATA_DIR / "transfers_summer_2026.csv"    # every summer 2026 transfer and loan in English football
TRANSFERMARKT_GZ = DATA_DIR / "tm_players.csv.gz"          # downloaded by `scout-finder fetch`, not committed

# Europe's top five leagues, 2025/26 (see top5.py)
TOP5_SEASON = 2526
TOP5_URL = "https://raw.githubusercontent.com/m-mahadi/top5-football-dataset/master/data/clean/sofascore_player_seasons.csv"
TOP5_CSV = DATA_DIR / "top5_players_2025-26.csv"           # downloaded by `scout-finder fetch --top5`, not committed
TOP5_VALUES_CSV = DATA_DIR / "top5_values_2025-26.csv"     # Transfermarkt position, birth date and value per player
TOP5_NOW_CSV = DATA_DIR / "top5_clubs_now.csv"             # each player's club after the summer 2026 window
EUROPE_TRANSFERS_CSV = DATA_DIR / "transfers_summer_2026_europe.csv"   # Spanish, Italian, German and French moves
LEAGUES = {"ENG-Premier League": "Premier League", "ESP-La Liga": "La Liga", "ITA-Serie A": "Serie A",
           "GER-Bundesliga": "Bundesliga", "FRA-Ligue 1": "Ligue 1"}

MIN_MINUTES = 900                   # about ten full games: enough to trust per-90 numbers
IN_PROGRESS_SHARE = 0.4             # for a season still being played: 40% of the minutes so far


def players_csv(season: int) -> Path:
    return DATA_DIR / f"pl_players_{SEASONS[season]}.csv"


def values_csv(season: int) -> Path:
    """Transfermarkt value matched to each Premier League player of that season."""
    return DATA_DIR / f"pl_values_{SEASONS[season]}.csv"
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
# The top-five-leagues source doesn't publish three of these, so that mode uses the closest stat it has.
TOP5_LABELS = {"box_touches": "Shots inside the box", "through_balls": "Big chances created",
               "forward_passes": "Passes completed in the final third"}
GROUPS = ["Scoring", "Creating", "Passing", "Carrying", "Defending"]
POSITIONS = ["Defender", "Midfielder", "Forward"]
