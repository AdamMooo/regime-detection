"""Volatility descriptors — the continuous measurement spine (Level-0).

Presents volatility as what it provably is: a persistent, CONTINUOUS quantity
(volatility clustering — Mandelbrot 1963; Engle 1982 ARCH; Bollerslev 1986
GARCH), instead of thresholding it into a CALM/STRESSED regime label. The
thresholding step is what manufactures false positives/negatives (all the
classification error piles up at the boundary) and discards the graded
information in sigma_t. Here there is no regime and no positive claim — this is
descriptive measurement of a proven fact. Causal / point-in-time throughout.

This is the first axis (LEVEL): how large is vol, and how unusual is that level
vs its own history. Later axes (range-based estimator, shock persistence /
half-life, the integrated-variance "vol clock") build on this same spine.

Run:  python scripts/vol_descriptors.py
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

TRADING_DAYS = 252
EWMA_LAMBDA = 0.94   # RiskMetrics daily decay; lam == the vol process's persistence
BURN_IN = 252        # seed the recurrence on year 1; report NaN until warmed up


def load_returns() -> pd.Series:
    df = pd.read_csv(ROOT / "data/processed/market_daily.csv", parse_dates=["date"]).set_index("date")
    return df["mkt_ret"].astype(float)


def ewma_vol(r: pd.Series, lam: float = EWMA_LAMBDA, burn_in: int = BURN_IN) -> pd.Series:
    """>>> YOU WRITE THIS <<<  Annualised EWMA volatility, causal.

    The variance recurrence (RiskMetrics / IGARCH):

        sigma2_t = lam * sigma2_{t-1} + (1 - lam) * r_t**2

    Then  sigma_t = sqrt(sigma2_t),  annualise by  * sqrt(TRADING_DAYS).

    - Seed sigma2 with the sample variance of the first `burn_in` returns.
    - Return NaN for the burn-in window (estimate not warmed up yet).
    - Causal: sigma_t may use r_t and everything before it, nothing after.
    - Return a pd.Series aligned to r's index.
    """
    x = r.to_numpy(dtype=float)
    r2 = x * x
    n = len(x)
    sig2 = np.full(n, np.nan)
    prev = float(np.nanvar(x[:burn_in]))            # seed: year-1 sample variance
    for t in range(burn_in, n):
        prev = lam * prev + (1.0 - lam) * r2[t]      # RiskMetrics/IGARCH, causal
        sig2[t] = prev
    vol = np.sqrt(sig2) * np.sqrt(TRADING_DAYS)      # daily -> annualised
    return pd.Series(vol, index=r.index, name="vol_annual")


def expanding_percentile(x: pd.Series) -> pd.Series:
    """Causal expanding-window percentile, in [0, 1].

    For each t:  p_t = (# of valid {x_s : s <= t} with x_s <= x_t) / (# valid s <= t)

    Use ONLY data through t (EXPANDING window, not full-sample). A full-sample
    rank would leak the future distribution into today's reading — the exact
    look-ahead this repo forbids. Return a pd.Series in [0, 1] aligned to x,
    NaN where x is NaN.

    Hint: `x.expanding().rank(pct=True)` is the one-liner. Worth writing the
    loop by hand once first, to feel why "expanding" is what makes it causal.
    """
    return x.expanding().rank(pct=True).rename("vol_pctile")


# ── driver / presentation (wired for you) ───────────────────────────────────────

def build() -> pd.DataFrame:
    r = load_returns()
    vol = ewma_vol(r)
    pct = expanding_percentile(vol)
    out = pd.DataFrame({"mkt_ret": r, "vol_annual": vol, "vol_pctile": pct})
    return out


def _print_latest(df: pd.DataFrame) -> None:
    latest = df.dropna(subset=["vol_annual", "vol_pctile"]).iloc[-1]
    d = df.dropna(subset=["vol_annual", "vol_pctile"]).index[-1].date()
    print("=" * 60)
    print(f"VOL DESCRIPTORS — as of {d}")
    print("=" * 60)
    print(f"  EWMA vol (annualised):  {latest['vol_annual'] * 100:5.1f}%")
    print(f"  Level percentile:       {latest['vol_pctile'] * 100:5.1f}th  (of its own history to date)")
    # trajectory: is the percentile drifting up or down over the last ~10 sessions?
    tail = df["vol_pctile"].dropna().tail(11)
    if len(tail) == 11:
        drift = (tail.iloc[-1] - tail.iloc[0]) * 100
        arrow = "rising" if drift > 3 else ("falling" if drift < -3 else "flat")
        print(f"  10-session drift:       {drift:+5.1f} pts  ({arrow})")


def _plot(df: pd.DataFrame) -> Path:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    d = df.dropna(subset=["vol_annual", "vol_pctile"])
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 6), sharex=True, gridspec_kw={"height_ratios": [2, 1]})
    ax1.plot(d.index, d["vol_annual"] * 100, lw=0.6, color="#1f77b4")
    ax1.set_ylabel("EWMA vol (annualised %)")
    ax1.set_title("Volatility descriptors — level (continuous, no regime label)")
    ax2.fill_between(d.index, 0, d["vol_pctile"] * 100, color="#d62728", alpha=0.4)
    ax2.axhline(50, color="#888", lw=0.5, ls="--")
    ax2.set_ylabel("Level percentile")
    ax2.set_ylim(0, 100)
    fig.tight_layout()
    p = ROOT / "results" / "vol_descriptors.png"
    fig.savefig(p, dpi=110)
    plt.close(fig)
    return p


def main() -> int:
    df = build()
    _print_latest(df)
    csv = ROOT / "results" / "vol_descriptors.csv"
    df.to_csv(csv)
    png = _plot(df)
    print(f"\nwrote {csv.relative_to(ROOT)}  and  {png.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
