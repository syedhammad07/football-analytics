"""Download Understat shot and player data for the Premier League.

Understat (understat.com) publishes xG for every shot in the top European leagues from 2014/15.
This module downloads a public copy of that data from the GitHub dataset
https://github.com/douglasbc/scraping-understat-dataset (scraped from Understat), so the analysis
doesn't depend on Understat's own site being online.

Usage (from the repo root):
    python -m football_analytics.understat 14-15 15-16 16-17
Files are saved to data/raw/understat/ (git-ignored).
"""
import sys
import urllib.request
from pathlib import Path

ROOT_URL = "https://raw.githubusercontent.com/douglasbc/scraping-understat-dataset/main/datasets"
BASE = f"{ROOT_URL}/epl"
OUT = Path("data/raw/understat")


def download(seasons=("14-15", "15-16", "16-17")):
    OUT.mkdir(parents=True, exist_ok=True)
    for s in seasons:
        for kind in ("shots", "players"):
            name = f"{kind}_epl_{s}.csv"
            urllib.request.urlretrieve(f"{BASE}/{name}", OUT / name)
            print("saved", OUT / name)
    # 2015/16 player totals from Serie A and Ligue 1 (Alonso at Fiorentina; Luiz and Batshuayi in France)
    (OUT / "other").mkdir(exist_ok=True)
    for league in ("serie_a", "ligue_1"):
        name = f"players_{league}_15-16.csv"
        urllib.request.urlretrieve(f"{ROOT_URL}/{league}/{name}", OUT / "other" / name)
        print("saved", OUT / "other" / name)


if __name__ == "__main__":
    download(sys.argv[1:] or ("14-15", "15-16", "16-17"))
