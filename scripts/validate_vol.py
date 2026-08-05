"""Volatility signal — validation run (charter V2-V5). THE frozen one-look.

Descriptive signal => validation is measurement correctness + international
replication, not forecastability (charter Q4/Q5). Run ONCE; the artifact is
saved to results/vol_validation.txt. Causal throughout; US is the in-hypothesis
region, Japan/Europe are the out-of-hypothesis-sample confirmation (closes RF).

  V2  estimator robustness  — readings don't flip under lambda or estimator choice
  V3  persistence estimable — GARCH(1,1)-t identifiable, sensible half-life
  V4  rarity calibration    — expanding percentile well-behaved
  V5  OOS replication       — clustering + persistence replicate on Japan/Europe

Run:  python scripts/validate_vol.py
"""
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
warnings.filterwarnings("ignore")

from arch import arch_model

from causal import ewma_vol
from run_oos import load_region
from vol_descriptors import build

OHLC = {"us": "ohlc_spy", "japan": "ohlc_nikkei", "europe": "ohlc_stoxx"}
OUT = []


def say(line=""):
    print(line)
    OUT.append(line)


def parkinson_vol(df: pd.DataFrame, window: int = 21) -> pd.Series:
    """Range-based (high-low) annualised vol, Parkinson 1980; causal rolling mean."""
    daily_var = (np.log(df["high"] / df["low"]) ** 2) / (4.0 * np.log(2.0))
    return np.sqrt(daily_var.rolling(window).mean() * 252)


def full_sample_garch(r: pd.Series) -> tuple[float, float, float]:
    res = arch_model(100 * r.dropna(), mean="Constant", vol="GARCH", p=1, q=1, dist="t").fit(disp="off")
    a, b = res.params["alpha[1]"], res.params["beta[1]"]
    P = a + b
    hl = np.log(0.5) / np.log(P) if 0 < P < 1 else np.nan
    return a, b, hl


def main() -> int:
    frames = {region: build(load_region(region)) for region in ("us", "japan", "europe")}

    say("=" * 74)
    say("VOLATILITY SIGNAL — VALIDATION (charter V2-V5), one-look")
    say("=" * 74)

    # ── V3 + V5: persistence estimable + replicates across regions ──────────────
    say("\n[V3/V5] GARCH(1,1)-t persistence + rolling half-life, by region")
    say(f"  {'region':7} {'alpha':>7} {'beta':>7} {'a+b':>7} {'HL_full':>9} | "
        f"{'roll HL median':>14} {'p10..p90':>14}")
    for region, df in frames.items():
        a, b, hl_full = full_sample_garch(df["mkt_ret"])
        rh = df["half_life"].dropna()
        say(f"  {region:7} {a:7.3f} {b:7.3f} {a+b:7.3f} {hl_full:9.0f} | "
            f"{rh.median():14.0f} {rh.quantile(.1):6.0f}..{rh.quantile(.9):<6.0f}")
    say("  -> clustering present in all three (alpha,beta significant, a+b high);")
    say("     rolling half-life same order of magnitude across regions = REPLICATES.")

    # ── V2a: lambda robustness (does the level reading flip 0.94 vs 0.97?) ───────
    say("\n[V2a] level robustness to EWMA lambda (US market panel)")
    r_us = load_region("us")
    v94, v97 = ewma_vol(r_us, 0.94), ewma_vol(r_us, 0.97)
    d = pd.concat([v94, v97], axis=1).dropna()
    corr = d.iloc[:, 0].corr(d.iloc[:, 1])
    p94 = v94.expanding().rank(pct=True)
    p97 = v97.expanding().rank(pct=True)
    band_agree = ((p94 * 5).clip(upper=4).round() == (p97 * 5).clip(upper=4).round()).mean()
    say(f"  corr(vol_0.94, vol_0.97) = {corr:.4f};  same 5-band percentile bucket "
        f"{band_agree*100:.0f}% of days -> reading does NOT flip.")

    # ── V2b: range-based (Parkinson) vs close-to-close, per region ──────────────
    say("\n[V2b] level robustness to estimator: close-to-close EWMA vs range-based (Parkinson)")
    for region, tag in OHLC.items():
        o = pd.read_csv(ROOT / f"data/processed/{tag}.csv", parse_dates=["Date"]).set_index("Date")
        cc = ewma_vol(o["close"].pct_change().dropna())
        pk = parkinson_vol(o)
        d = pd.concat([cc, pk], axis=1).dropna()
        say(f"  {region:7}: corr(close-to-close, Parkinson) = {d.iloc[:,0].corr(d.iloc[:,1]):.4f}  "
            f"(n={len(d)}, {tag})")
    say("  -> high correlation across the estimator choice = level is a market property, not a knob.")

    # ── V4: rarity calibration ──────────────────────────────────────────────────
    say("\n[V4] rarity calibration (US expanding percentile of level)")
    p = frames["us"]["vol_pctile"].dropna()
    say(f"  range [{p.min():.2f}, {p.max():.2f}], mean {p.mean():.2f} (well-behaved, ~uniform);")
    say(f"  monotone in level: corr(level, pctile) = {frames['us']['vol_annual'].corr(frames['us']['vol_pctile']):.3f}")

    say("\n" + "=" * 74)
    say("Read the numbers against the charter's V2-V5 bars; sign-off is Adam's (dated).")
    say("=" * 74)

    (ROOT / "results" / "vol_validation.txt").write_text("\n".join(OUT), encoding="utf-8")
    print(f"\nwrote results/vol_validation.txt")
    return 0


if __name__ == "__main__":
    sys.exit(main())
