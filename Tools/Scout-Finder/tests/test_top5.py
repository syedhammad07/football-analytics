"""Europe's top five leagues: club names, possession estimate, Transfermarkt matching and summer moves."""
import pandas as pd
import pytest

from scout_finder.config import TOP5_CSV, TOP5_VALUES_CSV
from scout_finder.top5 import (PROMOTED, RELEGATED, canon, clubs_in_top5_now, follow_moves, match_top5_values,
                               team_possession)


def test_one_spelling_per_club():
    assert canon("Wolverhampton Wanderers") == canon("Wolverhampton") == "Wolves"
    assert canon("Bayern München") == canon("Bayern Munich") == "Bayern Munich"
    assert canon("Betis") == "Real Betis"
    assert canon("Paris FC") == "Paris FC" != canon("Paris Saint-Germain")      # two different clubs
    assert canon("Trabzonspor") == "Trabzonspor"                                 # outside these leagues: unchanged


def test_possession_estimate_follows_passes():
    raw = pd.DataFrame({"league": ["L"] * 3, "team": ["Pass", "Even", "Long"],
                        "totalPasses": [6000, 4500, 3000], "minutesPlayed": [9000] * 3})
    p = team_possession(raw).set_index("team").possession
    assert p["Pass"] > 50 > p["Long"] and p["Pass"] > p["Even"] > p["Long"]


def test_relegated_clubs_leave_and_promoted_join():
    now = clubs_in_top5_now({"Arsenal": "Premier League", "Burnley": "Premier League"})
    assert "Arsenal" in now and "Burnley" not in now and now["Coventry City"] == "Premier League"
    assert not RELEGATED & set(PROMOTED)


def moves(*rows):
    t = pd.DataFrame(rows, columns=["kind", "player", "from_c", "to_c", "date", "fee"])
    t["when"] = pd.to_datetime(t.date, errors="coerce", dayfirst=True)
    by_club = {}
    for m in t.itertuples():
        by_club.setdefault(m.from_c, []).append(m)
    return by_club


def test_follow_moves_chains_a_loan_return_and_a_sale():
    by_club = moves(("return", "Ana Player", "Loan FC", "Parent FC", "", ""),
                    ("transfer", "Ana Player", "Parent FC", "New FC", "1 August 2026", "£10m"))
    assert follow_moves("Ana Player", "Loan FC", by_club) == ("New FC", "joined New FC (Aug 2026, £10m)")
    assert follow_moves("Someone Else", "Loan FC", by_club) == ("Loan FC", "")


def test_follow_moves_stops_on_a_loop():
    by_club = moves(("loan", "Ana Player", "A", "B", "", ""), ("return", "Ana Player", "B", "A", "", ""))
    assert follow_moves("Ana Player", "A", by_club)[0] == "B"


def tm(*rows):
    cols = ["player_id", "name", "last_season", "current_club_name", "current_club_domestic_competition_id",
            "position", "sub_position", "date_of_birth", "market_value_in_eur"]
    return pd.DataFrame(rows, columns=cols)


def test_namesakes_are_settled_by_club():
    raw = pd.DataFrame({"player_id": [1, 2], "player": ["Vitinha", "Vitinha"], "team": ["Paris Saint-Germain", "Genoa"],
                        "minutesPlayed": [2000, 2000]})
    t = tm((10, "Vitinha", 2025, "Paris Saint-Germain Football Club", "FR1", "Midfield", "Central Midfield", "2000-02-13", 9e7),
           (11, "Vitinha", 2025, "Genoa Cricket and Football Club", "IT1", "Attack", "Centre-Forward", "2000-03-15", 1e7))
    v = match_top5_values(raw, t).set_index("pl_id")
    assert v.loc[1, "tm_player_id"] == 10 and v.loc[1, "position"] == "Midfielder"
    assert v.loc[2, "tm_player_id"] == 11 and v.loc[2, "position"] == "Forward"


def test_short_names_match_at_the_same_club_only():
    raw = pd.DataFrame({"player_id": [1], "player": ["Javier Guerra"], "team": ["Valencia"], "minutesPlayed": [2000]})
    t = tm((10, "Javi Guerra", 2025, "Valencia CF", "ES1", "Midfield", "Central Midfield", "2003-05-13", 2e7),
           (11, "Javier Guerra", 2025, "Club Atlético Somewhere", "AR1", "Attack", "Centre-Forward", "1990-01-01", 5e4))
    assert match_top5_values(raw, t).iloc[0].tm_player_id == 10


@pytest.mark.skipif(not (TOP5_CSV.exists() and TOP5_VALUES_CSV.exists()), reason="top-five-leagues data not downloaded")
def test_real_data_loads_with_current_clubs():
    from scout_finder.similarity import find_player
    from scout_finder.top5 import load_top5
    d = load_top5()
    assert set(d.league) == {"Premier League", "La Liga", "Serie A", "Bundesliga", "Ligue 1"}
    rodri = find_player(d, "Rodri")
    assert rodri.club_now == "Barcelona" and bool(rodri.in_pl_now)
