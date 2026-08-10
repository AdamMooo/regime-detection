"""Assumption ledger — assembly, rendering and the offline delivery path.

Every test here runs offline with no credentials. The send path is exercised only
through its dry run and through the absent-secret branch, which is the branch that
exists so a missing secret can never fail a build.
"""

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import assumption_ledger as al
import mailer
import send_ledger


@pytest.fixture(scope="module")
def ledger():
    return al.build_ledger()


# --- assembly: the ledger is a VIEW of the observation log, never a recomputation ---

def test_ledger_source_is_the_observation_history():
    """A presentation layer that recomputes can print a number that disagrees with the
    published record. Structural check on imports and literals, not on prose: the module
    must not reach for the descriptor spines, the results CSVs, or pandas."""
    import ast

    tree = ast.parse((ROOT / "scripts" / "assumption_ledger.py").read_text(encoding="utf-8"))
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported |= {a.name.split(".")[0] for a in node.names}
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    assert imported & {"observation_history", "signal_output_schema"} == {
        "observation_history", "signal_output_schema",
    }
    assert not imported & {"vol_descriptors", "stockbond_corr", "vol_level0",
                           "stockbond_level0", "pandas", "numpy"}, imported
    literals = [n.value for n in ast.walk(tree) if isinstance(n, ast.Constant)
                and isinstance(n.value, str)]
    assert not [s for s in literals if s.endswith(".csv")]


def test_only_admitted_signals_appear(ledger):
    """Valuation is deliberately absent while R9 is open and credit's one-look is
    unspent. The observation-history EMITTERS registry is the admission gate."""
    from observation_history import EMITTERS

    rendered = {r["signal"] for r in ledger["level0_state_vector"]}
    assert rendered == set(EMITTERS) == {"volatility", "stock_bond_correlation"}


def test_assumption_text_is_verbatim_from_the_record(ledger):
    texts = {r["signal"]: r["assumption_monitored"] for r in ledger["level0_state_vector"]}
    for entry in ledger["level1_assumption_ledger"]:
        for signal in entry["signals"]:
            assert entry["assumption"] == texts[signal]


def test_status_and_derivation_are_verbatim_from_the_record(ledger):
    by_signal = {r["signal"]: r for r in ledger["level0_state_vector"]}
    for entry in ledger["level1_assumption_ledger"]:
        for signal in entry["signals"]:
            state = by_signal[signal].get("assumption_state")
            assert entry["status"] == (state or {}).get("status")
            assert entry["status_derivation"] == (state or {}).get("derivation")


def test_stock_bond_carries_its_declared_status(ledger):
    entry = next(e for e in ledger["level1_assumption_ledger"]
                 if e["assumption"] == "bonds hedge equity drawdowns")
    assert entry["kind"] == "assumption_monitor"
    assert entry["status"] == "violated"
    assert "pre-committed 2026-08-02" in entry["status_derivation"]


def test_volatility_is_a_context_axis_with_no_status(ledger):
    """The volatility charter registered N/A deliberately: 'introducing one would
    re-import the CALM/STRESSED state the reframe exists to remove.'"""
    entry = next(e for e in ledger["level1_assumption_ledger"]
                 if e["signals"] == ["volatility"])
    assert entry["kind"] == "context_axis"
    assert entry["status"] is None
    assert entry["status_derivation"] is None


# --- the module owns no thresholds --------------------------------------------------

def _monitor_record():
    return {"signal": "example", "assumption_monitored": "bonds hedge equity drawdowns"}


def test_a_monitor_without_a_declared_mapping_is_refused():
    """The whole point of this layer: it will not invent an intact/under_test/violated
    cut-off for a signal whose charter never declared one."""
    with pytest.raises(ValueError, match="declares no assumption_state"):
        al.status_of(_monitor_record())


def test_a_context_axis_carrying_a_status_is_refused():
    record = {
        "signal": "example",
        "assumption_monitored": "N/A because it is a context axis",
        "assumption_state": {"status": "intact", "derivation": "whatever"},
    }
    with pytest.raises(ValueError, match="context axis"):
        al.status_of(record)


# --- rarity is never shown without the basis that makes it comparable ---------------

def test_every_percentile_carries_its_basis(ledger):
    for entry in ledger["level1_assumption_ledger"]:
        for ev in entry["evidence"]:
            rarity = ev["rarity"]
            assert rarity["basis"] in al.BASIS_MEANING
            assert rarity["basis_meaning"] == al.BASIS_MEANING[rarity["basis"]]
            assert al.BASIS_MEANING[rarity["basis"]] in al._rarity_text(rarity)


