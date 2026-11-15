"""Europe's top five leagues (Premier League, La Liga, Serie A, Bundesliga, Ligue 1), 2025/26.

The Premier League's own stats API only covers England, so this mode uses one source for all five leagues:
SofaScore season totals from the open m-mahadi/top5-football-dataset. Players are compared the same way as in
the Premier League mode (per 90, possession-adjusted, percentiles by position), on 27 stats. Three stats the
source doesn't publish are swapped for the closest thing it does (see config.TOP5_LABELS).

Position, date of birth and market value come from Transfermarkt, matched by name and club.
"""
import pandas as pd

from .config import (AGE_ON, EUROPE_TRANSFERS_CSV, LEAGUES, METRICS, MIN_MINUTES, TOP5_CSV, TOP5_NOW_CSV, TOP5_SEASON,
                     TOP5_URL, TOP5_VALUES_CSV, TRANSFERMARKT_GZ, TRANSFERS_CSV)
from .features import add_percentiles, per90, possession_factor, share
from .similarity import normalise
from .transfers import _names_match

TM_POSITIONS = {"Defender": "Defender", "Midfield": "Midfielder", "Attack": "Forward"}
TM_TOP5 = {"GB1", "ES1", "IT1", "L1", "FR1"}
CLUB_NOISE = {"fc", "cf", "ac", "as", "sc", "ssc", "afc", "ud", "cd", "rc", "rcd", "sv", "vfl", "vfb", "tsg", "fsv", "us",
              "ss", "bc", "club", "football", "futbol", "de", "calcio", "1", "04", "05", "1899", "1846", "sad", "olympique",
              "stade", "real", "sporting", "association", "societa", "sportiva", "balompie", "the", "und", "e", "s", "p", "a"}
RAW_COLUMNS = ["league", "player_id", "player", "team", "minutesPlayed", "appearances", "goals", "penaltyGoals",
               "expectedGoals", "totalShots", "shotsFromInsideTheBox", "assists", "expectedAssists", "keyPasses",
               "bigChancesCreated", "accurateCrosses", "totalPasses", "accuratePasses", "accurateOppositionHalfPasses",
               "accurateLongBalls", "accurateFinalThirdPasses", "successfulDribbles", "totalContest", "touches",
               "possessionLost", "wasFouled", "tacklesWon", "interceptions", "ballRecovery", "outfielderBlocks",
               "clearances", "totalDuelsWon", "duelLost", "aerialDuelsWon", "aerialLost"]


# ---------- raw data ----------

def load_raw() -> pd.DataFrame:
    if not TOP5_CSV.exists():
        raise FileNotFoundError(f"{TOP5_CSV} not found. Run `scout-finder fetch --top5` first.")
    d = pd.read_csv(TOP5_CSV)
    d["league"] = d.league.map(lambda x: LEAGUES.get(x, x))
    d["team"] = d.team.map(short_team)
    return d[d.minutesPlayed > 0].reset_index(drop=True)


