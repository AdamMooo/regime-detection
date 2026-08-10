"""Phase 6 credit/EBP — THE ONE LOOK. Runs ONCE. Charter v1.0, signed 2026-08-09.

    ┌──────────────────────────────────────────────────────────────────────────┐
    │  READ BEFORE RUNNING                                                     │
    │                                                                          │
    │  This script spends Phase 6's single look. There is no way to unspend    │
    │  it. Do not run it to "see how it's going", do not run it with a bar     │
    │  commented out, and do not adjust a threshold after seeing a number —    │
    │  every threshold below is frozen in                                      │
    │  .planning/phases/06-credit-signal/06-CREDIT-CHARTER.md and was signed   │
    │  before any value existed.                                               │
    │                                                                          │
    │  Output → results/credit_validation.txt, then overnight cooling-off,     │
    │  then a SEPARATE dated results sign-off. The charter signature           │
    │  authorised the build, not the conclusion.                               │
    └──────────────────────────────────────────────────────────────────────────┘

WHAT V2 ASKS, and why it is the decisive bar
--------------------------------------------
Not "is the EBP a good signal" but "is its HISTORY stable enough that a percentile
computed against it means anything?"

The EBP is an OLS residual, `EBP_t = s_t − x_t'β̂_v`, where β̂_v is refit on all data
through vintage v. So adding one month moves β̂ and therefore moves EVERY historical
residual. The revision has a closed form:

    r_v(t) = EBP_v(t) − EBP_today(t) = x_t'(β̂_today − β̂_v)

which is proportional to the regressor vector at t. Revisions should therefore
concentrate in months with extreme regressors — the crisis months. Registered in the
charter as a prior, not a bar: "revisions are small on average" and "revisions are small
where it matters" are different claims, and bar A only measures the first.

`assert_causal` cannot see any of this. It guards the CODE; the instability is in the
DATA. That is exactly why V2 exists and why V1 alone is not enough.

Standard literature: real-time / vintage data analysis — Orphanides (2001),
Croushore & Stark (2001), both cited in the charter.

Run:  python scripts/validate_credit.py            # THE LOOK. Once.
      python scripts/validate_credit.py --self-test # plumbing only, synthetic data
"""

from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import credit_ebp
from causal import assert_causal, expanding_percentile

VINTAGE_DIR = ROOT / "data" / "vintages" / "ebp"
OUT = ROOT / "results" / "credit_validation.txt"

# ── frozen thresholds — charter v1.0 §"Validation bars", do not touch ──────────
SETTLED_LAG_MONTHS = 12      # a month is "settled" 12m before a vintage's last obs
BAR_A_MAX = 0.25             # RMS revision ÷ full-sample σ
BAR_B_MIN = 0.95             # MINIMUM Spearman across vintages (clarified 2026-08-09)
BAR_C_MIN = 0.90            # POOLED ±1-decile agreement share (clarified 2026-08-09)
BAR_R4_MAX = 0.90            # |Spearman| vs the monthly volatility reading → demote
BURN_IN_MONTHS = 120         # matches credit_ebp.BURN_IN_MONTHS
N_DECILES = 10
SUB_PERIOD_SPLIT = "1999-01-01"   # V6: 1973–1998 vs 1999–2026


# ══════════════════════════════════════════════════════════════════════════════
#  SCAFFOLDING — plumbing, provided. Read it, but the bars below are yours.
# ══════════════════════════════════════════════════════════════════════════════

def load_vintage(payload: bytes) -> pd.Series:
    """One archived vintage → a clean monthly `ebp` series indexed by observation date.

    The `errors="coerce"` + dropna is NOT defensive boilerplate. The 2025-06-12 capture
    ships a trailing bare `,,,` line, and `build_credit.py:41` parses this family of
    file with no `errors=` guard — so that row becomes a NaT-indexed all-NaN row
    WITHOUT raising. The charter registers handling it as a requirement of this script.
    `est_prob` is dropped entirely: it is an explicit recession forecast and has no
    place in this repo.
    """
    frame = pd.read_csv(io.StringIO(payload.decode("utf-8-sig")))
    frame.columns = [c.strip().lower() for c in frame.columns]
    datecol = next(c for c in frame.columns if "date" in c)
    frame[datecol] = pd.to_datetime(frame[datecol], errors="coerce")
    frame = frame.dropna(subset=[datecol]).set_index(datecol).sort_index()
    return frame["ebp"].astype(float).rename("ebp")


