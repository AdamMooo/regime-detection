"""Build a time-series-momentum (trend / managed-futures) proxy return series and validate
it against the live managed-futures ETFs (DBMF, KMLM).

WHY: the Path-B hedge kit (PROGRAM.md) needs a TREND sleeve, but the managed-futures ETFs
only start 2019 (DBMF) / 2020 (KMLM) — too short to see 2008. This builds a transparent
TSMOM proxy from long-history liquid ETFs so the static-vs-timed backtest can run across
2008/2020/2022, then GATES it on correlation with the real products so we know the proxy is
faithful (same trick build_assets.py uses: synthetic long series validated on the overlap).

METHOD (Moskowitz, Ooi & Pedersen 2012, "Time Series Momentum"):
  universe = liquid ETFs across equity / fixed income / commodity / FX; each market ENTERS
    when it has >=12m history (real trend books expand their universe over time).
  monthly rebalance. For each market m at month-end t (all causal, data <= t):
    signal_{m,t}   = sign(12-month return)                       # long/short trend
    sigma_{m,t}    = trailing 63d realized vol, annualized       # ex-ante risk
    position_{m,t} = signal * min(target_inst_vol / sigma, cap)  # inverse-vol sizing
  strategy raw daily return = mean over available markets of position * next-day return
  strategy vol scaling: multiply by target_port_vol / trailing-252d realized vol (causal,
    lagged) so the series sits near a constant ~10% annualized vol like a real CTA.

Causality: positions set at month-end t use only data <= t and are applied to returns AFTER
t (shift). Vol scalers use trailing/lagged windows only.

GATE: corr(proxy_monthly, DBMF_monthly) >= 0.50 on the overlap (a faithful trend proxy);
also reports corr vs KMLM and the 2022 crisis-alpha sign check.

Writes data/processed/trend_proxy_daily.csv + results/trend_proxy_gate.csv.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "data" / "raw" / "trend_universe_prices.csv"

# diversified universe, 4 sectors, no intra-sector double-counting (DBC is broad commodity;
# GLD the distinct monetary metal). FX joins ~2007-08 as history allows.
UNIVERSE = {
    "SPY": "equity-US", "EFA": "equity-dev", "EEM": "equity-EM",
    "IEF": "bond-10y", "TLT": "bond-30y",
    "DBC": "commodity-broad", "GLD": "gold",
    "UUP": "fx-USD", "FXE": "fx-EUR", "FXY": "fx-JPY",
}
VALIDATION = ["DBMF", "KMLM"]

MOM_LB = 252          # 12-month momentum lookback
VOL_LB = 63           # 3-month realized-vol window
TARGET_INST_VOL = 0.10
TARGET_PORT_VOL = 0.10
LEV_CAP = 2.0         # per-market leverage cap (guards tiny-vol blowups)
PORT_VOL_LB = 252


def load_prices(refresh=False):
    if CACHE.exists() and not refresh:
        return pd.read_csv(CACHE, index_col=0, parse_dates=True)
    import yfinance as yf
    tk = list(UNIVERSE) + VALIDATION
    px = yf.download(tk, start="2003-01-01", auto_adjust=True, progress=False)["Close"]
    px = px.reindex(columns=tk)
    px = px[px["SPY"].notna()]
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    px.to_csv(CACHE)
    return px


def build_proxy(px):
    mkts = list(UNIVERSE)
    prices = px[mkts]
    rets = prices.pct_change()
    month_ends = prices.resample("ME").last().index

    # per-market position at each month-end (causal)
    pos_me = pd.DataFrame(index=month_ends, columns=mkts, dtype=float)
    for me in month_ends:
        hist = prices.loc[:me]
        if len(hist) < MOM_LB + 1:
            continue
        for m in mkts:
            s = hist[m].dropna()
            if len(s) < MOM_LB + 1:
                continue
            mom = s.iloc[-1] / s.iloc[-1 - MOM_LB] - 1.0
            vol = rets[m].loc[:me].dropna().iloc[-VOL_LB:].std() * np.sqrt(252)
            if not np.isfinite(vol) or vol <= 0:
                continue
            pos_me.loc[me, m] = np.sign(mom) * min(TARGET_INST_VOL / vol, LEV_CAP)

    # expand month-end positions to daily, EFFECTIVE from the day AFTER the month-end
    pos_daily = pos_me.reindex(prices.index, method="ffill").shift(1)
    contrib = pos_daily * rets                              # per-market daily P&L
    raw = contrib.mean(axis=1, skipna=True)                 # equal-weight available markets
    raw = raw.dropna()

    # strategy-level vol targeting (causal: trailing realized vol, lagged one day)
    pvol = raw.rolling(PORT_VOL_LB).std().shift(1) * np.sqrt(252)
    scaler = (TARGET_PORT_VOL / pvol).clip(upper=3.0)
    trend = (raw * scaler).dropna()
    n_mkts = pos_daily.notna().sum(axis=1).reindex(trend.index)
    return trend.rename("trend_ret"), n_mkts


def main():
    refresh = "--refresh" in sys.argv
    px = load_prices(refresh=refresh)
    trend, n_mkts = build_proxy(px)
    ann_vol = trend.std() * np.sqrt(252)
    ann_ret = trend.mean() * 252
    print(f"proxy {trend.index[0].date()}..{trend.index[-1].date()}  n={len(trend)}")
    print(f"  markets active: {int(n_mkts.iloc[0])} -> {int(n_mkts.iloc[-1])} "
          f"(median {int(n_mkts.median())})")
    print(f"  annualized: ret {ann_ret:+.2%}  vol {ann_vol:.2%}  Sharpe {ann_ret/ann_vol:.2f}")

    # ---- validation vs live managed-futures ETFs (monthly returns) ----
    tm = (1 + trend).resample("ME").prod() - 1
    gate = []
    corrs = {}
    for v in VALIDATION:
        vr = px[v].dropna().pct_change()
        vm = (1 + vr).resample("ME").prod() - 1
        both = pd.DataFrame({"proxy": tm, v.lower(): vm}).dropna()
        c = both["proxy"].corr(both[v.lower()])
        corrs[v] = (c, len(both))
        print(f"  corr(proxy, {v}) = {c:.3f}  (n={len(both)} months, "
              f"{both.index[0].date()}..{both.index[-1].date()})")

    # crisis-alpha sanity: proxy return in the 2022 inflation crisis
    infl22 = trend.loc["2022-01-19":"2023-01-10"]
    cum22 = (1 + infl22).prod() - 1
    print(f"  2022 crisis (2022-01-19..2023-01-10) cumulative: {cum22:+.1%}")

    dbmf_c = corrs["DBMF"][0]
    gate.append(("G1_dbmf_corr", dbmf_c >= 0.50, f"corr={dbmf_c:.3f} (bar 0.50)"))
    gate.append(("G2_vol_sane", 0.05 <= ann_vol <= 0.15, f"ann_vol={ann_vol:.2%} (target ~10%)"))
    gate.append(("G3_crisis_alpha_2022", cum22 > 0, f"2022 cum={cum22:+.1%} (>0 expected)"))
    res = pd.DataFrame(gate, columns=["gate", "passed", "detail"])

    out = pd.DataFrame({"trend_ret": trend, "n_markets": n_mkts.astype("Int64")})
    out.to_csv(ROOT / "data" / "processed" / "trend_proxy_daily.csv")
    res.to_csv(ROOT / "results" / "trend_proxy_gate.csv", index=False)
    print("\n" + res.to_string(index=False))
    print("\nTREND PROXY GATE:", "PASS" if res["passed"].all() else "FAIL")
    return 0 if res["passed"].all() else 1


if __name__ == "__main__":
    sys.exit(main())