# The source's club names -> the everyday names shown on screen
TEAM_NAMES = {
    "Brighton & Hove Albion": "Brighton", "Leeds United": "Leeds", "Liverpool FC": "Liverpool", "Newcastle United": "Newcastle",
    "Tottenham Hotspur": "Tottenham", "West Ham United": "West Ham", "Wolverhampton": "Wolves",
    "Athletic Club": "Athletic Bilbao", "Deportivo Alavés": "Alavés", "Girona FC": "Girona", "Levante UD": "Levante",
    "AS Monaco": "Monaco", "Olympique Lyonnais": "Lyon", "Olympique de Marseille": "Marseille", "RC Lens": "Lens",
    "RC Strasbourg": "Strasbourg", "Rodez AF": "Rodez", "Stade Brestois": "Brest", "Stade Rennais": "Rennes",
    "1. FSV Mainz 05": "Mainz 05", "1. Heidenheim": "Heidenheim", "1. Köln": "Köln", "1. Union Berlin": "Union Berlin",
    "Bayer 04 Leverkusen": "Bayer Leverkusen", "Bayern München": "Bayern Munich", "Borussia M'gladbach": "Gladbach",
    "SC Freiburg": "Freiburg", "SV Werder Bremen": "Werder Bremen", "TSG Hoffenheim": "Hoffenheim",
    "VfB Stuttgart": "Stuttgart", "VfL Wolfsburg": "Wolfsburg",
    "AC Milan": "Milan", "AS Roma": "Roma", "SSC Napoli": "Napoli", "Hellas Verona": "Verona",
}
# Other spellings of the same clubs (Wikipedia's transfer lists, the Premier League's short names) -> the names above
CLUB_ALIASES = {
    "wolverhampton wanderers": "Wolves", "afc bournemouth": "Bournemouth", "man city": "Manchester City",
    "man utd": "Manchester United", "nott'm forest": "Nottingham Forest", "a villa": "Aston Villa", "c palace": "Crystal Palace",
    "spurs": "Tottenham", "coventry": "Coventry City", "hull": "Hull City", "ipswich": "Ipswich Town",
    "betis": "Real Betis", "oviedo": "Real Oviedo", "athletic club": "Athletic Bilbao", "deportivo la coruna": "Deportivo A Coruña", "deportivo": "Deportivo A Coruña",
    "inter milan": "Inter", "internazionale": "Inter", "hellas verona": "Verona",
    "borussia monchengladbach": "Gladbach", "fc augsburg": "Augsburg", "1. fc koln": "Köln", "fc koln": "Köln",
    "1. fc heidenheim": "Heidenheim", "fc st. pauli": "St. Pauli", "1. fc union berlin": "Union Berlin", "mainz": "Mainz 05",
    "psg": "Paris Saint-Germain", "saint-etienne": "Saint-Étienne", "unattached": "Free agent",
}
# Clubs that changed division after 2025/26: who dropped out of these five leagues and who came up
RELEGATED = {"Burnley", "West Ham", "Wolves", "Girona", "Mallorca", "Real Oviedo", "Cremonese", "Verona", "Pisa",
             "Wolfsburg", "Heidenheim", "St. Pauli", "Metz", "Nantes", "Rodez", "Saint-Étienne"}
PROMOTED = {"Coventry City": "Premier League", "Hull City": "Premier League", "Ipswich Town": "Premier League",
            "Deportivo A Coruña": "La Liga", "Málaga": "La Liga", "Racing Santander": "La Liga",
            "Frosinone": "Serie A", "Monza": "Serie A", "Venezia": "Serie A",
            "Schalke 04": "Bundesliga", "SV Elversberg": "Bundesliga", "SC Paderborn": "Bundesliga",
            "Troyes": "Ligue 1", "Le Mans": "Ligue 1"}


def short_team(name: str) -> str:
    """The source's club name as people say it: 'Liverpool FC' -> 'Liverpool', 'Bayern München' -> 'Bayern Munich'."""
    name = str(name).strip()
    return TEAM_NAMES.get(name, name)


_BY_NORMALISED = {normalise(v): v for v in list(TEAM_NAMES.values()) + list(PROMOTED)}
_BY_NORMALISED.update({normalise(k): v for k, v in TEAM_NAMES.items()})
_BY_NORMALISED.update({normalise(k): v for k, v in CLUB_ALIASES.items()})


def canon(club: str) -> str:
    """One spelling per club, whichever source it came from. Clubs outside these leagues keep their name."""
    club = str(club).strip()
    return _BY_NORMALISED.get(normalise(club), club)


def download_top5() -> pd.DataFrame:
    """Download the SofaScore season table from m-mahadi/top5-football-dataset and keep 2025/26 and the columns used."""
    import io

    import requests
    r = requests.get(TOP5_URL, timeout=120)
    r.raise_for_status()
    d = pd.read_csv(io.BytesIO(r.content), low_memory=False)
    d = d[d.season == TOP5_SEASON][RAW_COLUMNS].sort_values(["league", "team", "player"])
    d.to_csv(TOP5_CSV, index=False)
    return d


def team_possession(raw: pd.DataFrame) -> pd.DataFrame:
    """Each team's share of the ball, estimated from passes: its passes against an average opponent's in its league.

    The source has no possession figure, and passes attempted track possession closely.
    """
    t = raw.groupby(["league", "team"], as_index=False).agg(passes=("totalPasses", "sum"), minutes=("minutesPlayed", "sum"))
    t = t[t.minutes >= t.groupby("league").minutes.transform("max") * 0.5]         # real squads only, not play-off cameos
    t["rate"] = t.passes / t.minutes
    total, n = t.groupby("league").rate.transform("sum"), t.groupby("league").rate.transform("count")
    others = (total - t.rate) / (n - 1)
    t["possession"] = (100 * t.rate / (t.rate + others)).round(1)
    return t[["league", "team", "possession"]]


