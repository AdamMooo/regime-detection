"""Inflation / real-rate sensor (PC2) — the stock-bond correlation regime.

Reads assets_daily.csv (mkt_ret x bond10_ret, 1962+) and computes the CAUSAL trailing
correlation between equity and 10-year-bond daily returns. That correlation is the observable
proxy for the nominal-real covariance (the inflation-growth correlation), and its SIGN is the
state of the market assumption "bonds will hedge an equity drawdown":

    corr < 0  -> INTACT    demand-shock world: equities fall, yields fall, bonds RALLY (2000-2021)
    corr > 0  -> VIOLATED  supply/inflation world: bonds AND equities fall together (1970s-80s, 2022)

This is a MEASUREMENT INSTRUMENT for the assumption ledger (see .planning/REGIME-SENSOR-ARCHITECTURE.md),
NOT a forecast: it reports the CURRENT realized correlation state; it does not predict when the sign flips.
No-look descriptive characterization — writes results/stockbond_corr.csv.

Run:  python scripts/stockbond_corr.py
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from causal import ewma_vol, expanding_z

PRIMARY_W = 126          # 6-month primary window (pre-committed 2026-08-02, before looking)
ROBUST_W = (63, 252)     # quarter / year robustness windows
NEUTRAL_BAND = 0.10      # |corr| <= band -> ambiguous transition zone ("under test")

# ex-post regime datings — used only to CHECK the sensor reads sensibly (descriptive), not to fit it
EPISODES = {
    "1970s-80s  (expect +, supply/inflation)": ("1970-01-01", "1989-12-31"),
    "1990s      (transition)":                  ("1990-01-01", "1999-12-31"),
    "2000-2021  (expect -, demand/deflation)":  ("2000-01-01", "2021-12-31"),
    "2022+      (expect + flip)":               ("2022-01-01", "2026-12-31"),
}


PANEL_COLUMNS = ("eq", "bond")   # the two-column schema every region must supply


def load_us_panel() -> pd.DataFrame:
    """US equity x 10y-bond daily returns, the signal's home panel (1962+)."""
    df = pd.read_csv(ROOT / "data" / "processed" / "assets_daily.csv",
                     parse_dates=["date"]).set_index("date")
    panel = df[["mkt_ret", "bond10_ret"]].dropna()   # bond10_ret starts 1962
    return panel.rename(columns={"mkt_ret": "eq", "bond10_ret": "bond"})


def load_returns():
    p = load_us_panel()
    return p["eq"], p["bond"]


def rolling_corr(eq, bond, window):
    """Causal trailing Pearson correlation of equity vs bond daily returns.
    rolling(window) uses only [t-window+1, t] -> no look-ahead by construction."""
    return eq.rolling(window).corr(bond)


def sign_state(corr, band=NEUTRAL_BAND):
    """Map the correlation to the assumption's status (observation, never an instruction)."""
    s = pd.Series(np.where(corr < -band, "intact",
                  np.where(corr > band, "violated", "under_test")), index=corr.index)
    return s.where(corr.notna())


def monthly_corr(eq, bond, window_m=24):
    """Same state at MONTHLY frequency (the literature's convention). Daily comovement is noisier
    and understates the slow nominal-real covariance; monthly is the honest read of the regime."""
    m_eq = (1.0 + eq).resample("ME").prod() - 1.0
    m_bond = (1.0 + bond).resample("ME").prod() - 1.0
    return m_eq.rolling(window_m).corr(m_bond)


# ---- context layer: what these environments were, how long they lasted, how assets behaved ----

def contiguous_runs(state):
    """Maximal constant runs of the state: list of (value, start, end, n_days)."""
    grp = (state != state.shift()).cumsum()
    runs = []
    for _, seg in state.groupby(grp):
        runs.append((seg.iloc[0], seg.index[0], seg.index[-1], len(seg)))
    return runs


def asset_panel(eq, bond):
    """Daily returns of the assets whose behavior we characterize by regime state."""
    df = pd.read_csv(ROOT / "data" / "processed" / "assets_daily.csv",
                     parse_dates=["date"]).set_index("date")
    panel = pd.DataFrame({
        "equity": df["mkt_ret"],
        "bond10": df["bond10_ret"],
        "gold": df.get("gold_ret"),
    })
    return panel


