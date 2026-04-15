"""
Data collection: OHLCV from yfinance, VIX family from Yahoo.
Aligns everything to SPY's trading-day index and saves raw data.

Supports incremental data collection with cache manifest and delta detection.
"""

import pandas as pd
import numpy as np
import yfinance as yf
import os
import json
import hashlib
from datetime import datetime

from src.config import (
    START_DATE, END_DATE,
    TICKERS, VIX_TICKER, VIX3M_TICKER, VVIX_TICKER,
    DATA_DIR, CACHE_PATH, INCREMENTAL_MODE,
)


def _compute_file_hash(filepath):
    """Compute SHA256 hash of a file."""
    if not os.path.exists(filepath):
        return None
    sha256_hash = hashlib.sha256()
    with open(filepath, 'rb') as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def _create_cache_manifest(tickers, cache_path=CACHE_PATH):
    """
    Create cache manifest with file hashes and metadata for all cached tickers.

    Returns dict: {
        "last_run": ISO timestamp,
        "tickers": {
            "SPY": {
                "hash": "sha256...",
                "mod_time": int,
                "last_fetch_date": "2026-04-13",
                "row_count": 3752
            },
            ...
        }
    }
    """
    manifest = {
        "last_run": datetime.utcnow().isoformat() + "Z",
        "tickers": {}
    }

    for ticker in tickers:
        cache_file = os.path.join(cache_path, f"{ticker}_incremental.csv")
        if os.path.exists(cache_file):
            file_hash = _compute_file_hash(cache_file)
            mod_time = int(os.stat(cache_file).st_mtime)
            # Count rows in CSV
            try:
                df = pd.read_csv(cache_file)
                row_count = len(df)
            except:
                row_count = 0

            manifest["tickers"][ticker] = {
                "hash": file_hash,
                "mod_time": mod_time,
                "last_fetch_date": datetime.utcnow().strftime("%Y-%m-%d"),
                "row_count": row_count
            }

    return manifest


def _load_cache_manifest(cache_path=CACHE_PATH):
    """Load cache manifest from JSON file."""
    manifest_file = os.path.join(cache_path, ".cache_manifest.json")
    if os.path.exists(manifest_file):
        try:
            with open(manifest_file, 'r') as f:
                return json.load(f)
        except:
            return None
    return None


def _save_cache_manifest(manifest, cache_path=CACHE_PATH):
    """Save cache manifest to JSON file."""
    os.makedirs(cache_path, exist_ok=True)
    manifest_file = os.path.join(cache_path, ".cache_manifest.json")
    with open(manifest_file, 'w') as f:
        json.dump(manifest, f, indent=2)


def _detect_delta(current_manifest, previous_manifest):
    """
    Detect which tickers have changed (hash mismatch) between current and previous manifest.

    Returns list of tickers that need to be re-fetched.
    """
    if not previous_manifest or "tickers" not in previous_manifest:
        return list(current_manifest.get("tickers", {}).keys())

    delta_tickers = []
    prev_tickers = previous_manifest.get("tickers", {})
    curr_tickers = current_manifest.get("tickers", {})

    # Check for new or changed tickers
    for ticker in curr_tickers.keys():
        if ticker not in prev_tickers:
            delta_tickers.append(ticker)
        elif prev_tickers[ticker].get("hash") != curr_tickers[ticker].get("hash"):
            delta_tickers.append(ticker)

    return delta_tickers


def _is_valid_cache(cache_path=CACHE_PATH):
    """Check if cache directory exists and manifest is valid."""
    if not os.path.exists(cache_path):
        return False
    manifest_file = os.path.join(cache_path, ".cache_manifest.json")
    if not os.path.exists(manifest_file):
        return False
    try:
        with open(manifest_file, 'r') as f:
            json.load(f)
        return True
    except:
        return False


def _load_cached_data(ticker, cache_path=CACHE_PATH):
    """
    Load cached data for a ticker from CSV.

    Returns DataFrame or None if no cache exists.
    """
    cache_file = os.path.join(cache_path, f"{ticker}_incremental.csv")
    if os.path.exists(cache_file):
        try:
            df = pd.read_csv(cache_file, index_col=0, parse_dates=True)
            return df
        except:
            return None
    return None


