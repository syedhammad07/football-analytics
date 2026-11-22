"""Command line: `scout-finder find "Rodri" --max-age 25 --max-value 30`."""
import argparse
import sys

import pandas as pd

from .config import GROUPS, LEAGUES, METRICS, MIN_MINUTES, SEASON, SEASONS, TOP5_LABELS, VALUE_DATE
from .data import (build_values_file, download_transfermarkt, fetch_pl_season, load_players, min_minutes,
                   season_label)
from .similarity import find_player, find_similar, label


def money(v) -> str:
    if pd.isna(v):
        return "n/a"
    return f"€{v / 1e6:.0f}m" if v >= 1e6 else f"€{v / 1e3:.0f}k"


def bar(p, width: int = 20) -> str:
    if pd.isna(p):
        return "n/a".ljust(width)
    n = int(round(p / 100 * width))
    return "█" * n + "·" * (width - n)


def club(r: pd.Series) -> str:
    """His club now, marked when he's no longer in the Premier League."""
    now = r.get("club_now")
    if not isinstance(now, str) or not now:
        now = r.team
    if r.get("in_pl_now", True):
        return now
    return f"{now} (left top 5)" if "league" in r else f"{now} (left PL)"


def describe(r: pd.Series) -> str:
    age = "age n/a" if pd.isna(r.age) else int(r.age)
    return (f"{r['name']} ({club(r)}, {r.position.lower()}, {age}, {money(r.market_value_eur)}, "
            f"{int(r.timePlayed):,} mins in {season_label(r.season)})")


def moved_line(r: pd.Series) -> str:
    move = r.get("move")
    return f"{move}, was {r.team}" if isinstance(move, str) and move else ""


def find_target(name: str, season: int, pools: dict) -> pd.Series:
    """The player in the season being searched, or else his most recent season with minutes."""
    try:
        return find_player(pools[season], name)
    except LookupError as first_error:
        for s in sorted(pools, reverse=True):
            if s == season:
                continue
            try:
                return find_player(pools[s], name)
            except LookupError:
                pass
        raise first_error


LEAGUE_CODES = {"pl": "Premier League", "laliga": "La Liga", "seriea": "Serie A", "bundesliga": "Bundesliga", "ligue1": "Ligue 1"}


def cmd_find_top5(args) -> None:
    from .top5 import load_top5
    players = load_top5()
    target = find_player(players, args.player)
    leagues = [LEAGUE_CODES[c] for c in args.league] if args.league else None
    minutes = args.min_minutes if args.min_minutes is not None else MIN_MINUTES
    found = find_similar(players, target, same_position=not args.any_position, max_age=args.max_age,
                         max_value_m=args.max_value, min_minutes=minutes, exclude_team=args.other_clubs,
                         in_pl_only=not args.include_departed, top=args.top, labels=TOP5_LABELS, leagues=leagues)
    filters = [f"age ≤ {args.max_age:g}" if args.max_age else "", f"value ≤ €{args.max_value:g}m" if args.max_value else "",
               "other clubs only" if args.other_clubs else "", "any position" if args.any_position else f"{target.position.lower()}s only",
               ", ".join(leagues) if leagues else "all five leagues", "" if args.include_departed else "still in the top 5 leagues"]
    print(f"\nPlayers most like {describe(target)}")
    if moved_line(target):
        print(f"  {moved_line(target)}")
    print(f"2025/26, Europe's top five leagues · {', '.join(f for f in filters if f)} · {minutes}+ minutes")
    print(f"Clubs as of now, summer 2026 moves included · values: Transfermarkt, {VALUE_DATE}\n")
    if found.empty:
        print("Nobody passes those filters. Try a higher --max-value or --max-age.")
        return
    print(f"{'':>3} {'Player':<24} {'Club now':<20} {'25/26 league':<15} {'Age':>3} {'Value':>6} {'Match':>6}")
    for i, (_, r) in enumerate(found.iterrows(), 1):
        print(f"{i:>3} {r['name'][:24]:<24} {club(r)[:20]:<20} {r.league:<15} {int(r.age):>3} {money(r.market_value_eur):>6} {r.match:>5.0f}%")
        if moved_line(r):
            print(f"      {moved_line(r)}")
        if r.shared:
            print(f"      also strong at: {r.shared}")
        print(f"      biggest difference: {r.gap}")
    best_cheaper(target, found)


