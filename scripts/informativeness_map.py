"""Informativeness map — the presentation layer's output object. Phase 10, plan 10-02.

WHY THIS OBJECT REPLACES THE STATUS TABLE AS THE PRODUCT
--------------------------------------------------------
The {intact | under_test | violated} vocabulary is only honest for a quantity with a
natural mechanical boundary, and exactly one quantity in this repo has one: the SIGN of
the stock-bond correlation. Three charters independently refused to emit a status for
that reason and all three refusals stand:

- volatility: "There is deliberately no {intact | under-test | violated} status field —
  introducing one would re-import the CALM/STRESSED state the reframe exists to remove."
- concentration (04-CONCENTRATION-CHARTER-DRAFT.md:16-17): "Ledger status — recommend
  NONE: eff_n has no mechanical boundary (unlike sign zero in stock-bond correlation);
  banding it re-introduces the knob the volatility reframe removed."
- tail (09-TAIL-CHARTER-DRAFT.md:7): "Ledger status: none ... any threshold here is an
  arbitrary percentile knob, the exact failure the volatility reframe removed."

So the fix is the OUTPUT OBJECT, not the vocabulary. Here a statusless axis is a
first-class row rather than a footnote, and the question each axis answers becomes
"when has this axis carried information, and what is it saying now" — never "what should
be done about it." The assumption ledger survives as a SECTION inside this object,
carrying its one honest row.

TWO INDEPENDENT DIMENSIONS, NEVER MERGED — the correction that shaped this module
---------------------------------------------------------------------------------
"This axis is not moving" and "this axis is not important" are completely different
claims, and one word cannot carry both. A structural break in the bond hedge that has
held for 52 months is MAXIMALLY IMPORTANT and MINIMALLY NOVEL. Calling that "dormant"
would bury a live structural fact by framing it as uninteresting — the single-label
failure this repo exists to prevent, one level down.

So every axis carries two sibling blocks, given equal prominence in the JSON and in
rendering, and there is deliberately NO combined field and NO one-word axis summary:

- STANDING — what the axis says about the world right now, independent of whether it
  just changed. A declared status of `violated` reads high here however old it is; a
  reading at the 1.8th percentile of a century reads high here whether it arrived
  yesterday or a decade ago.
- NOVELTY — whether the reading has changed, and how recently it arrived where it is.
  A 52-month latch reads low here, and that is a statement about novelty alone.

PERSISTENCE IS CONTEXT FOR BOTH, NOT A VERDICT. "52 months in, against a historical
median of 52 and a longest of 129" informs novelty (an ordinary duration so far, so
today's print is not news) AND standing (it is still broken, and half of comparable
episodes ran longer). The fact is reported; it is never compressed into a rank.

Nothing is sorted, grouped or styled by either dimension. Axes appear in alphabetical
sequence — deterministic and deliberately not a precedence — so an axis with extreme
standing and zero novelty stays exactly as prominent as any other.

WHAT INFORMATIVENESS MEANS HERE — the whole definition, and its limits
----------------------------------------------------------------------
"Informative" means THIS READING DISTINGUISHES NOW FROM THIS AXIS'S OWN PAST, or the
axis's own pre-registered status says something is not holding. It never means the axis
predicted anything. Every figure is built from readings that were already ranked
expanding-only at their own date:

1. the tail mass beyond the current reading, min(p, 1-p), against the tail the AXIS
   ITSELF declares (`extreme_conditions.threshold_percentile`) — this module owns no
   threshold, exactly as `assumption_ledger.status_of` owns none;
2. the share of that axis's own published vintages whose reading fell in that same tail,
   with the number of distinct spells and their median length — a mostly-flat axis
   enters its tails rarely and briefly, a frequently-moving one often;
3. the declared status episode, verbatim from the record, plus the comparison of its
   current length against the median and longest of its own comparable episodes.

Nothing is fitted, no hypothesis is tested, no outcome variable exists, and no look is
spent: every figure is a min, a mean, a run-length count, or a comparison against a
number the axis published itself.

CAUSALITY — the hazard this object invites
------------------------------------------
"When in history did this axis carry information" computed on the full sample would be
look-ahead: it would rank each historical date against data that did not exist yet.
Every percentile used here was computed by `causal.expanding_percentile` at its own date
and published in `observations/<signal>/history.ndjson`, and every summary is taken over
the log AS FILTERED TO `known_at` — so `build_map(known_at=T)` is unchanged by anything
that became available after T, and `tests/test_informativeness_map.py` asserts it.

THE OTHER HAZARD, carried verbatim from 09-TAIL-CHARTER-DRAFT.md:36
-------------------------------------------------------------------
"no forward-return, drawdown, hit-rate, or lead/lag statistic is computed anywhere in
this phase — not as a headline, not as a robustness check, not in a scratch script. The
signal makes no forward claim, so there is nothing for such a statistic to validate, and
computing one is how a measurement system drifts into a prediction system."

ADMITTED vs CANDIDATE — structurally separate, never mixed
----------------------------------------------------------
`admitted_axes` are the signals with a signed charter, a spent one-look, a dated results
sign-off and a published observation log. `candidate_axes` are built and
construction-gated with NO signed charter and NO validation bar run; their reading is
RECOMPUTED from the committed panel because no observation log exists for them. The two
live in different lists and render in different sections, so a reader cannot mistake one
for the other, and `tests/test_informativeness_map.py` fails if a candidate ever appears
among the admitted.

Run:  python scripts/informativeness_map.py
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import assumption_ledger as al
import concentration
from causal import expanding_percentile
from observation_history import current_view, log_path, read_log

JSON_OUT = ROOT / "results" / "informativeness_map.json"
HTML_OUT = ROOT / "results" / "informativeness_map.html"

MAP_SPEC_VERSION = "1.0"

# Quoted, not paraphrased: this is a registered pre-commitment from a charter, and the
# whole hazard of the reframe is that it is easy to relax by rewording.
NO_FORWARD_STATISTIC = (
    "no forward-return, drawdown, hit-rate, or lead/lag statistic is computed anywhere "
    "in this phase - not as a headline, not as a robustness check, not in a scratch "
    "script. The signal makes no forward claim, so there is nothing for such a statistic "
    "to validate, and computing one is how a measurement system drifts into a prediction "
    "system. [09-TAIL-CHARTER-DRAFT.md:36, carried verbatim]"
)

STANDING_QUESTION = (
    "What is this axis saying about the world right now, independent of whether it has "
    "just changed?"
)

NOVELTY_QUESTION = (
    "Has this reading changed, and how recently did it arrive where it is?"
)

INFORMATIVENESS_DEFINITION = {
    "question_each_axis_answers": (
        "When has this axis carried information, and what is it saying now?"
    ),
    "informative_means": (
        "This reading distinguishes now from this axis's own past, or the axis's own "
        "pre-registered status says something is not holding. It NEVER means the axis "
        "predicted anything, and no reading here is compared with what happened "
        "afterwards."
    ),
    "two_dimensions_never_merged": (
        "Standing and novelty are independent and are reported side by side with equal "
        "prominence. 'This axis is not moving' and 'this axis is not important' are "
        "different claims and no single field carries both. An axis where nothing has "
        "changed AND the situation remains extreme is the most consequential thing this "
        "page can say, not a quiet row - so there is no combined field, no one-word axis "
        "summary, and no sorting, grouping or styling by either dimension."
    ),
    "standing": STANDING_QUESTION + (
        " Read from the axis's own declared status, where it declares one, and from how "
        "far into its own causal history the current reading sits: the tail mass beyond "
        "it, min(p, 1-p), against the tail the axis itself declares."
    ),
    "novelty": NOVELTY_QUESTION + (
        " Read from the trend descriptor the axis's own signed charter registered, from "
        "how long its declared status has held unchanged, and from how long ago it was "
        "last inside its own tail. Novelty carries no threshold at all - only counts and "
        "the axis's own declared direction."
    ),
    "persistence_is_context_for_both": (
        "A duration such as '52 months in, against a historical median of 52 and a "
        "longest of 129' informs novelty (an ordinary duration so far, so today's print "
        "is not news) and standing (it is still not holding, and half of comparable "
        "episodes ran longer). It is reported as a fact and never compressed into a rank."
    ),
    "owns_no_threshold": (
        "The tail is read from each axis's own declared extreme_conditions."
        "threshold_percentile and travels beside every figure that uses it, the same "
        "discipline as rarity.basis. This module invents no cut-off, exactly as "
        "assumption_ledger.status_of invents no status."
    ),
    "needs_no_preregistration": (
        "There is no hypothesis, no estimated parameter and no outcome variable: every "
        "figure is a min, a mean, a run-length count, or a comparison against a number "
        "the axis published itself. A preregistration exists to prevent a specification "
        "search over outcomes; there is no outcome here to search over, and no look is "
        "spent."
    ),
    "caveat": (
        "An expanding percentile is mechanically extreme during its own burn-in - with "
        "n observations the largest is always the 100th percentile - so every share and "
        "spell count below is inflated by the early history, and the earliest spells are "
        "one observation long for that reason. The same inflation is already present in "
        "the records' own extreme_conditions.share_of_history. Disclosed rather than "
        "tuned away with a burn-in cut, which would be a new knob."
    ),
    "registered_constraint": NO_FORWARD_STATISTIC,
}

READING_NOTES = [
    "Every axis is a row here whether or not it carries a status. Only a quantity with "
    "a mechanical boundary can carry one honestly, and exactly one in this repo has "
    "one: the sign of the stock-bond correlation.",
    "Standing and novelty are read together and neither is subordinate. Low novelty "
    "with high standing means nothing has changed AND the situation remains extreme - "
    "which is a finding, not a quiet row.",
    "The readings are never combined into one number, never reduced to one word, and "
    "never ranked against each other. Axes appear in alphabetical sequence, which is "
    "deterministic and deliberately not a precedence.",
    "Candidate axes are rendered in their own section. A candidate has no signed "
    "charter and no validation bar has run on it; its reading is a recomputation, not a "
    "point-in-time record. It is not evidence of anything yet.",
    "Values, units, estimators and every status are carried verbatim from the source "
    "record. Nothing is converted or re-derived here.",
]

# ── the candidate axis ────────────────────────────────────────────────────────────
# NOT a Level-0 emitter and deliberately not shaped like one. `observation_history.
# EMITTERS` is the admission registry and stays untouched, so nothing here can reach the
# admitted set or the contract-shaped observation logs.

CANDIDATE_THRESHOLD_PERCENTILE = 0.95

CONCENTRATION_AXIS = {
    "axis": "concentration",
    "kind": "context_axis",
    "assumption": (
        "N/A because concentration has no mechanical boundary. Its charter (unsigned) "
        "recommends no ledger status: 'eff_n has no mechanical boundary (unlike sign "
        "zero in stock-bond correlation); banding it re-introduces the knob the "
        "volatility reframe removed.' It is a structural context axis: how much of the "
        "index's capital sits in its largest buckets, how unusual that is, and nothing "
        "further."
    ),
    "clock": "monthly",
    "units": "effective_buckets",
    "estimator": (
        "eff_n = 1 / sum_i s_i^2 over the 25 Ken French ME x BE/ME buckets (reciprocal "
        "Herfindahl), from the monthly firm-count and average-market-cap blocks; "
        "s_i = n_i * c_i / sum_j n_j * c_j"
    ),
    "provenance": {
        "admission": "candidate",
        "charter": ".planning/phases/04-concentration-signal/04-CONCENTRATION-CHARTER-DRAFT.md",
        "charter_state": "DRAFT - NOT FROZEN, NOT SIGNED (v0.2, 2026-08-06)",
        "validation_bars_run": (
            "NONE. V1-V6 are registered in the draft and not one has been run; no look "
            "has been spent; there is no results sign-off and no derived maturity."
        ),
        "what_has_been_run": (
            "Construction only: results/concentration_gate.csv C1-C5 all pass (1200 "
            "months 1926-07..2026-06, 25/25 blocks agree, eff_n in [2.064, 10.627], "
            "shares sum to 1 within 4.4e-16, zero gaps), the panel is in "
            "data/processed/MANIFEST.csv, and tests/test_concentration.py holds "
            "concentration.build under assert_causal."
        ),
        "reading_source": (
            "RECOMPUTED by concentration.build() from data/processed/"
            "concentration_monthly.csv. There is no observations/concentration/ log, so "
            "unlike an admitted axis this reading is not a published point-in-time "
            "record and carries no available_at. Acceptable for a candidate, whose "
            "purpose is to be visible while undecided; NOT acceptable for an admitted "
            "axis, where the published record is the source of truth and a "
            "recomputation could silently disagree with it."
        ),
        "point_in_time": (
            "Excluded from --known-at replay: with no vintage log there is no honest "
            "answer to 'what would this axis have read as of instant T'."
        ),
        "no_trend_descriptor": (
            "No trend reading is emitted. The admitted emitters band a percentile change "
            "into rising/falling/flat with a threshold declared in their signed "
            "charters; concentration's charter is unsigned, and this layer owns no "
            "thresholds."
        ),
        "maturity_ceiling_registered": (
            "research, per the draft charter's header (resolution, coverage, "
            "restatement) - a ceiling registered before any look, not an earned tag."
        ),
    },
    "promotion_requires": [
        "Open item 1 - PROCEED on the respecified level measure, or DROP? The draft "
        "recommends PROCEED with the level primary; spread-only is already ruled DROP.",
        "Open item 2 - drop the rate descriptor (recommended DROP: it duplicates smb and "
        "reads only as a risk premium), or retain it behind the |corr(smb)| >= 0.90 bar?",
        "Open item 3 - authorise the fetch (recommended YES; already fetched and gated).",
        "Open item 4 - confirm V3 reported first, ledger status NONE, and the numeric "
        "bars as drafted (every number in the draft is marked [recommended - Adam to "
        "confirm/override]).",
        "Open item 5 - if R3 fires, close NOT MEASURABLE and record paid constituent "
        "data as a costed item rather than a phase?",
        "V3 (resolution) is the decisive one and its own charter expects it to fire: "
        "'R3 => close NOT MEASURABLE - expected: the Mag-7 question is seven names "
        "inside one bucket.' Under this reframe V3 is arguably the right question rather "
        "than a gate - the axis can be informative about bucket-level capital "
        "concentration while being blind to concentration inside the top bucket - but "
        "that is a ruling for the owner, not a reading this module may make.",
        "Then the standard chain: dated charter sign-off, one frozen validation script, "
        "one look, overnight cooling-off, separate dated results sign-off. Only then a "
        "derived maturity, an observations/concentration/ log, and a row in "
        "observation_history.EMITTERS.",
    ],
}


def build(panel=None):
    """Candidate-axis spine plus its informativeness columns, all causal.

    Registered under `assert_causal` in tests/test_informativeness_map.py. Everything
    added on top of `concentration.build` is expanding-only: the percentile it already
    computes, the tail mass derived from it, and the expanding share of history spent
    inside the declared tail.
    """
    if panel is None:
        panel = concentration.load_panel()
    df = concentration.build(panel).copy()
    p = df["eff_n_pctile"]
    # Re-derived from the same expanding percentile the descriptor publishes, imported
    # rather than reproduced, so the two cannot disagree.
    assert p.equals(expanding_percentile(df["eff_n"]).rename("eff_n_pctile"))
    tail_mass = p.where(p <= 0.5, 1.0 - p)
    inside = tail_mass <= 1.0 - CANDIDATE_THRESHOLD_PERCENTILE
    df["tail_mass"] = tail_mass
    df["inside_the_tail"] = inside
    df["share_inside_the_tail"] = inside.expanding().mean()
    return df


# ── the two dimensions, computed identically for every axis ───────────────────────

def _tail_mass(p):
    return None if p is None else round(min(p, 1.0 - p), 4)


def _spells(dates, flags):
    """Contiguous runs during which the axis sat inside its own declared tail.

    Backward-looking by construction: a run is closed by the next observation, never by
    a later one, and no run is compared with anything that happened after it.
    """
    out, run = [], None
    for date, flag in zip(dates, flags):
        if flag and run is None:
            run = {"from": date, "to": date, "length": 1}
        elif flag:
            run["to"] = date
            run["length"] += 1
        elif run is not None:
            out.append(run)
            run = None
    if run is not None:
        out.append(run)
    return out


def _median(values):
    ordered = sorted(values)
    n = len(ordered)
    if not n:
        return None
    mid = ordered[n // 2] if n % 2 else (ordered[n // 2 - 1] + ordered[n // 2]) / 2
    return int(mid) if float(mid).is_integer() else mid


def _history(dates, percentiles, threshold, grid):
    """When this axis has been inside its own declared tail — context for both
    dimensions, and the answer to 'when has this axis carried information at all'."""
    tail = round(1.0 - threshold, 4)
    flags = [p is not None and min(p, 1.0 - p) <= tail for p in percentiles]
    spells = _spells(dates, flags)
    trailing = 0
    for flag in reversed(flags):
        if flag:
            break
        trailing += 1
    return {
        "grid": grid,
        "observations": len(dates),
        "first_as_of": dates[0] if dates else None,
        "last_as_of": dates[-1] if dates else None,
        "share_inside_the_tail": round(sum(flags) / len(flags), 4) if flags else None,
        "spell_count": len(spells),
        "spell_median_length": _median([s["length"] for s in spells]),
        "spell_max_length": max((s["length"] for s in spells), default=None),
        "current_spell_length": spells[-1]["length"] if flags and flags[-1] else 0,
        "observations_since_inside_the_tail": trailing,
        "last_as_of_inside_the_tail": spells[-1]["to"] if spells else None,
        "spells": spells,
    }


def _persistence(record):
    """The axis's declared status episode, verbatim, plus one comparison.

    Not reimplemented: `stockbond_level0.build_record` already computes the run length
    and the median/longest of comparable episodes, and the record carries them. All that
    is added is the comparison of one against the other — and it is named for what it
    measures, not turned into a verdict word.
    """
    episodes = (record.get("extreme_conditions") or {}).get("episodes")
    if not episodes or episodes.get("current_length") is None:
        return None
    span = episodes.get("major_episode_median_max")
    return {
        "of_what": "the axis's own declared assumption status",
        "current_value": (record.get("assumption_state") or {}).get("status"),
        "current_length": episodes["current_length"],
        "current_start": episodes["current_start"],
        "length_units": episodes["length_units"],
        "comparable_definition": episodes["major_episode_definition"],
        "comparable_median_length": None if not span else span[0],
        "comparable_longest_length": None if not span else span[1],
        "at_or_beyond_the_comparable_median": (
            None if not span else episodes["current_length"] >= span[0]
        ),
        "informs": (
            "novelty AND standing, differently: an unchanged duration makes today's "
            "print unsurprising, and says nothing at all about whether the situation is "
            "serious. It is a fact here, never a rank."
        ),
    }


def _standing(status, percentile, basis, threshold, threshold_source, history, persistence):
    tail_mass = _tail_mass(percentile)
    tail = round(1.0 - threshold, 4)
    inside = None if tail_mass is None else tail_mass <= tail

    reads = []
    if status is None:
        reads.append(
            "this axis declares no status by design, so its standing is the reading "
            "itself"
        )
    else:
        clause = f"the declared status reads {status}"
        if persistence:
            clause += (
                f", and has since {persistence['current_start']} "
                f"({persistence['current_length']} {persistence['length_units']})"
            )
            if persistence["comparable_median_length"] is not None:
                clause += (
                    f"; comparable episodes ran "
                    f"{persistence['comparable_median_length']} at the median and "
                    f"{persistence['comparable_longest_length']} at the longest, so this "
                    f"one is "
                    + ("at or past the median - it is still not holding, and half of "
                       "comparable episodes ran longer"
                       if persistence["at_or_beyond_the_comparable_median"]
                       else "shorter than the median so far")
                )
        reads.append(clause)
    if tail_mass is not None:
        reads.append(
            f"the reading sits at the {al._pct(percentile)} of its own causal history, "
            f"with {tail_mass * 100:.1f}% of that history further out, "
            + ("INSIDE the tail this axis declares distinguishing"
               if inside else "outside the tail this axis declares distinguishing")
        )
    if history["current_spell_length"]:
        reads.append(
            f"it has been inside that tail for {history['current_spell_length']} "
            f"consecutive observations, against a median spell of "
            f"{history['spell_median_length']}"
        )

    return {
        "question": STANDING_QUESTION,
        "declared_status": status,
        "current_percentile": percentile,
        "basis": basis,
        "basis_meaning": al.BASIS_MEANING[basis],
        "tail_mass_beyond_reading": tail_mass,
        "threshold_percentile": threshold,
        "threshold_source": threshold_source,
        "tail_definition": (
            f"inside the tail means the causal expanding percentile is >= {threshold} "
            f"or <= {tail}, two-sided: an unusually low reading distinguishes now from "
            f"history exactly as much as an unusually high one"
        ),
        "inside_the_tail_now": inside,
        "reads": "; ".join(reads) + ".",
    }


def _novelty(trend, history, persistence):
    reads = []
    if persistence:
        reads.append(
            f"the declared status has not changed for {persistence['current_length']} "
            f"{persistence['length_units']} (since {persistence['current_start']}), so "
            f"today's print is not news"
        )
    if trend and trend.get("level_percentile_change") is not None:
        reads.append(
            f"its level percentile moved {trend['level_percentile_change']:+} over the "
            f"last {trend['lookback_observations']} observations ({trend['direction']})"
        )
    elif trend is None:
        reads.append("no trend descriptor is declared for this axis")
    if history["current_spell_length"]:
        reads.append(
            f"it has been inside its own tail for "
            f"{history['current_spell_length']} consecutive observations, so the "
            f"extremity itself is not new either"
        )
    elif history["last_as_of_inside_the_tail"]:
        reads.append(
            f"it last sat inside that tail at "
            f"{history['last_as_of_inside_the_tail']}, "
            f"{history['observations_since_inside_the_tail']} observations ago"
        )

    return {
        "question": NOVELTY_QUESTION,
        "trend": trend,
        "observations_since_the_declared_status_changed": (
            None if not persistence else persistence["current_length"]
        ),
        "observations_since_inside_the_tail": history["observations_since_inside_the_tail"],
        "current_spell_length_inside_the_tail": history["current_spell_length"],
        "carries_no_threshold": (
            "Novelty bands nothing. It reports counts and the direction the axis's own "
            "signed charter registered, so a low novelty reading can never be mistaken "
            "for a judgement that the axis does not matter."
        ),
        "reads": "; ".join(reads) + ".",
    }


def _informativeness(status, percentile, basis, threshold, threshold_source, history, record=None):
    persistence = _persistence(record) if record else None
    trend = record.get("trend") if record else None
    return {
        "standing": _standing(
            status, percentile, basis, threshold, threshold_source, history, persistence
        ),
        "novelty": _novelty(trend, history, persistence),
        "persistence": persistence,
        "history": history,
    }


# ── axis rows ─────────────────────────────────────────────────────────────────────

VINTAGE_GRID = (
    "available_at vintage grid - one observation per publication instant, which is what "
    "a consumer standing at that instant could have read"
)

PANEL_GRID = (
    "the monthly panel's own grid - a recomputation, NOT a point-in-time vintage log; "
    "no observations/concentration/ history exists"
)


def _log_series(signal, known_at):
    log = read_log(log_path(signal))
    if known_at is not None:
        log = [r for r in log if r["available_at"] <= known_at]
    view = current_view(log)
    return ([r["as_of"] for r in view],
            [r["rarity"]["level_percentile"] for r in view])


def _admitted_axis(record, known_at):
    signal = record["signal"]
    status, derivation = al.status_of(record)
    threshold = (record.get("extreme_conditions") or {}).get("threshold_percentile")
    if threshold is None:
        raise ValueError(
            f"{signal}: declares no extreme_conditions.threshold_percentile, so the tail "
            f"it considers distinguishing is undeclared. This layer will not pick one — "
            f"declare it in the signal's Level-0 emitter."
        )
    dates, percentiles = _log_series(signal, known_at)
    reading, rarity = record["reading"], record["rarity"]
    return {
        "axis": signal,
        "kind": "context_axis" if al._is_context_axis(record) else "assumption_monitor",
        "admission": "admitted",
        "assumption": record["assumption_monitored"],
        "status": status,
        "status_derivation": derivation,
        "as_of": record["as_of"],
        "available_at": record["available_at"],
        "clock": record["clock"],
        "reading": {
            "value": reading["value"],
            "units": reading["units"],
            "estimator": reading["estimator"],
            "context_band": reading.get("context_band"),
            "undefined_reason": reading.get("undefined_reason"),
            "secondary_readings": reading.get("secondary_readings", []),
        },
        "rarity": {
            "level_percentile": rarity["level_percentile"],
            "basis": rarity["basis"],
            "basis_meaning": al.BASIS_MEANING[rarity["basis"]],
            "window": rarity["window"],
            "calibration": rarity.get("calibration"),
        },
        "maturity": record["maturity"],
        "maturity_note": al.MATURITY_NOTE.get(record["maturity"], record["maturity"]),
        "provenance": {
            "admission": "admitted",
            "reading_source": (
                "observations/<signal>/history.ndjson via "
                "observation_history.current_view - the published point-in-time record, "
                "never a recomputation"
            ),
            "point_in_time": "included in --known-at replay; filtered on available_at",
        },
        "informativeness": _informativeness(
            status,
            rarity["level_percentile"],
            rarity["basis"],
            threshold,
            "the axis's own record: extreme_conditions.threshold_percentile",
            _history(dates, percentiles, threshold, VINTAGE_GRID),
            record=record,
        ),
    }


def candidate_axes():
    """The candidate rows. Empty under a point-in-time replay, by construction."""
    df = build()
    d = df.dropna(subset=["eff_n", "eff_n_pctile"])
    latest = d.iloc[-1]
    dates = [ts.date().isoformat() for ts in d.index]
    percentiles = [round(float(x), 4) for x in d["eff_n_pctile"]]
    spec = CONCENTRATION_AXIS
    z = latest["eff_n_z"]
    history = _history(dates, percentiles, CANDIDATE_THRESHOLD_PERCENTILE, PANEL_GRID)
    return [{
        "axis": spec["axis"],
        "kind": spec["kind"],
        "admission": "candidate",
        "assumption": spec["assumption"],
        "status": None,
        "status_derivation": None,
        "as_of": dates[-1],
        "available_at": None,
        "clock": spec["clock"],
        "reading": {
            "value": round(float(latest["eff_n"]), 4),
            "units": spec["units"],
            "estimator": spec["estimator"],
            "context_band": None,
            "undefined_reason": None,
            "secondary_readings": [
                {
                    "name": "top_share",
                    "value": round(float(latest["top_share"]), 4),
                    "units": "share_of_index_capital",
                    "estimator": "the largest of the 25 buckets' share of total bucket capital",
                },
                {
                    "name": "eff_n_z",
                    "value": None if z != z else round(float(z), 4),
                    "units": "standard_deviations",
                    "estimator": "causal expanding-window standardization of eff_n, minimum 120 months",
                    "undefined_reason": None if z == z else "inside the expanding-z burn-in",
                },
            ],
        },
        "rarity": {
            "level_percentile": percentiles[-1],
            "basis": "expanding",
            "basis_meaning": al.BASIS_MEANING["expanding"],
            "window": None,
            "calibration": (
                "causal expanding percentile of eff_n over 1926-07..2026-06. A LOW "
                "percentile means FEW effective buckets, i.e. capital unusually "
                "concentrated - the reading is not signed so that high reads bad."
            ),
        },
        "maturity": None,
        "maturity_note": (
            "NO MATURITY: not admitted. The charter is unsigned and no validation bar "
            "has run, so no maturity has been derived and none may be inferred from this "
            "row. The registered ceiling, if it is ever admitted, is `research`."
        ),
        "provenance": spec["provenance"],
        "promotion_requires": spec["promotion_requires"],
        "informativeness": _informativeness(
            None,
            percentiles[-1],
            "expanding",
            CANDIDATE_THRESHOLD_PERCENTILE,
            (
                "declared here for the candidate at the same value the two admitted "
                "records declare (0.95), because no signed charter declares one for this "
                "axis. Disclosed as a presentation convention, not a registered bar."
            ),
            history,
        ),
    }]


def build_map(known_at=None):
    ledger = al.build_ledger(known_at)
    records = {r["signal"]: r for r in ledger["level0_state_vector"]}
    # Alphabetical: deterministic, and deliberately NOT a precedence. Nothing here is
    # sequenced by standing or by novelty — an axis with extreme standing and zero novelty
    # must not be sorted away from the top of the page.
    admitted = [_admitted_axis(records[s], known_at) for s in sorted(records)]
    # A candidate has no vintage log, so a point-in-time replay cannot include it
    # honestly. Dropping it is the correct answer, not a limitation to work around.
    candidates = [] if known_at is not None else candidate_axes()
    return {
        "spec_version": MAP_SPEC_VERSION,
        "known_at": known_at,
        "source": (
            "admitted axes: observations/<signal>/history.ndjson via "
            "observation_history.current_view. candidate axes: recomputed from the "
            "committed monthly panel, no observation log exists."
        ),
        "axis_sequence": (
            "alphabetical by axis name - deterministic and deliberately not a "
            "precedence. Axes are never sequenced, grouped or styled by standing or by "
            "novelty; the only structural split is admitted versus candidate, which is "
            "about evidence, not about either dimension."
        ),
        "informativeness_definition": INFORMATIVENESS_DEFINITION,
        "reading_notes": READING_NOTES,
        "admitted_axes": admitted,
        "candidate_axes": candidates,
        "assumption_ledger": ledger["level1_assumption_ledger"],
        "level2_context": ledger["level2_context"],
    }


# ── rendering ─────────────────────────────────────────────────────────────────────
# Shares the ledger's visual system deliberately: same helpers, same badges, so the
# ledger section inside this page looks identical to the standalone artifact. Two new
# elements only — the candidate treatment, which must be impossible to miss, and the
# STANDING / NOVELTY pair, which are given identical prominence in every axis card.

_BADGE_CANDIDATE = (
    "display:inline-block;padding:1px 8px;border-radius:3px;background:#f4eef6;"
    "border:2px dashed #7a4a86;font-weight:bold"
)
_CANDIDATE_CARD = (
    "border:2px dashed #7a4a86;border-radius:4px;padding:14px 18px;margin:0 0 18px 0;"
    "background:#fdfaFe"
)
# One chip style for BOTH dimensions. Styling either differently would rank them.
_CHIP = (
    "display:inline-block;padding:2px 9px;border-radius:3px;border:2px solid #1a1a1a;"
    "font-weight:bold;font-variant:small-caps;letter-spacing:0.04em;min-width:64px;"
    "text-align:center"
)


def _esc(value):
    return al._esc(value)


def _row(label, value, style=""):
    return al._row(label, value, style)


def _dimension_html(label, text):
    return (
        '<p style="margin:0 0 6px 0">'
        f'<span style="{_CHIP}">{_esc(label)}</span>&nbsp;{_esc(text)}</p>'
    )


def _history_text(h):
    parts = [
        f"{h['observations']} observations, {h['first_as_of']} to {h['last_as_of']}",
        f"inside its own tail on {h['share_inside_the_tail'] * 100:.1f}% of them",
        f"{h['spell_count']} distinct spells, median {h['spell_median_length']} and "
        f"longest {h['spell_max_length']} observations",
    ]
    if h["current_spell_length"]:
        parts.append(f"inside it now, {h['current_spell_length']} observations so far")
    elif h["last_as_of_inside_the_tail"]:
        parts.append(
            f"last inside it {h['observations_since_inside_the_tail']} observations ago, "
            f"at {h['last_as_of_inside_the_tail']}"
        )
    return "; ".join(parts)


def _axis_html(axis):
    candidate = axis["admission"] == "candidate"
    info = axis["informativeness"]
    standing, novelty = info["standing"], info["novelty"]
    rows = []

    if candidate:
        rows.append(_row(
            "not admitted",
            "candidate axis: the charter is unsigned and NO validation bar has run. "
            "Rendered so it is visible while undecided, not as evidence.",
        ))
    rows += [
        _row("reading", al._reading_text(axis["reading"]), al._MONO),
        _row("estimator", axis["reading"]["estimator"], al._MUTED),
        _row("rarity", al._rarity_text(axis["rarity"])),
    ]
    for sec in axis["reading"]["secondary_readings"]:
        text = (
            f"undefined: {sec.get('undefined_reason')}" if sec["value"] is None
            else f"{sec['value']} {sec['units']}"
        )
        rows.append(_row(sec["name"], f"{text}  [{sec['estimator']}]"))
    if axis["rarity"]["calibration"]:
        rows.append(_row("calibration", axis["rarity"]["calibration"], al._MUTED))
    rows.append(_row(
        "tail mass",
        f"{standing['tail_mass_beyond_reading'] * 100:.1f}% of its own history sits "
        f"further out than today  [{standing['tail_definition']}]",
    ))
    trend = al._trend_text(novelty["trend"])
    if trend:
        rows.append(_row("trend", trend))
    if info["persistence"]:
        p = info["persistence"]
        rows.append(_row(
            "persistence",
            f"{p['current_value']} for {p['current_length']} {p['length_units']} since "
            f"{p['current_start']}; comparable episodes ({p['comparable_definition']}) ran "
            f"{p['comparable_median_length']} at the median and "
            f"{p['comparable_longest_length']} at the longest. {p['informs']}",
        ))
    rows.append(_row("when informative", _history_text(info["history"])))

    if axis["status"] is not None:
        rows.append(_row("ledger status", axis["status"]))
        rows.append(_row("derived by", axis["status_derivation"], al._MUTED))
    else:
        rows.append(_row(
            "ledger status",
            "none by design: this axis has no mechanical boundary, so it carries a "
            "reading and no status",
            al._MUTED,
        ))

    badge = (
        _BADGE_CANDIDATE if candidate
        else al._BADGE_RESEARCH if axis["maturity"] == "research"
        else al._BADGE_PROD
    )
    rows.append(
        f'<tr><td style="{al._LABEL};padding:3px 14px 3px 0;vertical-align:top">maturity</td>'
        f'<td style="padding:3px 0"><span style="{badge}">'
        f'{_esc(axis["maturity"] or "candidate - no maturity")}</span> '
        f'<span style="{al._MUTED}">{_esc(axis["maturity_note"])}</span></td></tr>'
    )
    rows.append(_row("reading source", axis["provenance"]["reading_source"], al._MUTED))
    if candidate:
        rows.append(_row("what has run", axis["provenance"]["what_has_been_run"], al._MUTED))
        rows.append(_row("bars run", axis["provenance"]["validation_bars_run"], al._MUTED))
        rows.append(_row("to promote", " | ".join(axis["promotion_requires"]), al._MUTED))
    dated = f"as_of {axis['as_of']}"
    dated += (
        f"  |  knowable {axis['available_at']}" if axis["available_at"]
        else "  |  no available_at: no vintage log"
    )
    rows.append(_row("dated", dated, al._MONO))

    card = _CANDIDATE_CARD if candidate else al._CARD
    return (
        f'<div style="{card}">'
        f'<p style="margin:0 0 8px 0;font-weight:bold">{_esc(axis["axis"])}'
        + (f' <span style="{_BADGE_CANDIDATE}">CANDIDATE</span>' if candidate else "")
        + "</p>"
        + _dimension_html("standing", standing["reads"])
        + _dimension_html("novelty", novelty["reads"])
        + f'<p style="margin:6px 0 10px 0;{al._MUTED}">{_esc(axis["assumption"])}</p>'
        '<table style="border-collapse:collapse;width:100%">' + "".join(rows) + "</table>"
        "</div>"
    )


def render_html(imap):
    axes = imap["admitted_axes"]
    dates = sorted({a["as_of"] for a in axes + imap["candidate_axes"]})
    span = dates[-1] if len(dates) == 1 else f"{dates[0]} to {dates[-1]}"
    d = imap["informativeness_definition"]
    notes = "".join(f"<li>{_esc(n)}</li>" for n in imap["reading_notes"])
    ledger = "".join(al._entry_html(e) for e in imap["assumption_ledger"])
    candidates = "".join(_axis_html(a) for a in imap["candidate_axes"])
    return (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        "<title>Informativeness map</title></head>"
        f'<body style="{al._BODY}">'
        '<h1 style="margin:0 0 2px 0;font-size:20px">Informativeness map</h1>'
        f'<p style="margin:0 0 14px 0;{al._MUTED}">{_esc(d["question_each_axis_answers"])} '
        f"Observed on {_esc(span)}. {len(axes)} admitted "
        f"{'axis' if len(axes) == 1 else 'axes'}, "
        f"{len(imap['candidate_axes'])} candidate.</p>"
        f'<div style="{al._CARD};background:#fafafa">'
        f'<p style="{al._LABEL};margin:0 0 6px 0">what informative means here</p>'
        f'<p style="margin:0 0 8px 0">{_esc(d["informative_means"])}</p>'
        f'<p style="margin:0 0 8px 0"><b>{_esc(d["two_dimensions_never_merged"])}</b></p>'
        f'<p style="margin:0 0 8px 0"><span style="{_CHIP}">standing</span>&nbsp;'
        f'{_esc(d["standing"])}</p>'
        f'<p style="margin:0 0 8px 0"><span style="{_CHIP}">novelty</span>&nbsp;'
        f'{_esc(d["novelty"])}</p>'
        f'<p style="margin:0 0 8px 0">{_esc(d["persistence_is_context_for_both"])}</p>'
        f'<p style="margin:0 0 8px 0;{al._MUTED}">{_esc(d["owns_no_threshold"])}</p>'
        f'<p style="margin:0 0 8px 0;{al._MUTED}">{_esc(d["caveat"])}</p>'
        f'<p style="margin:0;{al._MUTED}">{_esc(d["registered_constraint"])}</p></div>'
        f'<div style="{al._CARD};background:#fafafa">'
        f'<p style="{al._LABEL};margin:0 0 6px 0">how to read this</p>'
        f'<ul style="margin:0;padding-left:20px">{notes}</ul>'
        f'<p style="margin:8px 0 0 0;{al._MUTED}">{_esc(imap["axis_sequence"])}</p></div>'
        '<h2 style="font-size:16px;margin:22px 0 10px 0">Admitted axes</h2>'
        + "".join(_axis_html(a) for a in axes)
        + (
            '<h2 style="font-size:16px;margin:22px 0 4px 0">Candidate axes</h2>'
            f'<p style="margin:0 0 10px 0;{al._MUTED}">Built and construction-gated, '
            "charter UNSIGNED, no validation bar run. Not admitted, not validated, and "
            "not comparable with the axes above.</p>" + candidates
            if candidates else ""
        )
        + '<h2 style="font-size:16px;margin:22px 0 4px 0">Assumption ledger</h2>'
        f'<p style="margin:0 0 10px 0;{al._MUTED}">The monitored market assumptions, '
        "unchanged: one row, because only one quantity here has a mechanical boundary. "
        "A status is an observation of the market, never an instruction.</p>" + ledger
        + f'<div style="{al._CARD};background:#fafafa"><p style="{al._LABEL};margin:0 0 6px 0">'
        f'level 2</p><p style="margin:0;{al._MUTED}">{_esc(al.LEVEL2_SEAM)}</p></div>'
        f'<p style="{al._MUTED};margin:0">Built from {_esc(imap["source"])} '
        "This layer presents measurements and their historical context, and goes no "
        "further.</p>"
        "</body></html>"
    )


def render_text(imap):
    d = imap["informativeness_definition"]
    lines = ["INFORMATIVENESS MAP", f"  {d['question_each_axis_answers']}"]
    for label, group in (("ADMITTED", imap["admitted_axes"]),
                         ("CANDIDATE", imap["candidate_axes"])):
        for axis in group:
            info = axis["informativeness"]
            lines.append("")
            lines.append(f"  {label}: {axis['axis']}  ({axis['clock']} clock)")
            lines.append(f"    STANDING:  {info['standing']['reads']}")
            lines.append(f"    NOVELTY:   {info['novelty']['reads']}")
            lines.append(f"    reading:   {al._reading_text(axis['reading'])}")
            lines.append(f"    rarity:    {al._rarity_text(axis['rarity'])}")
            lines.append(f"    history:   {_history_text(info['history'])}")
            lines.append(f"    maturity:  {axis['maturity_note']}")
    lines.append("")
    lines.append(f"  ASSUMPTION LEDGER: {len(imap['assumption_ledger'])} row(s)")
    for entry in imap["assumption_ledger"]:
        lines.append(f"    {entry['kind']}: {entry['assumption'][:70]}")
        lines.append(f"      status: {al._status_text(entry)}")
    lines.append("")
    lines.append("  LEVEL 2 (joint rarity + historical analogues): not built. "
                 "Seam: assumption_ledger.level2_context().")
    return "\n".join(lines)


def write_artifacts(imap, json_out=JSON_OUT, html_out=HTML_OUT):
    json_out.write_text(json.dumps(imap, indent=2) + "\n", encoding="utf-8", newline="\n")
    html_out.write_text(render_html(imap), encoding="utf-8", newline="\n")
    return json_out, html_out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument(
        "--known-at", default=None,
        help="ISO instant; keep only observations with available_at <= this "
             "(point-in-time replay). Candidate axes are excluded: they have no vintage "
             "log. Default: everything in the log.",
    )
    args = ap.parse_args()

    imap = build_map(args.known_at)
    print(render_text(imap))
    for path in write_artifacts(imap):
        print(f"\nwrote {path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
