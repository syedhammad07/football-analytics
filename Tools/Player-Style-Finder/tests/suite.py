"""Player Style Finder — full test suite (~100 checks).

A  Data integrity (site/data JSON)
B  Website maths vs the Python pipeline
C  Routing and page loading
D  Interactions
E  Layout at five screen widths
F  Accessibility, content quality and performance
G  Goalkeepers
H  Seasons (club seasons and 2015/16 halves)
I  Recent seasons (Premier League 2025/26 and 2026/27, shared stats)
Writes tests/results.json and prints a summary.
"""
import os
import json, math, random, subprocess, sys, time, re
from collections import Counter, defaultdict
import numpy as np, pandas as pd
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.dirname(HERE); STYLE = os.path.join(SITE, "pipeline", "data")
D = json.load(open(f"{SITE}/data/players.json")); T = json.load(open(f"{SITE}/data/teams.json"))
R = json.load(open(f"{SITE}/data/roles.json")); X = json.load(open(f"{SITE}/data/extras.json"))
P = D["players"]; F = D["feats"]; GKP = [p for p in P if p["fam"] == "Goalkeepers"]; OUT = [p for p in P if p["fam"] != "Goalkeepers"]; NO = len(OUT)
RES = []
S = json.load(open(f"{SITE}/data/seasons.json")); SPP = S["profiles"]; NB = len(P)
NW = json.load(open(f"{SITE}/data/now.json")); NS = len(NW["stats"])

def check(cat, name, fn):
    try:
        ok, detail = fn()
    except Exception as e:
        ok, detail = False, f"EXCEPTION: {type(e).__name__}: {e}"
    RES.append(dict(cat=cat, name=name, ok=bool(ok), detail=str(detail)[:400]))

# ======================= A. DATA INTEGRITY =======================
A = "A Data"
check(A, "1,251 outfield + 99 goalkeeper seasons exported", lambda: (NO == 1251 and len(GKP) == 99, (NO, len(GKP))))
check(A, "42 features with 42 labels", lambda: (len(F) == 42 and len(D["labels"]) == 42, (len(F), len(D["labels"]))))
check(A, "Outfield players have 42 stats, keepers 16", lambda: (all(len(p["v"]) == 42 for p in OUT) and all(len(p["v"]) == 16 for p in GKP), Counter(len(p["v"]) for p in P)))
check(A, "Style vectors: 8-D outfield, 7-D keepers", lambda: (all(len(p["e"]) == 8 for p in OUT) and all(len(p["e"]) == 7 for p in GKP), ""))
check(A, "No NaN/inf in stats or vectors", lambda: (all(all(math.isfinite(v) for v in p["v"] + p["e"]) for p in P), ""))
check(A, "All players have 900+ minutes", lambda: (min(p["min"] for p in P) >= 900, min(p["min"] for p in P)))
check(A, "Goalkeepers only in the Goalkeepers group", lambda: (all((p["p"] == "Goalkeeper") == (p["fam"] == "Goalkeepers") for p in P), ""))
check(A, "Role index valid (0–10 outfield, 11–12 keepers)", lambda: (all(0 <= p["r"] <= 10 for p in OUT) and all(p["r"] in (11, 12) for p in GKP), ""))
check(A, "Role family matches player family", lambda: (all(D["roles"][p["r"]]["family"] == p["fam"] for p in P),
      [p["n"] for p in P if D["roles"][p["r"]]["family"] != p["fam"]][:5]))
check(A, "Role fit within 0–1", lambda: (all(0 <= p["fit"] <= 1 for p in P), (min(p["fit"] for p in P), max(p["fit"] for p in P))))
check(A, "Map coordinates within 0–1000 (outfield)", lambda: (all(0 <= p["x"] <= 1000 and 0 <= p["y"] <= 1000 for p in OUT) and all(p["x"] is None for p in GKP), ""))
check(A, "Display names unique", lambda: (len({p["n"] for p in P}) == len(P), [n for n, c in Counter(p["n"] for p in P).items() if c > 1][:5]))
check(A, "No empty or placeholder names", lambda: (all(p["n"].strip() and p["n"] not in ("nan", "None") for p in P), ""))
check(A, "No doubled apostrophes in names (data quirk)", lambda: (not any("''" in p["n"] for p in P), [p["n"] for p in P if "''" in p["n"]]))
check(A, "Percentage stats within 0–1", lambda: (all(0 <= p["v"][j] <= 1 for p in OUT for j, (n, u, d) in enumerate(D["labels"]) if u == "%") and all(0 <= p["v"][j] <= 1 for p in GKP for j, (n, u, d) in enumerate(D["gk"]["labels"]) if u == "%"), ""))
check(A, "Pass completion plausible (40–97%)", lambda: (all(.4 <= p["v"][F.index("pass_cmp_pct")] <= .97 for p in OUT), ""))
check(A, "Each league has 20 clubs", lambda: (Counter(t["l"] for t in T["teams"]) == {l: 20 for l in ["Premier League", "La Liga", "Serie A", "Ligue 1"]},
      Counter(t["l"] for t in T["teams"])))
check(A, "Points = 3W + D for every club", lambda: (all(t["pts"] == 3 * t["w"] + t["d"] for t in T["teams"]), ""))
check(A, "Each club played 37–38 matches", lambda: (all(37 <= t["w"] + t["d"] + t["lo"] <= 38 for t in T["teams"]),
      [(t["t"], t["w"] + t["d"] + t["lo"]) for t in T["teams"] if t["w"] + t["d"] + t["lo"] != 38]))
check(A, "League goals for = goals against", lambda: (all(sum(t["gf"] for t in T["teams"] if t["l"] == l) == sum(t["ga"] for t in T["teams"] if t["l"] == l)
      for l in {t["l"] for t in T["teams"]}), ""))
check(A, "Real 2015/16 champions on top", lambda: ({t["l"]: t["t"] for t in T["teams"] if t["pos"] == 1} ==
      {"Premier League": "Leicester City", "La Liga": "Barcelona", "Serie A": "Juventus", "Ligue 1": "Paris Saint-Germain"}, {t["l"]: t["t"] for t in T["teams"] if t["pos"] == 1}))
check(A, "League positions 1–20 unique per league", lambda: (all(sorted(t["pos"] for t in T["teams"] if t["l"] == l) == list(range(1, 21)) for l in {t["l"] for t in T["teams"]}), ""))
check(A, "Squad lists point at players of that club", lambda: (all(P[i]["t"] == t["t"] for t in T["teams"] for i in t["squad"]), ""))
check(A, "Every qualified player appears in a squad", lambda: (sorted(i for t in T["teams"] for i in t["squad"]) == list(range(len(P))), ""))
check(A, "Team percentiles within 0–100", lambda: (all(0 <= v[1] <= 100 for t in T["teams"] for v in t["s"].values()), ""))
check(A, "Possession averages ~50% across clubs", lambda: (abs(np.mean([t["s"]["possession"][0] for t in T["teams"]]) - 50) < 1.5, np.mean([t["s"]["possession"][0] for t in T["teams"]])))
check(A, "13 roles; counts sum to 1,350", lambda: (len(R) == 13 and sum(r["n"] for r in R) == len(P), sum(r["n"] for r in R)))
check(A, "Typical players belong to their role", lambda: (all(P[i]["r"] == k for k, r in enumerate(R) for i in r["typical"]), ""))
check(A, "Extremes belong to their role", lambda: (all(P[e["i"]]["r"] == k for k, r in enumerate(R) for e in r["extremes"]), ""))
check(A, "League role-usage shares sum to 100% per family", lambda: (all(abs(sum(R[k]["use"][l] for k in range(13) if R[k]["family"] == f) - 100) < 0.6
      for f in {r["family"] for r in R} for l in R[0]["use"]), ""))
