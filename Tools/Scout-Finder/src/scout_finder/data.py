"""Loading the data, matching Transfermarkt values to players, and downloading fresh copies."""
import time

import pandas as pd

from .config import (AGE_ON, CURRENT_SEASON, IN_PROGRESS_SHARE, MIN_MINUTES, POSITIONS, POSSESSION_CSV, SEASON,
                     SEASONS, SQUADS_CSV, TRANSFERMARKT_GZ, TRANSFERS_CSV, players_csv, values_csv)
from .features import add_percentiles, adjust_for_possession, build_metrics
from .similarity import normalise
from .transfers import SHORT_NAMES, current_clubs

PL_API = "https://sdp-prem-prod.premier-league-prod.pulselive.com/api/"
PL_HEADERS = {"Origin": "https://www.premierleague.com", "Referer": "https://www.premierleague.com/",
              "User-Agent": "Mozilla/5.0 (Scout Finder)"}
TRANSFERMARKT_URL = "https://pub-e682421888d945d684bcae8890b0ec20.r2.dev/data/players.csv.gz"
RAW_FIELDS = ("appearances,starts,timePlayed,goals,penaltyGoals,goalAssists,expectedGoals,expectedAssists,totalShots,"
              "shotsOnTargetIncGoals,headedGoals,totalTouchesInOppositionBox,keyPassesAttemptAssists,throughBalls,"
              "totalPasses,totalUnsuccessfulPassesExclCrossesAndCorners,successfulPassesOppositionHalf,"
              "successfulShortPasses,successfulLongPasses,unsuccessfulLongPasses,forwardPasses,backwardPasses,"
              "successfulCrossesOpenPlay,unsuccessfulCrossesOpenPlay,touches,successfulDribbles,unsuccessfulDribbles,"
              "timesTackled,totalLossesOfPossession,totalFoulsWon,offsides,tacklesWon,totalTackles,interceptions,"
              "recoveries,blocks,totalClearances,duelsWon,duelsLost,aerialDuelsWon,aerialDuelsLost,groundDuelsWon,"
              "groundDuelsLost,totalFoulsConceded,yellowCards").split(",")


# ---------- loading ----------

def season_label(season: int) -> str:
    return f"{season}/{str(season + 1)[-2:]}"


def possession(season: int) -> pd.DataFrame:
    p = pd.read_csv(POSSESSION_CSV)
    return p[p.season == season]


def min_minutes(season: int) -> int:
    """900 for a finished season; 40% of the minutes played so far for the season in progress."""
    games = possession(season).games.median()
    if pd.isna(games) or games >= 38:
        return MIN_MINUTES
    return int(min(MIN_MINUTES, max(270, round(IN_PROGRESS_SHARE * games * 90 / 10) * 10)))


def load_players(season: int = SEASON) -> pd.DataFrame:
    """Every outfield player of the season with metrics, percentiles, age, market value and his club now."""
    raw = pd.read_csv(players_csv(season))
    raw["team"] = raw.team.map(lambda t: SHORT_NAMES.get(t, t))
    raw = raw[raw.position.isin(POSITIONS) & (raw.timePlayed > 0)].reset_index(drop=True)
    d = build_metrics(raw)
    d = adjust_for_possession(d, possession(season))
    d = add_percentiles(d, min_minutes(season))
    d["season"] = season
    born = pd.to_datetime(d.birth_date, errors="coerce")
    d["age"] = ((pd.Timestamp(AGE_ON) - born).dt.days / 365.25).round(1)
    if values_csv(season).exists():
        values = pd.read_csv(values_csv(season))
        d = d.merge(values[["pl_id", "market_value_eur", "contract_until", "tm_url"]], on="pl_id", how="left")
    else:
        d["market_value_eur"] = pd.NA
        d["contract_until"] = pd.NA
        d["tm_url"] = pd.NA
    if SQUADS_CSV.exists() and TRANSFERS_CSV.exists():
        now = current_clubs(d, pd.read_csv(SQUADS_CSV), pd.read_csv(TRANSFERS_CSV))
        d = d.merge(now, on="pl_id", how="left")
    else:
        d["club_now"], d["in_pl_now"], d["move"] = d.team, True, ""
    return d


# ---------- matching Transfermarkt values ----------

def surname(name: str) -> str:
    return normalise(name).split()[-1] if name.strip() else ""


def similar_spelling(a: str, b: str) -> bool:
    """'Yarmoliuk' and 'Yarmolyuk': the same surname transliterated differently."""
    from difflib import SequenceMatcher
    return len(a) >= 4 and len(b) >= 4 and SequenceMatcher(None, a, b).ratio() >= 0.8


