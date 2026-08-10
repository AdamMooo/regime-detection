"""The observation contract and the producer-side validator must not drift apart.

`contracts/market-observation-v1.schema.json` is canonical and language-neutral —
consumers vendor it with a sha256 check. `scripts/signal_output_schema.py` is the
producer-side validator this repo actually calls. Two implementations of one rule set is
duplication; the duplication is only safe if something proves they agree.

That is this file. Every vector in `contracts/vectors/` is run through BOTH, and both
must reach the same verdict. A rule added to one and forgotten in the other turns red
here rather than silently letting a bad record through one path.
"""

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from signal_output_schema import SPEC_VERSION, validate  # noqa: E402

jsonschema = pytest.importorskip("jsonschema")

CONTRACTS = ROOT / "contracts"
SCHEMA_PATH = CONTRACTS / "market-observation-v1.schema.json"
VALID_DIR = CONTRACTS / "vectors" / "valid"
INVALID_DIR = CONTRACTS / "vectors" / "invalid"


def _load(p: Path):
    return json.loads(p.read_text(encoding="utf-8"))


SCHEMA = _load(SCHEMA_PATH)
VALID = sorted(VALID_DIR.glob("*.json"))
INVALID = sorted(INVALID_DIR.glob("*.json"))


def _validator():
    cls = jsonschema.validators.validator_for(SCHEMA)
    cls.check_schema(SCHEMA)
    return cls(SCHEMA)


def test_schema_is_itself_valid_draft_2020_12():
    assert SCHEMA["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    _validator()  # raises SchemaError if the schema itself is malformed


def test_schema_declares_the_spec_version_the_producer_emits():
    assert SCHEMA["properties"]["spec_version"]["const"] == SPEC_VERSION


def test_vectors_exist():
    # A conformance suite that silently collects nothing is worse than none: it goes green.
    assert VALID, "no valid vectors found"
    assert INVALID, "no invalid vectors found"


@pytest.mark.parametrize("path", VALID, ids=lambda p: p.stem)
def test_valid_vector_passes_json_schema(path):
    _validator().validate(_load(path))


@pytest.mark.parametrize("path", VALID, ids=lambda p: p.stem)
def test_valid_vector_passes_producer_validator(path):
    validate(_load(path))


@pytest.mark.parametrize("path", INVALID, ids=lambda p: p.stem)
def test_invalid_vector_rejected_by_json_schema(path):
    payload = _load(path)
    assert payload["_violates"].strip(), f"{path.name} must state the rule it violates"
    with pytest.raises(jsonschema.ValidationError):
        _validator().validate(payload["record"])


@pytest.mark.parametrize("path", INVALID, ids=lambda p: p.stem)
def test_invalid_vector_rejected_by_producer_validator(path):
    with pytest.raises(ValueError):
        validate(_load(path)["record"])


# ---------------------------------------------------------------------------
# The rules that exist specifically to prevent leakage and boundary erosion.
# Asserted directly, not only via vectors, so deleting a vector cannot quietly
# delete the guarantee.
# ---------------------------------------------------------------------------


def test_full_sample_rarity_can_never_be_production():
    """A full-sample rank embeds the future distribution in today's reading.

    Ranking against the whole series means a 1990 percentile already knows about the
    2008 and 2020 volatility spikes, so it reads lower than anyone in 1990 could have
    computed. A rule conditioned on that percentile is conditioned on the future. It
    does not surface as an error — it surfaces as a better Sharpe.
    """
    rec = _load(VALID_DIR / "full-sample-research-is-legal.json")
    validate(rec)  # research is legal
    _validator().validate(rec)

    rec["maturity"] = "production"
    with pytest.raises(ValueError, match="full_sample"):
        validate(rec)
    with pytest.raises(jsonschema.ValidationError):
        _validator().validate(rec)


def test_window_is_null_unless_trailing_fixed():
    """`window` must not be readable as meaningful for an expanding rank."""
    rec = _load(VALID_DIR / "minimal-production.json")
    rec["rarity"]["window"] = 1260
    with pytest.raises(ValueError, match="window"):
        validate(rec)
    with pytest.raises(jsonschema.ValidationError):
        _validator().validate(rec)


def test_both_timestamps_required_and_neither_inferred():
    """available_at is not derivable from as_of, so dropping either is fatal.

    A backtest filters on available_at. Filtering on as_of for a published-with-lag
    series is the revised-macro-data look-ahead the charter forbids outright.
    """
    for field in ("as_of", "available_at"):
        rec = _load(VALID_DIR / "minimal-production.json")
        rec.pop(field)
        with pytest.raises(ValueError, match=field):
            validate(rec)
        with pytest.raises(jsonschema.ValidationError):
            _validator().validate(rec)


def test_renamed_decision_field_is_rejected_as_unknown():
    """The denylist alone is not the enforcement — the closed allowlist is.

    A producer could rename `allocation` to something benign and slip past a denylist.
    `additionalProperties: false` rejects it for being *unknown*, which is the rule that
    actually holds.
    """
    rec = _load(VALID_DIR / "minimal-production.json")
    rec["alpha_hint"] = 0.35
    with pytest.raises(ValueError):
        validate(rec)
    with pytest.raises(jsonschema.ValidationError):
        _validator().validate(rec)


EMITTED = sorted((ROOT / "results").glob("*_level0.json"))


@pytest.mark.parametrize("path", EMITTED, ids=lambda p: p.stem)
def test_emitted_record_satisfies_the_canonical_contract(path):
    """The records this repo actually publishes must satisfy the vendored contract.

    Globbed, not named: a new signal cannot skip the contract by not being listed.
    Passing the producer validator is not sufficient — consumers vendor the JSON Schema,
    so that is the artifact a real record has to satisfy.
    """
    _validator().validate(_load(path))


def test_emitted_records_exist():
    assert EMITTED, "no Level-0 records found — run scripts/<signal>_level0.py"


@pytest.mark.parametrize(
    "path",
    sorted((ROOT / "contracts").rglob("*.json")) + sorted((ROOT / "observations").rglob("*.ndjson")),
    ids=lambda p: str(p.relative_to(ROOT)).replace("\\", "/"),
)
def test_contract_artifacts_have_no_crlf(path):
    """Consumers vendor these by sha256, so their bytes must not vary by platform.

    `core.autocrlf` rewrites line endings on checkout, which changes the file hash —
    the same commit would present different sha256s on Windows and Linux, and every
    consumer's pinned-copy check would report contract drift that did not happen.
    `.gitattributes` pins `eol=lf` for both trees; this test is what notices if that
    pin is removed or a new artifact lands outside it.
    """
    assert b"\r\n" not in path.read_bytes(), (
        f"{path.name} contains CRLF — check .gitattributes covers it, then re-checkout"
    )


def test_maturity_is_the_only_behaviour_bearing_field():
    """Documented invariant, asserted so a future edit has to confront it.

    Consumers key behaviour off `maturity` and nothing else. If another enumerated,
    behaviour-shaped field is added at top level, this test should fail and force the
    consumer rules in the implementation plan to be revisited at the same time.
    """
    enumerated = {
        name for name, spec in SCHEMA["properties"].items()
        if "enum" in spec or "const" in spec
    }
    assert enumerated == {"maturity", "clock", "spec_version"}, (
        "a new enumerated top-level field appeared: consumers may only derive behaviour "
        f"from `maturity`. Found {sorted(enumerated)}"
    )
