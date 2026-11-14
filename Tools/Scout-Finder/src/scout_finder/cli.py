"""Command line: `scout-finder find "Rodri" --max-age 25 --max-value 30`."""
import argparse
import sys

import pandas as pd

from .config import GROUPS, METRICS, MIN_MINUTES, VALUE_DATE
from .data import build_values_file, download_transfermarkt, fetch_pl_season, load_players
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


def describe(r: pd.Series) -> str:
    return f"{r['name']} ({r.team}, {r.position.lower()}, {r.age:.0f}, {money(r.market_value_eur)}, {int(r.timePlayed):,} mins)"


def cmd_find(args, players: pd.DataFrame) -> None:
    target = find_player(players, args.player)
    found = find_similar(players, target, same_position=not args.any_position, max_age=args.max_age,
                         max_value_m=args.max_value, min_minutes=args.min_minutes, exclude_team=args.other_clubs, top=args.top)
    filters = [f"age ≤ {args.max_age:g}" if args.max_age else "", f"value ≤ €{args.max_value:g}m" if args.max_value else "",
               "other clubs only" if args.other_clubs else "", "any position" if args.any_position else f"{target.position.lower()}s only"]
    print(f"\nPlayers most like {describe(target)}")
    print(f"2025/26 Premier League · {', '.join(f for f in filters if f)} · {args.min_minutes}+ minutes")
    print(f"Values: Transfermarkt, {VALUE_DATE}\n")
    if found.empty:
        print("Nobody passes those filters. Try a higher --max-value or --max-age.")
        return
    print(f"{'':>3} {'Player':<24} {'Club':<14} {'Age':>4} {'Value':>7} {'Match':>6}")
    for i, (_, r) in enumerate(found.iterrows(), 1):
        print(f"{i:>3} {r['name'][:24]:<24} {r.team[:14]:<14} {r.age:>4.0f} {money(r.market_value_eur):>7} {r.match:>5.0f}%")
        if r.shared:
            print(f"      also strong at: {r.shared}")
        print(f"      biggest difference: {r.gap}")
    if pd.notna(target.market_value_eur):
        cheaper = found[found.market_value_eur <= 0.75 * target.market_value_eur]   # only worth saying if it's a real saving
        if not cheaper.empty:
            best = cheaper.iloc[0]
            saving = target.market_value_eur - best.market_value_eur
            print(f"\nBest cheaper option: {best['name']} ({best.team}),")
            print(f"a {best.match:.0f}% match for {money(best.market_value_eur)}, {money(saving)} less than {target['name']}.")


def cmd_profile(args, players: pd.DataFrame) -> None:
    r = find_player(players, args.player)
    print(f"\n{describe(r)}")
    print(f"Percentiles against Premier League {r.position.lower()}s with {MIN_MINUTES}+ minutes, 2025/26 (adjusted for team possession)\n")
    for g in GROUPS:
        print(g.upper())
        for m in [m for m in METRICS if m.group == g]:
            p = r["p_" + m.key]
            print(f"  {m.label:<42} {bar(p)} {'' if pd.isna(p) else int(p):>3}")
        print()


def cmd_fetch(args) -> None:
    if args.stats:
        print("Downloading Premier League stats (takes a few minutes)...")
        d = fetch_pl_season()
        print(f"Saved {len(d)} players.")
    if args.values:
        print("Downloading Transfermarkt values...")
        download_transfermarkt()
    if args.values or args.match:
        v = build_values_file()
        print(f"Matched {len(v)} players to a Transfermarkt value.")


def main(argv=None) -> int:
    try:   # Windows terminals can default to an old code page; make sure € and the bars print
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
    ap = argparse.ArgumentParser(prog="scout-finder", description="Find Premier League players who play like someone else, for less.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    f = sub.add_parser("find", help="players most like a given player")
    f.add_argument("player")
    f.add_argument("--max-age", type=float)
    f.add_argument("--max-value", type=float, help="in millions of euros")
    f.add_argument("--any-position", action="store_true", help="compare with every outfield player, not just the same position")
    f.add_argument("--other-clubs", action="store_true", help="leave out the player's own club")
    f.add_argument("--min-minutes", type=int, default=MIN_MINUTES)
    f.add_argument("--top", type=int, default=10)
    p = sub.add_parser("profile", help="one player's percentiles")
    p.add_argument("player")
    g = sub.add_parser("fetch", help="download fresh data")
    g.add_argument("--stats", action="store_true", help="Premier League stats (slow)")
    g.add_argument("--values", action="store_true", help="Transfermarkt values, then match them")
    g.add_argument("--match", action="store_true", help="only re-match the Transfermarkt file you already have")
    args = ap.parse_args(argv)
    try:
        if args.cmd == "fetch":
            cmd_fetch(args)
            return 0
        players = load_players()
        {"find": cmd_find, "profile": cmd_profile}[args.cmd](args, players)
    except (LookupError, FileNotFoundError) as e:
        print(e, file=sys.stderr)
        return 1
    return 0