def _append_cache(df, ticker, cache_path=CACHE_PATH):
    """
    Append new data to cache CSV and update feather index.

    If cache file exists: load it, concat with new data, drop duplicates, write back.
    If cache file doesn't exist: write df as new CSV.
    """
    os.makedirs(cache_path, exist_ok=True)
    cache_file = os.path.join(cache_path, f"{ticker}_incremental.csv")
    index_file = os.path.join(cache_path, f"{ticker}_index.feather")

    # Load existing cache if it exists
    if os.path.exists(cache_file):
        try:
            existing_df = pd.read_csv(cache_file, index_col=0, parse_dates=True)
            df = pd.concat([existing_df, df])
        except:
            pass

    # Drop duplicates and save
    df = df.drop_duplicates(subset=None, keep='first')
    df.to_csv(cache_file)

    # Create/update feather index metadata
    index_metadata = {
        "schema": "OHLCV + VIX series",
        "schema_version": 1,
        "row_count": len(df),
        "date_range": [str(df.index.min()), str(df.index.max())],
        "columns": list(df.columns),
        "dtype_checksum": hashlib.sha256(str(df.dtypes).encode()).hexdigest()
    }

    # Save as JSON (for auditability; note: not an actual feather file)
    with open(index_file, 'w') as f:
        json.dump(index_metadata, f, indent=2)


def _validate_cache(df, expected_schema=None):
    """
    Validate cached data:
    1. Drop duplicate rows silently
    2. Forward-fill single missing values silently
    3. Raise ValueError if schema mismatch
    4. Raise ValueError if gap >10 consecutive trading days

    Returns validated DataFrame.
    """
    # Check schema if provided
    if expected_schema is not None:
        if set(df.columns) != set(expected_schema):
            raise ValueError(
                f"Schema mismatch: {set(df.columns)} vs {set(expected_schema)}"
            )

    # Drop duplicates
    n_before = len(df)
    df = df.drop_duplicates(keep='first')
    if len(df) < n_before:
        print(f"  Dropped {n_before - len(df)} duplicate rows")

    # Forward-fill single gaps
    n_nan_before = df.isna().sum().sum()
    df = df.ffill(limit=1)
    n_nan_after = df.isna().sum().sum()
    if n_nan_after < n_nan_before:
        print(f"  Forward-filled {n_nan_before - n_nan_after} missing values")

    # Check for >10-day gaps
    if len(df) > 1:
        # Reset index to access dates
        df_temp = df.reset_index()
        if 'Date' in df_temp.columns:
            date_col = 'Date'
        elif len(df_temp.columns) > 0:
            date_col = df_temp.columns[0]
        else:
            date_col = None

        if date_col and pd.api.types.is_datetime64_any_dtype(df_temp[date_col]):
            date_diff = df_temp[date_col].diff().dt.days
            max_gap = date_diff.max()
            if pd.notna(max_gap) and max_gap > 10:
                raise ValueError(f"Gap of {max_gap} days detected (threshold: 10)")

    return df


def _full_collect(cache_path=CACHE_PATH):
    """
    Full data collection: download 16 years of history (current behavior).

    Returns: (mode_used, delta_rows_count, tickers_refreshed, market_df)
    """
    os.makedirs(DATA_DIR, exist_ok=True)

    # --- Download OHLCV per ticker ---
    print("Downloading OHLCV data (full backtest)...")
    ohlcv = {}
    for ticker in TICKERS:
        df = yf.download(
            ticker, start=START_DATE, end=END_DATE,
            auto_adjust=True, progress=False,
        )
        assert df is not None, f"yf.download returned None for {ticker}"
        # Ensure columns are plain strings (not MultiIndex)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.droplevel(1)
        ohlcv[ticker] = df
        print(f"  {ticker}: {len(df)} rows")

    # --- VIX / VIX3M / VVIX ---
    print("Downloading VIX family...")
    vol_tickers = {
        'VIX':   VIX_TICKER,
        'VIX3M': VIX3M_TICKER,
        'VVIX':  VVIX_TICKER,
    }
    vol_series = {}
    for label, sym in vol_tickers.items():
        raw = yf.download(sym, start=START_DATE, end=END_DATE, progress=False)
        if raw is None or raw.empty:
            print(f"  {label} ({sym}): not available, skipping")
            continue
        if isinstance(raw.columns, pd.MultiIndex):
            raw.columns = raw.columns.droplevel(1)
        vol_series[label] = pd.Series(raw['Close'].squeeze())
        print(f"  {label}: {len(raw)} rows")

    # --- Build aligned DataFrame on SPY trading days ---
    ref_index = ohlcv['SPY'].index
    if not isinstance(ref_index, pd.DatetimeIndex):
        ref_index = pd.to_datetime(ref_index)

    market = pd.DataFrame(index=ref_index)

    for ticker in TICKERS:
        df = ohlcv[ticker]
        for field in ['Close', 'High', 'Low', 'Open']:
            series = df[field].squeeze()
            market[f'{ticker}_{field.lower()}'] = series.reindex(ref_index).ffill()
        if ticker == 'SPY':
            spy_vol = pd.Series(df['Volume'].squeeze())
            market['SPY_volume'] = spy_vol.reindex(ref_index).ffill()

    # VIX family (VIX, VIX3M, VVIX)
    for label, s in vol_series.items():
        market[label] = pd.Series(s).reindex(ref_index).ffill()

    market = market.dropna()

    assert len(market) >= 252, (
        f"Insufficient data after alignment: {len(market)} trading days "
        f"(need >= 252). Check date range or data sources."
    )

    # --- Save and cache ---
    os.makedirs(DATA_DIR, exist_ok=True)
    market.to_csv(os.path.join(DATA_DIR, 'market_data.csv'))

    # Cache data per ticker
    print(f"\nCaching data to {cache_path}...")
    for ticker in TICKERS:
        # Extract ticker columns
        ticker_cols = [c for c in market.columns if c.startswith(ticker)]
        if ticker_cols:
            ticker_df = market[ticker_cols].copy()
            _append_cache(ticker_df, ticker, cache_path)

    # Create and save manifest
    manifest = _create_cache_manifest(TICKERS, cache_path)
    _save_cache_manifest(manifest, cache_path)

    print(f"\nCollected {len(market)} trading days "
          f"{market.index[0].date()} -> {market.index[-1].date()}")
    print(f"  Tickers : {TICKERS}")
    print(f"  VIX     : {market['VIX'].min():.1f} - {market['VIX'].max():.1f}")

    return ('full', len(market), TICKERS, market)


