"""Macro data collection: FRED series via fredapi.

Fetches T10Y2Y (10Y-2Y yield spread), BAMLH0A0HYM2 (ICE BofA HY OAS), and
NFCI (Chicago Fed National Financial Conditions Index). Aligns everything
to business-day frequency with causal forward-fill and saves to
data/macro_data.csv.

Phase 5 FEAT-01: these three FRED series populate the Macro and Financial
Conditions sections of the sectioned funnel feature architecture.
"""

import os
import pandas as pd
from datetime import datetime

from src.config import START_DATE, DATA_DIR, FRED_API_KEY


# FRED series code -> canonical column name in features pipeline
FRED_SERIES = {
    'T10Y2Y':       'yield_curve_slope',  # daily; 10Y-2Y Treasury spread
    'BAMLH0A0HYM2': 'HY_OAS',             # daily; ICE BofA HY Option-Adjusted Spread
    'NFCI':         'NFCI',               # weekly (Friday); forward-fill to business day
}


def _fetch_via_fredapi(api_key: str, start_date: str) -> pd.DataFrame:
    """Primary path: authenticated fredapi client."""
    from fredapi import Fred
    fred = Fred(api_key=api_key)
    frames = {}
    for code, name in FRED_SERIES.items():
        s = fred.get_series(code, observation_start=start_date)
        if s is None or len(s) == 0:
            raise ValueError(f"FRED series '{code}' returned empty response")
        s.name = name
        frames[name] = s
    return pd.DataFrame(frames)


def _fetch_via_pdr(start_date: str) -> pd.DataFrame:
    """Fallback path: pandas_datareader (no API key needed, rate-limited)."""
    import pandas_datareader.data as pdr
    frames = {}
    for code, name in FRED_SERIES.items():
        df = pdr.get_data_fred(code, start=start_date)
        if df is None or df.empty:
            raise ValueError(f"FRED series '{code}' returned empty response (pdr)")
        # pdr returns a one-column DataFrame; rename to canonical name
        s = df.iloc[:, 0]
        s.name = name
        frames[name] = s
    return pd.DataFrame(frames)


def collect_macro_features(start_date: str | None = None,
                           api_key: str | None = None) -> pd.DataFrame:
    """Fetch FRED macro series, align to business-day frequency, return DataFrame.

    Args:
        start_date: ISO date string (e.g. '2010-01-01'). Defaults to config.START_DATE.
        api_key:    FRED API key. Defaults to config.FRED_API_KEY. Empty string triggers
                    pandas_datareader fallback.

    Returns:
        DataFrame with business-day DatetimeIndex and columns
        ['HY_OAS', 'NFCI', 'yield_curve_slope'] (forward-filled).

    Causal guarantee: all gaps are forward-filled, never back-filled. For weekly
    NFCI this means the Friday reading applies from Friday onward (see 05-RESEARCH.md
    Pitfall 2 for the publication-lag note).
    """
    start = start_date or START_DATE
    key = FRED_API_KEY if api_key is None else api_key

    if key:
        print(f"[collect_macro] Using fredapi with authenticated key (start={start})")
        raw = _fetch_via_fredapi(key, start)
    else:
        print(f"[collect_macro] FRED_API_KEY empty -- falling back to pandas_datareader (start={start})")
        raw = _fetch_via_pdr(start)

    # Align to business-day frequency with causal forward-fill
    # (weekly NFCI and gappy daily series both get filled)
    aligned = raw.resample('B').last().ffill()

    # Input validation (ASVS V5): assert non-empty result
    assert len(aligned) >= 252, (
        f"Insufficient macro data after alignment: {len(aligned)} business days "
        f"(need >= 252). Check FRED availability or start_date."
    )
    expected_cols = set(FRED_SERIES.values())
    missing = expected_cols - set(aligned.columns)
    assert not missing, f"Macro data missing expected columns: {missing}"

    aligned.index.name = 'Date'
    return aligned


def collect() -> pd.DataFrame:
    """Top-level entry: fetch macro features and save to data/macro_data.csv."""
    os.makedirs(DATA_DIR, exist_ok=True)
    macro = collect_macro_features()
    out_path = os.path.join(DATA_DIR, 'macro_data.csv')
    macro.to_csv(out_path)
    print(f"[collect_macro] Saved {len(macro)} rows to {out_path}")
    print(f"[collect_macro] Date range: {macro.index.min().date()} -> {macro.index.max().date()}")
    print(f"[collect_macro] Columns: {list(macro.columns)}")
    return macro


if __name__ == '__main__':
    collect()
