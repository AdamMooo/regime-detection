"""Closed Level-0 output schema — the executable HARD BOUNDARY (D-18).

Realizes signal-output-spec.md §4.1 (closed allowlist) + validation-standards.md §(m).
A Level-0 record may contain ONLY the enumerated fields; any allocation / decision /
composite-scalar field is schema-invalid. The denylist below LEGITIMATELY names the
forbidden vocabulary as data — that is the enforcement, not a boundary violation.

This is the PRODUCER-side validator. `contracts/market-observation-v1.schema.json` is
the canonical, language-neutral contract that consumers vendor. The two must accept and
reject exactly the same records — `tests/test_contract_conformance.py` asserts that
against every vector in `contracts/vectors/`, so the pair cannot drift silently.
"""

import re

LEVEL0_ALLOWED = {
    "signal",
    "as_of",
    "available_at",
    "supersedes",
    "assumption_monitored",
    "assumption_state",
    "reading",
    "rarity",
    "trend",
    "extreme_conditions",
    "cross_signal_relationships",
    "clock",
    "assessment",
    "maturity",
    "spec_version",
}

# Point-in-time fields (contracts/market-observation-v1.schema.json). `as_of` is the
# date the reading describes; `available_at` is when it was computable given data
# vintage and publication lag. Neither is derivable from the other, so both are
# required — a backtest filters on `available_at`, never on `as_of`.
REQUIRED_TOP_LEVEL = {
    "spec_version", "signal", "as_of", "available_at", "clock",
    "assumption_monitored", "reading", "rarity", "assessment", "maturity",
}

ASSESSMENT_ALLOWED = {
    "mechanism",
    "measurement_validity",
    "investment_usefulness",
    "evidence_maturity",
}

ALLOWED_KEYS = LEVEL0_ALLOWED | ASSESSMENT_ALLOWED

FORBIDDEN = {
    "weight", "target_weight", "allocation", "allocate", "exposure", "position",
    "position_size", "sizing", "size", "order", "trade", "buy", "sell", "entry",
    "entry_point", "exit", "exit_point", "stop", "stop_loss", "tilt", "sleeve",
    "cash_call", "overweight", "underweight", "recommendation", "action",
    "signal_action", "risk_score", "score", "rating", "target",
}

# Match on exact key tokens / snake-case SEGMENTS, never arbitrary substrings.
# Only single-token denylist entries seed the segment set — splitting multi-word
# entries (entry_point, risk_score) would leak benign segments like "point".
_FORBIDDEN_SEGMENTS = {t for t in FORBIDDEN if "_" not in t}

_ENUMS = {
    "mechanism": {"pass", "rejected"},
    "measurement_validity": {"H", "M", "L"},
    "investment_usefulness": {"H", "M", "L"},
    "evidence_maturity": {"H", "M", "L"},
    "maturity": {"production", "research", "rejected"},
    "clock": {"daily", "weekly", "monthly", "structural"},
    "basis": {"expanding", "trailing_fixed", "full_sample"},
    "status": {"intact", "under_test", "violated"},
}

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_SIGNAL_RE = re.compile(r"^[a-z][a-z0-9_]*$")

SPEC_VERSION = "1.0"


def is_forbidden_key(key):
    k = key.lower()
    if k in FORBIDDEN:
        return True
    return any(seg in _FORBIDDEN_SEGMENTS for seg in k.split("_"))


def collect_keys(obj):
    keys = set()
    if isinstance(obj, dict):
        for k, v in obj.items():
            keys.add(k)
            keys |= collect_keys(v)
    elif isinstance(obj, list):
        for item in obj:
            keys |= collect_keys(item)
    return keys


def _is_placeholder(value):
    return isinstance(value, str) and value.startswith("<") and value.endswith(">")


def _check_enum(field, value):
    if field in _ENUMS and not _is_placeholder(value):
        if value not in _ENUMS[field]:
            raise ValueError(f"{field}={value!r} not in {sorted(_ENUMS[field])}")


def validate(record):
    if not isinstance(record, dict):
        raise ValueError("Level-0 record must be an object")

    for key in collect_keys(record):
        if is_forbidden_key(key):
            raise ValueError(f"forbidden field name (boundary violation): {key!r}")

    for key in record:
        if key not in LEVEL0_ALLOWED:
            raise ValueError(f"unknown top-level key (allowlist violation): {key!r}")

    assessment = record.get("assessment", {})
    if not isinstance(assessment, dict):
        raise ValueError("assessment must be an object")
    for key in assessment:
        if key not in ASSESSMENT_ALLOWED:
            raise ValueError(f"unknown assessment key (allowlist violation): {key!r}")

    for field in ("clock", "maturity"):
        if field in record:
            _check_enum(field, record[field])
    for field in ASSESSMENT_ALLOWED:
        if field in assessment:
            _check_enum(field, assessment[field])

    _check_required(record)
    _check_point_in_time(record)
    _check_reading(record.get("reading"))
    _check_rarity(record.get("rarity"), record, assessment)
    _check_trend(record.get("trend"))
    _check_assumption_state(record.get("assumption_state"))


