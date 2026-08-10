"""Harvest archived vintages of the published EBP — the evidence base for Phase 6's V2.

The excess bond premium is a regression RESIDUAL refit monthly on the full sample, so
the Board states outright that "the entire history of the EBP may revise each month"
(FEDS Notes 2016-10-06). The number printed today for March 2008 embeds coefficients
estimated through today. `assert_causal` cannot see this at all: the code is causal,
the DATA is not.

There are no ALFRED vintages — the EBP is a FEDS-Notes CSV, not a FRED series — so the
only way to measure how much the history moves is to collect what the file said at
past moments. The Internet Archive has captures back to 2022-08.

WHY THIS RUNS BEFORE THE CHARTER IS SIGNED
    Harvesting is data acquisition, not a look: it assembles the evidence V2 will be
    run against and its outcome does not depend on the phase proceeding. The charter's
    open item 4 recommends it explicitly and independently, for one reason — Archive
    coverage is not guaranteed to persist, so waiting has an irreversible cost that
    waiting on everything else in this phase does not.

WHAT THIS SCRIPT DELIBERATELY DOES NOT DO
    It computes NO comparison between vintages. Not a revision magnitude, not a rank
    correlation, not a decile-agreement rate — those three ARE V2 (bars A, B and C),
    and V2 is a one-look that runs once, after sign-off, from a frozen script. This
    script fetches bytes and records structural coverage (rows, date span, checksum),
    which is the same coverage inspection the charter already performed pre-look.
    Adding "just a quick look at how much it moved" here would spend the look and
    there would be no way to unspend it.

Run:  python scripts/harvest_ebp_vintages.py            # fetch new captures
      python scripts/harvest_ebp_vintages.py --list     # show what the Archive has
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import sys
import time
import urllib.parse
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "vintages" / "ebp"
MANIFEST = OUT / "MANIFEST.csv"

TARGET = "federalreserve.gov/econres/notes/feds-notes/ebp_csv.csv"
CDX = "https://web.archive.org/cdx/search/cdx"

# `id_` asks the Wayback Machine for the ORIGINAL bytes, with no rewriting or banner
# injection. Without it the payload is a wrapped HTML page and the checksum would be
# a property of the Archive's presentation layer rather than of the Fed's file.
WAYBACK = "https://web.archive.org/web/{timestamp}id_/https://www.{target}"

COURTESY_SLEEP = 1.5  # a free service; don't hammer it

MANIFEST_COLUMNS = [
    "captured_at", "wayback_timestamp", "sha256",
    "rows", "dateless_rows", "first_obs", "last_obs", "columns",
]


def captures() -> list[dict]:
    """Successful captures of the EBP file, one row per distinct archived digest.

    `collapse=digest` only collapses ADJACENT duplicates, so the same content can
    still appear at two timestamps; dedupe by digest here and keep the earliest, which
    is the moment that content was first observably published.
    """
    query = urllib.parse.urlencode({
        "url": TARGET,
        "output": "json",
        "fl": "timestamp,statuscode,digest,length",
        "collapse": "digest",
        "filter": "statuscode:200",
    })
    rows = requests.get(f"{CDX}?{query}", timeout=90).json()
    header, body = rows[0], rows[1:]

    first_by_digest: dict[str, dict] = {}
    for row in body:
        rec = dict(zip(header, row))
        first_by_digest.setdefault(rec["digest"], rec)
    return sorted(first_by_digest.values(), key=lambda r: r["timestamp"])


def _iso(timestamp: str) -> str:
    """Wayback's 14-digit UTC stamp -> ISO-8601, the form the contract uses."""
    return (
        f"{timestamp[0:4]}-{timestamp[4:6]}-{timestamp[6:8]}"
        f"T{timestamp[8:10]}:{timestamp[10:12]}:{timestamp[12:14]}Z"
    )


def _coverage(payload: bytes) -> dict:
    """Structural description of one vintage. No values compared — see the docstring.

    `errors="coerce"` and the explicit `dateless_rows` count exist because a real
    capture needed them: the 2025-06-12 vintage ends with a bare `,,,` line. Silently
    parsing that to NaT put a NaT in `last_obs` and would put a NaT-indexed all-NaN
    row into any panel built from it — `build_credit.py:41` calls `pd.to_datetime`
    with no guard, so it would not raise. Counting the rows the vendor shipped
    without a date makes the anomaly a recorded property of the vintage instead of a
    surprise in whatever consumes it.
    """
    frame = pd.read_csv(io.StringIO(payload.decode("utf-8-sig")))
    frame.columns = [c.strip().lower() for c in frame.columns]
    datecol = next(c for c in frame.columns if "date" in c)
    dates = pd.to_datetime(frame[datecol], errors="coerce")
    valid = dates.dropna().sort_values()
    return {
        "rows": len(frame),
        "dateless_rows": int(dates.isna().sum()),
        "first_obs": valid.iloc[0].date().isoformat(),
        "last_obs": valid.iloc[-1].date().isoformat(),
        "columns": "|".join(frame.columns),
    }


