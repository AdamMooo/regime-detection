"""Emit the volatility signal's Level-0 historical-context record.

Level 0 = measurement + historical context, and STOPS there (signal-output-spec
§4). The record is GENERATED from the committed descriptor artifact and then
passed through `signal_output_schema.validate()`, so the HARD BOUNDARY is
enforced by the closed allowlist rather than by my care in writing JSON.

Signed off by Adam 2026-08-06 (see the phase charter's RESULTS SIGN-OFF).

Run:  python scripts/vol_level0.py
"""

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from data_vintage import KEN_FRENCH_MONTHLY_FILE, available_at, policy_note
from signal_output_schema import validate

SRC = ROOT / "results" / "vol_descriptors.csv"
OUT = ROOT / "results" / "vol_level0.json"

# market_daily.csv is built from Ken French's daily factor file, so a day's return is
# only visible to this pipeline once the file covering that month is posted.
SOURCE = KEN_FRENCH_MONTHLY_FILE


def _band(p: float) -> str:
    """Verbal band for a percentile. Presentation only — the continuous number
    is the reading (V2 showed the 5-band discretization drifts 22% of days)."""
    return ("very low" if p < 0.10 else "low" if p < 0.30 else
            "typical" if p < 0.70 else "elevated" if p < 0.90 else "very high")


def build_record(df: pd.DataFrame) -> dict:
    d = df.dropna(subset=["vol_annual", "vol_pctile"])
    now, asof = d.iloc[-1], d.index[-1].date().isoformat()

    pct = d["vol_pctile"]
    drift = float(pct.iloc[-1] - pct.iloc[-11]) if len(pct) >= 11 else None
    extreme = pct >= 0.95
    last_extreme = extreme[extreme].index[-1].date().isoformat() if extreme.any() else None

    hl, hl_p = now.get("half_life"), now.get("half_life_pctile")
    have_hl = pd.notna(hl)

    return {
        "spec_version": "1.0",
        "signal": "volatility",
        "as_of": asof,
        # Governed by the SOURCE's publication cadence, not by the trading day —
        # see scripts/data_vintage.py. A backtest filters on this, never on as_of.
        "available_at": available_at(asof, SOURCE),
        "supersedes": None,
        "assumption_monitored": (
            "N/A because volatility is a context axis (the PC1 barometer), not an assumption-monitor. "
            "It colors how every other signal should be read; it carries no intact/violated status."
        ),
        "clock": "daily",
        "reading": {
            "value": round(float(now["vol_annual"]), 4),
            "units": "annualised_volatility",
            "estimator": "EWMA lambda=0.94 on daily log returns, 252d burn-in",
            "context_band": _band(float(now["vol_pctile"])),
            "secondary_readings": [{
                "name": "shock_half_life",
                "value": round(float(hl), 1) if have_hl else None,
                "units": "trading_days",
                "estimator": (
                    "ln(0.5)/ln(alpha+beta) from GARCH(1,1)-t on a trailing 1260d window, "
                    "refit quarterly"
                ),
                "undefined_reason": (
                    None if have_hl else
                    "GARCH persistence alpha+beta >= 1 (IGARCH guard) or fit failed"
                ),
            }],
        },
        "rarity": {
            "level_percentile": round(float(now["vol_pctile"]), 4),
            # Expanding, therefore causal: p_t ranks x_t only against {x_s : s <= t}.
            # A full-sample rank would embed the future distribution in today's reading.
            "basis": "expanding",
            "window": None,
            "calibration": "expanding percentile ~uniform (mean 0.48); corr(level, percentile) = 0.735",
            "secondary_percentiles": [{
                "name": "durability",
                "level_percentile": round(float(hl_p), 4) if pd.notna(hl_p) else None,
                "basis": "expanding",
                "window": None,
            }],
        },
        "trend": {
            # null, never "flat": with fewer than 11 observations the drift is unknown,
            # and "flat" would assert something the data does not say. NaN would also
            # serialize as invalid strict JSON, which the history writer refuses.
            "level_percentile_change": None if drift is None else round(drift, 4),
            "lookback_observations": 10,
            "direction": None if drift is None else (
                "rising" if drift > 0.03 else "falling" if drift < -0.03 else "flat"
            ),
        },
        "extreme_conditions": {
            "threshold_percentile": 0.95,
            "observations_at_or_above": int(extreme.sum()),
            "share_of_history": round(float(extreme.mean()), 4),
            "most_recent_such_date": last_extreme,
            "undefined_eras": "US 1930-1950 (alpha+beta >= 1, non-stationary)",
        },
        "cross_signal_relationships": [
            "Conditions every other signal: the same valuation or concentration reading means something "
            "different in a high-volatility environment than a calm one.",
            "Partially overlaps the stock-bond correlation signal (corr of the 126d state with equity "
            "volatility is non-zero) — mechanistically distinct, kept separate per the mechanism gate.",
            "Descriptive only: persistence means volatility forecasts volatility, never returns or direction.",
        ],
        "assessment": {
            "mechanism": "pass",
            "measurement_validity": "H",
            "investment_usefulness": "H",
            "evidence_maturity": "H",
        },
        "maturity": "production",
    }


def load_history() -> pd.DataFrame:
    """Full descriptor history, date-indexed ascending.

    `build_record(load_history().loc[:as_of])` is the only supported way to obtain a
    past reading — same code path as the live one, with nothing after `as_of` in
    scope. `observation_history.py` relies on this signature.
    """
    return pd.read_csv(SRC, parse_dates=["date"]).set_index("date").sort_index()


def main() -> int:
    df = load_history()
    record = build_record(df)
    validate(record)
    OUT.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(f"schema-valid; wrote {OUT.relative_to(ROOT)}")
    print(json.dumps(record["reading"], indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
