"""Daily OHLC panels for the range-based-volatility detector probe (NO look — instrument QA).

The frozen detector uses close-to-close downside features on the Ken French return-only panel. Its
documented failure = fast crashes (1998 LTCM, 2018Q4): a one-day intraday plunge that closes only
modestly down barely moves a 10-day close-to-close EWM. Range-based estimators (Parkinson 1980;
Garman-Klass 1980) use the intraday High/Low and are ~5x more EFFICIENT for the same latent vol, so
they register the spike the day it happens. This is a sharper ESTIMATOR of the vol axis we already
use (NOT a new economic axis — it does not violate the "everything collapses onto vol" finding); it
targets detection LAG only, as descriptive instrument QA measured against ex-post bear datings.

US = SPY (1993+, contains both known misses). Confirmation = Nikkei (^N225, 1990+) and Euro Stoxx
(^STOXX50E, 2007+) — the out-of-hypothesis-sample check dispersion failed.

Outputs data/processed/ohlc_{spy,nikkei,stoxx}.csv (date, open, high, low, close) + results/ohlc_gate.csv.
"""

from pathlib import Path

import numpy as np
import pandas as pd
import yfinance as yf

ROOT = Path(__file__).resolve().parent.parent
TICKERS = {"spy": "SPY", "nikkei": "^N225", "stoxx": "^STOXX50E"}


def fetch(ticker):
    df = yf.download(ticker, start="1990-01-01", progress=False, auto_adjust=False)
    df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]
    df = df.rename(columns=str.lower)[["open", "high", "low", "close"]].dropna()
    # OHLC integrity: high is the max, low is the min of the day
    bad = ((df["high"] < df[["open", "close", "low"]].max(axis=1)) |
           (df["low"] > df[["open", "close", "high"]].min(axis=1)) |
           (df[["open", "high", "low", "close"]] <= 0).any(axis=1))
    return df[~bad]


def main():
    rows = []
    for name, tk in TICKERS.items():
        df = fetch(tk)
        df.to_csv(ROOT / "data" / "processed" / f"ohlc_{name}.csv")
        rng = np.log(df["high"] / df["low"])
        rows.append((name, tk, str(df.index[0].date()), str(df.index[-1].date()), len(df),
                     round(float(rng.mean()), 4), int((rng <= 0).sum())))
    gate = pd.DataFrame(rows, columns=["panel", "ticker", "first", "last", "n",
                                       "mean_log_hl_range", "nonpositive_ranges"])
    gate.to_csv(ROOT / "results" / "ohlc_gate.csv", index=False)
    print(gate.to_string(index=False))


if __name__ == "__main__":
    main()
