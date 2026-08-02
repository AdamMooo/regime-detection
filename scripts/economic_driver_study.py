"""Economic-driver STRUCTURAL sleeve study.

Structural characterization, NOT a tactical model (see .planning/PORTFOLIO-CONSTITUTION.md).
Phase 1 = learn the asset relationships FIRST, with no assumed macro states: enumerate the large
equity-drawdown episodes (the events that threaten the -30% budget) and look at what each sleeve
actually did, then contrast full-sample vs crash-conditional correlation to the core. The drivers
(growth/inflation/real-rate/liquidity/risk-appetite) are HYPOTHESES the data may support or simplify,
carried here only as a macro *signature* per episode — not as buckets we condition on.

Sleeves (monthly total returns):
- equity   : broad US market (French mkt_ret), 1926+          [the CORE — reference for corr]
- bond10   : synthetic constant-maturity 10y TR, 1962+        [ballast]
- gold     : LBMA monthly 1833+, used only post-1971 float    [inflation/crisis diversifier]
- commod   : investable BCOM/GSCI index (yfinance), ~1991+    [the exposure we'd actually own]
- cash     : French daily rf compounded monthly, 1926+        [real-rate + liquidity cover]
- trend    : TSMOM trend proxy, 2005+                          [trending-crisis diversifier]

Driver-proxy candidates (observable at month t; the hypothesis set, not yet tested/simplified):
- cpi_yoy       : CPIAUCSL 12m %                (inflation)
- real_rate     : DGS10 month-end minus cpi_yoy (real-rate / discount-rate; the 2022 axis)
- credit_spread : Moody's BAA minus AAA         (liquidity / financial stress; long history)
- growth        : INDPRO 12m %                  (real growth)
- eq_vol        : realized 21d equity vol, ann. (risk appetite / volatility)
- ppi_yoy       : PPIACO 12m %                  (spot inflation, cross-check; NOT a sleeve return)

Writes data/processed/econ_driver_monthly.csv, gold_monthly_1833.csv,
results/drawdown_episodes.csv, results/conditional_corr.csv.
"""

import io
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
GOLD_1833_URL = "https://raw.githubusercontent.com/datasets/gold-prices/main/data/monthly.csv"
GOLD_FLOAT_START = "1971-08"   # Bretton Woods ends; pre-1971 gold returns are ~0 by construction
CRASH_DD = -0.10               # peak-to-current drawdown that defines "core under pressure"
SLEEVES = ["equity", "bond10", "gold", "commod", "cash", "trend"]


def fred_series(series_id):
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
    df = pd.read_csv(io.StringIO(requests.get(url, timeout=120).text))
    df.columns = ["date", series_id]
    df["date"] = pd.to_datetime(df["date"])
    df[series_id] = pd.to_numeric(df[series_id], errors="coerce")
    return df.set_index("date")[series_id].dropna()


def _monthly_compound(daily_ret):
    return (1.0 + daily_ret).groupby(daily_ret.index.to_period("M")).prod() - 1.0


def _yf_monthly(tickers):
    """First ticker that returns a usable daily series -> monthly return. None if all fail."""
    try:
        import yfinance as yf
    except Exception:
        return None, None
    for t in tickers:
        try:
            px = yf.download(t, start="1990-01-01", auto_adjust=True, progress=False)["Close"]
            if isinstance(px, pd.DataFrame):
                px = px.iloc[:, 0]
            px = px.dropna()
            if len(px) < 500:
                continue
            m = (1.0 + px.pct_change()).groupby(px.index.to_period("M")).prod() - 1.0
            return m.dropna(), t
        except Exception:
            continue
    return None, None


