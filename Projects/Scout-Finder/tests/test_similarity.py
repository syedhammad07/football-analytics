import numpy as np
import pandas as pd
import pytest

from scout_finder.similarity import PCT_COLS, find_player, find_similar, normalise, similarity


def player(pid, name, pcts, team="A", position="Midfielder", age=25, value=10e6, minutes=2000):
    row = {"pl_id": pid, "name": name, "team": team, "position": position, "age": age,
           "market_value_eur": value, "timePlayed": minutes}
    row.update({c: p for c, p in zip(PCT_COLS, pcts)})
    return row


def frame(*rows):
    return pd.DataFrame(list(rows))


FLAT50 = [50] * len(PCT_COLS)
FLAT80 = [80] * len(PCT_COLS)


def test_identical_players_match_100():
    d = frame(player(1, "A", FLAT50), player(2, "B", FLAT50))
    assert similarity(d.iloc[0], d.iloc[1]) == pytest.approx(100)


def test_similarity_is_symmetric_and_drops_with_distance():
    d = frame(player(1, "A", FLAT50), player(2, "B", FLAT80))
    assert similarity(d.iloc[0], d.iloc[1]) == pytest.approx(70)
    assert similarity(d.iloc[1], d.iloc[0]) == pytest.approx(70)


def test_missing_metrics_are_ignored():
    a = list(FLAT50); a[0] = np.nan
    d = frame(player(1, "A", a), player(2, "B", FLAT50))
    assert similarity(d.iloc[0], d.iloc[1]) == pytest.approx(100)


def test_find_similar_ranks_and_filters():
    d = frame(player(1, "Target", FLAT80),
              player(2, "Close", [78] * len(PCT_COLS), value=5e6),
              player(3, "Far", FLAT50, value=5e6),
              player(4, "Too expensive", FLAT80, value=90e6),
              player(5, "Too old", FLAT80, age=33),
              player(6, "Defender", FLAT80, position="Defender"))
    out = find_similar(d, d.iloc[0], max_age=30, max_value_m=20)
    assert out["name"].tolist() == ["Close", "Far"]


def test_normalise_handles_accents():
    assert normalise("Martin Ødegaard") == "martin odegaard"
    assert normalise("Enzo Fernández") == "enzo fernandez"


def test_find_player_by_part_of_name():
    d = frame(player(1, "Martin Ødegaard", FLAT50), player(2, "Declan Rice", FLAT50))
    assert find_player(d, "odegaard")["name"] == "Martin Ødegaard"
    with pytest.raises(LookupError):
        find_player(d, "Messi")


def test_whole_word_beats_part_of_a_name():
    d = frame(player(1, "Bukayo Saka", FLAT50), player(2, "Aaron Wan-Bissaka", FLAT50))
    assert find_player(d, "Saka")["name"] == "Bukayo Saka"
    assert find_player(d, "bissaka")["name"] == "Aaron Wan-Bissaka"
