"""Command line: `scout-finder find "Rodri" --max-age 25 --max-value 30`."""
import argparse
import sys

import pandas as pd

from .config import GROUPS, METRICS, SEASON, SEASONS, VALUE_DATE
from .data import (build_values_file, download_transfermarkt, fetch_pl_season, load_players, min_minutes,
                   season_label)
from .similarity import find_player, find_similar


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
    return now if r.get("in_pl_now", True) else f"{now} (left PL)"


def describe(r: pd.Series) -> str:
    return (f"{r['name']} ({club(r)}, {r.position.lower()}, {r.age:.0f}, {money(r.market_value_eur)}, "
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


def cmd_find(args) -> None:
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
        print(f"{i:>3} {r['name'][:24]:<24} {club(r)[:16]:<16} {r.age:>4.0f} {money(r.market_value_eur):>7} {r.match:>5.0f}%")
        if moved_line(r):
            print(f"      {moved_line(r)}")
        if r.shared:
            print(f"      also strong at: {r.shared}")
        print(f"      biggest difference: {r.gap}")
    if pd.notna(target.market_value_eur):
        cheaper = found[found.market_value_eur <= 0.75 * target.market_value_eur]   # only worth saying if it's a real saving
        if not cheaper.empty:
            best = cheaper.iloc[0]
            saving = target.market_value_eur - best.market_value_eur
            print(f"\nBest cheaper option: {best['name']} ({club(best)}),")
            print(f"a {best.match:.0f}% match for {money(best.market_value_eur)}, {money(saving)} less than {target['name']}.")


def cmd_profile(args) -> None:
    pools = {s: load_players(s) for s in SEASONS}
    r = find_target(args.player, args.season, pools)
    print(f"\n{describe(r)}")
    if moved_line(r):
        print(f"  {moved_line(r)}")
    print(f"Percentiles against Premier League {r.position.lower()}s with {min_minutes(r.season)}+ minutes, "
          f"{season_label(r.season)} (adjusted for team possession)\n")
    for g in GROUPS:
        print(g.upper())
        for m in [m for m in METRICS if m.group == g]:
            p = r["p_" + m.key]
            print(f"  {m.label:<42} {bar(p)} {'' if pd.isna(p) else int(p):>3}")
        print()


def cmd_fetch(args) -> None:
    if args.stats:
        print(f"Downloading {season_label(args.season)} Premier League stats (takes a few minutes)...")
        d = fetch_pl_season(args.season)
        print(f"Saved {len(d)} players.")
    if args.values:
        print("Downloading Transfermarkt values...")
        download_transfermarkt()
    if args.values or args.match:
        for s in SEASONS:
            v = build_values_file(s)
            print(f"{season_label(s)}: matched {len(v)} players to a Transfermarkt value.")


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
    g = sub.add_parser("fetch", help="download fresh data")
    g.add_argument("--season", type=int, choices=seasons, default=SEASON)
    g.add_argument("--stats", action="store_true", help="Premier League stats (slow)")
    g.add_argument("--values", action="store_true", help="Transfermarkt values, then match them")
    g.add_argument("--match", action="store_true", help="only re-match the Transfermarkt file you already have")
    args = ap.parse_args(argv)
    try:
        {"find": cmd_find, "profile": cmd_profile, "fetch": cmd_fetch}[args.cmd](args)
    except (LookupError, FileNotFoundError) as e:
        print(e, file=sys.stderr)
        return 1
    return 0
