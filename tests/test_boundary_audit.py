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


# --- Test E: the presentation layer (Phase 10) ------------------------------------
#
# The ledger is the most dangerous artifact in the repo: it is the one thing a human
# reads, so it is where a verdict would be most useful and most wrong. Everything below
# audits the RENDERING as well as the record, because a boundary violation can enter as
# prose in an HTML page just as easily as a field name in JSON.

sys.path.insert(0, str(ROOT / "scripts"))

from assumption_ledger import build_ledger, render_html  # noqa: E402

# The ONE documented exception in CLAUDE.md: VENDOR IDENTIFIERS. Ken French's filenames
# and block headers literally contain a forbidden word, and a provenance citation cannot
# be written without them. They are SOURCE IDENTIFIERS, never concepts -- the same class
# as signal_output_schema.py naming the forbidden vocabulary as denylist data. Stripped
# before the prose scan so an honest citation cannot fail the audit; the scan still
# catches the concept used as a concept anywhere else in the same document.
_VENDOR_IDENTIFIER_RE = re.compile(
    r"\b\d+_Portfolios[A-Za-z0-9_.:\-]*"
    r"|\b[A-Za-z]+_\d+_Portfolios[A-Za-z0-9_.:\-]*"
    r"|Number of Firms in Portfolios",
    re.IGNORECASE,
)

_WORD_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
_STYLE_ATTR_RE = re.compile(r'\sstyle="[^"]*"')


def _prose_denylist_hits(text):
    """Forbidden vocabulary anywhere in a rendered document, not just in field names.

    Two checks the key-level audit cannot make: the singular stem (so `positions` is
    caught as well as `position`), and the allocation-SYSTEM tokens from Test D, which
    CLAUDE.md puts under a zero-references rule for prose as well as imports.
    """
    text = _VENDOR_IDENTIFIER_RE.sub(" ", text)
    hits = set()
    for token in _WORD_RE.findall(text):
        low = token.lower()
        stem = low[:-1] if low.endswith("s") else low
        if is_forbidden_key(low) or is_forbidden_key(stem):
            hits.add(token)
        if any(low.startswith(t) for t in _SYSTEM_TOKENS):
            hits.add(token)
    return sorted(hits)


def test_prose_denylist_actually_catches_things():
    """Guards the guard: a denylist scan that matches nothing is indistinguishable from
    a clean document, so prove it fires."""
    assert _prose_denylist_hits("<p>target exposure 0.25, trim the positions</p>")
    assert _prose_denylist_hits("<p>composite risk score 73/100</p>")
    assert not _prose_denylist_hits("<p>25_Portfolios_5x5_CSV.zip is the source file</p>")


@pytest.fixture(scope="module")
def ledger():
    return build_ledger()


def test_ledger_records_are_schema_valid(ledger):
    """Every Level-0 record the ledger renders goes back through the producer-side
    validator. The rendering is not trusted because the log was clean when written."""
    assert ledger["level0_state_vector"], "no state vector -- nothing was rendered"
    for record in ledger["level0_state_vector"]:
        validate(record)


def test_ledger_artifact_has_no_forbidden_field(ledger):
    hits = sorted(k for k in collect_keys(ledger) if is_forbidden_key(k))
    assert not hits, f"assumption ledger: forbidden field name(s) {hits}"


def test_ledger_artifact_prose_is_clean(ledger):
    hits = _prose_denylist_hits(json.dumps(ledger))
    assert not hits, f"assumption ledger: forbidden vocabulary in values {hits}"


def test_ledger_html_is_clean(ledger):
    """Style attributes are stripped first: CSS property names (`font-size`) are language
    identifiers, the same class as the vendor exception, and are not presented content."""
    html = _STYLE_ATTR_RE.sub(" ", render_html(ledger))
    hits = _prose_denylist_hits(html)
    assert not hits, f"assumption ledger HTML: forbidden vocabulary {hits}"


@pytest.mark.parametrize("path", sorted(RESULTS.glob("*.html")), ids=lambda p: p.name)
def test_shipped_html_renderings_are_clean(path):
    """The committed rendering, not only a fresh build -- a stale artifact is still a
    shipped one."""
    html = _STYLE_ATTR_RE.sub(" ", path.read_text(encoding="utf-8"))
    hits = _prose_denylist_hits(html)
    assert not hits, f"{path.name}: forbidden vocabulary {hits}"


# --- Test F: the ledger cannot grow a composite score or a summary ---------------
#
# The closed key sets below are literals ON PURPOSE. If they were imported from
# assumption_ledger.py, adding a field there would update the guard along with the
# artifact and the test would notice nothing.