def load_vintages() -> dict[str, pd.Series]:
    """All archived vintages, keyed by capture timestamp (ascending)."""
    out = {}
    for path in sorted(VINTAGE_DIR.glob("*.csv")):
        if path.name == "MANIFEST.csv":
            continue
        out[path.stem] = load_vintage(path.read_bytes())
    if not out:
        raise RuntimeError(f"no vintages in {VINTAGE_DIR} — run harvest_ebp_vintages.py")
    return out


def load_today() -> pd.Series:
    """The current vintage — the reference every archived vintage is compared against."""
    return credit_ebp.load_panel()["ebp"].astype(float).rename("ebp")


def settled_index(vintage: pd.Series, lag_months: int = SETTLED_LAG_MONTHS) -> pd.DatetimeIndex:
    """Months of `vintage` old enough that channel-3 refit effects dominate.

    The Board calls balance-sheet restatement and panel composition "modest,
    concentrated in recent months". Cutting the last `lag_months` removes most of those
    two so that what remains is mostly the full-sample refit — the channel the Board
    does not name and the one this bar is about. Also excludes the rarity burn-in,
    since a percentile does not exist there.
    """
    cutoff = vintage.index.max() - pd.DateOffset(months=lag_months)
    warm = vintage.index[BURN_IN_MONTHS:]
    return vintage.index[(vintage.index <= cutoff) & vintage.index.isin(warm)]


def causal_deciles(series: pd.Series) -> pd.Series:
    """Causal expanding percentile → decile bucket 0..9.

    `expanding_percentile` ranks each point only against `{s : s <= t}`, so the decile at
    t is what a reader holding THIS vintage could have computed AT t. That is the whole
    point of bar C: it compares published readings, not raw levels.
    """
    pct = expanding_percentile(series)
    return np.floor(pct * N_DECILES).clip(0, N_DECILES - 1).rename("decile")


# ══════════════════════════════════════════════════════════════════════════════
#  THE BARS — Adam writes these four. Signatures and contracts are fixed so the
#  report writer and the self-test work against them unchanged.
# ══════════════════════════════════════════════════════════════════════════════

def revisions(vintages: dict[str, pd.Series], today: pd.Series) -> pd.DataFrame:
    """Long-form revision table, one row per (vintage, settled month).

    Returns columns: `vintage` (str), `obs_date` (Timestamp), `ebp_vintage` (float),
    `ebp_today` (float), `revision` (float = ebp_vintage − ebp_today).

    Only months in `settled_index(vintage)` that also exist in `today`. This table is
    the input to all three bars, so build it once.
    """
    raise NotImplementedError("Adam writes this — see the docstring contract above")


def bar_a(rev: pd.DataFrame, today: pd.Series) -> dict:
    """A — RMS revision ÷ full-sample σ of today's EBP.  PASS if <= BAR_A_MAX.

    Return {"value": float, "rms": float, "sigma": float, "pass": bool}.

    σ is the standard deviation of `today` over its FULL sample — the scale-free
    normalisation, so the bar does not depend on the EBP's units.
    """
    raise NotImplementedError("Adam writes this")


def bar_b(rev: pd.DataFrame) -> dict:
    """B — Spearman(vintage, today) per vintage.  PASS if the MINIMUM >= BAR_B_MIN.

    Return {"value": float (the min), "median": float,
            "per_vintage": pd.Series indexed by vintage, "pass": bool}.

    Spearman, not Pearson: the emitted output is a percentile, so what must survive
    restatement is the ORDERING, not the levels. Gate on the min — a median would let
    one catastrophic restatement hide behind eighteen good ones (charter, 2026-08-09).
    """
    raise NotImplementedError("Adam writes this")


def bar_c(vintages: dict[str, pd.Series], today: pd.Series) -> dict:
    """C — POOLED share of settled months whose causal decile agrees within ±1. DECISIVE.

    PASS if the pooled share >= BAR_C_MIN. Return
    {"value": float, "n_pairs": int, "per_vintage": pd.Series, "pass": bool}.

    Use `causal_deciles` on each vintage AND on `today`, then compare on that vintage's
    `settled_index`. Pooled across all (vintage, month) pairs, so later vintages weigh
    more — accepted knowingly in the charter.

    This is the decisive bar because it tests the PRODUCT: whether the reading you would
    have published then matches the one you would publish now.
    """
    raise NotImplementedError("Adam writes this")


# ══════════════════════════════════════════════════════════════════════════════
#  V1 / V5 / V6 + report — scaffolding, provided
# ══════════════════════════════════════════════════════════════════════════════

