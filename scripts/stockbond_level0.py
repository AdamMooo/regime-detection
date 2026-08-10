"""Emit the stock-bond correlation signal's Level-0 historical-context record.

Level 0 = measurement + historical context, and STOPS there (signal-output-spec
§4). Generated from the committed monthly descriptor artifact and passed through
`signal_output_schema.validate()`, so the HARD BOUNDARY is enforced by the closed
allowlist rather than by my care in writing JSON.

Two things this record is deliberately careful about:

- **D-02b (continuous-first).** The ledger status is a DERIVED label. It is never
  emitted without the underlying correlation AND its rarity beside it. The number
  leads; the state is a view of the number, never a replacement for it.
- **The maturity ceiling.** `research`, capped by the scope limitation registered
  BEFORE the look: the international panels begin 1990 and contain no inflation
  regime, so the sign-flip cycle is untested out-of-sample. A strong V2 result is
  exactly when that cap is most tempting to drop.

Results signed off by Adam 2026-08-07 (see the phase charter's RESULTS SIGN-OFF).

Run:  python scripts/stockbond_level0.py
"""

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from data_vintage import KEN_FRENCH_MONTHLY_FILE, available_at
from signal_output_schema import validate

# Built from assets_daily.csv (Ken French equity returns + 10y bond returns). The slower
# source binds, so availability follows the Ken French file cadence.
SOURCE = KEN_FRENCH_MONTHLY_FILE

SRC = ROOT / "results" / "stockbond_monthly.csv"
OUT = ROOT / "results" / "stockbond_level0.json"

MAJOR_EPISODE_M = 12    # an episode long enough to be a regime rather than a blip


def _band(p: float) -> str:
    """Verbal band for a percentile. Presentation only — the continuous number is
    the reading."""
    return ("very low" if p < 0.10 else "low" if p < 0.30 else
            "typical" if p < 0.70 else "elevated" if p < 0.90 else "very high")


def _runs(state: pd.Series):
    grp = (state != state.shift()).cumsum()
    return [(seg.iloc[0], seg.index[0], seg.index[-1], len(seg))
            for _, seg in state.groupby(grp)]


def build_record(df: pd.DataFrame) -> dict:
    d = df.dropna(subset=["corr"])
    now, asof = d.iloc[-1], d.index[-1].date().isoformat()

    pct = d["level_pctile"]
    drift = float(pct.iloc[-1] - pct.iloc[-13]) if len(pct) >= 13 else float("nan")
    extreme = pct >= 0.95
    last_extreme = extreme[extreme].index[-1].date().isoformat() if extreme.any() else None

    runs = _runs(d["state"])
    _, cur_start, _, cur_len = runs[-1]
    major = [n for v, _, _, n in runs if v == "violated" and n >= MAJOR_EPISODE_M]

    return {
        "spec_version": "1.0",
        "signal": "stock_bond_correlation",
        "as_of": asof,
        "available_at": available_at(asof, SOURCE),
        "supersedes": None,
        "assumption_monitored": "bonds hedge equity drawdowns",
        "clock": "monthly",
        "assumption_state": {
            "status": str(now["state"]),
            "derivation": (
                "DERIVED from the correlation, never standalone: corr < -0.10 intact, "
                "|corr| <= 0.10 under_test, corr > +0.10 violated. The +/-0.10 neutral band "
                "was pre-committed 2026-08-02 before looking and is not re-tunable."
            ),
        },
        "reading": {
            "value": round(float(now["corr"]), 4),
            "units": "pearson_correlation",
            "estimator": "causal 24-month trailing Pearson correlation of monthly equity and 10y-bond total returns",
            "context_band": _band(float(now["level_pctile"])),
            "secondary_readings": [{
                "name": "level_z",
                "value": round(float(now["level_z"]), 4),
                "units": "standard_deviations",
                "estimator": "causal expanding-window standardization of the 24m correlation",
            }],
        },
        "rarity": {
            "level_percentile": round(float(now["level_pctile"]), 4),
            "basis": "expanding",
            "window": None,
            "calibration": (
                "expanding percentile mean 0.47 over 1963-2026. Note the status and the rarity "
                "disagree by design: the correlation is positive (violated) yet only mid-percentile, "
                "because the 1970s-80s were positive too. Violated is not the same as unprecedented."
            ),
        },
        "trend": {
            "level_percentile_change": round(drift, 4),
            "lookback_observations": 12,
            "direction": "rising" if drift > 0.05 else "falling" if drift < -0.05 else "flat",
        },
        "extreme_conditions": {
            "threshold_percentile": 0.95,
            "observations_at_or_above": int(extreme.sum()),
            "share_of_history": round(float(extreme.mean()), 4),
            "most_recent_such_date": last_extreme,
            "episodes": {
                "current_length": int(cur_len),
                "current_start": cur_start.date().isoformat(),
                "length_units": "months",
                "major_episode_definition": f"a contiguous violated run of >= {MAJOR_EPISODE_M} months",
                "major_episode_median_max": (
                    [int(np.median(major)), int(max(major))] if major else None
                ),
            },
        },
        "cross_signal_relationships": [
            "Partially overlaps the volatility signal statistically; mechanistically distinct "
            "(PC2 inflation/real-rate vs PC1 risk-off) and kept separate per the mechanism gate.",
            "Read alongside volatility: a violated hedge assumption in a calm market and in a "
            "stressed one are different environments, and neither reading substitutes for the other.",
            "Descriptive only: this reports the realized correlation state. It does not forecast "
            "when the sign will flip and does not claim the flip is forecastable.",
        ],
        "assessment": {
            "mechanism": "pass",
            "measurement_validity": "H",
            "investment_usefulness": "H",
            "evidence_maturity": "M",
        },
        "maturity": "research",
    }


def main() -> int:
    df = pd.read_csv(SRC, index_col=0, parse_dates=True)
    record = build_record(df)
    validate(record)
    OUT.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(f"schema-valid; wrote {OUT.relative_to(ROOT)}")
    print(json.dumps(record["reading"], indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
