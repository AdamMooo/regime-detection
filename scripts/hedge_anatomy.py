"""Composite hedge anatomy + behavioral fingerprint (descriptive, look-free).

Adam's steer (2026-07-26): rotation leans on bonds, but in THIS market bonds are not a
reliable hedge (2022: stocks AND bonds fell together). So: WHICH asset classes actually pay
when equity is stressed, especially when nominal bonds fail — and what do they COST in calm.

On a modern ETF panel (2004+, the regime that matters), for equity-stress episodes defined
by SPY's own K=2 jump-model regime, we report per asset:
  stress payoff : annualized mean return WHILE equity is in its bear state
  carry         : annualized mean return while equity is CALM (the cost of holding the hedge)
  GFC/COVID/INFL: cumulative return in the three reference crises (2008 deflation, 2020 covid,
                  2022 inflation — the last is the bonds-FAILED regime)
  own-bull lift : is the asset's OWN downside-vol regime 'calm' more often during equity stress
                  (>1). Compared vs stress payoff, this settles the feature-set fork: if an
                  asset PAYS but lift~1, own-vol features miss real refuge -> use conditional-
                  return features (lens B).

Menu spans: nominal bonds, credit, gold/silver, broad commodities, TIPS, dollar, cash,
TREND/managed futures, haven currencies, min-vol equity, intl/EM equity, REIT, crypto.
Cached to data/processed/hedge_etf_daily.csv.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from jumpmodel import build_features, fit_jump_model  # noqa: E402

CLASS = {
    "SPY": "equity-US", "IEF": "bond-7-10y", "TLT": "bond-20y+", "LQD": "credit-IG",
    "HYG": "credit-HY", "GLD": "gold", "SLV": "silver", "DBC": "commodities",
    "TIP": "TIPS", "UUP": "dollar", "BIL": "cash",
    "DBMF": "trend-MF", "KMLM": "trend-MF", "FXY": "haven-JPY", "FXF": "haven-CHF",
    "USMV": "eq-minvol", "EFA": "eq-intl-dev", "EEM": "eq-EM", "VNQ": "REIT",
    "BTC-USD": "crypto",
}
TICKERS = list(CLASS.keys())
LAM, BURN = 50.0, 252
CACHE = ROOT / "data" / "processed" / "hedge_etf_daily.csv"

# reference crises (from SPY-regime episodes): 2008 deflation, 2020 covid, 2022 inflation
CRISES = {"GFC08": ("2007-11-01", "2009-07-14"),
          "COVID20": ("2020-02-25", "2020-07-13"),
          "INFL22": ("2022-01-19", "2023-01-10")}


def load_returns(refresh=False):
    if CACHE.exists() and not refresh:
        px = pd.read_csv(CACHE, index_col=0, parse_dates=True)
    else:
        import yfinance as yf
        px = yf.download(TICKERS, start="2004-01-01", auto_adjust=True, progress=False)["Close"]
        px.to_csv(CACHE)
    px = px.reindex(columns=TICKERS)
    px = px[px["SPY"].notna()]          # restrict to equity trading days (drop crypto weekends)
    return px.pct_change()


def own_label(r):
    r = r.dropna()
    if len(r) < BURN + 500:
        return None
    f = build_features(r); f.index = r.index; f = f.iloc[BURN:].dropna()
    F = f.to_numpy(); Z = (F - F.mean(0)) / F.std(0)
    _, s, _, _ = fit_jump_model(Z, k=2, lam=LAM, seed=0)
    return pd.Series(s, index=f.index)


def episodes(mask):
    eps, a, idx = [], None, mask.index
    for i, v in enumerate(mask.to_numpy()):
        if v and a is None:
            a = i
        elif not v and a is not None:
            eps.append((idx[a], idx[i - 1])); a = None
    if a is not None:
        eps.append((idx[a], idx[-1]))
    return eps


def cum(r, lo, hi):
    seg = r.loc[lo:hi].dropna()
    return float((1 + seg).prod() - 1) if len(seg) else np.nan


def main():
    refresh = "--refresh" in sys.argv
    rets = load_returns(refresh=refresh)
    print(f"panel {rets.index[0].date()}..{rets.index[-1].date()}  {len(TICKERS)} assets")

    eq = own_label(rets["SPY"])
    eq_bear = eq == 1
    eps = [e for e in episodes(eq_bear) if (e[1] - e[0]).days >= 10]
    print(f"SPY own-regime: {eq_bear.mean():.1%} bear days, {len(eps)} stress episodes >=10d\n")

    HEDGES = [t for t in TICKERS if t != "SPY"]
    frows = []
    for t in HEDGES:
        r = rets[t]
        rb = r.reindex(eq.index)[eq_bear].dropna()      # returns while equity bear
        rc = r.reindex(eq.index)[~eq_bear].dropna()      # returns while equity calm
        lab = own_label(r)
        if lab is not None:
            lab = lab.reindex(eq.index)
            base = float((lab == 0).mean())
            lift = float((lab[eq_bear] == 0).mean()) / base if base else np.nan
        else:
            lift = np.nan
        row = dict(asset=t, cls=CLASS[t], hist=f"{r.dropna().index[0].year}",
                   stress=float(rb.mean()) * 252 if len(rb) else np.nan,
                   carry=float(rc.mean()) * 252 if len(rc) else np.nan,
                   n_bear=len(rb), lift=lift)
        for name, (lo, hi) in CRISES.items():
            row[name] = cum(r, lo, hi)
        frows.append(row)
    fp = pd.DataFrame(frows).sort_values("stress", ascending=False)

    print("=" * 108)
    print("BEHAVIORAL FINGERPRINT — sorted by STRESS PAYOFF (annualized return while equity is bear)")
    print("=" * 108)
    print(f"{'asset':<9}{'class':<13}{'since':>6}{'STRESS':>8}{'carry':>8}"
          f"{'GFC08':>8}{'COVID20':>9}{'INFL22':>8}{'lift':>6}{'nbear':>7}")
    for _, x in fp.iterrows():
        def pct(v, w=8):
            return f"{v*100:>{w}.1f}" if pd.notna(v) else f"{'--':>{w}}"
        print(f"{x.asset:<9}{x.cls:<13}{x['hist']:>6}{pct(x.stress)}{pct(x.carry)}"
              f"{pct(x.GFC08)}{pct(x.COVID20,9)}{pct(x.INFL22)}"
              f"{(f'{x.lift:.2f}' if pd.notna(x.lift) else '--'):>6}{x.n_bear:>7}")

    print("\nreading it:")
    print("  STRESS>0 & carry>=0  = pays in stress AND doesn't bleed in calm  (the grail)")
    print("  STRESS>0 & carry<0   = real hedge but you PAY carry to hold it   (convexity cost)")
    print("  INFL22 col           = the bonds-FAILED regime; who was still positive there")
    print("  lift~1 but STRESS>0  = own-vol regime BLIND to the payoff -> feature lens B")

    # bonds-failed vs bonds-hedged split (full menu, per-episode means)
    rows = []
    for lo, hi in eps:
        rows.append({"ief": cum(rets["IEF"], lo, hi),
                     **{t: cum(rets[t], lo, hi) for t in HEDGES}})
    ep = pd.DataFrame(rows).dropna(subset=["ief"])
    hedged, failed = ep[ep["ief"] > 0], ep[ep["ief"] <= 0]
    print("\n" + "-" * 108)
    print(f"BOND-HEDGE SPLIT — IEF positive {len(hedged)} episodes / negative (bonds failed) {len(failed)}")
    print("mean episode return, assets with data in the failed episodes, sorted by failed-regime return:")
    fa = failed.mean(numeric_only=True).drop("ief").dropna().sort_values(ascending=False)
    he = hedged.mean(numeric_only=True)
    for t, v in fa.items():
        print(f"  {t:<9}{CLASS[t]:<13} bonds-FAILED {v*100:+6.1f}%   bonds-hedged {he.get(t, np.nan)*100:+6.1f}%")

    fp.to_csv(ROOT / "results" / "hedge_fingerprint.csv", index=False)
    print("\nwrote results/hedge_fingerprint.csv")
    return 0


if __name__ == "__main__":
    sys.exit(main())
