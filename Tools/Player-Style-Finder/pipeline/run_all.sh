#!/usr/bin/env bash
# Rebuild everything from StatsBomb open data (needs internet; ~2 minutes).
set -e
cd "$(dirname "$0")"
python3 build_features.py   # download events -> data/player_match.csv
python3 make_features.py    # per-90 style features -> data/features.csv
python3 explore_family.py   # how many roles per position family (stability check)
python3 roles.py            # roles -> data/roles.csv
python3 validate.py         # split-half test, role agreement, similar.csv
python3 nicknames.py        # common player names from lineups -> data/nicknames.csv
python3 explain.py          # why each match: alike / different stats, % alike -> data/similar_explained.csv
python3 map_extremes.py     # 2-D map coordinates and role extremes
python3 site_data.py        # JSON for the website -> ../data
python3 gk_features.py      # goalkeeper stats -> data/gk_features.csv
python3 gk_model.py         # goalkeeper style space, roles, split-half test
python3 site_data.py        # re-export site data with goalkeepers
python3 club_seasons.py     # single-club seasons (Barcelona 2004-21, Arsenal 03/04, PSG, Leverkusen) -> data/season_match.csv
python3 seasons.py          # season profiles in the 2015/16 style space -> ../data/seasons.json