def v1_causal(panel: pd.DataFrame) -> dict:
    """V1 — the shared look-ahead guard, plus the publication lag it cannot check.

    `assert_causal` perturbs the input after a cut and requires every earlier reading to
    be bit-identical. It proves the CONSTRUCTION does not read forward. It structurally
    CANNOT detect vintage leak, which lives in the data — that is V2's job, and saying so
    here keeps a green V1 from being read as more than it is.
    """
    assert_causal(credit_ebp.build, panel)
    return {"pass": True, "lag_months": credit_ebp.PUBLICATION_LAG_MONTHS}


def v5_companion(today: pd.Series) -> dict:
    """V5 — PIT-clean companion: does `gz_spread` track unrevised Baa−10y?

    Plumbing verification only; the companion is NOT the signal. A failure here means a
    broken or mis-parsed input, which is a data failure rather than a finding.
    """
    panel = credit_ebp.load_panel()
    if "gz_spread" not in panel.columns:
        return {"pass": None, "note": "gz_spread absent from the panel"}
    gz = panel["gz_spread"].astype(float)
    both = pd.concat([gz, today], axis=1).dropna()
    return {
        "pass": None,  # judged in the report against the charter's wording, not a number
        "corr_gz_ebp": float(both.corr(method="spearman").iloc[0, 1]),
        "n": int(len(both)),
        "note": "OAS columns ig_oas/hy_oas start 2023-08-07 (FRED rolling licence window), "
                "so they are a 3-year cross-check, never history",
    }


def v6_subperiod(today: pd.Series) -> dict:
    """V6 — sub-period stability, a registered DEGRADED substitute for the intl bar.

    A temporal split would not have caught the sector-dispersion artifact that Japan and
    Europe killed, so this cannot lift evidence maturity — only fail it.
    """
    early, late = today.loc[:SUB_PERIOD_SPLIT], today.loc[SUB_PERIOD_SPLIT:]
    return {
        "early": {"n": int(early.count()), "mean": float(early.mean()), "sd": float(early.std())},
        "late": {"n": int(late.count()), "mean": float(late.mean()), "sd": float(late.std())},
        "split": SUB_PERIOD_SPLIT,
    }


def write_report(sections: list[str]) -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(sections) + "\n", encoding="utf-8")
    print("\n".join(sections))
    print(f"\nwrote {OUT.relative_to(ROOT)}")


def run_the_look() -> int:
    vintages, today = load_vintages(), load_today()
    panel = credit_ebp.load_panel()

    rev = revisions(vintages, today)
    a, b, c = bar_a(rev, today), bar_b(rev), bar_c(vintages, today)
    v1, v5, v6 = v1_causal(panel), v5_companion(today), v6_subperiod(today)

    failed = [n for n, r in (("A", a), ("B", b), ("C", c)) if not r["pass"]]
    r2_fires = len(failed) >= 2

    lines = [
        "=" * 78,
        "PHASE 6 — CREDIT / EXCESS BOND PREMIUM — ONE-LOOK VALIDATION",
        f"charter v1.0 signed 2026-08-09 | vintages compared: {len(vintages)}",
        f"reference vintage (today): {today.index.min().date()}..{today.index.max().date()}",
        "=" * 78,
        "",
        f"V1 causal guard            : PASS (lag {v1['lag_months']}m enforced in build)",
        "   NOTE: V1 guards the CODE. It cannot detect vintage leak, which is in the DATA.",
        "",
        "V2 — VINTAGE INSTABILITY (decisive)",
        f"   A  RMS revision / sigma : {a['value']:.4f}   (<= {BAR_A_MAX})  "
        f"{'PASS' if a['pass'] else 'FAIL'}",
        f"        RMS={a['rms']:.4f}  sigma={a['sigma']:.4f}",
        f"   B  min Spearman         : {b['value']:.4f}   (>= {BAR_B_MIN})  "
        f"{'PASS' if b['pass'] else 'FAIL'}",
        f"        median={b['median']:.4f}",
        f"   C  pooled +/-1 decile   : {c['value']:.4f}   (>= {BAR_C_MIN})  "
        f"{'PASS' if c['pass'] else 'FAIL'}   <- DECISIVE",
        f"        n pairs={c['n_pairs']}",
        "",
        f"   R2 (two of three fail)  : {'FIRES -> DROP' if r2_fires else 'not tripped'}"
        + (f"   failed: {', '.join(failed)}" if failed else ""),
        "",
        "   Registered prior (charter, pre-look): revisions should concentrate where the",
        "   regressors are extreme, i.e. crisis months. Bar A measures the AVERAGE only.",
        "   Largest absolute revisions, for reading A honestly:",
    ]
    worst = rev.reindex(rev["revision"].abs().sort_values(ascending=False).index).head(10)
    for row in worst.itertuples():
        lines.append(
            f"        {row.obs_date.date()}  rev={row.revision:+.4f}  vintage={row.vintage}"
        )

    lines += [
        "",
        "   Per-vintage detail (Spearman | +/-1 decile share):",
    ]
    for v in b["per_vintage"].index:
        lines.append(
            f"        {v}  rho={b['per_vintage'][v]:+.4f}  "
            f"decile_share={c['per_vintage'].get(v, float('nan')):.4f}"
        )

    lines += [
        "",
        f"V5 companion (plumbing)    : spearman(gz_spread, ebp)={v5.get('corr_gz_ebp', float('nan')):.4f} "
        f"n={v5.get('n', 0)}",
        f"   {v5['note']}",
        "",
        f"V6 sub-period (degraded)   : split {v6['split']}",
        f"   1973-1998  n={v6['early']['n']:3d}  mean={v6['early']['mean']:+.4f}  sd={v6['early']['sd']:.4f}",
        f"   1999-2026  n={v6['late']['n']:3d}  mean={v6['late']['mean']:+.4f}  sd={v6['late']['sd']:.4f}",
        "   Cannot lift evidence maturity, only fail it (registered degraded substitute).",
        "",
        "V7 international           : UNMET BY CONSTRUCTION (EBP is US-only). R7 caps",
        "                             evidence maturity; `production` unavailable.",
        "",
        "=" * 78,
        "MATURITY CEILING: `research`, registered pre-look and NOT reopenable on a strong",
        "result. G4 is UNOPPOSED, not confirmed — Phase 7 was dropped, so the registered",
        "leave-one-out can never run. Uniqueness is untested, not established.",
        "",
        "This file is a RESULT, not a conclusion. Overnight cooling-off, then a separate",
        "dated results sign-off in the charter.",
        "=" * 78,
    ]
    write_report(lines)
    return 0