LEDGER_TOP_LEVEL = {
    "spec_version",
    "known_at",
    "source",
    "reading_notes",
    "level1_assumption_ledger",
    "level0_state_vector",
    "level2_context",
}

LEDGER_ENTRY_KEYS = {
    "assumption",
    "kind",
    "status",
    "status_derivation",
    "signals",
    "evidence",
}

# Names a collapse would arrive under. Most are not in the schema denylist because they
# are not allocation words -- they are the OTHER failure mode: one number or one word
# standing in for the vector. A market can be low-vol and fragile at once; any of these
# fields would erase that.
COLLAPSE_SHAPED_KEYS = {
    "score", "risk_score", "composite", "composite_score", "aggregate", "overall",
    "summary", "verdict", "label", "regime", "regime_label", "state_label", "headline",
    "rank", "grade", "risk_level", "joint_score", "one_word", "conclusion",
}


def test_ledger_top_level_is_a_closed_set(ledger):
    assert set(ledger) == LEDGER_TOP_LEVEL, (
        f"assumption ledger grew or lost a top-level field: "
        f"added {sorted(set(ledger) - LEDGER_TOP_LEVEL)}, "
        f"removed {sorted(LEDGER_TOP_LEVEL - set(ledger))}. A new top-level field is how "
        f"a composite or a summary would arrive -- justify it before widening this set."
    )


def test_ledger_entries_are_a_closed_set(ledger):
    for entry in ledger["level1_assumption_ledger"]:
        assert set(entry) == LEDGER_ENTRY_KEYS, (
            f"ledger entry {entry.get('assumption')!r} key set drifted: {sorted(entry)}"
        )


def test_ledger_has_no_collapse_shaped_field(ledger):
    hits = sorted(collect_keys(ledger) & COLLAPSE_SHAPED_KEYS)
    assert not hits, (
        f"assumption ledger carries collapse-shaped field(s) {hits}. The full per-signal "
        f"vector is the product; it is never reduced to one number or one word."
    )


# --- Test G: the informativeness map (Phase 10, plan 10-02) ----------------------
#
# Same treatment as the ledger, for the same reason: this is the object a human reads.
# The key sets are literals here ON PURPOSE -- importing them from the module would let a
# new field update the guard alongside the artifact.

from informativeness_map import build_map  # noqa: E402
from informativeness_map import render_html as render_map_html  # noqa: E402

MAP_TOP_LEVEL = {
    "spec_version",
    "known_at",
    "source",
    "axis_sequence",
    "informativeness_definition",
    "reading_notes",
    "admitted_axes",
    "candidate_axes",
    "assumption_ledger",
    "level2_context",
}

MAP_AXIS_KEYS = {
    "axis",
    "kind",
    "admission",
    "assumption",
    "status",
    "status_derivation",
    "as_of",
    "available_at",
    "clock",
    "reading",
    "rarity",
    "maturity",
    "maturity_note",
    "provenance",
    "informativeness",
}

# A candidate carries exactly one field an admitted axis does not: what must be ruled to
# promote it. Anything else appearing only on a candidate is a divergence to justify.
MAP_CANDIDATE_EXTRA_KEYS = {"promotion_requires"}

# Standing and novelty are SIBLINGS. If a third key ever appeared here it would be the
# combined field this object exists to not have.
MAP_INFORMATIVENESS_KEYS = {"standing", "novelty", "persistence", "history"}

# A forward-looking statistic would arrive under one of these names. The tail charter's
# registered constraint (09-TAIL-CHARTER-DRAFT.md:36) is carried verbatim in the artifact;
# this is the executable half of it. KEY names only -- the records' own prose legitimately
# says things like "does not forecast when the sign will flip", and a prose scan would
# fail on the disclaimer while missing the field.
FORWARD_LOOKING_KEY_TOKENS = (
    "forward", "ahead", "hit_rate", "hitrate", "lead_lag", "leadlag", "future",
    "subsequent", "next_", "t_plus", "lookahead", "look_ahead", "predict", "forecast",
    "drawdown", "outcome", "realized_return", "excess_return", "horizon_return",
)


@pytest.fixture(scope="module")
def imap():
    return build_map()


def test_map_top_level_is_a_closed_set(imap):
    assert set(imap) == MAP_TOP_LEVEL, (
        f"informativeness map grew or lost a top-level field: "
        f"added {sorted(set(imap) - MAP_TOP_LEVEL)}, "
        f"removed {sorted(MAP_TOP_LEVEL - set(imap))}. A new top-level field is how a "
        f"composite, a summary, or a cross-axis ranking would arrive -- justify it before "
        f"widening this set."
    )


