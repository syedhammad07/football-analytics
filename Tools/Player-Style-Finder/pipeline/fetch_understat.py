"""Download Understat season stats for the top 5 leagues -> data/understat/<league>_<season>.csv

Understat (understat.com) has every player of the Premier League, La Liga, Bundesliga, Serie A and
Ligue 1 from 2014/15, with xG-based season totals: minutes, goals, npxG, shots, key passes, xA,
xGChain and xGBuildup. Season 2014 means 2014/15.

  python fetch_understat.py                 # every league, 2014 to the current season
  python fetch_understat.py --season 2026   # one season for every league
"""
import argparse, csv, json, os, re, sys, time
from datetime import date
import urllib.request

LEAGUES = {"EPL": "Premier League", "La_liga": "La Liga", "Bundesliga": "Bundesliga", "Serie_A": "Serie A", "Ligue_1": "Ligue 1"}
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "understat")
COLS = ["id", "player_name", "team_title", "position", "games", "time", "goals", "npg", "xG", "npxG", "assists", "xA",
        "shots", "key_passes", "xGChain", "xGBuildup", "yellow_cards", "red_cards"]
UA = {"User-Agent": "Mozilla/5.0 (football-analytics Player Style Finder)", "X-Requested-With": "XMLHttpRequest"}


def get(url, headers):
    for attempt in range(5):
        try:
            return urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=60).read().decode("utf-8")
        except Exception as e:
            err = e; time.sleep(3 * (attempt + 1))
    raise RuntimeError(f"{url}: {err}")


def players(league, season):
    """Understat serves the league data as JSON (getLeagueData); older pages embed it in the HTML."""
    try:
        d = json.loads(get(f"https://understat.com/getLeagueData/{league}/{season}", {**UA, "Referer": f"https://understat.com/league/{league}/{season}"}))
        return d["players"]
    except Exception as e:
        html = get(f"https://understat.com/league/{league}/{season}", {"User-Agent": UA["User-Agent"]})
        m = re.search(r"playersData\s*=\s*JSON\.parse\('(.*?)'\)", html)
        if not m:
            raise RuntimeError(f"no player data for {league} {season} ({e})")
        return json.loads(m.group(1).encode().decode("unicode_escape"))


def probe():
    """Print what Understat returns, to diagnose blocked or changed endpoints."""
    for url, h in [("https://understat.com/getLeagueData/EPL/2015", {**UA, "Referer": "https://understat.com/league/EPL/2015"}),
                   ("https://understat.com/league/EPL/2015", {"User-Agent": UA["User-Agent"]})]:
        try:
            r = urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=60)
            body = r.read().decode("utf-8", "replace")
            print("PROBE", url, r.status, len(body), repr(body[:300]), "| vars:", re.findall(r"var (\w+)\s*=", body)[:10], flush=True)
        except Exception as e:
            print("PROBE", url, "ERROR", repr(e)[:300], flush=True)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--season", type=int); ap.add_argument("--probe", action="store_true")
    a = ap.parse_args()
    if a.probe:
        return probe()
    now = date.today().year if date.today().month >= 8 else date.today().year - 1
    seasons = [a.season] if a.season else list(range(2014, now + 1))
    os.makedirs(OUT, exist_ok=True)
    bad = []
    for s in seasons:
        for lg in LEAGUES:
            try:
                rows = players(lg, s)
            except Exception as e:
                bad.append(str(e)); print("FAILED", lg, s, e, flush=True); continue
            with open(os.path.join(OUT, f"{lg}_{s}.csv"), "w", newline="", encoding="utf-8") as f:
                w = csv.writer(f); w.writerow(COLS)
                for r in rows:
                    w.writerow([r.get(c, "") for c in COLS])
            print(lg, s, len(rows), "players", flush=True)
            time.sleep(1)
    if bad:
        sys.exit(f"{len(bad)} downloads failed")


if __name__ == "__main__":
    main()
