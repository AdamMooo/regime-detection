"""Informativeness map — assembly, the two dimensions, causality, and the candidate gate.

Every test here runs offline: the only inputs are the committed observation logs, the
committed monthly panel, and the committed artifacts. Nothing fetches, sends or spends a
look.
"""

import json
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import assumption_ledger as al
import concentration
import informativeness_map as im
from causal import assert_causal


@pytest.fixture(scope="module")
def panel() -> pd.DataFrame:
    return concentration.load_panel()


@pytest.fixture(scope="module")
def imap():
    return im.build_map()


# --- causality: the hazard this object invites ---------------------------------------

def test_build_is_causal(panel):
    """The candidate axis adds a tail mass and an expanding share on top of
    concentration.build. Registered here so `test_every_signal_build_is_under_the_causal
    _guard` sees it — a new build() cannot skip the guard by omission."""
    assert_causal(im.build, panel)


def test_known_at_replay_is_not_revised_by_later_data(imap):
    """'When did this axis carry information' must be answerable AS OF a past instant, and
    the answer must not move when later data arrives. Every spell the earlier map closed
    has to appear identically in the full map."""
    past = im.build_map(known_at="2024-01-01T00:00:00Z")
    assert past["known_at"] == "2024-01-01T00:00:00Z"
    for old, new in zip(past["admitted_axes"], imap["admitted_axes"]):
        assert old["axis"] == new["axis"]
        assert old["as_of"] < new["as_of"]
        old_hist, new_hist = old["informativeness"]["history"], new["informativeness"]["history"]
        assert old_hist["observations"] < new_hist["observations"]
        closed = [s for s in old_hist["spells"] if s["to"] < old_hist["last_as_of"]]
        assert closed, "no closed spell to compare — the assertion would be vacuous"
        for spell in closed:
            assert spell in new_hist["spells"], (
                f"{old['axis']}: spell {spell} was revised by data that arrived later — "
                f"the history is being re-ranked against the future"
            )


def test_percentiles_are_never_full_sample(imap):
    for axis in imap["admitted_axes"] + imap["candidate_axes"]:
        assert axis["rarity"]["basis"] == "expanding"
        assert axis["informativeness"]["standing"]["basis"] == "expanding"


# --- the two dimensions are independent and neither is subordinate -------------------

def test_there_is_no_combined_or_one_word_axis_summary(imap):
    """The correction that shaped this module: 'this axis is not moving' and 'this axis is
    not important' are different claims. A single word carrying both is the single-label
    failure one level down."""
    banned_values = {"live", "dormant", "latched", "quiet", "calm", "stressed",
                     "risk-on", "risk-off", "intact and quiet"}
    for axis in imap["admitted_axes"] + imap["candidate_axes"]:
        info = axis["informativeness"]
        assert set(info) == {"standing", "novelty", "persistence", "history"}
        for key, value in info.items():
            assert not isinstance(value, str), (
                f"{axis['axis']}.informativeness.{key} is a bare string — a dimension "
                f"must arrive as a block of facts, not as a verdict"
            )
        flat = json.dumps(axis).lower()
        for word in banned_values:
            assert f'"{word}"' not in flat, (
                f"{axis['axis']}: carries {word!r} as a standalone value"
            )


def test_standing_and_novelty_are_siblings_with_their_own_prose(imap):
    for axis in imap["admitted_axes"] + imap["candidate_axes"]:
        standing = axis["informativeness"]["standing"]
        novelty = axis["informativeness"]["novelty"]
        assert standing["question"] == im.STANDING_QUESTION
        assert novelty["question"] == im.NOVELTY_QUESTION
        assert standing["reads"].strip() and novelty["reads"].strip()
        assert standing["reads"] != novelty["reads"]
        # Neither may be nested inside the other, at any depth.
        assert "novelty" not in json.dumps(standing)
        assert "standing" not in json.dumps(novelty)