# --- maturity is displayed honestly -------------------------------------------------

def test_research_maturity_is_visibly_distinguished(ledger):
    html = al.render_html(ledger)
    assert "RESEARCH GRADE, NOT PRODUCTION" in html
    research = [ev for e in ledger["level1_assumption_ledger"] for ev in e["evidence"]
                if ev["maturity"] == "research"]
    assert research, "no research-grade reading present -- this test would pass vacuously"
    for ev in research:
        assert "NOT PRODUCTION" in ev["maturity_note"]


# --- Level 2 is a seam, not an implementation ---------------------------------------

def test_level2_is_not_built(ledger):
    assert ledger["level2_context"] == {"built": False, "seam": al.LEVEL2_SEAM}
    assert al.level2_context(ledger["level0_state_vector"])["built"] is False


# --- point-in-time replay -----------------------------------------------------------

def test_known_at_filter_returns_an_earlier_read():
    """The ledger answers 'what did we believe, as of instant T' -- the same query the
    observation log exists to support."""
    now = al.build_ledger()
    past = al.build_ledger(known_at="2024-01-01T00:00:00Z")
    now_dates = {r["as_of"] for r in now["level0_state_vector"]}
    past_dates = {r["as_of"] for r in past["level0_state_vector"]}
    assert max(past_dates) < max(now_dates)
    assert past["known_at"] == "2024-01-01T00:00:00Z"


# --- the committed artifacts must still agree with their producer -------------------

def test_committed_artifacts_are_not_stale(ledger):
    """The exact failure this repo already had once (results/vol_descriptors.csv,
    2026-08-06): a committed artifact silently disagreeing with the code that claims to
    produce it. The ledger carries no wall-clock stamp precisely so this can be checked."""
    committed = json.loads(al.JSON_OUT.read_text(encoding="utf-8"))
    assert committed == ledger, (
        "results/assumption_ledger.json is STALE -- rerun "
        "`python scripts/assumption_ledger.py` and commit both artifacts."
    )
    assert al.HTML_OUT.read_text(encoding="utf-8") == al.render_html(ledger), (
        "results/assumption_ledger.html is STALE -- rerun scripts/assumption_ledger.py."
    )


# --- delivery: dry run is the default and needs no credentials ----------------------

def test_mailer_skips_when_the_secret_is_absent(monkeypatch, caplog):
    monkeypatch.delenv(mailer.PASSWORD_ENV, raising=False)
    monkeypatch.delenv(mailer.ADDRESS_ENV, raising=False)
    assert mailer.send_html("subject", "<p>body</p>") is False
    assert "skipping send" in caplog.text


def test_dry_run_writes_both_artifacts_offline(tmp_path, monkeypatch, capsys):
    monkeypatch.delenv(mailer.PASSWORD_ENV, raising=False)
    monkeypatch.delenv(mailer.ADDRESS_ENV, raising=False)
    json_out, html_out = tmp_path / "l.json", tmp_path / "l.html"
    monkeypatch.setattr(
        sys, "argv",
        ["send_ledger.py", "--json-out", str(json_out), "--html-out", str(html_out)],
    )
    assert send_ledger.main() == 0
    out = capsys.readouterr().out
    assert "dry run - nothing sent" in out
    assert json.loads(json_out.read_text(encoding="utf-8"))["level1_assumption_ledger"]
    assert "<html" in html_out.read_text(encoding="utf-8")


def test_send_without_credentials_does_not_fail_the_run(tmp_path, monkeypatch):
    """`--send` with no secret must log and skip, never raise and never exit non-zero:
    the artifact is the product and delivery is a convenience."""
    monkeypatch.delenv(mailer.PASSWORD_ENV, raising=False)
    monkeypatch.delenv(mailer.ADDRESS_ENV, raising=False)
    monkeypatch.setattr(
        sys, "argv",
        ["send_ledger.py", "--send",
         "--json-out", str(tmp_path / "l.json"), "--html-out", str(tmp_path / "l.html")],
    )
    assert send_ledger.main() == 0


def test_subject_line_carries_no_verdict(ledger):
    subject = send_ledger.subject_for(ledger)
    assert subject == "Assumption ledger - observations as of 2026-06-30"