def _check_assumption_state(state):
    """A status label is only admissible with the rule that produced it.

    The repo's standing objection to labels is that one word destroys the graded
    information. Requiring `derivation` answers it: the label is reproducible from
    reading.value, so it adds no axis — and a threshold invented after looking at the
    data cannot be described as pre-committed.
    """
    if state is None:
        return
    if not isinstance(state, dict):
        raise ValueError("assumption_state must be an object or null")
    for field in ("status", "derivation"):
        if field not in state:
            raise ValueError(f"assumption_state.{field} is required")
    _check_enum("status", state["status"])
    if not str(state.get("derivation") or "").strip():
        raise ValueError("assumption_state.derivation must be non-empty — a label needs its rule")


def _check_required(record):
    missing = REQUIRED_TOP_LEVEL - set(record)
    if missing:
        raise ValueError(f"missing required field(s): {sorted(missing)}")
    if record.get("spec_version") != SPEC_VERSION and not _is_placeholder(record.get("spec_version")):
        raise ValueError(f"spec_version must be {SPEC_VERSION!r}, got {record.get('spec_version')!r}")
    sig = record.get("signal")
    if isinstance(sig, str) and not _is_placeholder(sig) and not _SIGNAL_RE.match(sig):
        raise ValueError(f"signal must be snake_case matching {_SIGNAL_RE.pattern}: {sig!r}")
    if not str(record.get("assumption_monitored", "")).strip():
        raise ValueError(
            "assumption_monitored must be non-empty — a context axis states 'N/A because ...' explicitly"
        )


def _check_point_in_time(record):
    as_of = record.get("as_of")
    if isinstance(as_of, str) and not _is_placeholder(as_of) and not _DATE_RE.match(as_of):
        raise ValueError(f"as_of must be YYYY-MM-DD: {as_of!r}")
    # available_at is an instant, not a date: it is the wall-clock moment the value was
    # computable. For revised series it is FIRST-PRINT availability, never the revision.
    avail = record.get("available_at")
    if isinstance(avail, str) and not _is_placeholder(avail) and "T" not in avail:
        raise ValueError(f"available_at must be a timestamp (date-time), not a bare date: {avail!r}")


def _check_reading(reading):
    if not isinstance(reading, dict):
        raise ValueError("reading must be an object")
    for field in ("value", "units", "estimator"):
        if field not in reading:
            raise ValueError(f"reading.{field} is required")
    if not str(reading.get("units", "")).strip():
        raise ValueError("reading.units must be non-empty on every numeric leaf")
    if reading.get("value") is None and not str(reading.get("undefined_reason") or "").strip():
        raise ValueError("reading.undefined_reason is required when reading.value is null")
    for sec in reading.get("secondary_readings", []) or []:
        for field in ("name", "value", "units", "estimator"):
            if field not in sec:
                raise ValueError(f"secondary_reading.{field} is required")


def _check_rarity(rarity, record, assessment):
    if not isinstance(rarity, dict):
        raise ValueError("rarity must be an object")
    for field in ("level_percentile", "basis", "window"):
        if field not in rarity:
            raise ValueError(f"rarity.{field} is required")
    _check_enum("basis", rarity["basis"])
    _check_percentile("rarity.level_percentile", rarity["level_percentile"])

    # window is meaningful ONLY for a fixed trailing window; anything else must be null,
    # so a reader can never mistake an expanding rank for a windowed one.
    if rarity["basis"] == "trailing_fixed":
        if not isinstance(rarity["window"], int) or rarity["window"] < 1:
            raise ValueError("rarity.window must be a positive integer when basis='trailing_fixed'")
    elif rarity["window"] is not None:
        raise ValueError(f"rarity.window must be null when basis={rarity['basis']!r}")

    for sec in rarity.get("secondary_percentiles", []) or []:
        _check_enum("basis", sec.get("basis"))
        _check_percentile(f"secondary_percentile[{sec.get('name')}]", sec.get("level_percentile"))

    # A full-sample rank embeds the future distribution in today's reading, so it can
    # never be production. A rejected mechanism fails the first gate, likewise. Both are
    # enforced structurally rather than left to a producer's discipline.
    maturity = record.get("maturity")
    if rarity["basis"] == "full_sample" and maturity == "production":
        raise ValueError(
            "rarity.basis='full_sample' leaks the future distribution — maturity cannot be 'production'"
        )
    if assessment.get("mechanism") == "rejected" and maturity == "production":
        raise ValueError("assessment.mechanism='rejected' — maturity cannot be 'production'")


def _check_trend(trend):
    if trend is None:
        return
    if not isinstance(trend, dict):
        raise ValueError("trend must be an object or null")
    if trend.get("level_percentile_change") is not None and trend.get("lookback_observations") is None:
        raise ValueError(
            "trend.lookback_observations is required alongside level_percentile_change — "
            "a delta without its horizon is uninterpretable"
        )


def _check_percentile(label, value):
    if value is None or _is_placeholder(value):
        return
    if not isinstance(value, (int, float)) or not (0.0 <= float(value) <= 1.0):
        raise ValueError(f"{label} must be a number in [0, 1], got {value!r}")
