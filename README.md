# Football Analytics: Player Performance Analysis

> Status: 🚧 In progress · Started: November 2026 · Author: Hammad

## Goal

Analyse player performance using open event data to answer:

1. Which players create the most dangerous chances relative to minutes played?
2. How do playing styles differ between positions and teams?
3. Can a simple model flag under-rated players worth scouting?

## Data

| Source | What it contains | Licence / terms |
| --- | --- | --- |
| [StatsBomb Open Data](https://github.com/statsbomb/open-data) | Event-level data (passes, shots, xG) for selected competitions | Free for non-commercial use with attribution — see their licence |

Raw data is **not** stored in this repo. Run `python -m football_analytics.data` to download it locally into `data/raw/`.
See [`docs/dataset.md`](docs/dataset.md) for field descriptions and cleaning steps.

## Project structure

```
football-analytics/
├── data/
│   ├── raw/          ← downloaded data (git-ignored)
│   ├── processed/    ← cleaned data (git-ignored)
│   └── sample/       ← small samples safe to commit
├── notebooks/        ← exploration (01_eda.ipynb, 02_features.ipynb, ...)
├── src/football_analytics/  ← reusable Python code
├── reports/figures/  ← charts used in the README and LinkedIn posts
├── docs/
│   ├── dataset.md    ← data dictionary and cleaning log
│   ├── results.md    ← verified findings
│   └── decisions/    ← decision records (why I chose X over Y)
└── requirements.txt
```

## How to run

```bash
git clone https://github.com/syedhammad07/football-analytics.git
cd football-analytics
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pip install -e .                    # makes src/football_analytics importable
python -m football_analytics.data   # lists competitions you can download
jupyter lab
```

## Key findings

_To be filled in when the analysis is complete. Only verified results go here; details in [`docs/results.md`](docs/results.md)._

## Tools

Python · pandas · statsbombpy · matplotlib · mplsoccer · scikit-learn · Jupyter

## Progress

Tracked on my GitHub Project board **Portfolio** (Area: Football analytics).

## Acknowledgements

Data provided by [StatsBomb](https://statsbomb.com/) Open Data.
