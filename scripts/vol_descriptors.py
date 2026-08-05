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
sys.path.insert(0, str(ROOT / "scripts"))

from causal import ewma_vol, expanding_percentile, realized_vol


def load_returns() -> pd.Series:
    df = pd.read_csv(ROOT / "data/processed/market_daily.csv", parse_dates=["date"]).set_index("date")
    return df["mkt_ret"].astype(float)


def shock_half_life(r: pd.Series, garch_window: int = 1260, step: int = 63) -> pd.Series:
    """Mean-reversion half-life of a volatility shock, in trading days (descriptor v1.0).

    The 4th descriptor ("how durable is the current shock"), via GARCH(1,1)-t
    persistence — the canonical tool, since volatility clustering IS the GARCH
    stylized fact (Bollerslev 1986):

        sigma2_t = omega + alpha * eps2_{t-1} + beta * sigma2_{t-1}
        persistence = alpha + beta       (fraction of a variance shock surviving one day)
        half_life   = ln(0.5) / ln(alpha + beta)

    - Fit on a TRAILING `garch_window` (~5yr), refit every `step` days (quarterly)
      and forward-filled. A trailing window is deliberate: a full-sample / expanding
      GARCH over a century mixes volatility regimes and inflates alpha+beta toward 1
      (near-IGARCH, spurious persistence — Lamoureux-Lastrapes 1990). So this reads
      the CURRENT regime's persistence, which is genuinely regime-conditional and
      MOVES over time (a feature: sticky-vol vs fast-mean-reverting regimes).
    - Student-t innovations (equity returns are fat-tailed); returns scaled x100 for
      the optimiser. Causal: each fit uses only returns through its refit date.
    - Guard: half-life undefined (NaN) when alpha+beta >= 1 (IGARCH / non-stationary)
      or the fit fails.

    v-next (registered upgrade, charter): component / spline-GARCH (Engle-Rangel) to
    split short-run shock persistence from the slow-drifting baseline level.
    """
    import warnings

    from arch import arch_model

    x = (100.0 * r).dropna()
    hl = pd.Series(np.nan, index=x.index, name="half_life")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        for i in range(garch_window, len(x), step):
            sub = x.iloc[i - garch_window:i]
            try:
                res = arch_model(sub, mean="Constant", vol="GARCH", p=1, q=1, dist="t").fit(disp="off")
                persistence = res.params["alpha[1]"] + res.params["beta[1]"]
                hl.iloc[i] = np.log(0.5) / np.log(persistence) if 0.0 < persistence < 1.0 else np.nan
            except Exception:
                hl.iloc[i] = np.nan
    return hl.ffill().reindex(r.index)


# ── driver / presentation (wired for you) ───────────────────────────────────────

def build(r: pd.Series | None = None) -> pd.DataFrame:
    """Descriptor spine for a returns series. Defaults to the US market panel;
    pass any region's returns (the OOS harness does) to build the same
    descriptors elsewhere."""
    if r is None:
        r = load_returns()
    vol = ewma_vol(r)
    pct = expanding_percentile(vol)
    hl = shock_half_life(r)
    hl_pct = expanding_percentile(hl).rename("half_life_pctile")   # "how unusual" from its OWN history
    out = pd.DataFrame({"mkt_ret": r, "vol_annual": vol, "vol_pctile": pct,
                        "half_life": hl, "half_life_pctile": hl_pct})
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