def build_top5_metrics(raw: pd.DataFrame) -> pd.DataFrame:
    """The same 27 metric keys as the Premier League mode, from SofaScore's season totals."""
    d = raw.copy()
    m = d.minutesPlayed
    d["npg"] = per90(d.goals - d.penaltyGoals, m)
    d["xg"] = per90(d.expectedGoals, m)
    d["shots"] = per90(d.totalShots, m)
    d["box_touches"] = per90(d.shotsFromInsideTheBox, m)             # swapped: shots inside the box
    d["assists"] = per90(d.assists, m)
    d["xa"] = per90(d.expectedAssists, m)
    d["chances"] = per90(d.keyPasses, m)
    d["through_balls"] = per90(d.bigChancesCreated, m)                # swapped: big chances created
    d["crosses"] = per90(d.accurateCrosses, m)
    d["passes"] = per90(d.totalPasses, m)
    d["pass_pct"] = share(d.accuratePasses, d.totalPasses, 100)
    d["opp_half_passes"] = per90(d.accurateOppositionHalfPasses, m)
    d["long_passes"] = per90(d.accurateLongBalls, m)
    d["forward_passes"] = per90(d.accurateFinalThirdPasses, m)        # swapped: passes completed in the final third
    d["dribbles"] = per90(d.successfulDribbles, m)
    d["dribble_pct"] = share(d.successfulDribbles, d.totalContest, 15)
    d["touches"] = per90(d.touches, m)
    d["losses"] = per90(d.possessionLost, m)
    d["fouls_won"] = per90(d.wasFouled, m)
    d["tackles_won"] = per90(d.tacklesWon, m)
    d["interceptions"] = per90(d.interceptions, m)
    d["recoveries"] = per90(d.ballRecovery, m)
    d["blocks"] = per90(d.outfielderBlocks, m)
    d["clearances"] = per90(d.clearances, m)
    d["duel_pct"] = share(d.totalDuelsWon, d.totalDuelsWon + d.duelLost, 30)
    d["aerials_won"] = per90(d.aerialDuelsWon, m)
    d["aerial_pct"] = share(d.aerialDuelsWon, d.aerialDuelsWon + d.aerialLost, 15)
    return d


# ---------- Transfermarkt: position, date of birth, value ----------

def club_words(name: str) -> set:
    return {w for w in normalise(str(name)).replace("-", " ").replace(".", " ").replace("'", " ").split() if w not in CLUB_NOISE}


def _name_words(name: str) -> set:
    return set(normalise(str(name)).replace("-", " ").replace(".", " ").split())


def _similar(a: str, b: str, ratio: float = 0.82) -> bool:
    """'Yarmoliuk' / 'Yarmolyuk', 'Andy' / 'Andrew': the same name written a little differently."""
    from difflib import SequenceMatcher
    a, b = normalise(str(a)), normalise(str(b))
    if a.split()[-1:] == b.split()[-1:] and a[:1] == b[:1] and len(a.split()) > 1 and len(b.split()) > 1:
        return True                                              # same surname and first initial
    return SequenceMatcher(None, a, b).ratio() >= ratio