def test_high_standing_zero_novelty_axis_is_not_de_emphasised(imap):
    """THE test the correction asked for. Stock-bond has read `violated` for 52 months:
    maximally important, minimally novel. It must not be excluded, muted, or sequenced
    last in the JSON or in the HTML."""
    axes = imap["admitted_axes"]
    latched = [
        a for a in axes
        if (a["informativeness"]["persistence"] or {}).get("at_or_beyond_the_comparable_median")
    ]
    assert latched, "no latched axis present — this test would pass vacuously"
    html = im.render_html(imap)

    for axis in latched:
        info = axis["informativeness"]
        # 1. zero novelty by the status bit, and the standing says it is still not holding
        assert info["novelty"]["observations_since_the_declared_status_changed"] > 0
        assert axis["status"] == info["standing"]["declared_status"] is not None
        assert "still not holding" in info["standing"]["reads"]
        assert "not news" in info["novelty"]["reads"]

        # 2. not sequenced last: sequence is alphabetical, not by either dimension
        assert [a["axis"] for a in axes] == sorted(a["axis"] for a in axes)
        assert "alphabetical" in imap["axis_sequence"]

        # 3. not de-emphasised in the HTML: same card style as every other admitted axis,
        #    and both dimension chips rendered with the SAME chip style
        card = im._axis_html(axis)
        assert card.count(f'style="{im._CHIP}"') == 2, (
            "standing and novelty must render with one identical chip style each"
        )
        assert al._CARD in card and im._CANDIDATE_CARD not in card
        # De-emphasis would show up as this axis's headline block being styled
        # differently from every other admitted axis's. It is byte-identical apart from
        # the text itself.
        import re

        def header_styles(a):
            return re.findall(r'style="([^"]*)"', im._axis_html(a).split("<table")[0])

        assert header_styles(axis) == header_styles(axes[0]) == header_styles(axes[-1]), (
            "the latched axis's headline block is styled differently from the others"
        )

        # 4. and the standing sentence reaches the page verbatim, before the ledger
        standing_html = al._esc(info["standing"]["reads"])
        assert standing_html in html
        assert al._esc(info["novelty"]["reads"]) in html
        assert html.index(standing_html) < html.index("Assumption ledger</h2>")


def test_persistence_is_a_fact_not_a_rank(imap):
    for axis in imap["admitted_axes"] + imap["candidate_axes"]:
        p = axis["informativeness"]["persistence"]
        if p is None:
            continue
        for field in ("current_length", "current_start", "length_units",
                      "comparable_median_length", "comparable_longest_length"):
            assert p[field] is not None, field
        assert "never a rank" in p["informs"]
        assert "novelty AND standing" in p["informs"]


def test_persistence_is_carried_from_the_record_not_recomputed(imap):
    """`stockbond_level0.build_record` already computes the run length and the
    median/longest comparable episode. This layer adds one comparison and nothing else."""
    ledger = al.build_ledger()
    records = {r["signal"]: r for r in ledger["level0_state_vector"]}
    for axis in imap["admitted_axes"]:
        p = axis["informativeness"]["persistence"]
        episodes = (records[axis["axis"]].get("extreme_conditions") or {}).get("episodes")
        if p is None:
            assert not episodes or episodes.get("current_length") is None
            continue
        assert p["current_length"] == episodes["current_length"]
        assert p["current_start"] == episodes["current_start"]
        assert [p["comparable_median_length"], p["comparable_longest_length"]] == \
            episodes["major_episode_median_max"]
        assert p["at_or_beyond_the_comparable_median"] == (
            episodes["current_length"] >= episodes["major_episode_median_max"][0]
        )


# --- this layer owns no threshold ---------------------------------------------------