def match_values(pl: pd.DataFrame, tm: pd.DataFrame) -> pd.DataFrame:
    """Find each Premier League player in the Transfermarkt data.

    1. Same date of birth and shared name words, most shared words first, so twins (same birthday,
       same surname, e.g. Jurriën and Quinten Timber) are told apart. "Rodri" = "Rodrigo Hernández".
    2. Same date of birth and a surname spelled almost the same ("Yarmoliuk" / "Yarmolyuk").
    3. Same date of birth and only one Transfermarkt player born that day.
    4. Birth dates one day apart (a time-zone slip in one source) and at least two shared name words.
    Name alone is never enough: there are too many players called Rodrigo.
    """
    tm = tm.copy()
    tm["dob"] = pd.to_datetime(tm.date_of_birth, errors="coerce").dt.strftime("%Y-%m-%d")
    tm["words"] = (tm["name"].fillna("") + " " + tm.get("first_name", "").fillna("") + " " + tm.get("last_name", "").fillna("")).map(lambda s: set(normalise(s).split()))
    by_dob = {k: g for k, g in tm.dropna(subset=["dob"]).groupby("dob")}
    rows = []
    for _, p in pl.iterrows():
        cands = by_dob.get(str(p.birth_date)[:10])
        if cands is None:
            near = _one_day_out(p, by_dob)
            if near is not None:
                rows.append(_row(p, near, "name + birth date 1 day out"))
            continue
        words = set(normalise(p["name"]).split())
        overlap = cands.words.map(lambda w: len(w & words))
        named = cands[overlap > 0].assign(overlap=overlap[overlap > 0])
        spelled = cands[cands["name"].map(lambda n: similar_spelling(surname(n), surname(p["name"])))]
        if len(named) >= 1:   # most shared name words first, so twins (same birthday, same surname) don't swap
            hit, how = named.sort_values(["overlap", "last_season"], ascending=False).iloc[0], "birth date + name"
        elif len(spelled) == 1:
            hit, how = spelled.iloc[0], "birth date + similar spelling"
        elif len(cands) == 1:
            hit, how = cands.iloc[0], "birth date only"
        else:
            near = _one_day_out(p, by_dob)
            if near is not None:
                rows.append(_row(p, near, "name + birth date 1 day out"))
            continue
        rows.append(_row(p, hit, how))
    return pd.DataFrame(rows)


def _row(p, hit, how):
    until = str(hit.contract_expiration_date)[:10]
    return {"pl_id": p.pl_id, "pl_name": p["name"], "tm_player_id": hit.player_id, "tm_name": hit["name"],
            "market_value_eur": hit.market_value_in_eur, "contract_until": "" if until in ("nan", "NaT", "None") else until,
            "tm_url": hit.url, "matched_by": how}


def _one_day_out(p, by_dob):
    born = pd.to_datetime(str(p.birth_date)[:10], errors="coerce")
    if pd.isna(born):
        return None
    words = set(normalise(p["name"]).split())
    for shift in (-1, 1):
        cands = by_dob.get((born + pd.Timedelta(days=shift)).strftime("%Y-%m-%d"))
        if cands is None:
            continue
        good = cands[cands.words.map(lambda w: len(w & words) >= 2)]
        if len(good) == 1:
            return good.iloc[0]
    return None


def build_values_file(season: int = SEASON) -> pd.DataFrame:
    """Match the downloaded Transfermarkt file to one season's players and save the small result."""
    if not TRANSFERMARKT_GZ.exists():
        raise FileNotFoundError(f"{TRANSFERMARKT_GZ} not found. Run `scout-finder fetch --values` first.")
    pl = pd.read_csv(players_csv(season))
    pl = pl[pl.position.isin(POSITIONS)]
    values = match_values(pl, pd.read_csv(TRANSFERMARKT_GZ))
    values.to_csv(values_csv(season), index=False)
    return values


# ---------- downloading ----------

def _get(session, path):
    for attempt in range(5):
        try:
            r = session.get(PL_API + path, headers=PL_HEADERS, timeout=30)
            if r.status_code == 404:
                return None
            if r.ok:
                return r.json() if r.text else None
        except Exception:
            pass
        time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"could not fetch {path}")


def fetch_pl_season(season: int = SEASON) -> pd.DataFrame:
    """Download every outfield player's season totals from the official Premier League stats API."""
    import requests
    s = requests.Session()
    rows = []
    for tm in _get(s, f"v1/competitions/8/seasons/{season}/teams?_limit=60")["data"]:
        squad = _get(s, f"v1/competitions/8/seasons/{season}/teams/{tm['id']}/squad") or []
        for p in squad:
            if p.get("position") not in POSITIONS:
                continue
            stats = (_get(s, f"v2/competitions/8/seasons/{season}/players/{p['id']['playerId']}/stats") or {}).get("stats") or {}
            if not stats.get("timePlayed"):
                continue
            rows.append({"season": season, "pl_id": int(p["id"]["playerId"]), "name": p["name"]["display"],
                         "team": tm["shortName"], "position": p["position"], "birth_date": (p.get("dates") or {}).get("birth", ""),
                         "nationality": (p.get("country") or {}).get("country", ""), "height": p.get("height", ""),
                         **{f: stats.get(f) or 0 for f in RAW_FIELDS}})
        print(f"  {tm['shortName']}: {sum(r['team'] == tm['shortName'] for r in rows)} players")
    d = pd.DataFrame(rows).sort_values(["team", "name"])
    d.to_csv(players_csv(season), index=False)
    return d


def download_transfermarkt() -> None:
    """Download the Transfermarkt players file (dcaribou/transfermarkt-datasets), about 5 MB."""
    import requests
    r = requests.get(TRANSFERMARKT_URL, timeout=120)
    r.raise_for_status()
    TRANSFERMARKT_GZ.write_bytes(r.content)