def best_cheaper(target, found) -> None:
    if pd.notna(target.market_value_eur):
        cheaper = found[found.market_value_eur <= 0.75 * target.market_value_eur]   # only worth saying if it's a real saving
        if not cheaper.empty:
            best = cheaper.iloc[0]
            saving = target.market_value_eur - best.market_value_eur
            print(f"\nBest cheaper option: {best['name']} ({club(best)}),")
            print(f"a {best.match:.0f}% match for {money(best.market_value_eur)}, {money(saving)} less than {target['name']}.")


def cmd_find(args) -> None:
    if args.top5:
        return cmd_find_top5(args)
    pools = {s: load_players(s) for s in SEASONS}
    players = pools[args.season]
    target = find_target(args.player, args.season, pools)
    minutes = args.min_minutes if args.min_minutes is not None else min_minutes(args.season)
    found = find_similar(players, target, same_position=not args.any_position, max_age=args.max_age,
                         max_value_m=args.max_value, min_minutes=minutes, exclude_team=args.other_clubs,
                         in_pl_only=not args.include_departed, top=args.top)
    filters = [f"age ≤ {args.max_age:g}" if args.max_age else "", f"value ≤ €{args.max_value:g}m" if args.max_value else "",
               "other clubs only" if args.other_clubs else "", "any position" if args.any_position else f"{target.position.lower()}s only",
               "" if args.include_departed else "still in the PL"]
    print(f"\nPlayers most like {describe(target)}")
    if moved_line(target):
        print(f"  {moved_line(target)}")
    if target.season != args.season:
        print(f"  (no {season_label(args.season)} minutes, so his {season_label(target.season)} numbers are the target)")
    print(f"{season_label(args.season)} Premier League stats · {', '.join(f for f in filters if f)} · {minutes}+ minutes")
    print(f"Clubs as of now, summer 2026 moves included · values: Transfermarkt, {VALUE_DATE}\n")
    if found.empty:
        print("Nobody passes those filters. Try a higher --max-value or --max-age.")
        return
    print(f"{'':>3} {'Player':<24} {'Club now':<16} {'Age':>4} {'Value':>7} {'Match':>6}")
    for i, (_, r) in enumerate(found.iterrows(), 1):
        print(f"{i:>3} {r['name'][:24]:<24} {club(r)[:16]:<16} {int(r.age):>4} {money(r.market_value_eur):>7} {r.match:>5.0f}%")
        if moved_line(r):
            print(f"      {moved_line(r)}")
        if r.shared:
            print(f"      also strong at: {r.shared}")
        print(f"      biggest difference: {r.gap}")
    best_cheaper(target, found)


def cmd_profile(args) -> None:
    if args.top5:
        from .top5 import load_top5
        r, labels = find_player(load_top5(), args.player), TOP5_LABELS
        scale = f"top-five-league {r.position.lower()}s with {MIN_MINUTES}+ minutes, 2025/26"
    else:
        pools = {s: load_players(s) for s in SEASONS}
        r, labels = find_target(args.player, args.season, pools), None
        scale = f"Premier League {r.position.lower()}s with {min_minutes(r.season)}+ minutes, {season_label(r.season)}"
    print(f"\n{describe(r)}")
    if moved_line(r):
        print(f"  {moved_line(r)}")
    print(f"Percentiles against {scale} (adjusted for team possession)\n")
    for g in GROUPS:
        print(g.upper())
        for m in [m for m in METRICS if m.group == g]:
            p = r["p_" + m.key]
            print(f"  {label(m.key, labels):<42} {bar(p)} {'' if pd.isna(p) else int(p):>3}")
        print()