def test_the_tail_is_read_from_the_axis_own_record(imap):
    ledger = al.build_ledger()
    records = {r["signal"]: r for r in ledger["level0_state_vector"]}
    for axis in imap["admitted_axes"]:
        declared = records[axis["axis"]]["extreme_conditions"]["threshold_percentile"]
        standing = axis["informativeness"]["standing"]
        assert standing["threshold_percentile"] == declared
        assert "extreme_conditions.threshold_percentile" in standing["threshold_source"]


def test_an_admitted_axis_with_no_declared_tail_is_refused():
    """Same discipline as `assumption_ledger.status_of`: a missing declaration raises
    rather than getting a cut-off invented for it in the presentation layer."""
    ledger = al.build_ledger()
    record = dict(next(r for r in ledger["level0_state_vector"]
                       if r["signal"] == "volatility"))
    record["extreme_conditions"] = {}
    with pytest.raises(ValueError, match="threshold_percentile"):
        im._admitted_axis(record, None)


def test_tail_mass_is_two_sided_arithmetic_on_the_published_percentile(imap):
    for axis in imap["admitted_axes"] + imap["candidate_axes"]:
        p = axis["rarity"]["level_percentile"]
        standing = axis["informativeness"]["standing"]
        assert standing["current_percentile"] == p
        assert standing["tail_mass_beyond_reading"] == round(min(p, 1 - p), 4)
        assert standing["inside_the_tail_now"] == (
            standing["tail_mass_beyond_reading"] <= round(1 - standing["threshold_percentile"], 4)
        )


# --- admitted vs candidate ----------------------------------------------------------

def test_a_candidate_is_never_in_the_admitted_set(imap):
    from observation_history import EMITTERS

    admitted = {a["axis"] for a in imap["admitted_axes"]}
    candidates = {a["axis"] for a in imap["candidate_axes"]}
    assert candidates, "no candidate present — this test would pass vacuously"
    assert not admitted & candidates
    assert admitted == set(EMITTERS) == {"volatility", "stock_bond_correlation"}
    assert not candidates & set(EMITTERS), (
        "a candidate reached the admission registry — promotion goes through a signed "
        "charter, a spent look and a dated sign-off, not through the renderer"
    )
    for axis in imap["admitted_axes"]:
        assert axis["admission"] == "admitted"
    for axis in imap["candidate_axes"]:
        assert axis["admission"] == "candidate"


def test_the_candidate_cannot_be_mistaken_for_validated(imap):
    axis = imap["candidate_axes"][0]
    assert axis["maturity"] is None
    assert "NO MATURITY" in axis["maturity_note"]
    assert "NOT SIGNED" in axis["provenance"]["charter_state"]
    assert axis["provenance"]["validation_bars_run"].startswith("NONE")
    assert not (ROOT / "observations" / axis["axis"]).exists(), (
        "an observation log appeared for the candidate — if that is deliberate it is an "
        "admission, and it goes through the charter, not through this module"
    )
    assert axis["promotion_requires"], "a candidate must state what would promote it"
    assert any("V3" in item for item in axis["promotion_requires"])


def test_the_candidate_is_visually_distinct(imap):
    admitted_html = im._axis_html(imap["admitted_axes"][0])
    candidate_html = im._axis_html(imap["candidate_axes"][0])
    assert im._CANDIDATE_CARD in candidate_html
    assert im._CANDIDATE_CARD not in admitted_html
    assert "CANDIDATE" in candidate_html and "CANDIDATE" not in admitted_html
    assert "NO validation bar has run" in candidate_html
    full = im.render_html(imap)
    assert full.index("Admitted axes</h2>") < full.index("Candidate axes</h2>")


def test_the_candidate_reading_equals_its_producer(imap):
    """Sourced by recomputation because no observation log exists, so the one thing that
    can go wrong is disagreeing with the producer. It cannot."""
    produced = concentration.build().dropna(subset=["eff_n", "eff_n_pctile"]).iloc[-1]
    axis = imap["candidate_axes"][0]
    assert axis["reading"]["value"] == round(float(produced["eff_n"]), 4)
    assert axis["rarity"]["level_percentile"] == round(float(produced["eff_n_pctile"]), 4)
    top = next(s for s in axis["reading"]["secondary_readings"] if s["name"] == "top_share")
    assert top["value"] == round(float(produced["top_share"]), 4)