check(A, "Misfits: 6+ of 10 matches elsewhere, other family", lambda: (all(m["share"] >= .6 and m["like"] != P[m["i"]]["fam"] for m in X["misfits"]), len(X["misfits"])))
check(A, "Unique list sorted by best-match score", lambda: ([u["best"] for u in X["unique"]] == sorted(u["best"] for u in X["unique"]), [u["best"] for u in X["unique"]]))

# ======================= H. SEASONS (data) =======================
H = "H Seasons"
check(H, "Season profiles: club seasons and 2015/16 halves", lambda: (sum(p["k"] == "club" for p in SPP) > 250 and sum(p["k"] == "half" for p in SPP) > 2000, Counter(p["k"] for p in SPP)))
check(H, "Season stats and vectors have the right length", lambda: (all(len(p["v"]) == (16 if p["fam"] == "Goalkeepers" else 42) and len(p["e"]) == (7 if p["fam"] == "Goalkeepers" else 8) for p in SPP), ""))
check(H, "No NaN/inf in season profiles", lambda: (all(all(math.isfinite(v) for v in p["v"] + p["e"]) for p in SPP), ""))
check(H, "Minute floors: 900 club seasons, 600/450 halves", lambda: (all(p["min"] >= 900 for p in SPP if p["k"] == "club") and all(p["min"] >= (450 if p["fam"] == "Goalkeepers" else 600) for p in SPP if p["k"] == "half"), ""))
check(H, "Club seasons only for the club whose matches are open", lambda: ({p["t"] for p in SPP if p["k"] == "club"} == {"Barcelona", "Arsenal", "Paris Saint-Germain", "Bayer Leverkusen"}, {p["t"] for p in SPP if p["k"] == "club"}))
check(H, "Every half profile belongs to a 2015/16 player", lambda: ({(p["id"], p["t"]) for p in SPP if p["k"] == "half"} <= {(p["id"], p["t"]) for p in P}, ""))
check(H, "Season list matches the profiles", lambda: ({(x["t"], x["s"]) for x in S["seasons"]} == {(p["t"], p["s"]) for p in SPP if p["k"] == "club"}, len(S["seasons"])))
def h_reproduce():
    # the 2015/16 halves rebuilt from the match rows land in the same space: same player's halves are close to his full season
    full = {p["id"]: np.array(p["e"]) for p in OUT}
    d = [np.linalg.norm(np.array(p["e"]) - full[p["id"]]) for p in SPP if p["k"] == "half" and p["fam"] != "Goalkeepers" and p["id"] in full]
    return np.median(d) < D["scale"] * 1.2, round(float(np.median(d)), 3)
check(H, "A half season sits near the same player's full season", h_reproduce)
check(H, "Cross-season check: own 2015/16 in top 5 for adjacent seasons ≥ 70%", lambda: (S["check"]["other_seasons"]["adjacent_top5"] >= 70, S["check"]["other_seasons"]))

# ======================= I. RECENT SEASONS (data) =======================
I_ = "I Recent"
check(I_, "13 Premier League seasons, 2014/15 to 2026/27, minute floors respected", lambda: ([x["key"] for x in NW["pools"]] == [f"{y}/{str(y + 1)[-2:]}" for y in range(2014, 2027)] and all(min(b["min"] for b in x["players"]) >= x["floor"] for x in NW["pools"]) and all(len(x["players"]) > 250 for x in NW["pools"][:-1]), [(x["key"], len(x["players"])) for x in NW["pools"]]))
check(I_, "No player listed twice in one season", lambda: (all(len({(b["n"], b["t"]) for b in x["players"]}) == len(x["players"]) for x in NW["pools"]), ""))
check(I_, "No goalkeepers in the recent pools", lambda: (all(b["p"] in ("Defender", "Midfielder", "Forward") for x in NW["pools"] for b in x["players"]), ""))
check(I_, "Percentile vectors: 16 values from 1 to 99, everywhere", lambda: (all(len(v) == NS and all(1 <= t <= 99 for t in v) for v in [b["q"] for x in NW["pools"] for b in x["players"]] + [q for q in NW["base"] + NW["seasons"] if q]), NS))
check(I_, "Every outfield profile has percentiles, keepers none", lambda: (all((q is None) == (p["fam"] == "Goalkeepers") for q, p in zip(NW["base"], P)) and all((q is None) == (p["fam"] == "Goalkeepers") for q, p in zip(NW["seasons"], SPP)), ""))
def i_pct_recompute():
    x = next(p for p in NW["pools"] if p["key"] == "2025/26"); j = 0; vals = sorted(b["v"][j] for b in x["players"]); b = x["players"][7]
    lo = sum(v < b["v"][j] for v in vals); eq = sum(v == b["v"][j] for v in vals); py = min(99, max(1, round(100 * (lo + eq / 2) / len(vals)))); return abs(py - b["q"][j]) <= 1, (py, b["q"][j])
check(I_, "Stored percentiles match a recomputation", i_pct_recompute)
check(I_, "Two-provider check (all 2015/16 PL outfielders): same player first ≥ 85%", lambda: (NW["check"]["top1"] >= 85 and NW["check"]["n"] >= 250, {k: NW["check"][k] for k in ("n", "top1", "top5")}))
check(I_, "Every shared stat agrees across providers (rank corr ≥ 0.6)", lambda: (min(NW["check"]["rho"].values()) >= 0.6, min(NW["check"]["rho"].items(), key=lambda kv: kv[1])))
check(I_, "Raw values hidden for stats on different scales", lambda: (all(x["raw"] == (0.8 <= NW["check"]["ratio"][x["k"]] <= 1.25) for x in NW["stats"]) and not next(x for x in NW["stats"] if x["k"] == "touches_p90")["raw"], ""))

G = "G Keepers"
gk_csv = pd.read_csv(f"{STYLE}/gk_roles.csv")
check(G, "Keepers' save % between 55% and 90%", lambda: (all(.55 <= p["v"][D["gk"]["feats"].index("save_pct")] <= .9 for p in GKP), ""))
check(G, "Goals prevented average near zero", lambda: (abs(np.mean([p["v"][D["gk"]["feats"].index("goals_prevented_p90")] for p in GKP])) < 0.1, np.mean([p["v"][D["gk"]["feats"].index("goals_prevented_p90")] for p in GKP])))
check(G, "Every club has at least one 900-minute keeper", lambda: (all(any(P[i]["fam"] == "Goalkeepers" for i in t["squad"]) for t in T["teams"]), [t["t"] for t in T["teams"] if not any(P[i]["fam"] == "Goalkeepers" for i in t["squad"])]))
check(G, "Keeper roles anchored (Lloris ball-playing, Schmeichel long-ball)", lambda: (next(p for p in GKP if p["n"] == "Hugo Lloris")["r"] == 11 and next(p for p in GKP if p["n"] == "Kasper Schmeichel")["r"] == 12, ""))
check(G, "Keeper vectors match pipeline", lambda: (np.abs(np.array([p["e"] for p in GKP]) - np.load(f"{STYLE}/gk_embedding.npy")).max() < 1e-3, ""))
check(G, "Keeper split-half beats chance", lambda: (D["gk"]["check"]["top5"] > 3 * D["gk"]["check"]["random_top5"], D["gk"]["check"]))

