"""Common player names (e.g. 'David Silva') from StatsBomb lineups -> data/nicknames.csv."""
import os, json, urllib.request
from concurrent.futures import ThreadPoolExecutor
import pandas as pd
BASE = "https://raw.githubusercontent.com/statsbomb/open-data/master/data"
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
get = lambda u: json.loads(urllib.request.urlopen(u, timeout=60).read())
mids = [m["match_id"] for c in (2, 11, 12, 7) for m in get(f"{BASE}/matches/{c}/27.json")]
names = {}
with ThreadPoolExecutor(16) as ex:
    for lu in ex.map(lambda m: get(f"{BASE}/lineups/{m}.json"), mids):
        for team in lu:
            for p in team["lineup"]:
                names[p["player_id"]] = p.get("player_nickname") or p["player_name"]
pd.DataFrame(names.items(), columns=["player_id", "short_name"]).to_csv(os.path.join(D, "nicknames.csv"), index=False)
print(len(names), "names")
