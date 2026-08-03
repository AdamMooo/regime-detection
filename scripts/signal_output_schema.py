"""Closed Level-0 output schema — the executable HARD BOUNDARY (D-18).

Realizes signal-output-spec.md §4.1 (closed allowlist) + validation-standards.md §(m).
A Level-0 record may contain ONLY the enumerated fields; any allocation / decision /
composite-scalar field is schema-invalid. The denylist below LEGITIMATELY names the
forbidden vocabulary as data — that is the enforcement, not a boundary violation.
"""

LEVEL0_ALLOWED = {
    "signal",
    "assumption_monitored",
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
}


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
