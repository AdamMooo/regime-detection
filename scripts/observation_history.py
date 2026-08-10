"""Append-only point-in-time observation history (IMPLEMENTATION-PLAN.md §5.4).

Answers the one question a `results/<signal>_level0.json` snapshot cannot: *what did
we believe on date X, as of time T?* Without it, no consumer can honestly filter on
`available_at`, so nothing built on these signals is point-in-time no matter how
causal the estimator is.

FORM — a deviation from the plan's §5.4 sketch, disclosed rather than absorbed
------------------------------------------------------------------------------
The plan specifies `observations/<signal>/<as_of>.json`, one file per observation
date. Two problems, both found while implementing it:

1. **It cannot express its own correction model.** §5.4 says a correction is "a new
   record with a later `available_at`" for the same observation — but a path keyed on
   `as_of` alone holds exactly one record, so the first correction must either
   overwrite (destroying the append-only guarantee it states in the same paragraph)
   or have nowhere to go.

2. **Daily granularity is redundant, 22× over.** Volatility has 25,938 `as_of` dates
   but only 1,187 distinct `available_at` vintages, because Ken French publishes
   monthly. A consumer's only legitimate filter is `available_at <= T`, and records
   sharing an `available_at` are indistinguishable under it.

So: one NDJSON log per signal, one record per line, append-only in the literal sense
— a correction appends a line carrying `supersedes`, and no byte of history is ever
rewritten. Emission is on the VINTAGE grid: the freshest `as_of` per publication
instant, which is exactly what a consumer standing at that instant could have read.

Each line is canonical JSON (sorted keys, tight separators), so `sha256(line)` equals
the record hash in `MANIFEST.csv` and the hash `supersedes` points at. The manifest is
a regenerated index of the log, not the durable artifact — the log is.

RECONSTRUCTION, NOT A CONTEMPORANEOUS PRINT — read this before backtesting
-------------------------------------------------------------------------
Nobody was running this pipeline in 1927. Every backfilled record answers a
counterfactual: *if this signal, as specified and signed off today, had been running
from the start, what would it have read at each publication vintage?*

The split matters enough that the manifest carries it per row as `provenance`:

- **Causal, honestly point-in-time — every DATA-derived number.** Each record is
  built by the live `build_record()` on `df.loc[:as_of]`, so one code path produces
  both the history and the live reading, and no future observation is ever in scope.
- **NOT point-in-time — the SPECIFICATION.** The estimator, the assessment axes, the
  `maturity` tag, the calibration prose. A 1930 record carries a maturity derived
  from a 2026-08-06 sign-off.

The second half is unavoidable — it is true of any backtest of a signal designed
today — but it has to be stated rather than implied, because a consumer reading
`maturity: production` on a 1930 row would otherwise believe it was earned in 1930.

Run:  python scripts/observation_history.py            # backfill / extend
      python scripts/observation_history.py --check    # verify, write nothing
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import stockbond_level0
import vol_level0
from data_vintage import available_at
from signal_output_schema import validate

OBS = ROOT / "observations"

MANIFEST_COLUMNS = ["as_of", "available_at", "sha256", "spec_version", "provenance"]

RECONSTRUCTED = "reconstructed"
LIVE = "live"

# Signal name -> the emitter module that owns its record shape. Each must expose
# `load_history()`, `build_record(df)` and `SOURCE`; a new signal joins by adding a
# row here, and `tests/test_observation_history.py` asserts every emitted Level-0
# record has a history, so a signal cannot quietly skip this.
EMITTERS = {
    "volatility": vol_level0,
    "stock_bond_correlation": stockbond_level0,
}


def canonical_bytes(record: dict) -> bytes:
    """The byte form every hash is taken over.

    Sorted keys and tight separators make the hash a property of the record's
    CONTENT rather than of how `json.dumps` happened to format it — `supersedes`
    points at one of these, so it has to be stable across runs and machines.

    `allow_nan=False` is load-bearing: NaN serializes as bare `NaN`, which is invalid
    strict JSON that a non-Python consumer cannot parse. Better a loud failure here
    than a log that only this repo can read.
    """
    return json.dumps(
        record, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")


def record_sha256(record: dict) -> str:
    return hashlib.sha256(canonical_bytes(record)).hexdigest()


def key_of(record: dict) -> tuple[str, str]:
    return record["as_of"], record["available_at"]


def vintage_grid(index: pd.DatetimeIndex, source: str) -> list[pd.Timestamp]:
    """The freshest `as_of` per distinct publication instant.

    Two records sharing an `available_at` are indistinguishable to a consumer
    filtering on it, so the grid keeps the one that consumer would actually read:
    the latest. Built from the whole index, including rows the descriptor left NaN —
    availability is a property of the source's calendar, not of whether we happened
    to compute a value.
    """
    latest: dict[str, pd.Timestamp] = {}
    for ts in index:  # ascending, so a later as_of overwrites its vintage-mates
        latest[vintage_of(ts, source)] = ts
    return sorted(latest.values())


def vintage_of(ts: pd.Timestamp, source: str) -> str:
    return available_at(ts.date().isoformat(), source)


def build_records(signal: str) -> list[dict]:
    """Every distinct observation this signal's committed history supports.

    Each is built from a strictly backward-looking slice, then schema-validated
    before it can reach the log — an invalid record is never written and then fixed.
    """
    module = EMITTERS[signal]
    df = module.load_history()
    records: dict[tuple[str, str], dict] = {}
    started = False

    for ts in vintage_grid(df.index, module.SOURCE):
        try:
            record = module.build_record(df.loc[:ts])
        except (IndexError, KeyError, ValueError) as exc:
            # Leading burn-in: no valid reading exists yet, so there is nothing to
            # record. Once history HAS started, the same failure is a real defect
            # and must not be swallowed as more burn-in.
            if started:
                raise RuntimeError(
                    f"{signal}: build_record failed at vintage {ts.date()} after "
                    f"history had already started — this is not burn-in"
                ) from exc
            continue

        started = True
        if record["signal"] != signal:
            raise RuntimeError(
                f"{signal}: emitter produced signal={record['signal']!r}"
            )
        validate(record)
        # A vintage whose slice adds no new valid row resolves to the same
        # (as_of, available_at) as its predecessor and collapses onto it — correct:
        # nothing new became available.
        records[key_of(record)] = record

    return [records[k] for k in sorted(records)]


def read_log(path: Path) -> list[dict]:
    if not path.exists():
        return []
    out = []
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"{path.name}:{lineno} is not valid JSON") from exc
    return out


def append(path: Path, candidates: list[dict], provenance: str) -> list[dict]:
    """Append records the log does not already carry. Never rewrites a line.

    The integrity rule: a record whose `(as_of, available_at)` is already present but
    whose content hash DIFFERS is refused. That situation is a correction, and a
    correction is a new record with a LATER `available_at` plus a `supersedes` hash —
    never a silent substitution at the same instant. Refusing it is the whole value
    of the log; a history that can be quietly edited answers no question about what
    was believed when.
    """
    existing = {key_of(r): record_sha256(r) for r in read_log(path)}
    to_add, conflicts = [], []

    for record in candidates:
        key, sha = key_of(record), record_sha256(record)
        if key in existing:
            if existing[key] != sha:
                conflicts.append(key)
            continue
        to_add.append(record)

    if conflicts:
        listed = ", ".join(f"{a} @ {v}" for a, v in conflicts[:5])
        raise RuntimeError(
            f"{path.name}: {len(conflicts)} record(s) already logged at the same "
            f"(as_of, available_at) with DIFFERENT content: {listed}. History is "
            f"append-only. If the reading genuinely changed, emit a correction — a "
            f"new record with a later available_at and `supersedes` set to the "
            f"superseded record's sha256 — do not rewrite this log."
        )

    path.parent.mkdir(parents=True, exist_ok=True)
    # Append in `available_at` order so the log always reads in the order knowledge
    # arrived. A correction discovered today therefore lands after a routine record for
    # a later as_of that was publishable weeks ago — which is correct, and is why
    # "newest line" is not the same question as "current belief" (see `current_view`).
    with path.open("a", encoding="utf-8", newline="\n") as fh:
        for record in sorted(to_add, key=lambda r: (r["available_at"], r["as_of"])):
            fh.write(canonical_bytes(record).decode("utf-8") + "\n")

    _write_manifest(path.parent / "MANIFEST.csv", path, {key_of(r) for r in to_add}, provenance)
    return to_add


def _write_manifest(manifest: Path, log: Path, new_keys: set, provenance: str) -> None:
    """Regenerate the index of the log, preserving provenance already recorded.

    Derived, so regenerating it is safe — unlike the log, which is append-only.
    """
    known = {}
    if manifest.exists():
        prior = pd.read_csv(manifest)
        if "provenance" in prior.columns:
            known = {
                (r.as_of, r.available_at): r.provenance
                for r in prior.itertuples()
            }

    rows = []
    for record in read_log(log):
        key = key_of(record)
        rows.append({
            "as_of": key[0],
            "available_at": key[1],
            "sha256": record_sha256(record),
            "spec_version": record["spec_version"],
            "provenance": provenance if key in new_keys else known.get(key, RECONSTRUCTED),
        })
    pd.DataFrame(rows, columns=MANIFEST_COLUMNS).to_csv(manifest, index=False)


def log_path(signal: str) -> Path:
    return OBS / signal / "history.ndjson"


def current_view(records: list[dict]) -> list[dict]:
    """What we believe NOW: the latest `available_at` per `as_of`, ascending by `as_of`.

    This is the query a consumer actually wants, and the reason the log keeps superseded
    records instead of editing them — "what did we believe on date X, as of time T?" needs
    both the original and the correction to still be there. Filter to
    `available_at <= T` first to ask it as of a past instant.
    """
    latest: dict[str, dict] = {}
    for record in records:
        prior = latest.get(record["as_of"])
        if prior is None or record["available_at"] >= prior["available_at"]:
            latest[record["as_of"]] = record
    return [latest[k] for k in sorted(latest)]


def corrections_for(signal: str, now_iso: str) -> list[dict]:
    """Records whose content changed for an `(as_of, available_at)` already logged.

    A restatement is not an error and not something to overwrite. The source moved — the
    vendor revised, or a downstream input was back-adjusted — so the honest record is a
    NEW row carrying the new value, stamped with when we could first have known it, and
    pointing at the hash of what it replaces.

    `available_at` is the moment of REDISCOVERY (now), not the original publication
    instant: nobody could have held the corrected value before we recomputed it. Using
    the original `available_at` would both collide with the logged row and backdate
    knowledge, which is the look-ahead this whole contract exists to prevent.

    Compared against the CURRENT VIEW, not against the original row. Comparing against
    the original would re-emit the same correction on every run forever: the original
    keeps its old content by design, so it never stops differing. The question is
    "does what we believe now already match the data?", and only `current_view` answers
    it. Comparison ignores `available_at` and `supersedes`, since a correction differs in
    exactly those two fields and nothing else.
    """
    log = read_log(log_path(signal))
    current = {r["as_of"]: r for r in current_view(log)}
    out = []
    for record in build_records(signal):
        prior = current.get(record["as_of"])
        if prior is None or _payload_sha256(prior) == _payload_sha256(record):
            continue
        out.append(dict(record, available_at=now_iso, supersedes=record_sha256(prior)))
    return out


def _payload_sha256(record: dict) -> str:
    """Hash of a record's SUBSTANCE — everything except when we learned it."""
    return hashlib.sha256(
        canonical_bytes({k: v for k, v in record.items()
                         if k not in ("available_at", "supersedes")})
    ).hexdigest()


