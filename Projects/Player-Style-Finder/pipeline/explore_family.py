"""Choose k within each position family by silhouette and bootstrap stability."""
import os, warnings
import numpy as np, pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score, adjusted_rand_score
warnings.filterwarnings("ignore")

D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
f = pd.read_csv(os.path.join(D, "features.csv"))
META = ["player_id", "player", "team", "league", "position", "pos_group", "minutes", "matches", "team_poss"]
FEATS = [c for c in f.columns if c not in META]
FAMILY = {"CB": "Centre-backs", "FB": "Full-backs", "DM": "Midfielders", "CM": "Midfielders",
          "AM": "Attackers", "W": "Attackers", "FW": "Attackers"}
f["family"] = f.pos_group.map(FAMILY)
rng = np.random.default_rng(0)
for fam, g in f.groupby("family"):
    X = g[FEATS].copy()
    for c in FEATS:
        if c.endswith("_p90"): X[c] = np.log1p(X[c])
    Z = StandardScaler().fit_transform(X)
    pca = PCA(random_state=0).fit(Z)
    n = int(np.searchsorted(pca.explained_variance_ratio_.cumsum(), 0.8) + 1)
    P = PCA(n, random_state=0).fit_transform(Z)
    print(f"\n{fam} (n={len(g)}, {n} PCs)")
    for k in range(2, 7):
        km = KMeans(k, n_init=30, random_state=0).fit(P)
        aris = [adjusted_rand_score(km.labels_, KMeans(k, n_init=5, random_state=b)
                .fit(P[rng.choice(len(P), len(P))]).predict(P)) for b in range(15)]
        print(f"  k={k} sil={silhouette_score(P, km.labels_):.3f} stab={np.mean(aris):.3f} sizes={np.bincount(km.labels_).tolist()}")
