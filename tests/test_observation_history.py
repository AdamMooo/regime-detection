"""The point-in-time history must stay append-only, contract-valid and causal.

`results/<signal>_level0.json` says what we believe now. The history says what we
believed at every past publication vintage, and it is the only artifact that lets a
consumer filter on `available_at`. A history that can be silently edited, or that
drifts from the descriptor it claims to serialize, answers nothing — so each test
below pins one property the log would be worthless without.
"""

import hashlib
import json
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import observation_history as oh  # noqa: E402
from signal_output_schema import validate  # noqa: E402

SIGNALS = sorted(oh.EMITTERS)


def _log(signal):
    return oh.read_log(oh.log_path(signal))


@pytest.mark.parametrize("signal", SIGNALS)
def test_history_exists_and_is_non_empty(signal):
    # A history that silently collects nothing would make every test below vacuous.
    assert _log(signal), f"{signal}: no history — run scripts/observation_history.py"


@pytest.mark.parametrize("signal", SIGNALS)
def test_every_record_satisfies_the_contract(signal):
    for i, record in enumerate(_log(signal), 1):
        try:
            validate(record)
        except ValueError as exc:
            pytest.fail(f"{signal}:{i} violates the observation contract: {exc}")


@pytest.mark.parametrize("signal", SIGNALS)
def test_check_reports_clean(signal):
    assert oh.check(signal) == []


@pytest.mark.parametrize("signal", SIGNALS)
def test_no_duplicate_observation_keys(signal):
    keys = [oh.key_of(r) for r in _log(signal)]
    assert len(keys) == len(set(keys)), f"{signal}: repeated (as_of, available_at)"


@pytest.mark.parametrize("signal", SIGNALS)
def test_available_at_is_non_decreasing(signal):
    """Append-only means the log reads in publication order.

    Out-of-order `available_at` is the signature of a log that was rewritten or
    merged rather than appended to.
    """
    avail = [r["available_at"] for r in _log(signal)]
    assert avail == sorted(avail)


@pytest.mark.parametrize("signal", SIGNALS)
def test_each_line_hashes_to_its_manifest_row(signal):
    """`sha256(line)` must equal the manifest hash and the hash `supersedes` cites.

    This only holds because lines are written as canonical JSON. If a future edit
    pretty-prints the log, the hash stops being verifiable from the bytes on disk and
    a correction can no longer point at anything.
    """
    path = oh.log_path(signal)
    lines = [l for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]
    manifest = pd.read_csv(path.parent / "MANIFEST.csv")
    assert len(lines) == len(manifest)

    for line, row in zip(lines, manifest.itertuples()):
        assert hashlib.sha256(line.encode("utf-8")).hexdigest() == row.sha256
        assert oh.record_sha256(json.loads(line)) == row.sha256


@pytest.mark.parametrize("signal", SIGNALS)
def test_latest_record_matches_the_published_snapshot(signal):
    """The newest history row and `results/<signal>_level0.json` are one observation.

    Two artifacts describing the same reading is exactly how the stale
    `vol_descriptors.csv` defect happened — an artifact that disagreed with the code
    claiming to produce it. Tie them together instead of trusting them to agree.
    """
    published = json.loads(oh.EMITTERS[signal].OUT.read_text(encoding="utf-8"))
    assert oh.record_sha256(_log(signal)[-1]) == oh.record_sha256(published)


@pytest.mark.parametrize("signal", SIGNALS)
def test_reading_and_rarity_match_the_committed_descriptor(signal):
    """The serialization must not perturb the numbers it serializes.

    Each historical record is built from `df.loc[:as_of]`, so its reading has to equal
    the committed descriptor's value AT that date. Causality itself is guaranteed
    upstream — `test_causal.py` runs `assert_causal` over `vol_descriptors.build` and
    `stockbond_corr.build` — and this test is what carries that guarantee through the
    slice: if slicing changed a value, the expanding statistics were not causal after
    all and every historical record would be quietly wrong.
    """
    module = oh.EMITTERS[signal]
    df = module.load_history()
    for record in _log(signal):
        row = df.loc[pd.Timestamp(record["as_of"])]
        assert record["reading"]["value"] == pytest.approx(
            round(float(row[COLUMNS[signal][0]]), 4)
        )
        assert record["rarity"]["level_percentile"] == pytest.approx(
            round(float(row[COLUMNS[signal][1]]), 4)
        )


COLUMNS = {
    "volatility": ("vol_annual", "vol_pctile"),
    "stock_bond_correlation": ("corr", "level_pctile"),
}


