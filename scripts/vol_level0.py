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

from signal_output_schema import validate

SRC = ROOT / "results" / "vol_descriptors.csv"
OUT = ROOT / "results" / "vol_level0.json"


def _band(p: float) -> str:
    """Verbal band for a percentile. Presentation only — the continuous number
    is the reading (V2 showed the 5-band discretization drifts 22% of days)."""
    return ("very low" if p < 0.10 else "low" if p < 0.30 else
            "typical" if p < 0.70 else "elevated" if p < 0.90 else "very high")


def build_record(df: pd.DataFrame) -> dict:
    d = df.dropna(subset=["vol_annual", "vol_pctile"])
    now, asof = d.iloc[-1], d.index[-1].date().isoformat()

    pct = d["vol_pctile"]
    drift = float(pct.iloc[-1] - pct.iloc[-11]) if len(pct) >= 11 else float("nan")
    extreme = pct >= 0.95
    last_extreme = extreme[extreme].index[-1].date().isoformat() if extreme.any() else None

    hl, hl_p = now.get("half_life"), now.get("half_life_pctile")
    have_hl = pd.notna(hl)

    return {
        "signal": "volatility",
        "assumption_monitored": (
            "N/A — volatility is a context axis (the PC1 barometer), not an assumption-monitor. "
            "It colors how every other signal should be read; it carries no intact/violated status."
        ),
        "clock": "daily",
        "reading": {
            "as_of": asof,
            "annualised_volatility": round(float(now["vol_annual"]), 4),
            "history_band": _band(float(now["vol_pctile"])),
            "shock_half_life_trading_days": round(float(hl), 1) if have_hl else None,
            "half_life_note": (
                None if have_hl else
                "undefined: GARCH persistence alpha+beta >= 1 (IGARCH guard) or fit failed"
            ),
            "estimator": "EWMA lambda=0.94 (level); GARCH(1,1)-t on a trailing 1260d window, refit quarterly (durability)",
        },
        "rarity": {
            "level_percentile": round(float(now["vol_pctile"]), 4),
            "durability_percentile": round(float(hl_p), 4) if pd.notna(hl_p) else None,
            "basis": "causal expanding percentile against the signal's own history to date (no full-sample rank)",
            "calibration": "expanding percentile ~uniform (mean 0.48); corr(level, percentile) = 0.735",
        },
        "trend": {
            "level_percentile_change_10_sessions": round(drift, 4),
            "direction": "rising" if drift > 0.03 else "falling" if drift < -0.03 else "flat",
        },
        "extreme_conditions": {
            "days_at_or_above_95th_percentile": int(extreme.sum()),
            "share_of_history": round(float(extreme.mean()), 4),
            "most_recent_such_day": last_extreme,
            "durability_range_p10_p90_trading_days": [9, 276],
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
        "spec_version": "1.0",
    }


def main() -> int:
    df = pd.read_csv(SRC, parse_dates=["date"]).set_index("date")
    record = build_record(df)
    validate(record)
    OUT.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(f"schema-valid; wrote {OUT.relative_to(ROOT)}")
    print(json.dumps(record["reading"], indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