def match_top5_values(raw: pd.DataFrame, tm: pd.DataFrame) -> pd.DataFrame:
    """Find each player in the Transfermarkt data by name, using his club to settle namesakes.

    1. Exactly one Transfermarkt player with that name: him, unless he's at a club outside these leagues
       and never played in them (a namesake).
    2. Several: the one at the same club.
    3. No exact name: a player at the same club whose name contains every word of the shorter name
       ("Rodri" / "Rodrigo Hernández" is not enough; "Vitinha" / "Vitinha" at PSG is).
    Anyone still ambiguous is left without a value rather than guessed.
    """
    tm = tm[tm.last_season >= 2024].copy()
    tm["norm"] = tm["name"].map(normalise)
    tm["words"] = tm["name"].map(_name_words)
    tm["cwords"] = tm.current_club_name.map(club_words)
    tm["top5"] = tm.current_club_domestic_competition_id.isin(TM_TOP5)
    by_name = {k: g for k, g in tm.groupby("norm")}
    recent = tm[tm.last_season >= 2025]
    by_club_word: dict = {}
    for i, words in tm.cwords.items():
        for w in words:
            by_club_word.setdefault(w, []).append(i)
    rows = []
    for _, p in raw.iterrows():
        team = club_words(p.team)
        same_club = lambda c: c[c.cwords.map(lambda w: bool(w & team))]
        cands = by_name.get(normalise(p.player))
        hit, how = None, ""
        if cands is not None:
            at_club = same_club(cands)
            if len(at_club) == 1:
                hit, how = at_club.iloc[0], "name + club"
            elif len(cands) == 1 and bool(cands.iloc[0].top5):
                hit, how = cands.iloc[0], "name"
            elif len(cands[cands.top5]) == 1 and len(at_club) == 0:
                hit, how = cands[cands.top5].iloc[0], "name, only one in these leagues"
        squad, words = tm.iloc[0:0], _name_words(p.player)
        if hit is None:
            squad = tm.loc[sorted({i for w in team for i in by_club_word.get(w, [])})]
            if len(squad) and words:
                loose = squad[squad.words.map(lambda w: (words <= w or w <= words) and len(words & w) >= 1)]
                both = loose[loose.words.map(lambda w: len(w & words) >= min(2, len(words), len(w)))]
                if len(both) == 1:
                    hit, how = both.iloc[0], "club + part of name"
        if hit is None and len(squad) and words:                 # same club, name spelled a little differently
            close = squad[squad["name"].map(lambda n: _similar(n, p.player))]
            if len(close) == 1:
                hit, how = close.iloc[0], "club + similar name"
        if hit is None and cands is not None and len(cands) == 1 and cands.iloc[0].market_value_in_eur >= 1e6:
            hit, how = cands.iloc[0], "name, has since left these leagues"
        if hit is None and len(words) >= 2:                      # changed club: full name inside a longer one, anywhere
            full = recent[recent.words.map(lambda w: words <= w or (len(w) >= 2 and w <= words))]
            if len(full) == 1:
                hit, how = full.iloc[0], "full name"
            elif len(full) == 0:
                close = recent[recent["name"].map(lambda n: _similar(n, p.player, 0.9))]
                if len(close) == 1:
                    hit, how = close.iloc[0], "similar name"
        if hit is None:
            continue
        rows.append({"pl_id": int(p.player_id), "name": p.player, "tm_player_id": int(hit.player_id), "tm_name": hit["name"],
                     "position": TM_POSITIONS.get(hit.position, ""), "role": hit.sub_position if isinstance(hit.sub_position, str) else "",
                     "birth_date": str(hit.date_of_birth)[:10], "market_value_eur": hit.market_value_in_eur,
                     "tm_club": hit.current_club_name, "matched_by": how})
    out = pd.DataFrame(rows)
    # one Transfermarkt player can only be one person here: keep the match with the most minutes
    minutes = raw.set_index("player_id").minutesPlayed
    out["minutes"] = out.pl_id.map(minutes)
    out = out.sort_values("minutes", ascending=False).drop_duplicates("tm_player_id").drop(columns="minutes")
    return out.sort_values("pl_id").reset_index(drop=True)


def build_top5_values_file() -> pd.DataFrame:
    if not TRANSFERMARKT_GZ.exists():
        raise FileNotFoundError(f"{TRANSFERMARKT_GZ} not found. Run `scout-finder fetch --values` first.")
    values = match_top5_values(load_raw(), pd.read_csv(TRANSFERMARKT_GZ, low_memory=False))
    values.to_csv(TOP5_VALUES_CSV, index=False)
    return values


# ---------- everything together ----------

