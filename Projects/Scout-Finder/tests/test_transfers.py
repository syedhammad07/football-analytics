import pandas as pd

from scout_finder.transfers import current_clubs, short_club

TRANSFERS = pd.DataFrame([
    {"kind": "transfer", "date": "18 August 2026", "end": "", "player": "Rodri", "from_club": "Manchester City", "to_club": "Barcelona", "fee": "£65m"},
    {"kind": "transfer", "date": "26 August 2026", "end": "", "player": "Nico González", "from_club": "Manchester City", "to_club": "Newcastle United", "fee": "£52m"},
    {"kind": "loan", "date": "1 July 2026", "end": "30 June 2027", "player": "Álex Jiménez", "from_club": "AFC Bournemouth", "to_club": "Fiorentina", "fee": ""},
    {"kind": "transfer", "date": "1 July 2026", "end": "", "player": "Rodrigo Bentancur", "from_club": "Tottenham Hotspur", "to_club": "Juventus", "fee": "£20m"},
])
SQUADS = pd.DataFrame([{"pl_id": 1, "team": "Man City"},          # stale: Rodri still listed after leaving
                       {"pl_id": 2, "team": "Newcastle"}, {"pl_id": 5, "team": "Spurs"}, {"pl_id": 6, "team": "Arsenal"}])
PLAYERS = pd.DataFrame([{"pl_id": 1, "name": "Rodri", "team": "Man City"},
                        {"pl_id": 2, "name": "Nico González", "team": "Man City"},
                        {"pl_id": 3, "name": "Álex Jiménez", "team": "Bournemouth"},
                        {"pl_id": 4, "name": "Jarrod Bowen", "team": "West Ham"},
                        {"pl_id": 5, "name": "Pedro Porro", "team": "Spurs"},
                        {"pl_id": 6, "name": "Declan Rice", "team": "Arsenal"}])


def now():
    return current_clubs(PLAYERS, SQUADS, TRANSFERS).set_index("pl_id")


def test_club_names_are_shortened():
    assert short_club("Newcastle United") == "Newcastle"
    assert short_club("Barcelona") == "Barcelona"


def test_recorded_move_beats_a_stale_squad_list():
    r = now().loc[1]
    assert r.club_now == "Barcelona" and not r.in_pl_now and "£65m" in r.move


def test_move_within_the_league():
    r = now().loc[2]
    assert r.club_now == "Newcastle" and r.in_pl_now


def test_loan_abroad():
    r = now().loc[3]
    assert r.club_now == "Fiorentina" and not r.in_pl_now and r.move.startswith("on loan to")


def test_relegated_club():
    r = now().loc[4]
    assert r.club_now == "West Ham" and not r.in_pl_now and r.move == "relegated with West Ham"


def test_a_namesake_at_the_same_club_does_not_count():
    # "Rodrigo Bentancur" left Spurs, but Pedro Porro shares no name with him
    assert now().loc[5].club_now == "Spurs"


def test_unmoved_player_keeps_his_club():
    r = now().loc[6]
    assert r.club_now == "Arsenal" and r.in_pl_now and r.move == ""