def check(signal: str) -> list[str]:
    """Verify a log without writing. Returns problems; empty means clean."""
    path = log_path(signal)
    problems = []
    if not path.exists():
        return [f"{signal}: no history.ndjson — run scripts/observation_history.py"]

    records = read_log(path)
    seen = {}
    for i, record in enumerate(records, 1):
        try:
            validate(record)
        except ValueError as exc:
            problems.append(f"{signal}:{i} fails the contract: {exc}")
        key = key_of(record)
        if key in seen:
            # Legal only as an explicit correction, which needs a later
            # available_at — so a repeat of the SAME key is always wrong.
            problems.append(f"{signal}:{i} duplicates {key} first seen at line {seen[key]}")
        seen[key] = i

    avail = [r["available_at"] for r in records]
    if avail != sorted(avail):
        problems.append(f"{signal}: available_at is not non-decreasing — log was reordered")

    manifest = path.parent / "MANIFEST.csv"
    if not manifest.exists():
        problems.append(f"{signal}: MANIFEST.csv missing")
    else:
        listed = pd.read_csv(manifest)
        if len(listed) != len(records):
            problems.append(
                f"{signal}: manifest has {len(listed)} rows, log has {len(records)}"
            )
        else:
            for row, record in zip(listed.itertuples(), records):
                if row.sha256 != record_sha256(record):
                    problems.append(f"{signal}: manifest sha256 mismatch at {row.as_of}")
                    break
    return problems


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--signal", choices=sorted(EMITTERS) + ["all"], default="all")
    ap.add_argument("--check", action="store_true", help="verify only, write nothing")
    ap.add_argument(
        "--provenance", choices=[RECONSTRUCTED, LIVE], default=RECONSTRUCTED,
        help="how newly-appended rows were obtained; backfill is 'reconstructed'",
    )
    ap.add_argument(
        "--emit-corrections", action="store_true",
        help="after a data refresh restates history: append corrections (new records with "
             "available_at=now and `supersedes` set) instead of refusing. Never rewrites.",
    )
    args = ap.parse_args()

    signals = sorted(EMITTERS) if args.signal == "all" else [args.signal]

    if args.check:
        problems = [p for s in signals for p in check(s)]
        for p in problems:
            print(f"FAIL  {p}")
        print("clean" if not problems else f"{len(problems)} problem(s)")
        return 1 if problems else 0

    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    for signal in signals:
        path = log_path(signal)
        candidates = build_records(signal)
        fixes = []
        if args.emit_corrections:
            fixes = corrections_for(signal, now_iso)
            # Drop candidates for as_ofs already in the log. An identical one is a no-op
            # anyway; a CHANGED one must enter as its correction, not as itself — leaving
            # it in would re-trigger the same-key conflict the corrections exist to
            # resolve, which is exactly what happened the first time this ran.
            logged_keys = {key_of(r) for r in read_log(path)}
            candidates = [r for r in candidates if key_of(r) not in logged_keys]
        added = append(path, candidates + fixes, args.provenance)
        n_fix = sum(1 for r in added if r.get("supersedes"))
        total = len(read_log(path))
        print(
            f"{signal:24s} +{len(added) - n_fix:4d} new  +{n_fix:3d} corrections  "
            f"({total} records)  {path.relative_to(ROOT)}"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
