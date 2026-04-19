"""Data collection tier.

FRED macro series collection (collect_macro.py) complements the yfinance OHLCV
collection in src/features/collect.py. Kept as a separate subpackage because
FRED is authenticated via env var and has different frequency-alignment rules.
"""