def load_top5() -> pd.DataFrame:
    """Every outfield player in the five leagues in 2025/26, in the same shape `load_players` returns."""
    raw = load_raw()
    raw = raw.sort_values("minutesPlayed", ascending=False).drop_duplicates("player_id")   # moved between leagues: longer stint
    values = pd.read_csv(TOP5_VALUES_CSV)
    d = raw.merge(values[["pl_id", "position", "role", "birth_date", "market_value_eur"]], left_on="player_id", right_on="pl_id")
    d = d[d.position.isin(TM_POSITIONS.values())].reset_index(drop=True)
    d = build_top5_metrics(d).rename(columns={"player": "name", "minutesPlayed": "timePlayed"})
    d = d.merge(team_possession(raw), on=["league", "team"], how="left")
    d["possession"] = d.possession.fillna(50)
    for metric in METRICS:
        if metric.adjust:
            d[metric.key] = d[metric.key] * possession_factor(d.possession, metric.adjust)
    d = add_percentiles(d, MIN_MINUTES)
    d["season"] = 2025
    d["age"] = ((pd.Timestamp(AGE_ON) - pd.to_datetime(d.birth_date, errors="coerce")).dt.days / 365.25).round(1)
    if TOP5_NOW_CSV.exists():
        now = pd.read_csv(TOP5_NOW_CSV, keep_default_na=False)
        d = d.merge(now[["pl_id", "club_now", "in_pl_now", "move"]], on="pl_id", how="left")
        d["club_now"] = d.club_now.fillna(d.team)
        d["in_pl_now"] = d.in_pl_now.map(lambda v: str(v).lower() != "false")
        d["move"] = d.move.fillna("")
    else:
        d["club_now"], d["in_pl_now"], d["move"] = d.team, True, ""
    return d


# ---------- where each player is now ----------

def all_moves() -> pd.DataFrame:
    """Every summer 2026 move in English, Spanish, Italian, German and French football, clubs in one spelling."""
    frames = [pd.read_csv(f, keep_default_na=False) for f in (TRANSFERS_CSV, EUROPE_TRANSFERS_CSV) if f.exists()]
    t = pd.concat(frames, ignore_index=True)
    t["from_c"], t["to_c"] = t.from_club.map(canon), t.to_club.map(canon)
    t["when"] = pd.to_datetime(t.date, errors="coerce", dayfirst=True)
    return t


def clubs_in_top5_now(teams_2025: dict) -> dict:
    """Club -> league for 2026/27: last season's clubs, minus the relegated, plus the promoted."""
    now = {t: lg for t, lg in teams_2025.items() if t not in RELEGATED}
    now.update(PROMOTED)
    return now


def _note(move) -> str:
    when = move.when.strftime("%b %Y") if pd.notna(move.when) else "summer 2026"
    fee = "" if move.kind != "transfer" or not str(move.fee).strip() else f", {move.fee}"
    if move.kind == "loan":
        return f"on loan to {move.to_c} ({when})"
    if move.kind == "return":
        return f"back at {move.to_c} after his loan"
    if move.kind == "released":
        return "released, no club yet"
    if move.kind == "retired":
        return "retired"
    return f"joined {move.to_c} ({when}{fee})"


def follow_moves(name: str, club: str, by_club: dict, max_steps: int = 4):
    """Follow a player's summer moves from `club`: a loan return and then a sale are two steps. Returns (club, note)."""
    note, seen = "", {club}
    for _ in range(max_steps):
        hits = [m for m in by_club.get(club, []) if _names_match(m.player, name)]
        if not hits:
            break
        move = sorted(hits, key=lambda m: (pd.notna(m.when), m.when if pd.notna(m.when) else pd.Timestamp(0)))[-1]
        if move.to_c in seen:
            break
        club, note = move.to_c, _note(move)
        seen.add(club)
    return club, note


def build_clubs_now() -> pd.DataFrame:
    """Each player's club after the summer 2026 window, and whether that club is in the five leagues this season."""
    raw = load_raw().sort_values("minutesPlayed", ascending=False).drop_duplicates("player_id")
    moves = all_moves()
    by_club: dict = {}
    for m in moves.itertuples():
        by_club.setdefault(m.from_c, []).append(m)
    big = raw.groupby("team").minutesPlayed.sum()
    teams_2025 = {r.team: r.league for r in raw.drop_duplicates("team").itertuples() if big[r.team] > 5000}
    top5_now = clubs_in_top5_now(teams_2025)
    rows = []
    for p in raw.itertuples():
        club, note = follow_moves(p.player, p.team, by_club)
        if not note and p.team in RELEGATED:
            note = f"relegated with {p.team}"
        rows.append({"pl_id": int(p.player_id), "name": p.player, "club_2025": p.team, "club_now": club,
                     "in_pl_now": club in top5_now, "league_now": top5_now.get(club, ""), "move": note})
    out = pd.DataFrame(rows)
    out.to_csv(TOP5_NOW_CSV, index=False)
    return out