# ======================= B. SITE MATHS vs PIPELINE =======================
B = "B Maths"
roles_csv = pd.read_csv(f"{STYLE}/roles.csv"); sim_csv = pd.read_csv(f"{STYLE}/similar.csv"); ex_csv = pd.read_csv(f"{STYLE}/similar_explained.csv")
E = np.array([p["e"] for p in OUT])
check(B, "Player order matches pipeline roles.csv", lambda: (len(roles_csv) == NO and all(int(a) == p["id"] for a, p in zip(roles_csv.player_id, OUT)), ""))
check(B, "Exported vectors match pipeline embedding", lambda: (np.abs(E - np.load(f"{STYLE}/embedding.npy")).max() < 1e-3, np.abs(E - np.load(f"{STYLE}/embedding.npy")).max()))
def py_top10_match():
    rnd = random.Random(1); bad = 0; n = 0
    for i in rnd.sample(range(NO), 60):
        d = np.linalg.norm(E - E[i], axis=1); d[i] = np.inf
        mine = [int(roles_csv.player_id[j]) for j in np.argsort(d)[:10]]
        ref = sim_csv[(sim_csv.player_id == P[i]["id"]) & (sim_csv.team == P[i]["t"])].sort_values("rank").similar_id.astype(int).tolist()
        n += 1; bad += mine != ref
    return bad == 0, f"{bad}/{n} players differ"
check(B, "Top-10 lists reproduce pipeline (60 players)", py_top10_match)
check(B, "Similarity reproduces similar.csv (Özil–Insigne)", lambda: (abs(100 * math.exp(-np.linalg.norm(E[[p["n"] for p in P].index("Mesut Özil")] - E[[p["n"] for p in P].index("Lorenzo Insigne")]) / (2 * D["scale"])) - float(sim_csv[(sim_csv.player == "Mesut Özil") & (sim_csv["rank"] == 1)].similarity.iloc[0])) < 0.1, ""))
check(B, "Typical best match recomputes to ~66", lambda: (abs(np.median([100 * math.exp(-np.sort(np.linalg.norm(E - E[i], axis=1))[1] / (2 * D["scale"])) for i in range(NO)]) - D["typical_best"]) < 0.5, D["typical_best"]))
twin_ok = lambda: (all(np.argsort(np.linalg.norm(E - E[t["a"]], axis=1))[1] == t["b"] and np.argsort(np.linalg.norm(E - E[t["b"]], axis=1))[1] == t["a"] for t in X["twins"]), "")
check(B, "Style twins are mutual nearest neighbours", twin_ok)