def build():
    proc = ROOT / "data" / "processed"

    g = pd.read_csv(io.StringIO(requests.get(GOLD_1833_URL, timeout=120).text))
    g.columns = [c.strip().lower() for c in g.columns]
    price_col = [c for c in g.columns if c != "date"][0]
    g["date"] = pd.to_datetime(g["date"])
    g = g.set_index("date")[price_col].astype(float).sort_index()
    g.to_frame("gold_usd_oz").to_csv(proc / "gold_monthly_1833.csv")
    g.index = g.index.to_period("M")
    gold_ret = g.pct_change().rename("gold").dropna()

    a = pd.read_csv(proc / "assets_daily.csv", index_col=0, parse_dates=True)
    equity = _monthly_compound(a["mkt_ret"].dropna()).rename("equity")
    bond10 = _monthly_compound(a["bond10_ret"].dropna()).rename("bond10")
    cash = _monthly_compound(a["rf"].dropna()).rename("cash")
    eq_vol = (a["mkt_ret"].rolling(21).std() * np.sqrt(252)).groupby(
        a.index.to_period("M")).last().rename("eq_vol")

    tr = pd.read_csv(proc / "trend_proxy_daily.csv", index_col=0, parse_dates=True)
    trend = _monthly_compound(tr["trend_ret"].dropna()).rename("trend")

    commod, commod_src = _yf_monthly(["^BCOM", "^SPGSCI", "GD=F", "DBC"])
    if commod is None:
        print("WARN: investable commodity fetch failed — commod column will be empty")
        commod = pd.Series(dtype=float, name="commod")
    else:
        commod = commod.rename("commod")
        print(f"commodity sleeve source = {commod_src}")

    def _yoy(fred_id):
        s = fred_series(fred_id)
        s.index = s.index.to_period("M")
        return s.pct_change(12)

    cpi_yoy = _yoy("CPIAUCSL").rename("cpi_yoy").dropna()
    ppi_yoy = _yoy("PPIACO").rename("ppi_yoy").dropna()
    growth = _yoy("INDPRO").rename("growth").dropna()

    y10 = fred_series("DGS10")
    y10_m = y10.groupby(y10.index.to_period("M")).last() / 100.0
    real_rate = (y10_m - cpi_yoy).rename("real_rate").dropna()

    baa = fred_series("BAA"); baa.index = baa.index.to_period("M")
    aaa = fred_series("AAA"); aaa.index = aaa.index.to_period("M")
    credit_spread = (baa - aaa).rename("credit_spread").dropna()

    cols = [equity, bond10, gold_ret, commod, cash, trend,
            cpi_yoy, real_rate, credit_spread, growth, eq_vol, ppi_yoy]
    panel = pd.concat(cols, axis=1, sort=True)
    panel.index = panel.index.to_timestamp("M")
    panel = panel.sort_index()
    panel.to_csv(proc / "econ_driver_monthly.csv")

    cov = [(c, panel[c].dropna().index[0].date(), panel[c].dropna().index[-1].date(),
            int(panel[c].notna().sum())) for c in panel.columns]
    print(pd.DataFrame(cov, columns=["series", "start", "end", "n"]).to_string(index=False))
    return panel


def _drawdown(equity_ret):
    wealth = (1.0 + equity_ret).cumprod()
    peak = wealth.cummax()
    return wealth / peak - 1.0


def _episodes(dd):
    """Peak-to-recovery drawdown episodes; each = (peak_date, trough_date, recovery_date, depth)."""
    out, in_dd, start = [], False, None
    for dt, v in dd.items():
        if not in_dd and v < 0:
            in_dd, start = True, dt
        elif in_dd and v >= 0:
            seg = dd.loc[start:dt]
            out.append((start, seg.idxmin(), dt, seg.min()))
            in_dd = False
    if in_dd:  # ongoing at series end
        seg = dd.loc[start:]
        out.append((start, seg.idxmin(), pd.NaT, seg.min()))
    return out