def cmd_fetch(args) -> None:
    if args.stats:
        print(f"Downloading {season_label(args.season)} Premier League stats (takes a few minutes)...")
        d = fetch_pl_season(args.season)
        print(f"Saved {len(d)} players.")
    if args.values:
        print("Downloading Transfermarkt values...")
        download_transfermarkt()
    if args.top5:
        from .top5 import download_top5
        print("Downloading 2025/26 stats for the top five leagues...")
        print(f"Saved {len(download_top5())} players.")
    if args.values or args.match:
        for s in SEASONS:
            v = build_values_file(s)
            print(f"{season_label(s)}: matched {len(v)} players to a Transfermarkt value.")
    if args.values or args.match or args.top5:
        from .config import TOP5_CSV
        from .top5 import build_clubs_now, build_top5_values_file
        if TOP5_CSV.exists():
            print(f"Top five leagues: matched {len(build_top5_values_file())} players to Transfermarkt.")
            now = build_clubs_now()
            print(f"Top five leagues: {(now.move != '').sum()} players have moved, gone down or stopped since 2025/26.")


def cmd_page(args) -> None:
    from .web import build_page
    out = build_page()
    print(f"Saved the web version to {out} ({out.stat().st_size / 1e3:.0f} KB). Open it in a browser.")


def main(argv=None) -> int:
    try:   # Windows terminals can default to an old code page; make sure € and the bars print
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
    ap = argparse.ArgumentParser(prog="scout-finder", description="Find Premier League players who play like someone else, for less.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    seasons = sorted(SEASONS)
    f = sub.add_parser("find", help="players most like a given player")
    f.add_argument("player")
    f.add_argument("--season", type=int, choices=seasons, default=SEASON,
                   help="2025 = 2025/26 (default), 2026 = 2026/27 so far, which includes this summer's signings")
    f.add_argument("--top5", action="store_true", help="search Europe's top five leagues (2025/26) instead of the Premier League")
    f.add_argument("--league", action="append", choices=sorted(LEAGUE_CODES), help="with --top5: only these leagues (repeatable)")
    f.add_argument("--max-age", type=float)
    f.add_argument("--max-value", type=float, help="in millions of euros")
    f.add_argument("--any-position", action="store_true", help="compare with every outfield player, not just the same position")
    f.add_argument("--other-clubs", action="store_true", help="leave out the player's current club")
    f.add_argument("--include-departed", action="store_true", help="also show players who have left the Premier League")
    f.add_argument("--min-minutes", type=int, help="default: 900, or 40%% of the minutes so far for 2026/27")
    f.add_argument("--top", type=int, default=10)
    p = sub.add_parser("profile", help="one player's percentiles")
    p.add_argument("player")
    p.add_argument("--season", type=int, choices=seasons, default=SEASON)
    p.add_argument("--top5", action="store_true", help="percentiles against Europe's top five leagues")
    g = sub.add_parser("fetch", help="download fresh data")
    g.add_argument("--season", type=int, choices=seasons, default=SEASON)
    g.add_argument("--stats", action="store_true", help="Premier League stats (slow)")
    g.add_argument("--top5", action="store_true", help="top-five-leagues stats, then match values and clubs")
    g.add_argument("--values", action="store_true", help="Transfermarkt values, then match them")
    g.add_argument("--match", action="store_true", help="only re-match the Transfermarkt file you already have")
    sub.add_parser("page", help="build the web version (index.html)")
    args = ap.parse_args(argv)
    try:
        {"find": cmd_find, "profile": cmd_profile, "fetch": cmd_fetch, "page": cmd_page}[args.cmd](args)
    except (LookupError, FileNotFoundError) as e:
        print(e, file=sys.stderr)
        return 1
    return 0
