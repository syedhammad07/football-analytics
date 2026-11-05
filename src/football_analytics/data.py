"""Download StatsBomb open event data into data/raw/.

Usage:
    python -m football_analytics.data              # lists competitions
    python -m football_analytics.data 9 281        # downloads competition 9, season 281
"""
from pathlib import Path
import sys
import warnings

import pandas as pd
from statsbombpy import sb

warnings.filterwarnings("ignore", message="credentials were not supplied")

RAW_DIR = Path(__file__).resolve().parents[2] / "data" / "raw"


def list_competitions() -> pd.DataFrame:
    comps = sb.competitions()
    return comps[["competition_id", "season_id", "competition_name", "season_name"]]


def download_season(competition_id: int, season_id: int) -> Path:
    out_dir = RAW_DIR / f"{competition_id}_{season_id}"
    out_dir.mkdir(parents=True, exist_ok=True)

    matches = sb.matches(competition_id=competition_id, season_id=season_id)
    matches.to_csv(out_dir / "matches.csv", index=False)

    events = [sb.events(match_id=m) for m in matches["match_id"]]
    pd.concat(events, ignore_index=True).to_pickle(out_dir / "events.pkl")

    print(f"Saved {len(matches)} matches to {out_dir}")
    return out_dir


if __name__ == "__main__":
    if len(sys.argv) == 3:
        download_season(int(sys.argv[1]), int(sys.argv[2]))
    else:
        print(list_competitions().to_string(index=False))
        print("\nRun again with: python -m football_analytics.data <competition_id> <season_id>")