def analyze(panel):
    p = panel.copy()
    p.loc[p.index < GOLD_FLOAT_START, "gold"] = np.nan   # gold only in the float era

    eq = p["equity"].dropna()
    dd = _drawdown(eq)
    peak_prev = dd.shift(1)  # peak month is the last dd==0 before the decline

    rows = []
    for start, trough, recov, depth in _episodes(dd):
        if depth > CRASH_DD:
            continue
        peak_date = dd.loc[:start].index[dd.loc[:start].values >= 0][-1] if (dd.loc[:start] >= 0).any() else start
        span = p.loc[peak_date:trough].iloc[1:]  # decline months, peak excluded
        rec = {"peak": peak_date.date(), "trough": trough.date(),
               "recov": recov.date() if pd.notna(recov) else "ongoing",
               "depth": round(depth, 3),
               "months": len(span)}
        for s in SLEEVES:
            r = span[s].dropna()
            rec[s] = round((1.0 + r).prod() - 1.0, 3) if len(r) == len(span) and len(r) > 0 else np.nan
        for m in ["cpi_yoy", "real_rate", "credit_spread", "growth"]:
            rec[m] = round(p.loc[trough, m], 3) if pd.notna(p.loc[trough, m]) else np.nan
        rows.append(rec)

    ep = pd.DataFrame(rows).sort_values("depth")
    ep.to_csv(ROOT / "results" / "drawdown_episodes.csv", index=False)

    # full-sample vs crash-conditional correlation to equity + mean monthly return
    crash = dd < CRASH_DD
    cc = []
    for s in SLEEVES:
        if s == "equity":
            continue
        both = p[[s, "equity"]].dropna()
        rho_all = both[s].corr(both["equity"])
        cm = both.index.intersection(crash[crash].index)
        rho_cr = both.loc[cm, s].corr(both.loc[cm, "equity"]) if len(cm) > 20 else np.nan
        mu_all = both[s].mean() * 12
        mu_cr = both.loc[cm, s].mean() * 12 if len(cm) > 20 else np.nan
        cc.append((s, round(rho_all, 2), round(rho_cr, 2) if pd.notna(rho_cr) else np.nan,
                   round(mu_all, 3), round(mu_cr, 3) if pd.notna(mu_cr) else np.nan,
                   len(cm), f"{both.index[0].year}-{both.index[-1].year}"))
    corr = pd.DataFrame(cc, columns=["sleeve", "corr_all", "corr_crash",
                                     "ann_ret_all", "ann_ret_crash", "n_crash_mo", "sample"])
    corr.to_csv(ROOT / "results" / "conditional_corr.csv", index=False)

    print("\n=== LARGE EQUITY-DRAWDOWN EPISODES (depth <= -10%), sleeve return peak->trough ===")
    print(ep.to_string(index=False))
    print("\n=== CORRELATION TO EQUITY: full-sample vs crash-conditional (dd < -10%) ===")
    print("    (a genuine hedge's corr should FALL or stay negative in crashes; a fake one RISES)")
    print(corr.to_string(index=False))
    return ep, corr


def driver_dimensionality(panel):
    """Do the 5 candidate macro drivers collapse to a few independent axes? (support-or-simplify)"""
    drivers = ["growth", "cpi_yoy", "real_rate", "credit_spread", "eq_vol"]
    X = panel[drivers].dropna()
    Z = (X - X.mean()) / X.std()

    print("\n=== DRIVER-PROXY CORRELATION (common sample "
          f"{X.index[0].date()}..{X.index[-1].date()}, n={len(X)}) ===")
    print(Z.corr().round(2).to_string())

    U, S, Vt = np.linalg.svd(Z.values, full_matrices=False)
    ev = S ** 2 / (len(Z) - 1)
    vr = ev / ev.sum()
    print("\nPCA scree (variance explained):")
    for i, (e, r) in enumerate(zip(ev, np.cumsum(vr)), 1):
        print(f"  PC{i}: {vr[i-1]:5.1%}  cumulative {r:5.1%}")
    n90 = int(np.searchsorted(np.cumsum(vr), 0.90) + 1)
    print(f"  -> {n90} components explain >=90% of the 5-driver variance")
    print("\nLoadings (how each proxy maps onto the independent axes):")
    load = pd.DataFrame(Vt[:3].T, index=drivers, columns=["PC1", "PC2", "PC3"])
    print(load.round(2).to_string())
    return load