def test_the_candidate_is_excluded_from_a_point_in_time_replay():
    past = im.build_map(known_at="2024-01-01T00:00:00Z")
    assert past["candidate_axes"] == [], (
        "a candidate has no vintage log, so it has no honest answer to 'what would this "
        "have read as of T'"
    )


def test_the_candidate_carries_no_status_and_no_trend(imap):
    axis = imap["candidate_axes"][0]
    assert axis["kind"] == "context_axis"
    assert axis["status"] is None and axis["status_derivation"] is None
    assert axis["assumption"].upper().startswith("N/A")
    assert axis["informativeness"]["novelty"]["trend"] is None
    assert "owns no thresholds" in axis["provenance"]["no_trend_descriptor"]


# --- the ledger survives inside the new object, unchanged ---------------------------

def test_the_assumption_ledger_is_carried_verbatim(imap):
    assert imap["assumption_ledger"] == al.build_ledger()["level1_assumption_ledger"]
    kinds = {e["kind"] for e in imap["assumption_ledger"]}
    assert kinds == {"assumption_monitor", "context_axis"}
    monitor = next(e for e in imap["assumption_ledger"]
                   if e["kind"] == "assumption_monitor")
    assert monitor["status"] == "violated"
    assert monitor["status_derivation"]


def test_the_ledger_guards_still_hold():
    """Unchanged by the reframe: a monitor with no declared mapping raises, and a context
    axis arriving with a status raises."""
    with pytest.raises(ValueError, match="declares no assumption_state"):
        al.status_of({"signal": "x", "assumption_monitored": "bonds hedge equity drawdowns"})
    with pytest.raises(ValueError, match="context axis"):
        al.status_of({
            "signal": "x",
            "assumption_monitored": "N/A because it is a context axis",
            "assumption_state": {"status": "intact", "derivation": "whatever"},
        })


def test_admitted_readings_are_verbatim_from_the_published_record(imap):
    records = {r["signal"]: r for r in al.build_ledger()["level0_state_vector"]}
    for axis in imap["admitted_axes"]:
        record = records[axis["axis"]]
        assert axis["reading"]["value"] == record["reading"]["value"]
        assert axis["reading"]["estimator"] == record["reading"]["estimator"]
        assert axis["rarity"]["level_percentile"] == record["rarity"]["level_percentile"]
        assert axis["assumption"] == record["assumption_monitored"]
        assert axis["maturity"] == record["maturity"]
        assert "never a recomputation" in axis["provenance"]["reading_source"]


def test_level2_is_still_only_a_seam(imap):
    assert imap["level2_context"] == {"built": False, "seam": al.LEVEL2_SEAM}


# --- the committed artifacts must still agree with their producer -------------------

def test_committed_artifacts_are_not_stale(imap):
    committed = json.loads(im.JSON_OUT.read_text(encoding="utf-8"))
    assert committed == imap, (
        "results/informativeness_map.json is STALE — rerun "
        "`python scripts/informativeness_map.py` and commit both artifacts."
    )
    assert im.HTML_OUT.read_text(encoding="utf-8") == im.render_html(imap), (
        "results/informativeness_map.html is STALE — rerun scripts/informativeness_map.py."
    )


def test_the_definition_carries_the_registered_no_forward_constraint(imap):
    d = imap["informativeness_definition"]
    assert "no forward-return, drawdown, hit-rate, or lead/lag statistic" in \
        d["registered_constraint"]
    assert "09-TAIL-CHARTER-DRAFT.md:36" in d["registered_constraint"]
    assert "no outcome here to search over" in d["needs_no_preregistration"]
    assert d["registered_constraint"] in im.render_html(imap)
