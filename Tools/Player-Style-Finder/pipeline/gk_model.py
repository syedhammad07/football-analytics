"""Goalkeeper style space, roles and checks.

Same method as outfield players, on the 16 goalkeeper features:
standardise (log for per-90 counts) -> PCA (85% variance) -> nearest neighbours; k-means roles chosen by
bootstrap stability; split-half re-identification test. Outputs data/gk_roles.csv, data/gk_embedding.npy, data/gk_check.json
"""
import os, json, warnings
import numpy as np, pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score, adjusted_rand_score
warnings.filterwarnings("ignore")
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
META = ["player_id", "player", "team", "league", "minutes", "matches"]


def prep(df, feats):
    X = df[feats].copy()
    for c in feats:
        if c.endswith("_p90"):
            X[c] = np.log1p(X[c])
    return X


def features_from(gm, min_minutes):
    """Rebuild per-keeper features from match rows (used for the split-half test)."""
    num = [c for c in gm.columns if c not in ("match_id", "player_id", "player", "team", "league", "top_position", "half")]
    a = gm.groupby(["player_id", "team"])[num].sum().reset_index()
    a = a[a.minutes >= min_minutes].copy()
    p90 = lambda c: a[c] / a.minutes * 90
    sh = lambda x, y: np.where(a[y] > 0, a[x] / a[y].replace(0, np.nan), 0)
    F = pd.DataFrame(dict(sot_faced_p90=p90("sot_faced"), save_pct=1 - sh("goals_conceded", "sot_faced"),
        goals_prevented_p90=(a.xg_faced - a.goals_conceded) / a.minutes * 90, xg_per_shot_faced=sh("xg_faced", "shots_faced"),
        gk_passes_p90=p90("passes"), gk_pass_cmp=sh("passes_ok", "passes"), op_pass_len=sh("op_len", "op_passes"),
        launch_share=sh("launches", "op_passes"), goal_kick_len=sh("gk_len", "goal_kicks"), short_goal_kicks=sh("gk_short", "goal_kicks"),
        sweeper_p90=p90("sweeper"), sweeper_dist=np.where(a.sweeper > 0, a.sweeper_x / a.sweeper.replace(0, np.nan), np.nan),
        gk_avg_x=sh("gk_x_sum", "gk_n"), claims_p90=p90("claims"), punches_p90=p90("punches"),
        catch_share=np.where(a.claims + a.punches > 0, a.claims / (a.claims + a.punches).replace(0, np.nan), 0)), index=a.index)
    F["sweeper_dist"] = F.sweeper_dist.fillna(F.sweeper_dist.median())
    return pd.concat([a[["player_id", "team"]], F], axis=1)


g = pd.read_csv(os.path.join(D, "gk_features.csv"))
feats = [c for c in g.columns if c not in META]
sc = StandardScaler().fit(prep(g, feats)); Z = sc.transform(prep(g, feats))
p0 = PCA(random_state=0).fit(Z)
n = int(np.searchsorted(p0.explained_variance_ratio_.cumsum(), 0.85) + 1)
pca = PCA(n, random_state=0).fit(Z); E = pca.transform(Z)
print(f"{len(feats)} features -> {n} PCs (85%)")

rng = np.random.default_rng(0); res = {}
for k in range(2, 5):
    km = KMeans(k, n_init=50, random_state=0).fit(E)
    aris = [adjusted_rand_score(km.labels_, KMeans(k, n_init=5, random_state=b).fit(E[rng.choice(len(E), len(E))]).predict(E)) for b in range(30)]
    res[k] = (silhouette_score(E, km.labels_), float(np.mean(aris)), np.bincount(km.labels_).tolist())
    print(f"k={k} silhouette={res[k][0]:.3f} stability={res[k][1]:.3f} sizes={res[k][2]}")
K = max([k for k in res if res[k][1] >= 0.7] or [2])
km = KMeans(K, n_init=50, random_state=0).fit(E)
# anchor the labels: 0 = ball-playing keeper (Lloris, Keylor Navas), 1 = long-ball keeper (Ochoa, Schmeichel)
anc = {0: ["Hugo Lloris", "Keylor Navas Gamboa"], 1: ["Francisco Guillermo Ochoa Magaña", "Kasper Schmeichel"]}
raw = {k: max(set(h := [km.labels_[i] for i, p in enumerate(g.player) if p in v]), key=h.count) for k, v in anc.items()}
assert len(set(raw.values())) == K == 2, raw
inv = {r: k for k, r in raw.items()}
km.labels_ = np.array([inv[l] for l in km.labels_]); km.cluster_centers_ = km.cluster_centers_[[raw[0], raw[1]]]
zdf = pd.DataFrame(Z, columns=feats).groupby(km.labels_).mean()
for c in range(K):
    print(f"\ncluster {c} n={(km.labels_ == c).sum()}  high: " + ", ".join(f"{k} {v:+.1f}" for k, v in zdf.loc[c].sort_values()[::-1][:5].items()))
    print("   low: " + ", ".join(f"{k} {v:+.1f}" for k, v in zdf.loc[c].sort_values()[:4].items()))
    d = np.linalg.norm(E[km.labels_ == c] - km.cluster_centers_[c], axis=1)
    print("   typical:", "; ".join(g[km.labels_ == c].assign(d=d).nsmallest(6, "d").player))
g["cluster"] = km.labels_
ds = np.sort(km.transform(E), axis=1); g["role_fit"] = 1 - ds[:, 0] / ds[:, 1] if K > 1 else 1.0
g.to_csv(os.path.join(D, "gk_roles.csv"), index=False); np.save(os.path.join(D, "gk_embedding.npy"), E)

# split-half re-identification
gm = pd.read_csv(os.path.join(D, "gk_match.csv")).sort_values("match_id")
gm["half"] = gm.groupby(["player_id", "team"]).cumcount() % 2
A = features_from(gm[gm.half == 0], 450); B = features_from(gm[gm.half == 1], 450)
key = ["player_id", "team"]; both = A[key].merge(B[key]).merge(g[key])
A = both.merge(A, on=key); B = both.merge(B, on=key)
emb = lambda df: pca.transform(sc.transform(prep(df, feats)))
dd = np.linalg.norm(emb(A)[:, None] - emb(B)[None], axis=2)
rank = (dd < np.diag(dd)[:, None]).sum(1); N = len(A)
chk = dict(n=N, top1=round(100 * float(np.mean(rank < 1)), 1), top5=round(100 * float(np.mean(rank < 5)), 1),
           random_top5=round(100 * 5 / N, 1), median_rank=int(np.median(rank)) + 1, n_pcs=n, k=K, stability=round(res[K][1], 3))
cent = km.cluster_centers_
la = np.linalg.norm(emb(A)[:, None] - cent[None], axis=2).argmin(1); lb = np.linalg.norm(emb(B)[:, None] - cent[None], axis=2).argmin(1)
chk["role_agree"] = round(100 * float(np.mean(la == lb)), 1)
json.dump(chk, open(os.path.join(D, "gk_check.json"), "w"))
print("\nsplit-half:", chk)
