"""2-D role map coordinates (UMAP) and the two outermost players of each role -> data/map.json, data/extremes.json"""
import os
DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
import json, warnings, numpy as np, pandas as pd, umap
warnings.filterwarnings("ignore")
from site_data_roles import ROLE_ID
r = pd.read_csv("data/roles.csv"); E = np.load("data/embedding.npy")
e = umap.UMAP(n_neighbors=20, min_dist=0.25, random_state=0).fit_transform(E)
e = (e - e.min(0)) / (e.max(0) - e.min(0))
ri = r.role_id.map(ROLE_ID.index).values
pts = [[int(a * 1000), int(b * 1000), int(k)] for (a, b), k in zip(e, ri)]
json.dump({"roles": ROLE_ID, "pts": pts}, open(os.path.join(DATA, "map.json"), "w"), separators=(",", ":"))
P = np.array(pts); out = []
for k in range(11):
    idx = np.where(P[:, 2] == k)[0]; xy = P[idx, :2].astype(float)
    d = np.linalg.norm(xy - xy.mean(0), axis=1); d8 = np.linalg.norm(E[idx] - E[idx].mean(0), axis=1)
    for j in np.argsort(-d)[:2]:
        out.append(dict(role=k, i=int(idx[j]), pct8=int(100 * (d8 < d8[j]).mean())))
json.dump(out, open(os.path.join(DATA, "extremes.json"), "w"))
print("map + extremes ok")
