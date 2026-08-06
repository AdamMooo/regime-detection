"""Content manifest for the processed data panels.

Results are only reproducible if you know exactly which data vintage produced
them. Ken French restates, FRED revises, SKEW gets rebased, and yfinance
back-adjusts — so "market_daily.csv" is not a stable identifier for a dataset.
This records the sha256, shape and date span of every processed panel so a
result can be tied to the bytes it was computed from.

The manifest is a RECORD, not a lock: refreshing data legitimately changes the
hashes. Regenerate it when data is refreshed and commit the change alongside,
so the diff shows exactly which panels moved.

Run:  python scripts/data_manifest.py
"""

import hashlib
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
OUT = PROCESSED / "MANIFEST.csv"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def describe(path: Path) -> dict:
    df = pd.read_csv(path)
    date_col = next((c for c in df.columns if str(c).lower() in ("date", "month", "week")), None)
    if date_col is None and df.columns[0].startswith("Unnamed"):
        date_col = df.columns[0]      # panels written with an unnamed date index
    dates = pd.to_datetime(df[date_col], errors="coerce") if date_col else None
    return {
        "file": path.name,
        "sha256": sha256(path),
        "bytes": path.stat().st_size,
        "rows": len(df),
        "columns": ";".join(df.columns),
        "first": dates.min().date().isoformat() if dates is not None and dates.notna().any() else "",
        "last": dates.max().date().isoformat() if dates is not None and dates.notna().any() else "",
    }


def build_manifest() -> pd.DataFrame:
    # deliberately not named `build()` — that name is reserved for signal
    # constructions, which tests/test_reproducibility.py forces under assert_causal
    files = sorted(p for p in PROCESSED.glob("*.csv") if p.name != OUT.name)
    return pd.DataFrame([describe(p) for p in files])


def main() -> int:
    m = build_manifest()
    m.to_csv(OUT, index=False)
    print(f"{len(m)} panels -> {OUT.relative_to(ROOT)}")
    for _, r in m.iterrows():
        print(f"  {r['file']:28} {r['rows']:>7} rows  {r['first']} .. {r['last']}  {r['sha256'][:12]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
