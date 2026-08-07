"""Stock-bond correlation signal — the registered one-look (charter V2-V5).

Charter: .planning/phases/02-stockbond-signal/02-STOCKBOND-CHARTER.md (v1.0,
signed off 2026-08-06). ONE LOOK. Do not rerun to "refresh" — a second look is a
second look.

Order is deliberate and matches the charter: the V4 POWER PRE-CHECK runs FIRST
and gates interpretation of everything after it. A region that spends nearly all
its sample in one state cannot produce a meaningful by-state contrast, and
saying so afterwards is how noise becomes a finding.

Run:  python scripts/validate_stockbond.py
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from stockbond_corr import (MONTHLY_ROBUST, MONTHLY_W, build_monthly,
                            load_region_monthly, rolling_corr, sign_state)

REGIONS = ("us", "japan", "europe")
STATES = ("intact", "under_test", "violated")
MIN_MONTHS = 24          # charter V4: below this, a state is UNDERPOWERED, not weak
OUT = ROOT / "results" / "stockbond_validation.txt"

lines: list[str] = []


def say(s: str = "") -> None:
    print(s)
    lines.append(s)


def v4_power(frames: dict[str, pd.DataFrame]) -> dict[str, bool]:
    """Charter V4. Returns {region: powered}. Runs BEFORE any contrast is read."""
    say("=" * 78)
    say("[V4] POWER PRE-CHECK (runs FIRST; gates every contrast below)")
    say("=" * 78)
    say(f"  bar: every state needs >= {MIN_MONTHS} months, else the region is UNDERPOWERED")
    say(f"  {'region':9}{'span':26}{'n':>6}" + "".join(f"{s:>12}" for s in STATES) + "   verdict")
    powered = {}
    for r in REGIONS:
        df = frames[r]
        counts = {s: int((df["state"] == s).sum()) for s in STATES}
        ok = all(c >= MIN_MONTHS for c in counts.values())
        powered[r] = ok
        span = f"{df.index[0].date()} .. {df.index[-1].date()}"
        say(f"  {r:9}{span:26}{len(df):>6}" + "".join(f"{counts[s]:>12}" for s in STATES)
            + ("   POWERED" if ok else "   UNDERPOWERED"))
    say()
    return powered


def v2_hedge_behaviour(frames: dict[str, pd.DataFrame], powered: dict[str, bool]) -> None:
    """Charter V2 (primary metric). On EQUITY-DOWN months, did bonds cushion or
    fall too? Bar: fraction-bonds-also-fell monotone increasing across
    intact -> under_test -> violated. Not confounded by the rate cycle, unlike
    average returns by state."""
    say("=" * 78)
    say("[V2] HEDGE BEHAVIOUR BY STATE — the on-mechanism read (PRIMARY)")
    say("=" * 78)
    say("  on months when equity fell, how often did bonds ALSO fall?")
    say("  bar: monotone INCREASING across intact -> under_test -> violated")
    for r in REGIONS:
        df = frames[r]
        say(f"\n  {r.upper()}" + ("" if powered[r] else "   [UNDERPOWERED — reported as coverage, not evidence]"))
        say(f"    {'state':12}{'eq-down mths':>14}{'bonds also fell':>18}{'avg bond ret':>15}")
        fracs = {}
        for s in STATES:
            m = (df["state"] == s) & (df["eq"] < 0)
            b = df.loc[m, "bond"]
            if len(b) < 6:
                say(f"    {s:12}{len(b):>14}{'--':>18}{'--':>15}")
                continue
            fracs[s] = float((b < 0).mean())
            say(f"    {s:12}{len(b):>14}{fracs[s]:>17.0%}{b.mean():>+15.2%}")
        present = [s for s in STATES if s in fracs]
        if len(present) >= 2:
            vals = [fracs[s] for s in present]
            mono = all(x <= y + 1e-12 for x, y in zip(vals, vals[1:]))
            say(f"    -> across {' < '.join(present)}: "
                f"{' -> '.join(f'{v:.0%}' for v in vals)}  "
                f"{'MONOTONE (bar met)' if mono else 'NOT monotone (bar NOT met)'}")
        else:
            say("    -> insufficient state coverage for a contrast")
    say()


def v5_window_robustness(panels: dict[str, pd.DataFrame]) -> None:
    """Charter V5. The state must not be an artifact of the window: 12/24/36-month
    correlations must agree on sign in the same periods."""
    say("=" * 78)
    say("[V5] WINDOW ROBUSTNESS — is the state an artifact of the window?")
    say("=" * 78)
    say(f"  {'region':9}" + "".join(f"{f'sign agree {w}m':>18}" for w in MONTHLY_ROBUST)
        + f"{'corr(12m,36m)':>16}")
    for r in REGIONS:
        p = panels[r]
        base = rolling_corr(p["eq"], p["bond"], MONTHLY_W)
        cells = []
        for w in MONTHLY_ROBUST:
            alt = rolling_corr(p["eq"], p["bond"], w)
            both = pd.concat([base, alt], axis=1).dropna()
            cells.append(float((np.sign(both.iloc[:, 0]) == np.sign(both.iloc[:, 1])).mean()))
        a = rolling_corr(p["eq"], p["bond"], MONTHLY_ROBUST[0])
        b = rolling_corr(p["eq"], p["bond"], MONTHLY_ROBUST[1])
        rho = float(pd.concat([a, b], axis=1).dropna().corr().iloc[0, 1])
        say(f"  {r:9}" + "".join(f"{c:>17.0%}" for c in cells) + f"{rho:>16.2f}")
    say()


def v3_replication(frames: dict[str, pd.DataFrame]) -> None:
    """Charter V3 descriptive layer: does the correlation LEVEL itself replicate
    in shape and range out-of-sample?"""
    say("=" * 78)
    say("[V3] CROSS-REGION LEVELS — does the measurement look like the same object?")
    say("=" * 78)
    say(f"  {'region':9}{'mean':>9}{'min':>9}{'max':>9}{'latest':>9}{'  latest state':>16}")
    for r in REGIONS:
        c = frames[r]["corr"]
        say(f"  {r:9}{c.mean():>+9.2f}{c.min():>+9.2f}{c.max():>+9.2f}{c.iloc[-1]:>+9.2f}"
            f"{frames[r]['state'].iloc[-1]:>16}")
    say()


def main() -> int:
    panels = {r: load_region_monthly(r) for r in REGIONS}
    frames = {r: build_monthly(panels[r]) for r in REGIONS}

    say("=" * 78)
    say("STOCK-BOND CORRELATION — ONE-LOOK VALIDATION (charter V2-V5)")
    say("assumption monitored: 'bonds hedge equity drawdowns'")
    say("=" * 78)
    say(f"clock: monthly | primary window {MONTHLY_W}m | robustness {MONTHLY_ROBUST} | "
        f"neutral band |corr| <= 0.10")
    say("REGISTERED LIMITATION: the international sample begins 1990 and therefore does")
    say("NOT contain the 1970s-80s inflation regime. This run cannot test the full")
    say("sign-flip cycle out-of-sample; 'production' is unavailable to this phase.")
    say()

    powered = v4_power(frames)
    v3_replication(frames)
    v2_hedge_behaviour(frames, powered)
    v5_window_robustness(panels)

    say("=" * 78)
    say("Read against the charter's V2-V5 bars and R1-R5 reject conditions.")
    say("Results sign-off is Adam's, dated, after overnight cooling-off.")
    say("=" * 78)

    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nwrote {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
