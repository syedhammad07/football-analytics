"""Style roles within position families + a global similar-player index.

k per family was chosen with explore_family.py (largest k with bootstrap stability >= 0.7).
Outputs data/roles.csv and data/similar.csv.
"""
import os, warnings
import numpy as np, pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
from sklearn.neighbors import NearestNeighbors
warnings.filterwarnings("ignore")

D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
META = ["player_id", "player", "team", "league", "position", "pos_group", "minutes", "matches", "team_poss"]
FAMILY = {"CB": "Centre-backs", "FB": "Full-backs", "DM": "Midfielders", "CM": "Midfielders",
          "AM": "Attackers", "W": "Attackers", "FW": "Attackers"}
K = {"Centre-backs": 2, "Full-backs": 2, "Midfielders": 2, "Attackers": 5}
# k-means numbers clusters arbitrarily; fix the order by anchoring each role to two well-known players
ANCHORS = {
    "Attackers": [["Mesut Özil", "Riyad Mahrez"], ["Pedro León Sánchez Gil", "Markel Susaeta Laskurain"],
                  ["José Salomón Rondón Giménez", "Shane Long"], ["Wissam Ben Yedder", "Joshua King"], ["Matt Ritchie", "Steven Davis"]],
    "Centre-backs": [["Winston Reid", "Boštjan Cesar"], ["Antonio Rüdiger", "Alessio Romagnoli"]],
    "Full-backs": [["Joel Ward", "Alberto Lora Ramos"], ["Danny Rose", "Nathaniel Edwin Clyne"]],
    "Midfielders": [["Radja Nainggolan", "Daniel Parejo Muñoz"], ["Eric Dier", "Victor Wanyama"]],
}
ROLE_NAMES = {"Attackers": ["Creative playmaker", "Touchline winger", "Target striker", "Mobile forward", "Deep wide midfielder"],
              "Centre-backs": ["Stopper", "Ball-playing centre-back"], "Full-backs": ["Defensive full-back", "Attacking full-back"],
              "Midfielders": ["Box-to-box midfielder", "Holding midfielder"]}


def canonical(labels, names, fam):
    """Map raw k-means labels to the anchored role order for this family."""
    m = {}
    for k, anchors in enumerate(ANCHORS[fam]):
        hits = [labels[i] for i, n in enumerate(names) if n in anchors]
        if not hits:
            raise ValueError(f"anchor players for {fam} role {k} not found")
        m[max(set(hits), key=hits.count)] = k
    if len(m) != K[fam]:
        raise ValueError(f"anchors for {fam} landed in the same cluster: {m}")
    return np.array([m[l] for l in labels])


def prep(df, feats):
    X = df[feats].copy()
    for c in feats:
        if c.endswith("_p90"):
            X[c] = np.log1p(X[c])
    return X


def embed(df, feats, var=0.8):
    """Standardise -> PCA keeping `var` of variance. Returns (scores, z-scores, fitted objects)."""
    sc = StandardScaler().fit(prep(df, feats))
    Z = sc.transform(prep(df, feats))
    pca = PCA(random_state=0).fit(Z)
    n = int(np.searchsorted(pca.explained_variance_ratio_.cumsum(), var) + 1)
    pca = PCA(n, random_state=0).fit(Z)
    return pca.transform(Z), Z, (sc, pca)


def main():
    f = pd.read_csv(os.path.join(D, "features.csv"))
    feats = [c for c in f.columns if c not in META]
    f["family"] = f.pos_group.map(FAMILY)
    f["role_id"], f["role_fit"] = "", np.nan
    for fam, idx in f.groupby("family").groups.items():
        g = f.loc[idx]
        P, Z, _ = embed(g, feats)
        km = KMeans(K[fam], n_init=50, random_state=0).fit(P)
        lab = canonical(km.labels_, g.player.tolist(), fam)
        d = km.transform(P)
        # reorder distance columns to the canonical labels
        inv = {raw: lab[np.where(km.labels_ == raw)[0][0]] for raw in range(K[fam])}
        d = d[:, [next(r for r, c in inv.items() if c == k) for k in range(K[fam])]]
        km.labels_ = lab
        # fit = how much closer to own centre than to the next one (0 = on the border, 1 = at centre)
        ds = np.sort(d, axis=1)
        f.loc[idx, "role_id"] = [f"{fam}:{l}" for l in km.labels_]
        f.loc[idx, "role_fit"] = 1 - ds[:, 0] / ds[:, 1]
        prof = pd.DataFrame(Z, columns=feats).groupby(km.labels_).mean()
        for c in range(K[fam]):
            m = g[km.labels_ == c]
            top = prof.loc[c].sort_values()
            ex = m.assign(d=d[km.labels_ == c, c]).query("minutes>=1800").nsmallest(8, "d")
            print(f"\n== {fam}:{c} {ROLE_NAMES[fam][c]}  n={len(m)}  {m.pos_group.value_counts().to_dict()}")
            print("  high:", ", ".join(f"{k} {v:+.1f}" for k, v in top[::-1][:7].items()))
            print("  low: ", ", ".join(f"{k} {v:+.1f}" for k, v in top[:5].items()))
            print("  typical:", "; ".join(f"{p} ({t})" for p, t in zip(ex.player, ex.team)))
    f.to_csv(os.path.join(D, "roles.csv"), index=False)


if __name__ == "__main__":
    main()