@pytest.mark.parametrize("signal", SIGNALS)
def test_historical_context_is_as_of_date_not_full_sample(signal):
    """`share_of_history` must be computed over history TO DATE.

    If it were a full-sample figure, every record would carry the same value — and a
    1930 record would be reporting how often volatility has been extreme including
    2008 and 2020. That is the leak this whole design exists to prevent, and it is
    invisible in a single snapshot: you can only see it across records.
    """
    shares = [r["extreme_conditions"]["share_of_history"] for r in _log(signal)]
    assert len(set(shares)) > 1, "identical across all records — looks full-sample"


@pytest.mark.parametrize("signal", SIGNALS)
def test_rebuilding_reproduces_the_log_exactly(signal):
    """The log is reproducible from the committed descriptor, hash for hash.

    Also proves the writer is idempotent: a second run appends nothing, which is what
    makes "append-only" safe to run on a schedule.
    """
    rebuilt = {oh.key_of(r): oh.record_sha256(r) for r in oh.build_records(signal)}
    logged = {oh.key_of(r): oh.record_sha256(r) for r in _log(signal)}
    assert rebuilt == logged


def test_append_refuses_to_rewrite_an_existing_observation(tmp_path):
    """The guarantee the log exists for: same key + different content is REFUSED.

    Without this, a routine re-run after a descriptor refresh would silently restate
    history — the exact failure mode the EBP's monthly full-sample refit shows in the
    wild, where today's print for March 2008 embeds coefficients fitted through 2026.
    A correction has to be a NEW record with a later `available_at` and a
    `supersedes` hash, so this must raise rather than overwrite.
    """
    path = tmp_path / "history.ndjson"
    record = _log(SIGNALS[0])[-1]
    oh.append(path, [record], oh.RECONSTRUCTED)
    assert len(oh.read_log(path)) == 1

    oh.append(path, [record], oh.RECONSTRUCTED)  # identical: a no-op, not an error
    assert len(oh.read_log(path)) == 1

    # Mutate a numeric leaf, not `maturity` — a signal already tagged `research`
    # would make that a no-op and the test would pass without testing anything.
    restated = dict(record, reading=dict(record["reading"], value=-99.0))
    assert oh.record_sha256(restated) != oh.record_sha256(record)
    with pytest.raises(RuntimeError, match="append-only"):
        oh.append(path, [restated], oh.RECONSTRUCTED)


def test_a_correction_is_appendable_as_a_new_record(tmp_path):
    """The correction path the plan's `<as_of>.json` layout could not express.

    Same `as_of`, later `available_at`, `supersedes` naming the superseded hash — two
    rows, both readable, so "what did we believe on date X as of time T?" still has a
    different answer before and after the correction.
    """
    path = tmp_path / "history.ndjson"
    original = _log(SIGNALS[0])[-1]
    oh.append(path, [original], oh.RECONSTRUCTED)

    correction = dict(
        original,
        available_at="2099-01-15T14:00:00Z",
        supersedes=oh.record_sha256(original),
    )
    oh.append(path, [correction], oh.LIVE)

    log = oh.read_log(path)
    assert len(log) == 2
    assert log[0]["as_of"] == log[1]["as_of"]
    assert log[1]["supersedes"] == oh.record_sha256(log[0])


def test_nan_is_refused_rather_than_written_as_invalid_json(tmp_path):
    """NaN serializes as bare `NaN`, which no strict JSON parser accepts.

    A consumer in another language would simply fail to read the log. This is a real
    defect that was live in both emitters: `trend.level_percentile_change` was NaN
    during burn-in, so the earliest records of both histories were unparseable.
    """
    bad = dict(_log(SIGNALS[0])[-1])
    bad["trend"] = dict(bad["trend"], level_percentile_change=float("nan"))
    with pytest.raises(ValueError):
        oh.canonical_bytes(bad)


def test_every_published_signal_has_a_history():
    """Globbed, not listed: a new signal cannot skip point-in-time history.

    Same structural enforcement as the boundary audit and the causal-guard registry —
    the alternative is remembering, which is what D-18 rejects.
    """
    published = {p.name for p in (ROOT / "results").glob("*_level0.json")}
    assert published, "no Level-0 records found"

    covered = {oh.EMITTERS[s].OUT.name for s in SIGNALS}
    missing = published - covered
    assert not missing, (
        f"signal(s) publish a Level-0 record but have no observation history: "
        f"{sorted(missing)} — add them to observation_history.EMITTERS"
    )
