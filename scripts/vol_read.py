"""Vol read — PRESENTATION of the volatility signal (how to view it).

Not a state, not a verdict. A continuous read of three things: where volatility
sits (level + percentile), which way it is moving (drift), and how unusual that
is vs a century of its own history (rarity). Consumes the descriptor spine
(vol_descriptors.build) and produces a plain-language read + an annotated figure
that teaches how to view it.

Run:  python scripts/vol_read.py
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from vol_descriptors import build


def current_read(df: pd.DataFrame) -> dict:
    d = df.dropna(subset=["vol_annual", "vol_pctile"])
    latest, asof = d.iloc[-1], d.index[-1]
    vol = float(latest["vol_annual"] * 100)
    pct = float(latest["vol_pctile"] * 100)
    drift = float((d["vol_pctile"].tail(11).iloc[-1] - d["vol_pctile"].tail(11).iloc[0]) * 100)
    trend = "rising" if drift > 3 else ("cooling" if drift < -3 else "holding")
    # what fraction of the past year ran hotter than today (stable context read)
    yr_higher = float((d["vol_annual"].tail(252) > latest["vol_annual"]).mean() * 100)
    # how durable is the current shock: mean-reversion half-life in trading days,
    # plus how unusual that durability is vs its own history
    hl = df["half_life"].dropna()
    half_life = float(hl.iloc[-1]) if len(hl) else float("nan")
    hlp = df["half_life_pctile"].dropna()
    half_life_pct = float(hlp.iloc[-1] * 100) if len(hlp) else float("nan")
    return dict(asof=asof.date(), vol=vol, pct=pct, drift=drift, trend=trend,
                yr_higher=yr_higher, half_life=half_life, half_life_pct=half_life_pct)


def text_read(r: dict) -> str:
    band = ("very low" if r["pct"] < 20 else "below-normal" if r["pct"] < 40 else
            "middling" if r["pct"] < 60 else "elevated" if r["pct"] < 80 else "high")
    lines = [
        f"VOLATILITY READ — as of {r['asof']}",
        f"  Level:    {r['vol']:.0f}% annualised  ({band}, {r['pct']:.0f}th pctile of its own century)",
        f"  Moving:   {r['trend']}  ({r['drift']:+.0f} pctile pts over 10 sessions)",
    ]
    lines.append(f"  Context:  vol ran hotter than today on {r['yr_higher']:.0f}% of the past year")
    if np.isfinite(r["half_life"]):
        rare = (f", {r['half_life_pct']:.0f}th pctile of its own history" if np.isfinite(r["half_life_pct"]) else "")
        lines.append(f"  Durable:  a vol shock half-fades in ~{r['half_life']:.0f} trading days"
                     f" (mean-reversion{rare})")
    return "\n".join(lines)


def figure(df: pd.DataFrame, r: dict) -> Path:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    d = df.dropna(subset=["vol_annual"]).copy()
    d["vol_annual"] *= 100
    p50, p75, p90 = np.nanpercentile(d["vol_annual"], [50, 75, 90])
    recent = d[d.index >= d.index[-1] - pd.DateOffset(months=24)]
    cur_x, cur_y = recent.index[-1], recent["vol_annual"].iloc[-1]

    fig = plt.figure(figsize=(13, 7))
    gs = fig.add_gridspec(2, 2, height_ratios=[1.4, 1], hspace=0.3, wspace=0.25)

    # ── Panel 1: recent 24 months — WHERE + WHICH WAY, against historical bands
    ax1 = fig.add_subplot(gs[0, :])
    ax1.plot(recent.index, recent["vol_annual"], color="#1f77b4", lw=1.3)
    for lvl, lab in [(p50, "median"), (p75, "75th"), (p90, "90th")]:
        ax1.axhline(lvl, color="#bbb", lw=0.8, ls="--")
        ax1.text(recent.index[0], lvl, f" {lab} ({lvl:.0f}%)", va="bottom", fontsize=8, color="#888")
    ax1.scatter([cur_x], [cur_y], s=70, color="#d62728", zorder=5)
    ax1.annotate(f"you are here\n{r['vol']:.0f}% · {r['pct']:.0f}th pctile · {r['trend']}",
                 (cur_x, cur_y), xytext=(-120, 20), textcoords="offset points",
                 fontsize=9, color="#d62728",
                 arrowprops=dict(arrowstyle="->", color="#d62728"))
    ax1.set_title("Where is vol now, and which way is it moving? (last 24 months vs its historical bands)")
    ax1.set_ylabel("annualised vol %")

    # ── Panel 2: full century — SCALE (how big can this get?)
    ax2 = fig.add_subplot(gs[1, 0])
    ax2.plot(d.index, d["vol_annual"], color="#9ecae1", lw=0.4)
    ax2.axhline(cur_y, color="#d62728", lw=1.0)
    ax2.text(d.index[0], cur_y, f" now {r['vol']:.0f}%", va="bottom", fontsize=8, color="#d62728")
    ax2.set_title("Full century — for scale", fontsize=10)
    ax2.set_ylabel("annualised vol %")

    # ── Panel 3: distribution — RARITY (how unusual is this level?)
    ax3 = fig.add_subplot(gs[1, 1])
    ax3.hist(d["vol_annual"].dropna(), bins=80, color="#9ecae1")
    ax3.axvline(cur_y, color="#d62728", lw=1.5)
    ax3.text(cur_y, ax3.get_ylim()[1] * 0.9, f" now: {r['pct']:.0f}th pctile", fontsize=8, color="#d62728")
    ax3.set_title("How unusual is this level? (100yr distribution)", fontsize=10)
    ax3.set_xlabel("annualised vol %")

    p = ROOT / "results" / "vol_read.png"
    fig.savefig(p, dpi=110, bbox_inches="tight")
    plt.close(fig)
    return p


def main() -> int:
    df = build()
    r = current_read(df)
    print(text_read(r))
    png = figure(df, r)
    print(f"\nwrote {png.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
