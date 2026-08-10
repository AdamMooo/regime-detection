"""When could a reading actually have been known? (`available_at` policy)

`as_of` is the date a reading DESCRIBES. `available_at` is the wall-clock instant it was
COMPUTABLE. The gap is a property of the SOURCE, not of the estimator, and it is not
derivable from `as_of` — which is why the observation contract requires both.

Why this file exists rather than a constant inline: getting the gap wrong in the
optimistic direction is a look-ahead bug that shows up as better performance, never as
an error. So each source's lag is stated explicitly, with its reasoning, where it can be
reviewed and argued with.

    CONSERVATISM RULE
    Uncertainty resolves LATER, never earlier. Claiming data arrived sooner than it did
    leaks; claiming it arrived later only costs realism. When the true cadence is
    unknown, over-state the lag.

Tightening any lag below is exactly the direction that can introduce leakage, so it
requires evidence about the source's actual publication behaviour — not convenience.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pandas as pd

# Publication policies, keyed by the source a panel is built from.
#
# KEN_FRENCH_MONTHLY_FILE
#   data/processed/market_daily.csv (and the assets/industry panels) come from Ken
#   French's daily factor files. The individual daily return is knowable from prices at
#   that day's close, but THIS PIPELINE cannot see it until French posts the file
#   covering that month, which happens on a roughly monthly cadence some weeks after
#   month end. So availability is governed by the file, not the trading day.
#
#   Conservative rule: the 15th of the month AFTER the as_of month, 14:00 UTC. Historic
#   posting has generally been earlier than that; 15th is deliberately late.
#
# FRED_DAILY_SERIES
#   Market-priced daily series (Treasury yields, OAS, SOFR) publish next business day.
#   These are NOT revised, so first print is the only print.
#
# FRED_MONTHLY_REVISED
#   Macro series with a release lag AND subsequent revisions (the GZ/EBP inputs).
#   `available_at` must be FIRST-PRINT availability. Using the revision timestamp would
#   hand the backtest a number nobody had at the time — charter section 6, "revised
#   macro data".
#
# SHILLER_MONTHLY / AQR_MONTHLY
#   Manually-posted spreadsheets, irregular cadence, month-granular at best.

KEN_FRENCH_MONTHLY_FILE = "ken_french_monthly_file"
FRED_DAILY_SERIES = "fred_daily_series"
FRED_MONTHLY_REVISED = "fred_monthly_revised"
SHILLER_MONTHLY = "shiller_monthly"
AQR_MONTHLY = "aqr_monthly"

_POLICY_NOTES = {
    KEN_FRENCH_MONTHLY_FILE: "15th of the month following as_of, 14:00 UTC (file cadence, deliberately late)",
    FRED_DAILY_SERIES: "next business day 13:00 UTC (market-priced daily series, not revised)",
    FRED_MONTHLY_REVISED: "first print ~5 weeks after the reference month, 13:30 UTC; NEVER the revision date",
    SHILLER_MONTHLY: "20th of the month following as_of, 12:00 UTC (manual spreadsheet, irregular)",
    AQR_MONTHLY: "last day of the month following as_of, 12:00 UTC (manual spreadsheet, irregular)",
}


def policy_note(source: str) -> str:
    if source not in _POLICY_NOTES:
        raise ValueError(f"unknown source {source!r}; declare its policy in data_vintage.py")
    return _POLICY_NOTES[source]


def _month_end(ts: pd.Timestamp) -> pd.Timestamp:
    return ts + pd.offsets.MonthEnd(0)


def available_at(as_of, source: str) -> str:
    """The instant a reading for `as_of` first became computable from `source`.

    Returns an ISO-8601 UTC timestamp, the form the observation contract requires.
    """
    ts = pd.Timestamp(as_of)
    if ts.tzinfo is not None:
        ts = ts.tz_localize(None)

    if source == KEN_FRENCH_MONTHLY_FILE:
        nxt = (_month_end(ts) + timedelta(days=1)).replace(day=15)
        return _iso(nxt, hour=14)

    if source == FRED_DAILY_SERIES:
        nxt = ts + pd.offsets.BusinessDay(1)
        return _iso(nxt, hour=13)

    if source == FRED_MONTHLY_REVISED:
        # ~5 weeks past the reference month end: a typical first-print macro release.
        return _iso(_month_end(ts) + timedelta(days=35), hour=13, minute=30)

    if source == SHILLER_MONTHLY:
        nxt = (_month_end(ts) + timedelta(days=1)).replace(day=20)
        return _iso(nxt, hour=12)

    if source == AQR_MONTHLY:
        return _iso(_month_end(_month_end(ts) + timedelta(days=1)), hour=12)

    raise ValueError(f"unknown source {source!r}; declare its policy in data_vintage.py")


def _iso(ts: pd.Timestamp, hour: int, minute: int = 0) -> str:
    dt = datetime(
        ts.year, ts.month, ts.day, hour, minute, tzinfo=timezone.utc
    )
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
