"""Pick the number of style clusters: silhouette, GMM BIC and bootstrap stability."""
import os
import numpy as np, pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
from sklearn.mixture import GaussianMixture
from sklearn.metrics import silhouette_score, adjusted_rand_score

D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
f = pd.read_csv(os.path.join(D, "features.csv"))
META = ["player_id", "player", "team", "league", "position", "pos_group", "minutes", "matches", "team_poss"]
X = f.drop(columns=META)
for c in X.columns:
    if c.endswith("_p90"):
        X[c] = np.log1p(X[c])
Z = StandardScaler().fit_transform(X)
pca = PCA().fit(Z)
cum = pca.explained_variance_ratio_.cumsum()
n = int(np.searchsorted(cum, 0.85) + 1)
print("PCs for 85% variance:", n, "| first 5:", pca.explained_variance_ratio_[:5].round(3))
P = PCA(n, random_state=0).fit_transform(Z)

rng = np.random.default_rng(0)
print("k  silhouette  GMM_BIC  stability_ARI")
for k in range(4, 17):
    km = KMeans(k, n_init=20, random_state=0).fit(P)
    sil = silhouette_score(P, km.labels_)
    bic = GaussianMixture(k, covariance_type="diag", n_init=3, random_state=0).fit(P).bic(P)
    aris = []
    for b in range(10):
        idx = rng.choice(len(P), len(P), replace=True)
        kb = KMeans(k, n_init=5, random_state=b).fit(P[idx])
        aris.append(adjusted_rand_score(km.labels_, kb.predict(P)))
    print(f"{k:<3}{sil:10.3f}{bic:10.0f}{np.mean(aris):12.3f}")