# ══════════════════════════════════════════════════════════════════════════════
#  SELF-TEST — exercises the plumbing on synthetic data so the look stays unspent
# ══════════════════════════════════════════════════════════════════════════════

def self_test() -> int:
    """Verify the scaffolding without touching the real EBP.

    Everything here runs on synthetic frames. The point is that `load_vintage`,
    `settled_index` and `causal_deciles` can be trusted BEFORE the one look, because
    debugging them afterwards would mean having already spent it.
    """
    ok = []

    payload = b"date,gz_spread,ebp,est_prob\n" + b"".join(
        f"{m}/1/2000,1.0,{0.1 * i:.3f},0.05\n".encode() for i, m in enumerate([1, 2, 3], 1)
    ) + b",,,\n"
    s = load_vintage(payload)
    ok.append(("dateless trailing row dropped", len(s) == 3 and s.notna().all()))
    ok.append(("est_prob excluded", s.name == "ebp"))

    idx = pd.date_range("1970-01-01", periods=BURN_IN_MONTHS + 40, freq="MS")
    v = pd.Series(np.random.default_rng(0).normal(size=len(idx)), index=idx, name="ebp")
    settled = settled_index(v)
    ok.append(("settled excludes burn-in", settled.min() >= idx[BURN_IN_MONTHS]))
    ok.append((
        "settled excludes last 12m",
        settled.max() <= idx.max() - pd.DateOffset(months=SETTLED_LAG_MONTHS),
    ))

    d = causal_deciles(v)
    ok.append(("deciles in 0..9", bool(d.dropna().between(0, N_DECILES - 1).all())))
    ok.append(("deciles causal (len preserved)", len(d) == len(v)))

    for name, passed in ok:
        print(f"  {'ok  ' if passed else 'FAIL'}  {name}")
    failed = [n for n, p in ok if not p]
    print(f"\n{len(ok) - len(failed)}/{len(ok)} scaffolding checks pass")
    if failed:
        return 1
    print("\nBars A/B/C are NotImplementedError — the look has NOT been spent.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Phase 6 credit one-look")
    ap.add_argument(
        "--self-test", action="store_true",
        help="exercise the scaffolding on synthetic data; does NOT spend the look",
    )
    ap.add_argument(
        "--i-am-spending-the-one-look", action="store_true",
        help="required to run the actual validation. Read the header first.",
    )
    args = ap.parse_args()

    if args.self_test:
        return self_test()
    if not args.i_am_spending_the_one_look:
        print(__doc__)
        print("Refusing to run. This spends Phase 6's single look.")
        print("  plumbing check : python scripts/validate_credit.py --self-test")
        print("  spend the look : python scripts/validate_credit.py --i-am-spending-the-one-look")
        return 2
    return run_the_look()


if __name__ == "__main__":
    sys.exit(main())
