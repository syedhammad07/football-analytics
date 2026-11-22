"""Where each player is now: summer 2026 transfers and loans applied on top of last season's clubs.

The Premier League's own 2026/27 squad lists are not enough on their own: a player sold abroad can stay
listed (Rodri was still in Man City's list after joining Barcelona). So a recorded summer move wins,
then the current squad list, then "no longer in a Premier League squad".
"""
import pandas as pd

from .similarity import normalise

# Wikipedia's full club names -> the short names the Premier League data uses
PL_CLUBS = {
    "Arsenal": "Arsenal", "Aston Villa": "A Villa", "AFC Bournemouth": "Bournemouth", "Bournemouth": "Bournemouth",
    "Brentford": "Brentford", "Brighton & Hove Albion": "Brighton", "Burnley": "Burnley", "Chelsea": "Chelsea",
    "Coventry City": "Coventry", "Crystal Palace": "C Palace", "Everton": "Everton", "Fulham": "Fulham",
    "Hull City": "Hull", "Ipswich Town": "Ipswich", "Leeds United": "Leeds", "Liverpool": "Liverpool",
    "Manchester City": "Man City", "Manchester United": "Man Utd", "Newcastle United": "Newcastle",
    "Nottingham Forest": "Nott'm Forest", "Sunderland": "Sunderland", "Tottenham Hotspur": "Spurs",
    "West Ham United": "West Ham", "Wolverhampton Wanderers": "Wolves",
}
# The Premier League site's 2026/27 short names -> the names used everywhere else in this project
SHORT_NAMES = {"Villa": "A Villa", "Palace": "C Palace", "Forest": "Nott'm Forest"}


def short_club(name: str) -> str:
    """'Newcastle United' -> 'Newcastle'; non-Premier League clubs keep their full name."""
    name = str(name).strip()
    return SHORT_NAMES.get(PL_CLUBS.get(name, name), PL_CLUBS.get(name, name))


def _names_match(a: str, b: str) -> bool:
    """Same player? Every word of the shorter name appears in the longer one ('Rodri' vs 'Rodri')."""
    wa, wb = set(normalise(a).replace("-", " ").split()), set(normalise(b).replace("-", " ").split())
    small, big = (wa, wb) if len(wa) <= len(wb) else (wb, wa)
    return bool(small) and small <= big


def find_move(name: str, club: str, transfers: pd.DataFrame) -> pd.Series | None:
    """The most recent summer move out of `club` for this player, or None."""
    t = transfers[transfers.from_short == club]
    hits = t[t.player.map(lambda p: _names_match(p, name))]
    if hits.empty:
        return None
    return hits.sort_values("when").iloc[-1]


def current_clubs(players: pd.DataFrame, squads: pd.DataFrame, transfers: pd.DataFrame) -> pd.DataFrame:
    """For every player: his club now, whether he's still in the Premier League, and what happened.

    `players` needs pl_id, name, team (his club in the season the stats are from).
    `squads` is the 2026/27 squad list (pl_id, team): it also defines which 20 clubs are in the league now.
    `transfers` is the summer 2026 list.
    """
    tr = transfers.copy()
    tr["from_short"] = tr.from_club.map(short_club)
    tr["to_short"] = tr.to_club.map(short_club)
    tr["when"] = pd.to_datetime(tr.date, errors="coerce", dayfirst=True)
    squad_club = squads.drop_duplicates("pl_id").set_index("pl_id").team.map(lambda t: SHORT_NAMES.get(t, t))
    pl_now = set(squad_club.unique())          # the 20 clubs in the league this season
    rows = []
    for _, p in players.iterrows():
        move = find_move(p["name"], p.team, tr)
        if move is not None:
            club = move.to_short
            on_loan = move.kind == "loan"
            fee = "" if on_loan or not str(move.fee).strip() else f", {move.fee}"
            month = move.when.strftime("%b %Y") if pd.notna(move.when) else ""
            note = f"{'on loan to' if on_loan else 'joined'} {club} ({month}{fee})"
        elif p.pl_id in squad_club.index:
            club, note = squad_club[p.pl_id], ""
        elif p.team not in pl_now:
            club, note = p.team, f"relegated with {p.team}"
        else:
            club, note = "", "no longer in a Premier League squad"
        rows.append({"pl_id": p.pl_id, "club_now": club or "?", "in_pl_now": club in pl_now, "move": note})
    return pd.DataFrame(rows)