def harvest(retries: int = 3) -> pd.DataFrame:
    """Fetch any capture not already on disk, then rebuild the manifest from disk.

    The manifest is DERIVED from the stored files, never accumulated across runs —
    same discipline as `data_manifest.py`. That way a manifest schema change needs no
    re-download, and a manifest that disagrees with the files on disk cannot survive a
    run. The vintage CSVs are the durable artifact; Internet Archive coverage is not
    guaranteed to persist, so once fetched they are committed and never re-fetched.
    """
    OUT.mkdir(parents=True, exist_ok=True)
    fetched = 0

    for cap in captures():
        stamp = cap["timestamp"]
        path = OUT / f"{stamp}.csv"
        if path.exists():
            continue

        url = WAYBACK.format(timestamp=stamp, target=TARGET)
        for attempt in range(1, retries + 1):
            try:
                payload = requests.get(url, timeout=120).content
                coverage = _coverage(payload)
            except Exception as exc:
                if attempt == retries:
                    # A capture can be listed in the index yet not served. Report it
                    # rather than swallowing it: a missing vintage is missing evidence.
                    print(f"  {_iso(stamp)}  UNAVAILABLE after {retries} tries — "
                          f"{type(exc).__name__}: {str(exc)[:60]}")
                else:
                    time.sleep(COURTESY_SLEEP * 2 * attempt)
                continue

            path.write_bytes(payload)
            fetched += 1
            print(f"  {_iso(stamp)}  {coverage['rows']:4d} rows  "
                  f"{coverage['first_obs']}..{coverage['last_obs']}  -> {path.name}")
            break
        time.sleep(COURTESY_SLEEP)

    manifest = build_manifest()
    print(f"\nfetched {fetched} new; {len(manifest)} vintages on disk -> {MANIFEST.relative_to(ROOT)}")
    return manifest


def build_manifest() -> pd.DataFrame:
    """Regenerate MANIFEST.csv from the vintage files present on disk."""
    rows = []
    for path in sorted(OUT.glob("*.csv")):
        if path.name == MANIFEST.name:
            continue
        payload = path.read_bytes()
        rows.append({
            "captured_at": _iso(path.stem),
            "wayback_timestamp": path.stem,
            "sha256": hashlib.sha256(payload).hexdigest(),
            **_coverage(payload),
        })
    manifest = pd.DataFrame(rows, columns=MANIFEST_COLUMNS).sort_values("wayback_timestamp")
    manifest.to_csv(MANIFEST, index=False)
    return manifest


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--list", action="store_true", help="show Archive coverage, fetch nothing")
    ap.add_argument(
        "--rebuild-manifest", action="store_true",
        help="regenerate MANIFEST.csv from the vintages already on disk; no network",
    )
    args = ap.parse_args()

    if args.rebuild_manifest:
        manifest = build_manifest()
        print(f"{len(manifest)} vintages -> {MANIFEST.relative_to(ROOT)}")
        print(manifest[["captured_at", "rows", "dateless_rows", "last_obs"]].to_string(index=False))
        return 0

    if args.list:
        caps = captures()
        print(f"{len(caps)} distinct archived vintages of {TARGET}")
        for cap in caps:
            print(f"  {_iso(cap['timestamp'])}  digest={cap['digest']}  {cap['length']:>7} bytes")
        return 0

    manifest = harvest()
    if manifest.empty:
        print("no vintages harvested")
        return 1

    # Coverage summary only. The pre-2022 history is unreachable at any price without
    # paid bond-level and balance-sheet data, which is why the phase's maturity is
    # capped at `research` however V2 reads.
    print(
        f"span {manifest['captured_at'].iloc[0][:10]} .. {manifest['captured_at'].iloc[-1][:10]}  "
        f"| observation months per vintage {manifest['rows'].min()}..{manifest['rows'].max()}"
    )
    print("NOT computed here, by design: any revision magnitude or rank agreement — that is V2.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