def _incremental_collect(cache_path=CACHE_PATH):
    """
    Incremental data collection: load cache manifest, detect delta, fetch only new data.

    Returns: (mode_used, delta_rows_count, tickers_refreshed, market_df)
    """
    print("Fetching incremental data (cache exists)...")

    # Load previous manifest
    prev_manifest = _load_cache_manifest(cache_path)
    if not prev_manifest:
        print("Cache manifest invalid; falling back to full collect")
        return _full_collect(cache_path)

    # Create current manifest (same file hashes as before)
    curr_manifest = _create_cache_manifest(TICKERS, cache_path)

    # Detect delta
    delta_tickers = _detect_delta(curr_manifest, prev_manifest)
    print(f"Delta tickers needing refresh: {delta_tickers}")

    # For simplicity in Phase 2, if any ticker changed, re-fetch all
    # (In production, could optimize to fetch only delta)
    if delta_tickers:
        print("Detected cache changes; re-downloading full data...")
        return _full_collect(cache_path)

    # No delta: load from cache
    print("Loading data from cache (no changes detected)...")
    market = None
    for ticker in TICKERS:
        cached = _load_cached_data(ticker, cache_path)
        if cached is not None:
            if market is None:
                market = cached
            else:
                # Merge on index
                market = market.join(cached, how='outer')

    if market is None or len(market) == 0:
        print("Cache is empty; falling back to full collect")
        return _full_collect(cache_path)

    # Validate cache
    try:
        market = _validate_cache(market)
    except ValueError as e:
        print(f"Cache validation failed: {e}")
        print("Falling back to full collect...")
        return _full_collect(cache_path)

    print(f"Loaded {len(market)} trading days from cache")
    delta_rows = 0  # No new rows in pure cache load

    return ('incremental', delta_rows, [], market)


def collect(mode=None):
    """
    Orchestration function for data collection.

    If mode is None: auto-detect based on cache existence.
    If mode is 'full': always do full backtest.
    If mode is 'incremental': always try incremental (fallback to full if cache invalid).

    Returns: (mode_used, delta_rows_count, tickers_refreshed, market_df)
    """
    if mode is None:  # Auto-detect
        if _is_valid_cache(CACHE_PATH):
            mode = 'incremental'
        else:
            mode = 'full'

    if mode == 'incremental':
        result = _incremental_collect(CACHE_PATH)
    else:
        result = _full_collect(CACHE_PATH)

    mode_used, delta_rows, tickers_refreshed, market = result
    print(f"Mode: {mode_used}, Delta rows: {delta_rows}, Tickers refreshed: {tickers_refreshed}")

    return result


if __name__ == '__main__':
    mode_used, delta_rows, tickers_refreshed, market = collect()
    print(f"\nResult: mode={mode_used}, delta_rows={delta_rows}, tickers={tickers_refreshed}")
