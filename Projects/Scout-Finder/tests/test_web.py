"""The web version carries the same players and percentiles the command line uses."""
from scout_finder.config import METRICS, SEASONS
from scout_finder.web import page_data


def test_page_has_every_season_and_all_metrics():
    d = page_data()
    assert {str(s) for s in SEASONS} <= set(d["seasons"])            # plus "top5" when that data is present
    assert len(d["metrics"]) == len(METRICS)
    for s in d["seasons"].values():
        assert s["players"] and all(len(r[-1]) == len(METRICS) for r in s["players"])


def test_page_shows_clubs_now():
    rows = {r[1]: r for r in page_data()["seasons"]["2025"]["players"]}
    rodri, nico = rows["Rodri"], rows["Nico González"]
    assert rodri[3] == "Barcelona" and rodri[4] is False
    assert nico[3] == "Newcastle" and nico[4] is True