def failure_mode_coverage(ep):
    """Reframe: not 'is asset X a good hedge' but 'does the SET cover each failure mode, and what
    UNIQUE coverage does each sleeve add?' helped = positive return while equity crashed;
    strong = >= +5%. Cash excluded from 'unique helper' tally (always-on baseline)."""
    divers = ["bond10", "gold", "commod", "trend"]
    print("\n=== FAILURE-MODE COVERAGE MAP (per episode: who provided protection) ===")
    print("    helped '+' = return>0 ; strong '#' = return>=+5% ; '.' = hurt ; ' ' = no data")
    hdr = f"{'peak':>10} {'depth':>6}  " + "  ".join(f"{s:>6}" for s in SLEEVES[1:])
    print(hdr)
    strong_help = {s: [] for s in divers}
    rows = []
    for _, r in ep.iterrows():
        cells, marks = [], {}
        for s in SLEEVES[1:]:
            v = r[s]
            if pd.isna(v):
                cells.append(f"{'':>6}")
                marks[s] = ""
            else:
                mark = "#" if v >= 0.05 else ("+" if v > 0 else ".")
                cells.append(f"{mark}{v:>5.2f}")
                marks[s] = mark
                if s in divers and v >= 0.05:
                    strong_help[s].append(r["peak"])
        print(f"{str(r['peak']):>10} {r['depth']:>6.2f}  " + "  ".join(cells))
        rows.append({"peak": r["peak"], "depth": r["depth"], **marks})
    pd.DataFrame(rows).to_csv(ROOT / "results" / "failure_mode_coverage.csv", index=False)

    # who is the ONLY strong diversifier-helper in an episode = unique/gap-filling value
    print("\nUnique coverage (episodes where a diversifier was the ONLY strong helper "
          "among bond/gold/commod/trend, on episodes with that sleeve's data):")
    for _, r in ep.iterrows():
        helpers = [s for s in divers if pd.notna(r[s]) and r[s] >= 0.05]
        if len(helpers) == 1:
            print(f"  {r['peak']}  depth {r['depth']:.2f}  ONLY {helpers[0]} "
                  f"(inflation cpi_yoy={r['cpi_yoy']}, real_rate={r['real_rate']})")

    # pairwise overlap of strong-help episode sets (Jaccard) = redundancy vs complementarity
    print("\nStrong-help OVERLAP (Jaccard; high = redundant failure regimes, low = complementary):")
    for i, a in enumerate(divers):
        for b in divers[i+1:]:
            sa, sb = set(strong_help[a]), set(strong_help[b])
            if sa or sb:
                j = len(sa & sb) / len(sa | sb) if (sa | sb) else 0.0
                print(f"  {a:>7} vs {b:<7} Jaccard={j:.2f}  "
                      f"({a}:{len(sa)} {b}:{len(sb)} shared:{len(sa & sb)})")


def _own_drawdown(ret):
    w = (1.0 + ret.dropna()).cumprod()
    dd = w / w.cummax() - 1.0
    under = (dd < 0).astype(int)
    longest = maxrun = 0
    for v in under:
        maxrun = maxrun + 1 if v else 0
        longest = max(longest, maxrun)
    return dd.min(), longest


