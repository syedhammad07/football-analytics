"""The goalkeeper style space from gk_model.py, rebuilt without re-running the model (for seasons.py).

Refits the same scaler and PCA on data/gk_features.csv (checked against gk_embedding.npy) and takes the
role centres from data/gk_roles.csv. features_from is shared with gk_model.py.
"""
import os
import numpy as np, pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA

D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
META = ["player_id", "player", "team", "league", "minutes", "matches"]


def prep(df, feats):
    X = df[feats].copy()
    for c in feats:
        if c.endswith("_p90"):
            X[c] = np.log1p(X[c])
    return X


def features_from(gm, min_minutes):
    """Per-keeper features from match rows."""
    num = [c for c in gm.columns if c not in ("match_id", "player_id", "player", "team", "league", "top_position", "half", "season")]
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


G = pd.read_csv(os.path.join(D, "gk_roles.csv"))
FEATS = [c for c in pd.read_csv(os.path.join(D, "gk_features.csv")).columns if c not in META]
_sc = StandardScaler().fit(prep(G, FEATS)); _Z = _sc.transform(prep(G, FEATS))
_p0 = PCA(random_state=0).fit(_Z)
_pca = PCA(int(np.searchsorted(_p0.explained_variance_ratio_.cumsum(), 0.85) + 1), random_state=0).fit(_Z)
emb = lambda df: _pca.transform(_sc.transform(prep(df, FEATS)))
E = np.load(os.path.join(D, "gk_embedding.npy"))
assert np.allclose(emb(G), E, atol=1e-6), "keeper space does not reproduce gk_embedding.npy"
CENT = np.stack([E[G.cluster.values == k].mean(0) for k in sorted(G.cluster.unique())])