def test_map_axis_rows_are_a_closed_set(imap):
    for axis in imap["admitted_axes"]:
        assert set(axis) == MAP_AXIS_KEYS, (
            f"admitted axis {axis['axis']!r} key set drifted: {sorted(axis)}"
        )
    for axis in imap["candidate_axes"]:
        assert set(axis) == MAP_AXIS_KEYS | MAP_CANDIDATE_EXTRA_KEYS, (
            f"candidate axis {axis['axis']!r} key set drifted: {sorted(axis)}"
        )


def test_map_informativeness_is_two_siblings_plus_context(imap):
    """No combined field, ever. Standing and novelty are separate keys with separate
    prose, and `persistence` / `history` are context for both, not a third verdict."""
    for axis in imap["admitted_axes"] + imap["candidate_axes"]:
        assert set(axis["informativeness"]) == MAP_INFORMATIVENESS_KEYS, (
            f"{axis['axis']}: informativeness key set drifted: "
            f"{sorted(axis['informativeness'])}. A merged standing-plus-novelty field is "
            f"the single-label failure at the axis level."
        )


def test_map_artifact_has_no_forbidden_field(imap):
    hits = sorted(k for k in collect_keys(imap) if is_forbidden_key(k))
    assert not hits, f"informativeness map: forbidden field name(s) {hits}"


def test_map_artifact_prose_is_clean(imap):
    hits = _prose_denylist_hits(json.dumps(imap))
    assert not hits, f"informativeness map: forbidden vocabulary in values {hits}"


def test_map_html_is_clean(imap):
    html = _STYLE_ATTR_RE.sub(" ", render_map_html(imap))
    hits = _prose_denylist_hits(html)
    assert not hits, f"informativeness map HTML: forbidden vocabulary {hits}"


def test_map_has_no_collapse_shaped_field(imap):
    hits = sorted(collect_keys(imap) & COLLAPSE_SHAPED_KEYS)
    assert not hits, (
        f"informativeness map carries collapse-shaped field(s) {hits}. Every axis keeps "
        f"its own two dimensions; nothing is reduced to one number or one word."
    )


@pytest.mark.parametrize("name", ["assumption ledger", "informativeness map"])
def test_no_forward_looking_key_anywhere(name, ledger, imap):
    """The measurement system must not grow a prediction system by accretion.

    'no forward-return, drawdown, hit-rate, or lead/lag statistic is computed anywhere in
    this phase' (09-TAIL-CHARTER-DRAFT.md:36). A field name is where such a statistic
    would surface, so the guard is on names and it covers BOTH artifacts.
    """
    obj = ledger if name == "assumption ledger" else imap
    hits = sorted(
        k for k in collect_keys(obj)
        if any(tok in k.lower() for tok in FORWARD_LOOKING_KEY_TOKENS)
    )
    assert not hits, (
        f"{name}: forward-looking field name(s) {hits}. Computing one is how a "
        f"measurement system drifts into a prediction system."
    )


def test_forward_looking_scan_actually_catches_things():
    """Guards the guard: prove the token scan fires on the names it exists to catch."""
    for bad in ("forward_return_12m", "hit_rate", "lead_lag_months", "max_drawdown",
                "pctile_1y_ahead", "predicted_state"):
        assert any(tok in bad for tok in FORWARD_LOOKING_KEY_TOKENS), bad
    for good in ("level_percentile", "current_spell_length", "as_of", "share_of_history"):
        assert not any(tok in good for tok in FORWARD_LOOKING_KEY_TOKENS), good


def test_map_modules_contain_no_negative_shift():
    """`.shift(-n)` is how look-ahead actually enters pandas code. Neither presentation
    module may contain one, and this catches it in review-proof form."""
    for name in ("assumption_ledger.py", "informativeness_map.py"):
        src = (ROOT / "scripts" / name).read_text(encoding="utf-8")
        assert "shift(-" not in src.replace(" ", ""), f"{name} carries a negative shift"


def test_regime_card_stays_a_parked_blank():
    """The Phase 10 artifact has its own name and path. `results/regime_card.json` is a
    deliberate parked blank and repopulating it with a summary is the exact prohibited
    move -- so assert it still carries no reading."""
    card = json.loads((RESULTS / "regime_card.json").read_text(encoding="utf-8"))
    assert "status" in card and "replaced_by" in card, "regime_card.json is not a placeholder"
    for key in ("reading", "rarity", "assessment", "maturity", "level1_assumption_ledger"):
        assert key not in card, f"regime_card.json grew a {key!r} field"