def insurance_ledger(panel):
    """Break-test #4: the OTHER side of the trade. What does each crisis-hero cost in calm periods,
    and how brutal is its OWN drawdown? Include the years it FAILED, not just where it worked."""
    dd = _drawdown(panel["equity"].dropna())
    crisis = dd < CRASH_DD
    p = panel.copy()
    p.loc[p.index < GOLD_FLOAT_START, "gold"] = np.nan
    print("\n=== COST-OF-INSURANCE LEDGER (calm vs crisis ann. return; own worst drawdown) ===")
    print(f"    equity in crisis (dd<{CRASH_DD:.0%}) {crisis.mean():.0%} of months")
    rows = []
    for s in SLEEVES:
        r = p[s].dropna()
        cm = r.index.intersection(crisis[crisis].index)
        km = r.index.difference(cm)
        calm = r.loc[km].mean() * 12
        cris = r.loc[cm].mean() * 12 if len(cm) > 5 else np.nan
        own_dd, under = _own_drawdown(r)
        rows.append((s, round(calm, 3), round(cris, 3) if pd.notna(cris) else np.nan,
                     round(own_dd, 2), under, f"{r.index[0].year}-{r.index[-1].year}"))
    led = pd.DataFrame(rows, columns=["sleeve", "calm_ann", "crisis_ann",
                                      "own_maxDD", "underwater_mo", "sample"])
    print(led.to_string(index=False))
    led.to_csv(ROOT / "results" / "insurance_ledger.csv", index=False)
    return led


def spanning_test(panel):
    """Redundancy test (Adam's gold question): can a candidate be REPLICATED by the combination of the
    others? Regress each on {other diversifiers + bond + cash}; report R^2, annualized alpha, and the
    UNIQUE (orthogonalized) return's payoff in crises. Redundant iff high R^2 AND ~0 unique crisis payoff."""
    dd = _drawdown(panel["equity"].dropna())
    crisis = dd < CRASH_DD
    p = panel.copy()
    p.loc[p.index < GOLD_FLOAT_START, "gold"] = np.nan
    divers = ["gold", "commod", "trend"]
    print("\n=== SPANNING / REDUNDANCY (can the combination of the others replicate it?) ===")
    print("    high R^2 + ~0 unique-crisis-return => REDUNDANT ; low R^2 or real unique payoff => KEEP")
    rows = []
    for tgt in divers:
        basis = [d for d in divers if d != tgt] + ["bond10", "cash"]
        df = p[[tgt] + basis].dropna()
        if len(df) < 60:
            rows.append((tgt, np.nan, np.nan, np.nan, len(df), "insufficient"))
            continue
        y = df[tgt].values
        X = np.column_stack([np.ones(len(df)), df[basis].values])
        beta, *_ = np.linalg.lstsq(X, y, rcond=None)
        resid = y - X @ beta
        ss = 1.0 - resid.var() / y.var()
        alpha_ann = beta[0] * 12
        res = pd.Series(resid, index=df.index)
        cm = res.index.intersection(crisis[crisis].index)
        uniq_cris = res.loc[cm].mean() * 12 if len(cm) > 5 else np.nan
        rows.append((tgt, round(ss, 2), round(alpha_ann, 3),
                     round(uniq_cris, 3) if pd.notna(uniq_cris) else np.nan,
                     len(df), f"{df.index[0].year}-{df.index[-1].year} vs {'+'.join(basis)}"))
    sp = pd.DataFrame(rows, columns=["sleeve", "R2_by_others", "alpha_ann",
                                     "unique_crisis_ann", "n", "detail"])
    print(sp.to_string(index=False))
    sp.to_csv(ROOT / "results" / "spanning_test.csv", index=False)
    return sp


def load_or_build():
    csv = ROOT / "data" / "processed" / "econ_driver_monthly.csv"
    if csv.exists():
        print(f"(loading cached {csv.name}; delete it to re-fetch)")
        return pd.read_csv(csv, index_col=0, parse_dates=True)
    return build()


if __name__ == "__main__":
    panel = load_or_build()
    ep, _ = analyze(panel)
    driver_dimensionality(panel)
    failure_mode_coverage(ep)
    insurance_ledger(panel)
    spanning_test(panel)
    sys.exit(0)
