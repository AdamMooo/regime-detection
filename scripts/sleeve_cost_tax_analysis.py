"""Phase 4 gate check: does the 48-industry momentum sleeve survive realistic costs + Canadian tax drag?

NO-LOOK characterization (per PRODUCT-PLAN Phase 4 "A3 implementation harness" — costs/tax realism
TODO item), not a new hypothesis test. Reuses buffered_momentum() unmodified: monkeypatches the
module's COST constant per tier rather than editing momentum_breadth.py (buffering thresholds,
lookback, and weighting stay frozen a-priori).

Part 1: independent recomputation of the reported ~2.78x/yr turnover (sanity check).
Part 2: cost sensitivity at 20/50/100 bps per unit L1 turnover.
Part 3: illustrative Canadian tax-drag model (registered vs non-registered, flat cap-gains
inclusion — Canada has no US-style short/long distinction).
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import momentum_breadth as mb
from run_config import maxdd

ANN = 12
MARGINAL_RATE = 0.45          # illustrative top-bracket, NOT a claim about Adam's actual bracket
INCLUSION = 0.5                # Canadian capital-gains inclusion rate, flat regardless of holding period
EFFECTIVE_TAX = INCLUSION * MARGINAL_RATE   # 22.5% illustrative effective rate on realized gains


def independent_turnover_check(R):
    """Re-derive annualized L1 turnover independently of buffered_momentum(), same recipe,
    separate code path, to sanity-check the reported ~2.78x/yr figure."""
    inds = R.columns
    cum12 = (1 + R).rolling(12).apply(np.prod, raw=True) - 1
    score = ((1 + cum12) / (1 + R) - 1).shift(1)
    vol = R.rolling(12).std().shift(1)
    held = set()
    wp = pd.Series(0.0, index=inds)
    turns = []
    for i, t in enumerate(R.index):
        s = score.iloc[i]
        if s.isna().any() or vol.iloc[i].isna().any():
            continue
        pct = s.rank(pct=True)
        held = {n for n in held if pct[n] >= 0.5} | {n for n in inds if pct[n] >= 0.667}
        iv = (1.0 / vol.iloc[i])[list(held)]
        w = pd.Series(0.0, index=inds)
        if len(held):
            w[list(held)] = (iv / iv.sum()).values
        turns.append(np.abs(w - wp).sum())
        wp = w
    return float(np.mean(turns) * ANN), len(turns)


def toy_hand_example():
    """3-asset, 3-month hand-checkable example of the L1-turnover-mean*12 convention."""
    # month1: 100% A. month2: swap fully to B (L1 = |0-1|+|1-0|+0 = 2.0). month3: no change (L1=0).
    turns = [2.0, 0.0]
    ann = np.mean(turns) * 12
    # by hand: mean(2,0)=1.0 -> *12 = 12.0x/yr. A full swap every other month annualizes to 12x --
    # confirms the L1-sum convention is TWO-SIDED (counts both the sell and the buy leg).
    return ann


def cost_tier_perf(R, rf, cost_bps):
    mb.COST = cost_bps
    r, turn = mb.buffered_momentum(R, rf)
    common = r.index.intersection(rf.dropna().index)
    ret = r.loc[common].to_numpy()
    rfc = rf.loc[common].to_numpy()
    eq = np.cumprod(1 + ret)
    return dict(
        cost_bps=cost_bps,
        ann_ret=float(eq[-1] ** (ANN / len(ret)) - 1),
        sharpe=float((ret - rfc).mean() / ret.std() * np.sqrt(ANN)),
        max_dd=maxdd(ret),
        ann_turnover=turn,
    ), pd.Series(ret, index=common)


def annual_tax_drag(monthly_ret):
    """Illustrative approximation: at ~2.78x/yr turnover, the average holding period (~4-5
    months) is well under a year, so treat each calendar year's gain as if fully realized within
    that year (conservative/simple — ignores loss carryforwards and partial deferral from names
    held >1yr). Losses get no tax benefit in this simplified model (flagged, not resolved)."""
    annual = (1 + monthly_ret).resample("YE").prod() - 1
    after_tax = annual.where(annual <= 0, annual * (1 - EFFECTIVE_TAX))
    pretax_cagr = (1 + annual).prod() ** (1 / len(annual)) - 1
    aftertax_cagr = (1 + after_tax).prod() ** (1 / len(annual)) - 1
    return pretax_cagr, aftertax_cagr


def main():
    print("=" * 70)
    print("PART 1 — turnover validation")
    print("=" * 70)
    hand_ann = toy_hand_example()
    print(f"Hand example (full swap every other month) -> {hand_ann:.1f}x/yr")
    print("Confirms convention: L1 sum of |w_t - w_t-1| is TWO-SIDED (sells+buys both counted),")
    print("so 'turn[-1]*COST*1e-4' charges cost on both legs of every swap — this is the")
    print("conservative direction (over- not under-states cost), consistent with the plan's")
    print("'don't trust AQR's self-interested 23bps, treat as best-case' skepticism.\n")

    R = mb.load_industry(48)
    m = (1 + R).resample("ME").prod() - 1
    reported = pd.read_csv(ROOT / "results/momentum_breadth_48.csv")["ann_turnover"].iloc[0]
    indep_turn, n_months = independent_turnover_check(m)
    print(f"Reported ann_turnover (momentum_breadth_48.csv): {reported:.2f}x/yr")
    print(f"Independent recomputation (separate code path): {indep_turn:.2f}x/yr over {n_months} months")
    print(f"Match: {'YES' if abs(reported - indep_turn) < 0.01 else 'NO -- INVESTIGATE'}\n")

    print("=" * 70)
    print("PART 2 — cost sensitivity (20 / 50 / 100 bps per unit L1 turnover)")
    print("=" * 70)
    rf = ((1 + pd.read_csv(ROOT / "data/processed/assets_daily.csv", index_col=0, parse_dates=True)["rf"])
          .resample("ME").prod() - 1)
    rfc = rf.reindex(m.index)

    rows = []
    series_by_tier = {}
    for cost in (20.0, 50.0, 100.0):
        p, ret_series = cost_tier_perf(m, rfc, cost)
        rows.append(p)
        series_by_tier[cost] = ret_series
        print(f"  cost={cost:>5.0f}bps  ann_ret={p['ann_ret']:7.2%}  sharpe={p['sharpe']:6.3f}  "
              f"max_dd={p['max_dd']:7.2%}  turnover={p['ann_turnover']:.2f}x")
    mb.COST = 20.0  # restore default

    print("\n" + "=" * 70)
    print("PART 3 — Canadian tax-drag illustration (20bps cost tier, illustrative only)")
    print("=" * 70)
    print(f"Assumed: {INCLUSION:.0%} inclusion rate x {MARGINAL_RATE:.0%} illustrative top marginal "
          f"rate = {EFFECTIVE_TAX:.1%} effective tax on realized gains (Canada: flat, no holding-"
          f"period distinction, UNLIKE US short/long-term).")
    base_ret = series_by_tier[20.0]
    pretax_cagr, aftertax_cagr = annual_tax_drag(base_ret)
    print(f"  Registered account (RRSP/TFSA) -- zero tax drag:      CAGR {pretax_cagr:.2%}")
    print(f"  Non-registered, illustrative {EFFECTIVE_TAX:.1%} effective tax: CAGR {aftertax_cagr:.2%}")
    print(f"  Tax drag: {(pretax_cagr - aftertax_cagr):.2%}/yr\n")

    print("BUSINESS-INCOME RISK FLAG: ~2.78x/yr turnover with a sub-1-year average hold sits in a "
          "range CRA could plausibly assert is 'business income' (100% inclusion, no cap-gains "
          "treatment at all) rather than capital gains -- this is a real classification risk that "
          "needs a tax professional's read, not a number this script can resolve.\n")

    print("RECOMMENDATION: run this sleeve inside a registered account (RRSP/TFSA) if at all "
          "possible -- it eliminates the tax-drag question entirely and is a bigger lever than any "
          "turnover/cost optimization.")


if __name__ == "__main__":
    main()
