import json
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from signal_output_schema import (
    ALLOWED_KEYS,
    collect_keys,
    is_forbidden_key,
    validate,
)

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
EXAMPLES = ROOT / ".planning" / "framework" / "examples"

_KEY_RE = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*:")


def _level0_keys_from_declaration(text):
    heading = re.search(r"(?im)^#+.*level 0", text)
    assert heading, "no 'Level 0' heading found"
    rest = text[heading.end():]
    block = re.search(r"```(.*?)```", rest, re.DOTALL)
    assert block, "no fenced code block after 'Level 0' heading"
    keys = []
    for line in block.group(1).splitlines():
        m = _KEY_RE.match(line)
        if m:
            keys.append(m.group(1))
    return keys


# --- Test A: shipped outputs carry no forbidden field name -------------------

# No exceptions. The one that used to live here (gauge.position in
# regime_card.json) was resolved 2026-08-06 by retiring the card's generator
# rather than renaming the field -- the leak came from the retired jump-model
# state, so deleting the state deleted the leak. Empty is the correct state:
# an entry here is a debt, not a design.
KNOWN_DEFERRED_EXCEPTIONS: set[tuple[str, str]] = set()


@pytest.mark.parametrize("path", sorted(RESULTS.glob("*.json")), ids=lambda p: p.name)
def test_shipped_outputs_have_no_forbidden_field(path):
    obj = json.loads(path.read_text())
    hits = sorted(
        k
        for k in collect_keys(obj)
        if is_forbidden_key(k) and (path.name, k) not in KNOWN_DEFERRED_EXCEPTIONS
    )
    assert not hits, f"{path.name}: forbidden field name(s) {hits}"


# --- Test B: example Level-0 records conform to the closed schema ------------

@pytest.mark.parametrize(
    "path", sorted(EXAMPLES.glob("*-signal-declaration.md")), ids=lambda p: p.name
)
def test_example_level0_records_conform(path):
    keys = _level0_keys_from_declaration(path.read_text(encoding="utf-8"))
    assert keys, f"{path.name}: parsed no keys"
    unknown = [k for k in keys if k not in ALLOWED_KEYS]
    forbidden = [k for k in keys if is_forbidden_key(k)]
    assert not unknown, f"{path.name}: keys outside allowlist {unknown}"
    assert not forbidden, f"{path.name}: forbidden keys {forbidden}"


# --- Test C: schema rejects violations, accepts a minimal valid record -------

def _minimal_valid_record():
    """Minimal record satisfying the v1 observation contract.

    `as_of` / `available_at` and the structured reading/rarity became mandatory with
    contracts/market-observation-v1.schema.json — a percentile is uninterpretable
    without the basis that produced it, and a backtest needs to know when the value
    was knowable, not only what date it describes.
    """
    return {
        "spec_version": "1.0",
        "signal": "example_signal",
        "as_of": "2026-05-29",
        "available_at": "2026-06-15T14:00:00Z",
        "assumption_monitored": "bonds hedge equity drawdowns",
        "reading": {
            "value": 0.35,
            "units": "pearson_correlation",
            "estimator": "24m trailing Pearson correlation of monthly returns",
        },
        "rarity": {"level_percentile": 0.85, "basis": "expanding", "window": None},
        "clock": "monthly",
        "assessment": {
            "mechanism": "pass",
            "measurement_validity": "H",
            "investment_usefulness": "H",
            "evidence_maturity": "M",
        },
        "maturity": "research",
    }


def test_schema_accepts_minimal_valid_record():
    validate(_minimal_valid_record())


def test_schema_rejects_forbidden_key():
    record = _minimal_valid_record()
    record["target_weight"] = 0.25
    with pytest.raises(ValueError):
        validate(record)


def test_schema_rejects_unknown_key():
    record = _minimal_valid_record()
    record["some_new_field"] = "x"
    with pytest.raises(ValueError):
        validate(record)


def test_schema_rejects_bad_enum():
    record = _minimal_valid_record()
    record["maturity"] = "elite"
    with pytest.raises(ValueError):
        validate(record)


def test_schema_tolerates_placeholder_enum():
    record = _minimal_valid_record()
    record["clock"] = "<daily|weekly|monthly|structural>"
    validate(record)


# --- Test D: no script imports/references a downstream allocation system ------

_SYSTEM_TOKENS = ("portfolio", "allocation", "alloc", "broker", "execution", "order")
_IMPORT_RE = re.compile(r"^\s*(import|from)\s+.*", re.IGNORECASE)


def test_no_script_imports_allocation_system():
    scripts = ROOT / "scripts"
    exclude = {"signal_output_schema.py"}
    offenders = []
    for py in sorted(scripts.glob("*.py")):
        if py.name in exclude:
            continue
        for lineno, line in enumerate(py.read_text(encoding="utf-8").splitlines(), 1):
            if not _IMPORT_RE.match(line):
                continue
            low = line.lower()
            for tok in _SYSTEM_TOKENS:
                if re.search(rf"\b{tok}", low):
                    offenders.append(f"{py.name}:{lineno}: {line.strip()}")
    assert not offenders, f"allocation/decision-system references: {offenders}"
