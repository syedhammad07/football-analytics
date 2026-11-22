import numpy as np
import pandas as pd
import pytest

from scout_finder.features import add_percentiles, per90, possession_factor, share


def test_per90():
    assert per90(pd.Series([10]), pd.Series([900])).iloc[0] == pytest.approx(1.0)


def test_share_blanks_small_samples():
    out = share(pd.Series([5, 10]), pd.Series([10, 20]), min_attempts=15)
    assert np.isnan(out.iloc[0]) and out.iloc[1] == pytest.approx(50)


def test_possession_factor_is_neutral_at_50():
    p = pd.Series([50.0])
    assert possession_factor(p, "on_ball").iloc[0] == pytest.approx(1)
    assert possession_factor(p, "off_ball").iloc[0] == pytest.approx(1)


def test_possession_factor_scales_the_right_way():
    p = pd.Series([66.0])
    assert possession_factor(p, "on_ball").iloc[0] < 1      # possession teams' passing is scaled down
    assert possession_factor(p, "off_ball").iloc[0] > 1     # and their defending scaled up


def _toy(values, position="Midfielder", minutes=1000):
    n = len(values)
    d = pd.DataFrame({"position": [position] * n, "timePlayed": [minutes] * n})
    from scout_finder.config import METRICS
    for m in METRICS:
        d[m.key] = values
    return d


def test_percentiles_rank_within_position():
    d = pd.concat([_toy([1, 2, 3, 4]), _toy([10, 20, 30, 40], position="Defender")], ignore_index=True)
    out = add_percentiles(d)
    mids = out[out.position == "Midfielder"].p_tackles_won.tolist()
    defs = out[out.position == "Defender"].p_tackles_won.tolist()
    assert mids == defs                      # same rank inside each position, whatever the raw scale
    assert mids == sorted(mids)


def test_lower_is_better_metric_is_reversed():
    out = add_percentiles(_toy([1, 2, 3, 4]))
    assert out.p_losses.iloc[0] > out.p_losses.iloc[-1]    # losing the ball least = highest percentile


def test_players_below_minutes_bar_do_not_set_the_scale():
    d = _toy([1, 2, 3, 100])
    d.loc[3, "timePlayed"] = 100             # the 100 comes from a tiny sample
    out = add_percentiles(d)
    assert out.p_tackles_won.iloc[2] < 100   # so the 3 is not pushed down by it
    assert out.p_tackles_won.iloc[3] == 100
