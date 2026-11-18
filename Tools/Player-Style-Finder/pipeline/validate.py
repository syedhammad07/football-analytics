"""Checks for the similar-player search and the roles.

1. Split-half re-identification: build each player's features from odd and even matches
   separately. If style is a real, stable fingerprint, a player's odd-half profile should
   find his own even-half profile among everyone's. Report top-1 / top-5 / top-10 hit rates
   against the random baseline.
2. Role agreement between halves (assign each half to the nearest role centre).
3. Team leakage: how often a player's top-5 neighbours are his own team-mates.
Also writes data/similar.csv (top-10 neighbours in the full-season embedding).
"""
import os, warnings
import numpy as np, pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.neighbors import NearestNeighbors
from make_features import build
from roles import prep, META, FAMILY
warnings.filterwarnings("ignore")

D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
pm = pd.read_csv(os.path.join(D, "player_match.csv"))
full = pd.read_csv(os.path.join(D, "roles.csv"))
FEATS = [c for c in full.columns if c not in META + ["family", "role_id", "role_fit"]]

# global embedding fitted on full seasons
sc = StandardScaler().fit(prep(full, FEATS))
Zf = sc.transform(prep(full, FEATS))
p0 = PCA(random_state=0).fit(Zf)
n = int(np.searchsorted(p0.explained_variance_ratio_.cumsum(), 0.85) + 1)
pca = PCA(n, random_state=0).fit(Zf)
emb = lambda df: pca.transform(sc.transform(prep(df, FEATS)))
print(f"embedding: {len(FEATS)} features -> {n} PCs (85% variance)")

# --- 1. split-half re-identification
pm = pm.sort_values("match_id")
pm["half"] = pm.groupby(["player_id", "team"]).cumcount() % 2
A = build(pm[pm.half == 0], min_minutes=600)
B = build(pm[pm.half == 1], min_minutes=600)
key = ["player_id", "team"]
both = A[key].merge(B[key]).merge(full[key])
A = both.merge(A, on=key); B = both.merge(B, on=key)
EA, EB = emb(A), emb(B)
d = np.linalg.norm(EA[:, None, :] - EB[None, :, :], axis=2)
rank = (d < np.diag(d)[:, None]).sum(1)  # 0 = own other half is the nearest
N = len(A)
print(f"\n1) split-half re-identification over {N} players (search pool = {N})")
for k in (1, 5, 10):
    print(f"   top-{k}: {np.mean(rank < k):.1%}   (random: {k / N:.1%})")
print(f"   median rank of own other half: {int(np.median(rank)) + 1} of {N}")

# within the same position family only (harder, fairer test)
fam = A.pos_group.map(FAMILY).values
r2 = np.array([(d[i, fam == fam[i]] < d[i, i]).sum() for i in range(N)])
print("   within family: top-1 {:.1%}, top-5 {:.1%}".format(np.mean(r2 < 1), np.mean(r2 < 5)))

# --- 2. role agreement between halves
agree, tot = 0, 0
for f_name, g in full.groupby("family"):
    s2 = StandardScaler().fit(prep(g, FEATS)); Z = s2.transform(prep(g, FEATS))
    pp = PCA(random_state=0).fit(Z)
    k = int(np.searchsorted(pp.explained_variance_ratio_.cumsum(), 0.8) + 1)
    pp = PCA(k, random_state=0).fit(Z); P = pp.transform(Z)
    labs = g.role_id.values
    cents = {r: P[labs == r].mean(0) for r in np.unique(labs)}
    names = list(cents); C = np.stack([cents[r] for r in names])
    m = A.pos_group.map(FAMILY) == f_name
    pa = pp.transform(s2.transform(prep(A[m], FEATS))); pb = pp.transform(s2.transform(prep(B[m], FEATS)))
    la = np.linalg.norm(pa[:, None] - C[None], axis=2).argmin(1)
    lb = np.linalg.norm(pb[:, None] - C[None], axis=2).argmin(1)
    print(f"2) {f_name:<13} halves get the same role: {np.mean(la == lb):.1%}  (chance ≈ {1/len(names):.0%})")
    agree += (la == lb).sum(); tot += len(la)
print(f"   overall: {agree / tot:.1%}")

# --- 3. similar-player index + team leakage
E = emb(full)
nn = NearestNeighbors(n_neighbors=11).fit(E)
dist, idx = nn.kneighbors(E)
same_team = np.mean([(full.team.values[idx[i, 1:6]] == full.team.values[i]).mean() for i in range(len(full))])
team_share = full.team.value_counts(normalize=True)
base = (full.team.map(team_share) - 1 / len(full)).mean()
print(f"\n3) top-5 neighbours from the same team: {same_team:.1%} (random ≈ {base:.1%})")
scale = np.median(dist[:, 1:6])
rows = []
for i in range(len(full)):
    for r in range(1, 11):
        j = idx[i, r]
        rows.append(dict(player_id=full.player_id[i], player=full.player[i], team=full.team[i], rank=r,
                         similar_id=full.player_id[j], similar=full.player[j], similar_team=full.team[j],
                         similar_league=full.league[j], similar_role=full.role_id[j],
                         similarity=round(float(100 * np.exp(-dist[i, r] / (2 * scale))), 1)))
pd.DataFrame(rows).to_csv(os.path.join(D, "similar.csv"), index=False)
np.save(os.path.join(D, "embedding.npy"), E)
