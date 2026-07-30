"""Cross-sectional INDUSTRY momentum (Adam: try sectors, more breadth than 2-3 assets).

Different from strategy_combo (time-series trend, each asset vs its own past): this ranks industries
AGAINST EACH OTHER each month and harvests the winners-minus-losers spread (Jegadeesh-Titman 1993;
Moskowitz-Grinblatt 1999 industry momentum). Cross-sectional momentum has real historical Sharpe,
unlike single-index timing. Clean French 10-industry data, 1926+, zero survivorship bias.

Signal: 12-1 momentum (trailing 12 months skipping the most recent month, the standard reversal
skip). Monthly rebalance. Cost-aware (turnover x cost), causal (signal uses only past). Tests:
  WML          long top-k / short bottom-k industries (the anomaly, long-short) — is the spread real net of costs?
  long_only    equal-weight + a momentum tilt (advisor-appropriate, no shorting)
vs EW_market   equal-weight all industries (the baseline / 'the market of industries').
NO look spent in the prereg sense (comparative characterization); any deploy needs a proper OOS gate.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from run_config import maxdd

ANN = 12
COST_BPS = 20.0        # momentum turns over a lot; 20bps/side is honest for this
K = 3                  # long top 3 / short bottom 3 of 10 industries


def perf(ret, rf, name):
    ret = np.asarray(ret)
    eq = np.cumprod(1 + ret)
    ann = eq[-1] ** (ANN / len(ret)) - 1
    vol = ret.std() * np.sqrt(ANN)
    shp = (ret - rf).mean() / ret.std() * np.sqrt(ANN) if ret.std() > 0 else 0.0
    return dict(strategy=name, ann_ret=round(ann, 4), ann_vol=round(vol, 4),
                sharpe=round(shp, 3), max_dd=round(maxdd(ret), 4))


def main():
    d = pd.read_csv(ROOT / "data/processed/assets_daily.csv", index_col=0, parse_dates=True)
    inds = [c for c in d.columns if c.startswith("ind_")]
    # daily -> monthly compounded returns
    m = (1 + d[inds + ["rf"]]).resample("ME").prod() - 1
    R = m[inds]
    rf = m["rf"]

    # 12-1 momentum signal, known at end of month t (uses months t-12..t-1, skip t)
    cum12 = (1 + R).rolling(12).apply(np.prod, raw=True) - 1
    cum1 = R                                          # last month (to skip)
    signal = ((1 + cum12) / (1 + cum1) - 1).shift(1)  # shift: signal formed at t-1, traded at t

    wml_ret, lo_ret, ew_ret = [], [], []
    w_prev_l = w_prev_s = w_prev_lo = None
    idx = []
    for t in R.index:
        s = signal.loc[t]
        if s.isna().any():
            continue
        order = s.rank()
        longs = order[order > len(inds) - K].index          # top K
        shorts = order[order <= K].index                    # bottom K
        wl = pd.Series(0.0, index=inds); wl[longs] = 1.0 / K
        ws = pd.Series(0.0, index=inds); ws[shorts] = 1.0 / K
        wlo = pd.Series(1.0 / len(inds), index=inds)         # long-only momentum tilt
        wlo[longs] += 0.5 / K; wlo[shorts] -= 0.5 / K
        wlo = wlo.clip(lower=0); wlo /= wlo.sum()
        r_t = R.loc[t]
        # turnover cost (both legs for WML; the tilt for long_only)
        def cost(w, wp):
            return 0.0 if wp is None else np.abs(w - wp).sum() * COST_BPS * 1e-4
        wml_ret.append((wl * r_t).sum() - (ws * r_t).sum() - cost(wl, w_prev_l) - cost(ws, w_prev_s))
        lo_ret.append((wlo * r_t).sum() - cost(wlo, w_prev_lo))
        ew_ret.append(r_t.mean())
        w_prev_l, w_prev_s, w_prev_lo = wl, ws, wlo
        idx.append(t)

    res = pd.DataFrame({"ew": ew_ret, "lo": lo_ret, "wml": wml_ret, "rf": rf.loc[idx].to_numpy()},
                       index=pd.DatetimeIndex(idx))
    rf_a = res["rf"].to_numpy()
    rows = [perf(res["ew"], rf_a, "EW_market (baseline)"),
            perf(res["lo"], rf_a, "long_only_mom_tilt"),
            perf(res["wml"], np.zeros_like(rf_a), "WML_longshort (spread)")]
    print(f"CROSS-SECTIONAL INDUSTRY MOMENTUM ({idx[0].date()}..{idx[-1].date()}, {len(idx)} months, "
          f"{len(inds)} industries, {COST_BPS:.0f}bps cost)")
    print(f"{'strategy':26}{'ann ret':>9}{'ann vol':>9}{'Sharpe':>8}{'max DD':>9}")
    for r in rows:
        print(f"{r['strategy']:26}{r['ann_ret']:9.2%}{r['ann_vol']:9.2%}{r['sharpe']:8.2f}{r['max_dd']:9.1%}")

    # Barroso-Santa-Clara (2015): scale WML by trailing realized vol -> tames the momentum crash.
    sig = (res["wml"].rolling(6).std() * np.sqrt(ANN)).shift(1)      # causal trailing 6m vol
    target = res["wml"].std() * np.sqrt(ANN)
    expo = (target / sig).clip(0, 2.0).fillna(0.0)
    res["wml_vs"] = res["wml"] * expo
    rows.append(perf(res["wml_vs"], np.zeros(len(res)), "WML_vol_scaled"))
    print(f"{'WML_vol_scaled':26}{rows[-1]['ann_ret']:9.2%}{rows[-1]['ann_vol']:9.2%}"
          f"{rows[-1]['sharpe']:8.2f}{rows[-1]['max_dd']:9.1%}")

    print("\nDECAY + CRASH CHECK — Sharpe by era (raw WML vs vol-scaled WML):")
    print(f"{'era':16}{'EW':>8}{'long_only':>11}{'WML':>8}{'WML_volscaled':>15}")
    for lab, a, b in [("pre-1970", "1927", "1969"), ("1970-1999", "1970", "1999"),
                      ("2000-2009", "2000", "2009"), ("2010-now", "2010", "2026")]:
        seg = res.loc[a:b]
        sew = perf(seg["ew"], seg["rf"].to_numpy(), "")["sharpe"]
        slo = perf(seg["lo"], seg["rf"].to_numpy(), "")["sharpe"]
        swml = perf(seg["wml"], np.zeros(len(seg)), "")["sharpe"]
        svs = perf(seg["wml_vs"], np.zeros(len(seg)), "")["sharpe"]
        print(f"{lab:16}{sew:8.2f}{slo:11.2f}{swml:8.2f}{svs:15.2f}")
    pd.DataFrame(rows).to_csv(ROOT / "results/cross_sectional_momentum.csv", index=False)


if __name__ == "__main__":
    main()
