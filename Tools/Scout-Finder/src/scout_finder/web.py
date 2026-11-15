"""Builds the web version: one self-contained index.html with both seasons' percentiles baked in.

The page does the same search as `find` (same match %, filters, shared strengths and biggest difference),
just in the browser, so it can be hosted on GitHub Pages with no server.
"""
import json
from datetime import date
from pathlib import Path

import pandas as pd

from .config import GROUPS, LEAGUES, METRICS, MIN_MINUTES, PROJECT_DIR, SEASONS, TOP5_CSV, TOP5_LABELS, TOP5_VALUES_CSV, VALUE_DATE
from .data import load_players, min_minutes, season_label

TEMPLATE = Path(__file__).with_name("page_template.html")
OUTPUT = PROJECT_DIR / "index.html"


def _num(v, digits: int = 1):
    return None if pd.isna(v) else round(float(v), digits)


def _rows(d: pd.DataFrame, league: str | None = None) -> list:
    rows = []
    for _, r in d.iterrows():
        rows.append([
            int(r.pl_id), r["name"], r.team, r.club_now if isinstance(r.club_now, str) else r.team,
            bool(r.in_pl_now), r.move if isinstance(r.move, str) else "", r.position,
            _num(r.age), None if pd.isna(r.market_value_eur) else int(r.market_value_eur), int(r.timePlayed),
            league or r.league,
            [None if pd.isna(r["p_" + m.key]) else int(round(r["p_" + m.key])) for m in METRICS],
        ])
    return rows


def page_data() -> dict:
    seasons = {}
    for s in SEASONS:
        seasons[str(s)] = {"label": season_label(s), "minMinutes": min_minutes(s),
                           "players": _rows(load_players(s), "Premier League")}
    if TOP5_CSV.exists() and TOP5_VALUES_CSV.exists():      # the top-five-leagues mode, when its data has been fetched
        from .top5 import load_top5
        seasons["top5"] = {"label": "2025/26", "minMinutes": MIN_MINUTES, "players": _rows(load_top5()),
                           "labels": TOP5_LABELS}
    return {
        "fields": ["id", "name", "team", "club", "inPL", "move", "pos", "age", "value", "mins", "league", "p"],
        "leagues": list(LEAGUES.values()),
        "metrics": [{"key": m.key, "label": m.label, "group": m.group} for m in METRICS],
        "groups": GROUPS,
        "seasons": seasons,
        "valueDate": VALUE_DATE,
        "built": date.today().strftime("%d %B %Y").lstrip("0"),
    }


def build_page(output: Path = OUTPUT) -> Path:
    html = TEMPLATE.read_text(encoding="utf-8")
    payload = json.dumps(page_data(), ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    output.write_text(html.replace("/*__DATA__*/null", payload), encoding="utf-8")
    return output
