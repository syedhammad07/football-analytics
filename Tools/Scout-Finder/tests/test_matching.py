import pandas as pd

from scout_finder.data import match_values


def test_matches_on_birth_date_and_a_shared_name_word():
    pl = pd.DataFrame([{"pl_id": 1, "name": "Rodri", "birth_date": "1996-06-22"}])
    tm = pd.DataFrame([
        {"player_id": 10, "name": "Rodri", "first_name": "Rodrigo", "last_name": "Hernández", "date_of_birth": "1996-06-22 00:00:00",
         "last_season": 2025, "market_value_in_eur": 65e6, "contract_expiration_date": "2027-06-30", "url": "u1"},
        {"player_id": 11, "name": "Rodrigo", "first_name": "Rodrigo", "last_name": "Other", "date_of_birth": "1999-01-01 00:00:00",
         "last_season": 2025, "market_value_in_eur": 1e6, "contract_expiration_date": "2027-06-30", "url": "u2"},
    ])
    out = match_values(pl, tm)
    assert out.tm_player_id.tolist() == [10]
    assert out.matched_by.iloc[0] == "birth date + name"


def test_name_alone_is_not_enough():
    pl = pd.DataFrame([{"pl_id": 1, "name": "Rodrigo", "birth_date": "2001-05-05"}])
    tm = pd.DataFrame([{"player_id": 11, "name": "Rodrigo", "first_name": "Rodrigo", "last_name": "X", "date_of_birth": "1999-01-01",
                        "last_season": 2025, "market_value_in_eur": 1e6, "contract_expiration_date": "", "url": ""}])
    assert match_values(pl, tm).empty


def _tm(pid, name, dob, first="", last=""):
    return {"player_id": pid, "name": name, "first_name": first, "last_name": last, "date_of_birth": dob,
            "last_season": 2025, "market_value_in_eur": 1e6, "contract_expiration_date": "", "url": ""}


def test_twins_are_not_swapped():
    pl = pd.DataFrame([{"pl_id": 1, "name": "Jurriën Timber", "birth_date": "2001-06-17"}])
    tm = pd.DataFrame([_tm(10, "Quinten Timber", "2001-06-17"), _tm(11, "Jurriën Timber", "2001-06-17")])
    assert match_values(pl, tm).tm_player_id.tolist() == [11]


def test_different_spelling_same_birthday():
    pl = pd.DataFrame([{"pl_id": 1, "name": "Yehor Yarmoliuk", "birth_date": "2004-03-01"}])
    tm = pd.DataFrame([_tm(10, "Yegor Yarmolyuk", "2004-03-01"), _tm(11, "Someone Else", "2004-03-01")])
    out = match_values(pl, tm)
    assert out.tm_player_id.tolist() == [10] and out.matched_by.iloc[0] == "birth date + similar spelling"


def test_birth_date_one_day_out_needs_two_name_words():
    pl = pd.DataFrame([{"pl_id": 1, "name": "El Hadji Malick Diouf", "birth_date": "2004-12-29"},
                       {"pl_id": 2, "name": "Andy Diouf", "birth_date": "2003-05-18"}])
    tm = pd.DataFrame([_tm(10, "El Hadji Malick Diouf", "2004-12-28"), _tm(11, "Oumar Diouf", "2003-05-17")])
    out = match_values(pl, tm)
    assert out.tm_player_id.tolist() == [10]          # Andy is not matched to Oumar on surname alone


def test_one_day_out_still_works_when_someone_else_shares_the_recorded_birthday():
    pl = pd.DataFrame([{"pl_id": 1, "name": "El Hadji Malick Diouf", "birth_date": "2004-12-29"}])
    tm = pd.DataFrame([_tm(10, "El Hadji Malick Diouf", "2004-12-28"), _tm(11, "Other Player", "2004-12-29"),
                       _tm(12, "Another Player", "2004-12-29")])
    assert match_values(pl, tm).tm_player_id.tolist() == [10]