def behavior_by_state(state, panel, min_days=120):
    """Descriptive: annualized return / vol / Sharpe of each asset, conditional on the sensor state.
    CAVEAT: raw returns by state are CONFOUNDED by the secular rate cycle (the positive-corr era was
    also the high-rate era) — read hedge_behavior_by_state, not this, for whether the hedge worked."""
    rows = []
    for st in ("intact", "under_test", "violated"):
        m = state.reindex(panel.index) == st
        for a in panel.columns:
            r = panel[a][m].dropna()
            if len(r) < min_days:
                continue
            vol = r.std() * np.sqrt(252)
            rows.append({"state": st, "asset": a, "ann_ret": r.mean() * 252,
                         "ann_vol": vol, "sharpe": (r.mean() * 252) / vol if vol else np.nan})
    return pd.DataFrame(rows)


def hedge_behavior_by_state(state, eq, bond):
    """The on-mechanism read: on EQUITY-DOWN days, did bonds cushion (rise) or fail (fall too)?
    This measures whether the hedge WORKED, conditional on the sensor state — and unlike average
    returns it is not confounded by the secular rate level."""
    rows = []
    for st in ("intact", "under_test", "violated"):
        m = (state == st) & (eq < 0)
        b = bond[m.reindex(bond.index, fill_value=False)].dropna()
        if len(b) < 60:
            continue
        rows.append({"state": st, "eq_down_days": len(b),
                     "bond_also_fell": (b < 0).mean(),
                     "avg_bond_ret_on_eq_down_day": b.mean()})
    return pd.DataFrame(rows)


def build(panel: pd.DataFrame | None = None) -> pd.DataFrame:
    """Descriptor frame for ANY region's equity x bond panel (columns: eq, bond).

    Region-agnostic by signature so the shared OOS harness can drive it (D-20);
    defaults to the US home panel. Causal throughout — guarded by
    `assert_causal` in tests/test_causal.py.
    """
    if panel is None:
        panel = load_us_panel()
    eq, bond = panel["eq"], panel["bond"]

    corr = {w: rolling_corr(eq, bond, w) for w in (PRIMARY_W, *ROBUST_W)}
    primary = corr[PRIMARY_W]

    return pd.DataFrame({
        "corr_126": primary,
        "corr_63": corr[63],
        "corr_252": corr[252],
        "level_z": expanding_z(primary),
        "state": sign_state(primary),
        # the vol sensor's own estimator, so the orthogonality diagnostic compares
        # against the real signal rather than a local one-off (was ewm halflife=20)
        "eq_vol": ewma_vol(eq),
    }).dropna(subset=["corr_126"])