# ======================= C-F: browser =======================
srv = subprocess.Popen([sys.executable, "-m", "http.server", "8766", "-d", SITE], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(1)
URL = "http://localhost:8766/index.html"
OZ = [p["n"] for p in P].index("Mesut Özil"); MESSI = [p["n"] for p in P].index("Lionel Messi")
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path="/usr/bin/google-chrome")
    pg = br.new_page(viewport={"width": 1440, "height": 900})
    errs = []
    pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
    pg.on("pageerror", lambda e: errs.append(str(e)))
    t0 = time.time(); pg.goto(URL + "#home"); pg.wait_for_selector("h1", timeout=20000); load_s = time.time() - t0
    nav = lambda h, w=350: (pg.evaluate(f"location.hash='{h}'"), pg.wait_for_timeout(w))
    h1 = lambda: pg.evaluate("document.querySelector('#app h1, #app h2')?.innerText || ''")

    # ---- B (in-browser maths)
    def js_vs_py_sim():
        pairs = [(OZ, 0), (MESSI, 5), (10, 200), (300, 301), (999, 1000)]
        bad = []
        for a, b in pairs:
            js = pg.evaluate(f"simOf(P[{a}],P[{b}])"); py = 100 * math.exp(-np.linalg.norm(E[a] - E[b]) / (2 * D["scale"]))
            if abs(js - py) > 0.05: bad.append((a, b, js, py))
        return not bad, bad
    check(B, "Browser similarity = Python similarity", js_vs_py_sim)
    def js_overlap():
        rows = ex_csv[ex_csv.player == "Mesut Özil"].sort_values("rank")
        bad = []
        for _, r in rows.iterrows():
            j = int(roles_csv.index[(roles_csv.player_id == r.similar_id) & (roles_csv.team == r.similar_team)][0])
            o = pg.evaluate(f"explain({OZ},{j}).overlap")
            if abs(o - r.overlap_pct) > 0.6: bad.append((r.similar, o, r.overlap_pct))
        return not bad, bad
    check(B, "Browser '% alike' = pipeline (Özil's 10)", js_overlap)
    def js_alike():
        rows = ex_csv[ex_csv.player == "Mesut Özil"].sort_values("rank").head(5)
        bad = []
        for _, r in rows.iterrows():
            j = int(roles_csv.index[(roles_csv.player_id == r.similar_id) & (roles_csv.team == r.similar_team)][0])
            names = pg.evaluate(f"explain({OZ},{j}).alike.map(k=>LAB[k][0])")
            ref = [r[f"alike_{n}"].split(":")[0] for n in (1, 2, 3)]
            if names != ref: bad.append((r.similar, names, ref))
        return not bad, bad
    check(B, "Browser 'most alike' stats = pipeline", js_alike)
    def js_differ():
        rows = ex_csv[ex_csv.player == "Mesut Özil"].sort_values("rank").head(5)
        bad = []
        for _, r in rows.iterrows():
            j = int(roles_csv.index[(roles_csv.player_id == r.similar_id) & (roles_csv.team == r.similar_team)][0])
            names = pg.evaluate(f"explain({OZ},{j}).differ.map(k=>LAB[k][0])")
            ref = [r[f"differ_{n}"].split(":")[0] for n in (1, 2, 3)]
            if names != ref: bad.append((r.similar, names, ref))
        return not bad, bad
    check(B, "Browser 'biggest differences' = pipeline", js_differ)
    check(B, "Percentiles stay within 1–99", lambda: (pg.evaluate("Object.values(PF).every(r=>r.every(v=>v>=1&&v<=99)) && Object.values(PA).every(r=>r.every(v=>v>=1&&v<=99))"), ""))
    check(B, "Percentiles increase with the stat value", lambda: (pg.evaluate("""(()=>{const j=F.indexOf('key_passes_p90');const a=P.filter(p=>p.fam==='Attackers').sort((x,y)=>x.v[j]-y.v[j]);
          for(let k=1;k<a.length;k++) if(PF[a[k].i][j]<PF[a[k-1].i][j]) return false; return true})()"""), ""))
    check(B, "Özil key passes = 99th among attackers", lambda: (pg.evaluate(f"PF[{OZ}][F.indexOf('key_passes_p90')]") == 99, pg.evaluate(f"PF[{OZ}][F.indexOf('key_passes_p90')]")))

    # ---- C routing
    C = "C Routing"
    expect = [("home", "Find footballers"), ("players", "All 1,350"), (f"player-{OZ}", "Mesut Özil"), (f"compare-{OZ}-{MESSI}", "vs Lionel Messi"),
              (f"replace-{OZ}", "replace Mesut Özil"), ("roles", "13 ways"), ("role-2", "Target striker"), ("role-10", "Holding midfielder"),
              ("teams", "How each club"), ("team-0", ""), ("map", "Every outfield player"), ("misfits", "Listed in one position"), ("method", "How it works")]
    for h, want in expect:
        def f(h=h, want=want):
            errs.clear(); nav(h); t = h1()
            return (want in t if want else len(t) > 2) and not errs, f"h1='{t[:60]}' errors={errs[:2]}"
        check(C, f"#{h} loads", f)
    check(C, "Unknown page shows 'not found'", lambda: (nav("nothing-here"), "not found" in pg.inner_text("#app").lower())[1:] + ("",))
    check(C, "Bad player id shows 'not found'", lambda: (nav("player-99999"), "not found" in pg.inner_text("#app").lower())[1:] + ("",))
    check(C, "Bad role id shows 'not found'", lambda: (nav("role-42"), "not found" in pg.inner_text("#app").lower())[1:] + ("",))
    check(C, "Bad team id shows 'not found'", lambda: (nav("team-500"), "not found" in pg.inner_text("#app").lower())[1:] + ("",))
    check(C, "Bad compare ids fall back to defaults", lambda: (nav("compare-abc-xyz"), "vs" in h1())[1:] + (h1(),))
    check(C, "Compare with same player twice is avoided", lambda: (nav(f"compare-{OZ}-{OZ}"), h1().count("Mesut Özil") == 1)[1:] + (h1(),))
    check(C, "Nav highlights Players on a player page", lambda: (nav(f"player-{OZ}"), pg.evaluate("document.querySelector('#nav a.on')?.dataset.p") == "players")[1:] + ("",))
    check(C, "Tab title updates to player name", lambda: (nav(f"player-{OZ}"), pg.title().startswith("Mesut Özil"))[1:] + (pg.title(),))
    def back():
        nav("roles"); nav("role-3"); pg.go_back(); pg.wait_for_timeout(350); return "13 ways" in h1(), h1()
    check(C, "Browser Back returns to previous page", back)
    check(C, "Page scrolls to top on navigation", lambda: (nav("players"), pg.evaluate("window.scrollTo(0,2000)"), nav(f"player-{OZ}"), pg.evaluate("window.scrollY") == 0)[3:] + ("",))

    # ---- D interactions
    Dn = "D Interact"
    def s_accent():
        nav("home"); pg.fill("#homesearch input", "ozil"); pg.wait_for_timeout(150)
        return "Mesut Özil" in pg.inner_text("#homesearch .sugg"), pg.inner_text("#homesearch .sugg")[:80]
    check(Dn, "Search ignores accents ('ozil')", s_accent)
    def s_multi():
        pg.fill("#homesearch input", "silva city"); pg.wait_for_timeout(150); return "David Silva" in pg.inner_text("#homesearch .sugg"), pg.inner_text("#homesearch .sugg")[:80]
    check(Dn, "Search matches name + club words", s_multi)
    def s_kbd():
        pg.fill("#homesearch input", "kante"); pg.wait_for_timeout(150); pg.keyboard.press("Enter"); pg.wait_for_timeout(350); return "Kanté" in h1(), h1()
    check(Dn, "Search Enter opens the player", s_kbd)
    def s_esc():
        nav("home"); pg.fill("#homesearch input", "silva"); pg.wait_for_timeout(150); pg.keyboard.press("Escape"); return pg.evaluate("document.querySelector('#homesearch .sugg').hidden"), ""
    check(Dn, "Escape closes suggestions", s_esc)
    def s_none():
        pg.fill("#homesearch input", "zzzzqqq"); pg.wait_for_timeout(150); return pg.evaluate("document.querySelector('#homesearch .sugg').hidden"), ""
    check(Dn, "Nonsense search shows no list", s_none)
    def pl_filter():
        nav("players"); pg.select_option("#pllg", "Serie A"); pg.wait_for_timeout(150)
        clubs = pg.evaluate("[...document.querySelectorAll('#plbody tr td:nth-child(2)')].map(t=>t.innerText)")
        serie = {t["t"] for t in T["teams"] if t["l"] == "Serie A"}
        return clubs and all(c in serie for c in clubs), clubs[:3]
    check(Dn, "Players: league filter", pl_filter)
    def pl_role():
        pg.select_option("#plrole", "5"); pg.wait_for_timeout(150)
        roles = set(pg.evaluate("[...document.querySelectorAll('#plbody tr td:nth-child(4)')].map(t=>t.innerText)")); return roles == {"Stopper"}, roles
    check(Dn, "Players: role filter", pl_role)
    def pl_reset_count():
        pg.select_option("#pllg", "All"); pg.select_option("#plrole", "All"); pg.wait_for_timeout(150)
        return pg.evaluate("document.querySelectorAll('#plbody tr').length") == 60, pg.evaluate("document.querySelectorAll('#plbody tr').length")
    check(Dn, "Players: shows 60 rows by default", pl_reset_count)
    def pl_more():
        pg.click("#plmore"); pg.wait_for_timeout(150); return pg.evaluate("document.querySelectorAll('#plbody tr').length") == 180, ""
    check(Dn, "Players: Show more adds 120", pl_more)
    def pl_sort():
        pg.click("th[data-s='min']"); pg.wait_for_timeout(150)
        mins = pg.evaluate("[...document.querySelectorAll('#plbody tr td:nth-child(5)')].map(t=>+t.innerText.replace(/,/g,''))")
        return mins == sorted(mins), mins[:3]
    check(Dn, "Players: sort by minutes toggles", pl_sort)
    def pl_text():
        pg.fill("#plq-q", "arsenal"); pg.wait_for_timeout(150)
        clubs = set(pg.evaluate("[...document.querySelectorAll('#plbody tr td:nth-child(2)')].map(t=>t.innerText)")); return clubs == {"Arsenal"}, clubs
    check(Dn, "Players: text filter by club", pl_text)
    def pl_rowclick():
        pg.click("#plbody tr:first-child td:nth-child(3)"); pg.wait_for_timeout(350); return pg.evaluate("location.hash").startswith("#player-"), pg.evaluate("location.hash")
    check(Dn, "Players: clicking a row opens player", pl_rowclick)
    def pp_league():
        nav(f"player-{OZ}"); pg.click("#pfilt button[data-l='Ligue 1']"); pg.wait_for_timeout(150)
        lg = {s.split(" · ")[-1] for s in pg.evaluate("[...document.querySelectorAll('#plist .who small')].map(e=>e.innerText)")}; return lg == {"Ligue 1"}, lg
    check(Dn, "Player: league filter", pp_league)
    def pp_same():
        pg.click("#pfilt button[data-l='All']"); pg.check("#psame"); pg.wait_for_timeout(150)
        roles = set(pg.evaluate("[...document.querySelectorAll('#plist summary .chip')].map(e=>e.innerText)")); return roles == {"Creative playmaker"}, roles
    check(Dn, "Player: same-role toggle", pp_same)
    def pp_sorted():
        s = pg.evaluate("[...document.querySelectorAll('#plist .simcell b')].map(e=>+e.innerText)"); return s == sorted(s, reverse=True), s
    check(Dn, "Player: matches sorted by score", pp_sorted)
    def pp_details():
        pg.uncheck("#psame"); pg.wait_for_timeout(150)
        pg.click("#plist details:nth-of-type(2) summary"); pg.wait_for_timeout(100)
        return pg.evaluate("document.querySelectorAll('#plist details[open]').length") == 2, ""
    check(Dn, "Player: rows open to show 'why'", pp_details)
    def rp_excl():
        nav(f"replace-{OZ}"); clubs = pg.evaluate("[...document.querySelectorAll('#rplist .who small')].map(e=>e.innerText.split(' · ')[0])")
        return "Arsenal" not in clubs and len(clubs) == 15, len(clubs)
    check(Dn, "Replace: excludes own club, 15 results", rp_excl)
    def rp_lg():
        for l in ["Premier League", "La Liga", "Serie A"]: pg.click(f"#rplg button[data-l='{l}']")
        pg.wait_for_timeout(150); lg = {s.split(" · ")[-1] for s in pg.evaluate("[...document.querySelectorAll('#rplist .who small')].map(e=>e.innerText)")}
        return lg == {"Ligue 1"}, lg
    check(Dn, "Replace: league toggles", rp_lg)
    def rp_empty():
        pg.click("#rplg button[data-l='Ligue 1']"); pg.wait_for_timeout(150); return "No players match" in pg.inner_text("#rplist"), ""
    check(Dn, "Replace: no leagues shows a helpful message", rp_empty)
    def rp_min():
        nav("home"); nav(f"replace-{OZ}"); pg.evaluate("const r=document.querySelector('#rpmin'); r.value=2800; r.dispatchEvent(new Event('input'))"); pg.wait_for_timeout(150)
        ids = pg.evaluate("[...document.querySelectorAll('#rplist a')].map(a=>a.getAttribute('href')).filter(h=>h.startsWith('#player-')).map(h=>+h.split('-')[1])")
        mins = [P[i]["min"] for i in ids] if ids else []
        return mins and min(mins) >= 2800, mins[:5]
    check(Dn, "Replace: minimum-minutes slider", rp_min)
    def cmp_change():
        nav(f"compare-{OZ}-{MESSI}"); pg.fill("#cmpB input", "busquets"); pg.wait_for_timeout(150); pg.keyboard.press("Enter"); pg.wait_for_timeout(350)
        return "Busquets" in h1() and "Özil" in h1(), h1()
    check(Dn, "Compare: change second player", cmp_change)
    check(Dn, "Compare: radar has 14 spokes and 2 shapes", lambda: (pg.evaluate("document.querySelectorAll('#app svg polygon[fill-opacity]').length") == 2 and pg.evaluate("document.querySelectorAll('#app svg line').length") == 14, ""))
    def map_toggle():
        nav("map"); pg.click("#leg button[data-k='0']"); pg.wait_for_timeout(150)
        faded = pg.evaluate("[...document.querySelectorAll('#bigmap circle[data-i]')].filter(c=>P[+c.dataset.i].r===0 && +c.getAttribute('fill-opacity')<0.2).length")
        return faded == R[0]["n"], faded
    check(Dn, "Map: legend switches a role off", map_toggle)
    check(Dn, "Map: no goalkeepers plotted", lambda: (nav("map"), pg.evaluate("[...document.querySelectorAll('#bigmap circle[data-i]')].every(c=>P[+c.dataset.i].fam!=='Goalkeepers')"))[1:] + ("",))
    def map_search():
        pg.click("#legall"); pg.wait_for_timeout(150); pg.fill("#mapq input", "messi"); pg.wait_for_timeout(150); pg.keyboard.press("Enter"); pg.wait_for_timeout(200)
        return "Lionel Messi" in pg.inner_text("#bigmap"), ""
    check(Dn, "Map: search labels the player", map_search)
    def map_tip():
        c = pg.query_selector("#bigmap circle[data-i]"); c.hover(force=True); pg.wait_for_timeout(100)
        return pg.evaluate("document.querySelector('#bigmap .tip').style.display") == "block", ""
    check(Dn, "Map: hover shows a tooltip", map_tip)
    def map_click():
        pg.evaluate(f"document.querySelector('#bigmap circle[data-i=\"{OZ}\"]').dispatchEvent(new MouseEvent('click',{{bubbles:true}}))"); pg.wait_for_timeout(350)
        return "Mesut Özil" in h1(), h1()
    check(Dn, "Map: clicking a dot opens the player", map_click)
    def team_lg():
        nav("teams"); pg.click("#tlg button[data-l='La Liga']"); pg.wait_for_timeout(200); return "Barcelona" in pg.inner_text("#tbody").split("\n")[0], pg.inner_text("#tbody").split("\n")[0][:40]
    check(Dn, "Teams: switch league, champion first", team_lg)
    def team_click():
        pg.click("#tbody tr:first-child td:nth-child(4)"); pg.wait_for_timeout(350); return h1() == "Barcelona", h1()
    check(Dn, "Teams: row opens club page", team_click)
    check(Dn, "Team: role mix adds up to 100%", lambda: (abs(pg.evaluate("[...document.querySelectorAll('.stackbar div')].reduce((s,d)=>s+parseFloat(d.style.width),0)") - 100) < 0.5, ""))
    check(Dn, "Team: 5 similar clubs listed", lambda: (pg.evaluate("document.querySelectorAll('#app .list a[href^=\"#team-\"]').length") == 5, ""))
    def role_rows():
        nav("role-0"); n = pg.evaluate("document.querySelectorAll('#app tr[data-i]').length"); return n == R[0]["n"], n
    check(Dn, "Role: lists every member", role_rows)

    # ---- E layout
    Ecat = "E Layout"
    keyp = ["home", "players", f"player-{OZ}", f"player-{[p['n'] for p in P].index('Hugo Lloris')}", "role-11", f"compare-{OZ}-{MESSI}", f"replace-{OZ}", "role-0", "teams", "team-0", "map", "misfits", "method"]
    for w in (320, 390, 768, 1024, 1440):
        pg.set_viewport_size({"width": w, "height": 900})
        bad = []
        for h in keyp:
            nav(h, 300)
            sw, cw = pg.evaluate("[document.documentElement.scrollWidth, document.documentElement.clientWidth]")
            if sw > cw + 1: bad.append((h, sw))
        check(Ecat, f"No sideways scroll at {w}px (11 pages)", lambda bad=bad: (not bad, bad))
    pg.set_viewport_size({"width": 390, "height": 900})
    def clipped():
        bad = []
        for h in keyp:
            nav(h, 300)
            n = pg.evaluate("""[...document.querySelectorAll('#app *')].filter(e=>{const s=getComputedStyle(e);if(s.overflow!=='hidden'&&s.textOverflow!=='ellipsis')return false;
               return e.scrollWidth>e.clientWidth+2 && s.textOverflow!=='ellipsis' && e.children.length===0}).length""")
            if n: bad.append((h, n))
        return not bad, bad
    check(Ecat, "No hard-clipped text at 390px", clipped)
    def tap():
        nav(f"player-{OZ}"); small = pg.evaluate("[...document.querySelectorAll('#app button, #app summary, #app .pill')].filter(e=>e.offsetParent&&e.getBoundingClientRect().height<28).length")
        return small == 0, f"{small} controls under 28px tall"
    check(Ecat, "Tap targets at least 28px tall (phone)", tap)
    def navreach():
        nav("home"); return pg.evaluate("(()=>{const n=document.querySelector('#nav');return n.scrollWidth>n.clientWidth || [...n.querySelectorAll('a')].every(a=>a.getBoundingClientRect().right<=n.getBoundingClientRect().right+1)})()"), ""
    check(Ecat, "Phone nav: all links reachable (scrollable row)", navreach)
    pg.set_viewport_size({"width": 1440, "height": 900})
    def navfits():
        nav("home"); return pg.evaluate("(()=>{const n=document.querySelector('#nav');return n.scrollWidth<=n.clientWidth+1})()"), pg.evaluate("[document.querySelector('#nav').scrollWidth,document.querySelector('#nav').clientWidth]")
    check(Ecat, "Desktop nav fits without hidden links", navfits)
    def navfits1180():
        pg.set_viewport_size({"width": 1200, "height": 900}); nav("home")
        r = pg.evaluate("[document.querySelector('#nav').scrollWidth,document.querySelector('#nav').clientWidth]"); pg.set_viewport_size({"width": 1440, "height": 900})
        return r[0] <= r[1] + 1, r
    check(Ecat, "Nav fits at 1,200px (with search)", navfits1180)

    # ---- F accessibility, content, performance
    Fc = "F Quality"
    check(Fc, "First load under 3 seconds (local)", lambda: (load_s < 3, f"{load_s:.2f}s"))
    check(Fc, "players.json under 1 MB", lambda: (__import__("os").path.getsize(f"{SITE}/data/players.json") < 1_000_000, __import__("os").path.getsize(f"{SITE}/data/players.json")))
    def noundef():
        bad = []
        for h in keyp + ["role-5", "team-60", f"player-{MESSI}"]:
            nav(h, 300); t = pg.inner_text("#app")
            for w in ("undefined", "NaN", "null", "[object"):
                if re.search(rf"\b{re.escape(w)}\b", t): bad.append((h, w))
        return not bad, bad
    check(Fc, "No 'undefined'/'NaN'/'null' text on 14 pages", noundef)
    check(Fc, "Every page has exactly one h1", lambda: (all((nav(h, 250), pg.evaluate("document.querySelectorAll('#app h1').length") == 1)[1] for h in keyp), ""))
    def alts():
        return pg.evaluate("[...document.images].every(i=>i.alt)"), ""
    check(Fc, "Images have alt text", alts)
    def logo_loaded():
        nav("method"); return pg.evaluate("[...document.images].every(i=>i.complete&&i.naturalWidth>0)"), ""
    check(Fc, "StatsBomb logo loads", logo_loaded)
    def labels():
        bad = []
        for h in ["home", "players", f"replace-{OZ}", "map", f"compare-{OZ}-{MESSI}"]:
            nav(h, 250)
            bad += pg.evaluate("""[...document.querySelectorAll('input,select')].filter(e=>!(e.getAttribute('aria-label')||(e.id&&document.querySelector('label[for="'+e.id+'"]'))||e.closest('label'))).map(e=>e.outerHTML.slice(0,60))""")
        return not bad, bad[:3]
    check(Fc, "Every input and select has a label", labels)
    def ids():
        bad = []
        for h in ["home", "players", f"replace-{OZ}", "map", f"compare-{OZ}-{MESSI}"]:
            nav(h, 250); bad += pg.evaluate("[...document.querySelectorAll('input,select')].filter(e=>!e.id).map(e=>e.outerHTML.slice(0,50))")
        return not bad, bad[:3]
    check(Fc, "Every form control has an id", ids)
    def dup_ids():
        nav(f"player-{OZ}"); c = pg.evaluate("(()=>{const m={};document.querySelectorAll('[id]').forEach(e=>m[e.id]=(m[e.id]||0)+1);return Object.entries(m).filter(([k,v])=>v>1)})()")
        return not c, c
    check(Fc, "No duplicate element ids", dup_ids)
    def kbd_focus():
        nav("home"); pg.keyboard.press("Tab"); pg.keyboard.press("Tab")
        o = pg.evaluate("getComputedStyle(document.activeElement).outlineStyle"); return o != "none", o
    check(Fc, "Keyboard focus is visible", kbd_focus)
    def contrast_text():
        bad = []
        for h in keyp:
            nav(h, 250)
            bad += pg.evaluate("""[...document.querySelectorAll('body *')].filter(e=>e.offsetParent!==null && [...e.childNodes].some(n=>n.nodeType===3&&n.nodeValue.trim()) && getComputedStyle(e).color==='rgb(93, 104, 134)').map(e=>e.tagName+':'+e.textContent.trim().slice(0,30))""")
        return not bad, bad[:5]
    check(Fc, "No visible text in the low-contrast faint colour", contrast_text)
    def contrast():
        def lum(h):
            c = [int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)]; c = [x / 12.92 if x <= .03928 else ((x + .055) / 1.055) ** 2.4 for x in c]
            return .2126 * c[0] + .7152 * c[1] + .0722 * c[2]
        ratio = lambda a, b: (max(lum(a), lum(b)) + .05) / (min(lum(a), lum(b)) + .05)
        res = {k: round(ratio(v, "#111830"), 2) for k, v in {"text": "#EAEEF8", "muted": "#8E99B5", "accent": "#F5B13D"}.items()}
        return all(v >= 4.5 for v in res.values()), res
    check(Fc, "Text colours in use meet WCAG AA 4.5:1", contrast)
    def details_kbd():
        nav(f"player-{OZ}"); pg.focus("#plist details:nth-of-type(2) summary"); pg.keyboard.press("Enter"); pg.wait_for_timeout(100)
        return pg.evaluate("document.querySelectorAll('#plist details[open]').length") == 2, ""
    check(Fc, "Match rows open with the keyboard", details_kbd)
    def map_kbd():
        nav("home"); nav("map"); pg.focus("#bigmap .mapwrap"); pg.keyboard.press("ArrowRight"); pg.keyboard.press("ArrowRight"); pg.wait_for_timeout(100)
        tip = pg.evaluate("document.querySelector('#bigmap .tip').style.display")
        pg.keyboard.press("Enter"); pg.wait_for_timeout(350)
        return tip == "block" and pg.evaluate("location.hash").startswith("#player-"), (tip, pg.evaluate("location.hash"))
    check(Fc, "Map dots reachable by keyboard", map_kbd)
    def reduced():
        return "prefers-reduced-motion" in open(f"{SITE}/index.html").read(), ""
    check(Fc, "Respects reduced-motion setting", reduced)
    def credit():
        bad = [h for h in keyp if (nav(h, 200), "StatsBomb" not in pg.inner_text("footer"))[1]]; return not bad, bad
    check(Fc, "StatsBomb credit on every page", credit)
    def external_fonts():
        return "fonts.googleapis.com" in open(f"{SITE}/index.html").read(), "fonts load from Google; offline fallback = system fonts"
    check(Fc, "Fonts load from an allowed source", external_fonts)
    def mobile_matchrow():
        pg.set_viewport_size({"width": 390, "height": 900}); nav(f"player-{OZ}")
        hidden = pg.evaluate("getComputedStyle(document.querySelector('#plist summary .chip')).display")
        pg.set_viewport_size({"width": 1440, "height": 900}); return hidden == "none", f"role chip on phone rows display={hidden} (role not shown on phone)"
    check(Fc, "Phone match rows stay uncluttered", mobile_matchrow)
    def phone_role_visible():
        pg.set_viewport_size({"width": 390, "height": 900}); nav(f"player-{OZ}")
        vis = pg.evaluate("[...document.querySelectorAll('#plist summary')].every(s=>/playmaker|midfielder|winger|forward|striker|back/i.test(s.innerText))")
        pg.set_viewport_size({"width": 1440, "height": 900}); return vis, "phone rows hide the role and % alike until opened"
    check(Fc, "Phone match rows still show each match's role", phone_role_visible)
    GKI = [p["n"] for p in P].index("Hugo Lloris"); BRAVO = next(i for i, p in enumerate(P) if p["fam"] == "Goalkeepers" and "Bravo" in p["n"])
    def gk_page():
        errs.clear(); nav(f"player-{GKI}"); t = pg.inner_text("#app")
        return "Save percentage" in t and "Goals prevented" in t and not errs, errs[:2]
    check(G, "Keeper page shows keeper stats", gk_page)
    def gk_nb():
        nb = pg.evaluate(f"neighbours({GKI}).map(x=>x.b.fam)"); return set(nb) == {"Goalkeepers"} and len(nb) == 10, set(nb)
    check(G, "Keeper matches are all keepers", gk_nb)
    def out_nb():
        nb = pg.evaluate(f"neighbours({OZ}).map(x=>x.b.fam)"); return "Goalkeepers" not in nb, set(nb)
    check(G, "Outfield matches never include keepers", out_nb)
    def gk_mixed():
        nav(f"compare-{OZ}-{GKI}"); t = h1(); return "Lloris" not in t, t
    check(G, "Compare refuses outfield vs keeper", gk_mixed)
    def gk_cmp():
        errs.clear(); nav(f"compare-{GKI}-{BRAVO}"); return "Lloris" in h1() and "Bravo" in h1() and pg.evaluate("document.querySelectorAll('#app svg line').length") == 12 and not errs, (h1(), errs[:2])
    check(G, "Keeper vs keeper compare with 12-spoke radar", gk_cmp)
    def gk_units():
        nav(f"player-{GKI}"); t = pg.inner_text("#app"); m = re.search(r"Goal-kick length\s*\n?\s*([0-9.]+) m", t); return bool(m) and 30 < float(m.group(1)) < 75, m.group(0) if m else t[:0]
    check(G, "Goal-kick length shown in metres, plausible", gk_units)
    def gk_role():
        errs.clear(); nav("role-11"); return "Ball-playing keeper" in h1() and pg.evaluate("document.querySelectorAll('#app tr[data-i]').length") == R[11]["n"] and not errs, errs[:2]
    check(G, "Keeper role page lists all members", gk_role)
    def gk_replace():
        errs.clear(); nav(f"replace-{GKI}"); ids = pg.evaluate("[...document.querySelectorAll('#rplist a')].map(a=>a.getAttribute('href')).filter(h=>h.startsWith('#player-')).map(h=>+h.split('-')[1])")
        return ids and all(P[i]["fam"] == "Goalkeepers" and P[i]["t"] != "Tottenham Hotspur" for i in ids) and not errs, len(ids)
    check(G, "Replace a keeper suggests other clubs' keepers", gk_replace)
    def gk_team():
        nav("team-0"); return pg.evaluate("[...document.querySelectorAll('#app tr[data-i]')].some(tr=>P[+tr.dataset.i].fam==='Goalkeepers')"), ""
    check(G, "Club squads include their keeper", gk_team)
    def gk_search():
        nav("home"); pg.fill("#homesearch input", "buffon"); pg.wait_for_timeout(150); return "Buffon" in pg.inner_text("#homesearch .sugg"), ""
    check(G, "Search finds keepers", gk_search)
    def units_out():
        nav(f"player-{[p['n'] for p in P].index('Sergio Busquets')}"); t = pg.inner_text("#app")
        ok = pg.evaluate(f"fmt(P[{OZ}], F.indexOf('avg_pass_len'), 20)") == "18.3 m"; return ok, pg.evaluate(f"fmt(P[{OZ}], F.indexOf('avg_pass_len'), 20)")
    check(F_cat := "F Quality", "Pass length converted from yards to metres", units_out)
    # ======================= H. SEASONS (browser) =======================
    XAVI = pg.evaluate("SP.find(p => p.n === 'Xavi' && p.s === '2008/09').i"); MESSI = [p["n"] for p in P].index("Lionel Messi")
    def h_maths():
        a = np.array(SPP[XAVI - NB]["e"]); out = [(p["n"], np.linalg.norm(np.array(p["e"]) - a)) for p in OUT if p["id"] != SPP[XAVI - NB]["id"]]
        py = [n for n, _ in sorted(out, key=lambda x: x[1])[:5]]; js = pg.evaluate(f"neighbours({XAVI}, () => true, 5).map(x => x.b.n)"); return py == js, (py, js)
    check(H, "Season matches in the browser equal numpy's", h_maths)
    def h_pct():
        q = SPP[XAVI - NB]; j = F.index("passes_p90"); vals = sorted(p["v"][j] for p in OUT if p["fam"] == q["fam"])
        lo = sum(v < q["v"][j] for v in vals); eq = sum(v == q["v"][j] for v in vals); py = min(99, max(1, round(100 * (lo + eq / 2) / len(vals))))
        js = pg.evaluate(f"PF[{XAVI}][F.indexOf('passes_p90')]"); return py == js, (py, js)
    check(H, "Season percentiles measured against the 2015/16 pool", h_pct)
    def h_self():
        bad = pg.evaluate("SP.filter((p, k) => k % 7 === 0).filter(p => neighbours(p.i, () => true, 10).some(x => x.b.id === p.id)).length"); return bad == 0, bad
    check(H, "A season never matches the same player", h_self)
    def h_page():
        errs.clear(); nav(f"player-{XAVI}")
        on = pg.evaluate("[...document.querySelectorAll('.seastrip a[aria-current]')].map(a => a.textContent)")
        rows = pg.evaluate("document.querySelectorAll('.seatab tbody tr').length"); n = pg.evaluate(f"BYID[ALL[{XAVI}].id].length")
        return h1() == "Xavi" and on == ["08/09"] and rows == n and "2008/09" in pg.title() and not errs, (h1(), on, rows, n, errs[:2])
    check(H, "Past-season player page: strip, season table, title", h_page)
    def h_strip_nav():
        nav(f"player-{XAVI}"); pg.click(".seastrip a:has-text('10/11')"); pg.wait_for_timeout(300); return "2010/11" in pg.title(), pg.title()
    check(H, "Season strip switches season", h_strip_nav)
    def h_base_table():
        nav(f"player-{MESSI}"); cells = pg.evaluate("[...document.querySelectorAll('.seatab tr.cur td')].map(t => t.innerText.trim())")
        return bool(cells) and cells[0].startswith("2015/16") and cells[5] == "–", cells
    check(H, "2015/16 page lists his other seasons, current row marked", h_base_table)
    def h_replace():
        errs.clear(); nav(f"replace-{XAVI}"); ids = pg.evaluate("[...document.querySelectorAll('#rplist summary')].map(s => +s.parentElement.dataset.j)")
        return ids and all(i < NB and P[i]["t"] != "Barcelona" for i in ids) and "08/09" in h1() and not errs, (h1(), len(ids))
    check(H, "Replace a past season: 2015/16 players at other clubs", h_replace)
    def h_replace_strip():
        nav(f"replace-{MESSI}"); return pg.evaluate("[...document.querySelectorAll('.seastrip a')].every(a => a.getAttribute('href').startsWith('#replace-'))"), ""
    check(H, "Replace page season strip stays on Replace", h_replace_strip)
    def h_compare():
        errs.clear(); nav(f"compare-{XAVI}-{MESSI}"); return "Xavi 08/09" in h1() and pg.evaluate("document.querySelectorAll('#app svg polygon').length") >= 6 and not errs, (h1(), errs[:2])
    check(H, "Compare a past season with a 2015/16 player", h_compare)
    def h_seasons_all():
        errs.clear(); bad = []
        for k in range(len(S["seasons"])):
            nav(f"seasons-{k}"); n = pg.evaluate("document.querySelectorAll('#app tbody tr[data-i]').length")
            want = sum(p["k"] == "club" and p["t"] == S["seasons"][k]["t"] and p["s"] == S["seasons"][k]["s"] for p in SPP)
            if n != want: bad.append((k, n, want))
        return not bad and not errs, (bad, errs[:2])
    check(H, "Every club-season page lists its whole squad", h_seasons_all)
    def h_search():
        nav("home"); pg.fill("#homesearch input", "xavi"); pg.wait_for_timeout(150); t = pg.inner_text("#homesearch .sugg"); pg.keyboard.press("Enter"); pg.wait_for_timeout(300)
        return "Barcelona" in t and pg.title().startswith("Xavi "), (t[:80], pg.title())
    check(H, "Search finds players who only have past seasons", h_search)
    def h_phone():
        ph = br.new_page(viewport={"width": 360, "height": 800}); ph.goto(URL + f"#seasons"); ph.wait_for_timeout(600); w1 = ph.evaluate("document.documentElement.scrollWidth")
        ph.goto(URL + f"#player-{XAVI}"); ph.wait_for_timeout(600); w2 = ph.evaluate("document.documentElement.scrollWidth"); ph.close(); return w1 <= 360 and w2 <= 360, (w1, w2)
    check(H, "No sideways scroll on season pages at 360 px", h_phone)
    # ======================= I. RECENT SEASONS (browser) =======================
    CR = [p["n"] for p in P].index("Cristiano Ronaldo")
    def i_maths():
        q = np.array(NW["base"][CR]); x = next(p for p in NW["pools"] if p["key"] == "2025/26"); Q = np.array([b["q"] for b in x["players"]]); g = np.abs(Q - q).mean(1)
        py = [x["players"][j]["n"] for j in sorted(range(len(g)), key=lambda j: (g[j], j))[:5]]
        js = pg.evaluate(f"nowMatches(P[{CR}], poolOf('2025'), () => true, 5).map(x => x.b.n)"); return py == js, (py, js)
    check(I_, "Browser stat matches equal numpy's", i_maths)
    def i_dropdown():
        errs.clear(); nav(f"player-{CR}"); pg.select_option("#pfin", "2025"); pg.wait_for_timeout(300)
        rows = pg.evaluate("document.querySelectorAll('#plist > details').length"); h = pg.evaluate("location.hash")
        return rows == 10 and h.endswith("~2025") and "2025/26" in pg.inner_text("#psec") and not errs, (rows, h, errs[:2])
    check(I_, "Find in 2025/26 lists 10 Premier League players and updates the link", i_dropdown)
    def i_why():
        t = pg.inner_text("#pwhy").lower(); return "stat match" in t and "stats within 10 points" in t and "most alike" in t, t[:80]
    check(I_, "Why panel explains a stat match", i_why)
    def i_pos():
        pg.click("#pfilt button[data-pos='Midfielder']"); pg.wait_for_timeout(200)
        return pg.evaluate("[...document.querySelectorAll('#plist > details > summary .chip')].every(c => c.textContent.startsWith('Midfielder'))"), ""
    check(I_, "Position filter works in recent seasons", i_pos)
    def i_deeplink():
        nav(f"player-{CR}~2026"); return pg.evaluate("$('#pfin').value") == "2026" and "2026/27" in pg.inner_text("#psec"), pg.evaluate("$('#pfin').value")
    check(I_, "A link with ~2026 opens on 2026/27", i_deeplink)
    def i_back():
        pg.select_option("#pfin", "sb"); pg.wait_for_timeout(300); return pg.evaluate("location.hash") == f"#player-{CR}" and pg.evaluate("document.querySelectorAll('#plist > details').length") == 10, pg.evaluate("location.hash")
    check(I_, "Switching back to 2015/16 restores the style matches", i_back)
    def i_replace():
        errs.clear(); nav(f"replace-{XAVI}~2025"); pg.select_option("#rpval", str(int(25e6))); pg.wait_for_timeout(300)
        n = pg.evaluate("document.querySelectorAll('#rplist > details').length")
        names = pg.evaluate("[...document.querySelectorAll('#rplist > details')].map(d => +d.dataset.j)")
        pool = next(p for p in NW["pools"] if p["key"] == "2025/26")["players"]; ok = n > 0 and all(pool[j]["mv"] is not None and pool[j]["mv"] <= 25e6 for j in names)
        return ok and pg.evaluate("document.querySelector('.sb').hidden") and not errs, (n, errs[:2])
    check(I_, "Replace a past season in 2025/26 under a value cap", i_replace)
    def i_gk():
        nav(f"player-{GKI}"); o = pg.evaluate("[...$('#pfin').options].map(o => o.disabled)"); return o == [False] + [True] * 13, o
    check(I_, "Goalkeepers cannot pick the Premier League seasons", i_gk)
    def i_hist():
        errs.clear(); nav(f"player-{CR}~2014"); rows = pg.evaluate("document.querySelectorAll('#plist > details').length")
        return rows == 10 and "2014/15" in pg.inner_text("#psec") and not errs, (rows, errs[:2])
    check(I_, "An older season (2014/15) lists 10 players", i_hist)
    def i_hist_replace():
        errs.clear(); nav(f"replace-{CR}~2019"); return pg.evaluate("$('#rpvalbox').hidden") and pg.evaluate("document.querySelectorAll('#rplist > details').length") > 0 and not errs, errs[:2]
    check(I_, "Replace in a season without market values hides the value filter", i_hist_replace)
    def i_phone():
        ph = br.new_page(viewport={"width": 360, "height": 800}); ph.goto(URL + f"#player-{CR}~2025"); ph.wait_for_timeout(700)
        w1 = ph.evaluate("document.documentElement.scrollWidth"); ph.goto(URL + f"#replace-{CR}~2026"); ph.wait_for_timeout(700)
        w2 = ph.evaluate("document.documentElement.scrollWidth"); ph.close(); return w1 <= 360 and w2 <= 360, (w1, w2)
    check(I_, "No sideways scroll with recent seasons at 360 px", i_phone)
    def ordinals():
        bad = []
        for h in [f"player-{CR}", f"player-{XAVI}", f"player-{GKI}", f"compare-{CR}-{XAVI}"]:
            nav(h); t = pg.inner_text("#app"); bad += re.findall(r"\b\d*(?:1th|2th|3th)\b", t.replace("11th", "").replace("12th", "").replace("13th", ""))
        return not bad, bad[:5]
    check(Fc, "Percentiles use correct ordinals (1st, 2nd, 63rd)", ordinals)
    check(Fc, "No console errors during the whole run", lambda: (not errs, errs[:3]))
    br.close()
srv.terminate()

json.dump(RES, open(os.path.join(HERE, "results.json"), "w"), indent=1, ensure_ascii=False)
tot = len(RES); ok = sum(r["ok"] for r in RES)
print(f"\nTOTAL {ok}/{tot} passed = {100 * ok / tot:.1f}%\n")
for cat in sorted({r["cat"] for r in RES}):
    rs = [r for r in RES if r["cat"] == cat]; print(f"{cat:12} {sum(r['ok'] for r in rs)}/{len(rs)}")
print("\nFAILURES:")
for r in RES:
    if not r["ok"]: print(f" ✗ [{r['cat']}] {r['name']}  →  {r['detail']}")
