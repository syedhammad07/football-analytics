"""Parse player season stats copied from premierleague.com player pages.

Each line of data/external/pl_raw.txt is `<slug>@<season start year>#<label>|<value>|...`, taken from
https://www.premierleague.com/en/players/<id>/<slug>/stats?season=<year>. Section headers (Attack,
Possession, ...) carry no value. Missing stats (e.g. Goals for a player who scored none) mean zero.
"""
import re
from pathlib import Path

import pandas as pd

HEADERS = {"Attack", "Possession", "Physical", "Defence", "Discipline", "Goalkeeping"}
PL_IDS = {
    "jamie-vardy": 101668, "riyad-mahrez": 103025, "wes-morgan": 15033, "kasper-schmeichel": 17745,
    "danny-simpson": 40725, "jeffrey-schlupp": 86417, "marc-albrighton": 51938, "danny-drinkwater": 61603,
    "andy-king": 13152, "leonardo-ulloa": 54316, "ritchie-de-laet": 46695, "esteban-cambiasso": 13919,
    "paul-konchesky": 1413, "david-nugent": 12744, "robert-huth": 12413, "n-golo-kante": 116594,
    "christian-fuchs": 37402, "shinji-okazaki": 78412,
}


def _num(s):
    return float(s.replace(",", ""))


def parse_line(line):
    head, body = line.strip().split("#", 1)
    slug, year = head.split("@")
    year = int(re.sub(r"\D", "", year))
    items = [x for x in body.split("|") if x not in HEADERS]
    row = {"slug": slug, "season": f"{year}/{str(year + 1)[-2:]}"}
    i = 0
    while i < len(items) - 1:
        label, value = items[i], items[i + 1]
        m = re.match(r"([\d,\.]+)(?: \(([\d,\.]+)%?\))?$", value)
        if not m:          # label followed by another label: skip one
            i += 1
            continue
        key = re.sub(r"[^a-z0-9]+", "_", label.lower()).strip("_")
        first, second = _num(m.group(1)), m.group(2)
        if label.startswith("Appearances"):
            row["appearances"] = first
            row["sub_appearances"] = _num(second) if second else 0
        elif "(Completed %)" in label:
            row[key.replace("_completed", "")] = first
            row[key.replace("_completed", "") + "_pct"] = _num(second)
        elif label == "Penalties (Scored)":
            row["penalties_taken"], row["penalties_scored"] = first, _num(second)
        elif label == "Free Kicks (Scored)":
            pass  # ambiguous on the site; not used
        else:
            row.setdefault(key, first)  # 'Goals' appears twice
        i += 2
    return row


def load(path="data/external/pl_raw.txt"):
    rows = [parse_line(l) for l in Path(path).read_text(encoding="utf-8").splitlines() if l.strip()]
    df = pd.DataFrame(rows).fillna(0)
    df["pl_id"] = df.slug.map(PL_IDS)
    df["player"] = df.slug.str.replace("-", " ").str.title().str.replace("De Laet", "de Laet").replace({"N Golo Kante": "N'Golo Kanté"})
    return df


if __name__ == "__main__":
    out = load()
    out.to_csv("data/external/pl_player_seasons_2014_2016.csv", index=False)
    print(out[["player", "season", "appearances", "minutes_played", "goals", "assists", "xg", "xa",
               "total_tackles", "interceptions"]].to_string())