def main():
    panel = load_us_panel()
    eq, bond = panel["eq"], panel["bond"]
    out = build(panel)
    (ROOT / "results").mkdir(exist_ok=True)
    out.to_csv(ROOT / "results" / "stockbond_corr.csv")

    line = "=" * 78
    print(line)
    print("STOCK-BOND CORRELATION SENSOR (PC2) — assumption: 'bonds will hedge an equity drawdown'")
    print(f"{line}\ndata: {out.index[0].date()} .. {out.index[-1].date()}  ({len(out)} days)  |  "
          f"primary window {PRIMARY_W}d, neutral band |corr|<={NEUTRAL_BAND}")

    # (4) episode check — does the SIGN match the known regimes?
    print("\n(4) EPISODE CHECK — mean corr by window; does the sign match the known regime?")
    print(f"    {'period':42}{'126d':>8}{'63d':>8}{'252d':>8}   dominant sign")
    for name, (a, b) in EPISODES.items():
        seg = out.loc[a:b]
        if seg.empty:
            continue
        m126, m63, m252 = seg["corr_126"].mean(), seg["corr_63"].mean(), seg["corr_252"].mean()
        frac_pos = (seg["corr_126"] > 0).mean()
        sign = f"{'+' if m126 > 0 else '-'}  ({frac_pos:.0%} of days > 0)"
        print(f"    {name:42}{m126:8.2f}{m63:8.2f}{m252:8.2f}   {sign}")

    # (3) orthogonality-to-vol DIAGNOSTIC (not a gate): the corr state is distinct from vol magnitude
    mcorr = monthly_corr(eq, bond)
    rho_cv = out["corr_126"].corr(out["eq_vol"])
    print(f"\n(3) ORTHOGONALITY DIAGNOSTIC — corr(daily-126d state, equity vol) = {rho_cv:+.2f}"
          "  (partial overlap, not independent)")
    print("    THE 2022 FLIP — daily vs monthly, mean vs trajectory (calendar mean hides the window lag):")
    print(f"      {'year':6}{'d126 mean':>11}{'d126 peak':>11}{'d126 end':>10}{'mon24 mean':>12}{'eq vol':>9}")
    for yr in (2008, 2022, 2023):
        seg = out.loc[f"{yr}-01-01":f"{yr}-12-31"]
        mseg = mcorr.loc[f"{yr}-01-01":f"{yr}-12-31"]
        print(f"      {yr:<6}{seg['corr_126'].mean():>+11.2f}{seg['corr_126'].max():>+11.2f}"
              f"{seg['corr_126'].iloc[-1]:>+10.2f}{mseg.mean():>+12.2f}{seg['eq_vol'].mean():>9.0%}")

    # (6) failure surface — how often is the sensor in its ambiguous zone?
    frac = out["state"].value_counts(normalize=True)
    print("\n(6) FAILURE SURFACE — time spent in each state (the 'under_test' band is the ambiguous zone):")
    for st in ("intact", "under_test", "violated"):
        print(f"      {st:12}{frac.get(st, 0.0):6.1%}")

    # ---- CONTEXT LAYER — what this environment was, how long it lasted, how assets behaved ----
    panel = asset_panel(eq, bond)
    runs = contiguous_runs(out["state"])
    violated = [r for r in runs if r[0] == "violated" and r[3] >= 120]
    durations = np.array([r[3] for r in violated]) if violated else np.array([])
    cur_val, cur_start, _, cur_len = runs[-1]
    beh = behavior_by_state(out["state"], panel)
    beh.to_csv(ROOT / "results" / "stockbond_context.csv", index=False)

    print("\n" + line)
    print("CONTEXT LAYER — understanding the environment (descriptive; the human decides)")
    print(line)

    print("\nSIMILAR HISTORICAL ENVIRONMENTS (major 'violated' / positive-corr episodes, >=120d):")
    for _, a, b, n in violated:
        print(f"    {a.date()} .. {b.date()}   {n/252:4.1f}y")
    if durations.size:
        print(f"    -> such episodes last {np.median(durations)/252:.1f}y median, "
              f"{durations.max()/252:.1f}y max  ({durations.size} episodes)")

    pctile = (out["corr_126"] <= out["corr_126"].iloc[-1]).mean()
    print(f"\nHOW UNUSUAL / WHERE WE ARE:  current state '{cur_val}' for {cur_len/252:.1f}y "
          f"(since {cur_start.date()}); today's 126d corr sits at the {pctile:.0%} percentile of 1962-2026")

    print("\nDID THE HEDGE WORK? — on EQUITY-DOWN days, did bonds cushion or fail? (the on-mechanism read):")
    hb = hedge_behavior_by_state(out["state"], eq, bond)
    print(f"    {'state':12}{'eq-down days':>13}{'bonds also fell':>16}{'avg bond ret (that day)':>25}")
    for _, r in hb.iterrows():
        print(f"    {r['state']:12}{int(r['eq_down_days']):>13}{r['bond_also_fell']:>15.0%} "
              f"{r['avg_bond_ret_on_eq_down_day']:>+24.3%}")

    print("\n(raw returns by state — CONFOUNDED by the secular rate cycle, do NOT read as hedge quality):")
    print(f"    {'state':12}{'asset':8}{'ret':>8}{'vol':>8}{'sharpe':>8}")
    for _, r in beh.iterrows():
        print(f"    {r['state']:12}{r['asset']:8}{r['ann_ret']:>8.1%}{r['ann_vol']:>8.1%}{r['sharpe']:>8.2f}")

    # ---- the assumption-ledger entry: observation -> context -> relevance (the human decides) ----
    now = out.iloc[-1]
    med = f"{np.median(durations)/252:.1f}y" if durations.size else "n/a"
    print("\n" + line)
    print(f"ASSUMPTION-LEDGER ENTRY ({out.index[-1].date()}) — \"bonds will hedge an equity drawdown\"")
    print(line)
    print(f"  OBSERVATION:  {now['state'].upper()} — 126d stock-bond corr {now['corr_126']:+.2f} "
          f"(63d {now['corr_63']:+.2f} / 252d {now['corr_252']:+.2f}), {now['level_z']:+.1f}z vs history")
    print(f"  CONTEXT:      positive stock-bond correlation = the regime where bonds have historically hedged "
          f"equity drawdowns LESS")
    print(f"                (on equity-down days in this state bonds also fell more often — table above); "
          f"current episode {cur_len/252:.1f}y in, similar episodes historically lasted ~{med} median")
    print(f"  RELEVANCE:    relates to the assumption 'bonds hedge equity drawdowns' — historically less reliable "
          f"in this environment.")
    print(f"                (What this means / whether to act on it is not this system's job.)")
    print(f"\nwrote results/stockbond_corr.csv + results/stockbond_context.csv")
    return 0


if __name__ == "__main__":
    sys.exit(main())
