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
    # Per-column first/last VALID date, not just the index span. A wide panel with
    # ragged starts (credit_daily: baa_10y from 1986, ig_oas/hy_oas only from 2023
    # because FRED serves a rolling ~3yr window of ICE BofA series) otherwise reads
    # as 40 years of every column. That exact misreading produced a false
    # "OAS proxies 1986+" claim in a phase kickoff.
    spans = []
    if dates is not None:
        for c in df.columns:
            if c == date_col:
                continue
            valid = dates[df[c].notna()]
            if valid.notna().any():
                spans.append(f"{c}:{valid.min().date()}..{valid.max().date()}")
            else:
                spans.append(f"{c}:EMPTY")

    return {
        "file": path.name,
        "sha256": sha256(path),
        "bytes": path.stat().st_size,
        "rows": len(df),
        "first": dates.min().date().isoformat() if dates is not None and dates.notna().any() else "",
        "last": dates.max().date().isoformat() if dates is not None and dates.notna().any() else "",
        "column_spans": ";".join(spans),
    }


def build_manifest() -> pd.DataFrame:
    # deliberately not named `build()` — that name is reserved for signal
    # constructions, which tests/test_reproducibility.py forces under assert_causal
    files = sorted(p for p in PROCESSED.glob("*.csv") if p.name != OUT.name)
    return pd.DataFrame([describe(p) for p in files])


def check() -> int:
    """Detect SILENT UPSTREAM REVISION: recompute hashes and diff against the
    committed manifest.

    Motivated by a real discovery (2026-08-06): Cboe's published SKEW all-time
    low/high were 101.09 / 146.88 in the 2011 white paper and are 101.31 / 146.22
    in today's file — same dates, different values. Vendors silently restate
    history, and `assert_causal` cannot see it because the leak is in the data,
    not the code.

    A hash change is NOT a failure — refreshing data legitimately changes it. It
    is a prompt: confirm the change is the refresh you intended and not a vendor
    rewriting the past underneath a frozen result.
    """
    if not OUT.exists():
        print("no committed manifest; run without --check first")
        return 1
    old = pd.read_csv(OUT).set_index("file")
    new = build_manifest().set_index("file")

    changed = [f for f in old.index.intersection(new.index)
               if old.loc[f, "sha256"] != new.loc[f, "sha256"]]
    gone = sorted(set(old.index) - set(new.index))
    added = sorted(set(new.index) - set(old.index))

    for f in changed:
        o, n = old.loc[f], new.loc[f]
        print(f"CHANGED  {f}  rows {o['rows']}->{n['rows']}  span {o['last']}->{n['last']}")
        if str(o["column_spans"]) != str(n["column_spans"]):
            print(f"         column spans moved:\n           was {o['column_spans']}\n           now {n['column_spans']}")
    for f in gone:
        print(f"MISSING  {f}  (in manifest, not on disk)")
    for f in added:
        print(f"NEW      {f}  (on disk, not in manifest)")

    if not (changed or gone or added):
        print(f"clean — all {len(new)} panels byte-identical to the committed manifest")
        return 0
    print("\nIf a span moved BACKWARDS or rows changed without a refresh, a vendor "
          "restated history under you. Investigate before trusting any frozen result built on it.")
    return 1


def main() -> int:
    if "--check" in sys.argv:
        return check()
    m = build_manifest()
    m.to_csv(OUT, index=False)
    print(f"{len(m)} panels -> {OUT.relative_to(ROOT)}")
    for _, r in m.iterrows():
        print(f"  {r['file']:28} {r['rows']:>7} rows  {r['first']} .. {r['last']}  {r['sha256'][:12]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
