"""Assumption ledger — the presentation layer (Level 0 + Level 1). Phase 10, plan 10-01.

The state vector is the substrate; the assumption ledger is the product.

LEVEL 0 (the state vector) is read VERBATIM from `observations/<signal>/history.ndjson`
through `observation_history.current_view()` — the contract-shaped source of truth.
Nothing is recomputed here and the `results/*.csv` spines are never read directly: a
presentation layer that recomputes can present a number that disagrees with the
published record, which is the one failure this layer must not have.

LEVEL 1 (the ledger) is a VIEW of those records, never new information:

- The assumption text is the record's own `assumption_monitored`. This module does not
  paraphrase what a signal monitors.
- The {intact | under_test | violated} status is the record's own
  `assumption_state.status`, and its `derivation` — the pre-committed rule — travels
  beside it always. This module owns NO thresholds. A signal that monitors an assumption
  but declares no mapping raises: inventing a cut-off in the presentation layer would
  smuggle an undeclared decision rule into the one place designed to have none.
- A signal whose `assumption_monitored` opens with "N/A because ..." — the contract's own
  discriminator for a context axis — is carried as a READING WITH NO STATUS. That is what
  the volatility charter registered: "There is deliberately no {intact | under-test |
  violated} status field — introducing one would re-import the CALM/STRESSED state the
  reframe exists to remove. The ledger carries volatility as a reading."

Status is an OBSERVATION, never an instruction. There is no composite number, no
one-word verdict and no ranking between signals. Today's read is exactly why: volatility
sits at the 69.7th percentile while the bond-hedge assumption reads violated. Two
readings that disagree carry information neither one carries alone, and any collapse of
them destroys it.

LEVEL 2 (regime relevance) is NOT built — see `level2_context()` for the seam.

The artifacts are deterministic functions of the observation logs: no wall-clock stamp,
so `tests/test_assumption_ledger.py` can assert the committed artifact still equals a
fresh build. A report that silently disagrees with its producer is a failure this repo
has already had once (`results/vol_descriptors.csv`, 2026-08-06).

Run:  python scripts/assumption_ledger.py
"""

from __future__ import annotations

import argparse
import html
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from observation_history import EMITTERS, current_view, log_path, read_log
from signal_output_schema import validate

JSON_OUT = ROOT / "results" / "assumption_ledger.json"
HTML_OUT = ROOT / "results" / "assumption_ledger.html"

LEDGER_SPEC_VERSION = "1.0"

MATURITY_NOTE = {
    "production": "production: the full validation chain is complete and dated-signed-off",
    "research": (
        "RESEARCH GRADE, NOT PRODUCTION: a registered scope limitation or incomplete "
        "evidence base is unresolved; read as provisional"
    ),
}

# A percentile without its reference distribution is not a number. The three bases are
# not interchangeable, so the definition is carried next to every figure that uses it.
# ASCII only in these shared strings: they render to both an HTML page and a Windows
# console, and a mojibake dash in a dry-run print is a needless papercut.
BASIS_MEANING = {
    "expanding": "ranked only against the signal's own history up to that date (causal)",
    "trailing_fixed": "ranked within a fixed trailing window (causal; the window is a free parameter)",
    "full_sample": "ranked against the whole sample INCLUDING later data, so it leaks; research only",
}

READING_NOTES = [
    "Each row is one monitored market assumption and the sensor evidence behind it. "
    "A status is an observation of the market, never an instruction.",
    "The readings are never combined into one number and never ranked against each "
    "other. Disagreement between them is information, not a defect to resolve.",
    "Maturity is the only behaviour-bearing field in the underlying records. A research "
    "reading is not a production-grade one and is labelled as such wherever it appears.",
    "Values, units and estimators are carried verbatim from the observation record. "
    "Nothing is converted or re-derived here.",
]

LEVEL2_SEAM = (
    "Level 2 (regime relevance) is NOT built. It attaches here: joint rarity of the "
    "preserved state vector (Mahalanobis / turbulence distance) plus nearest-neighbour "
    "historical analogues of the CONFIGURATION, both forecasting-free. The inputs are "
    "already present: level0_state_vector is the live vector and "
    "observations/<signal>/history.ndjson is its full point-in-time history. A Level-2 "
    "lens is computed FROM the vector and sits BESIDE it; it never replaces the "
    "per-signal readings and is never a rank of good or bad."
)


def level2_context(state_vector=None):
    """SEAM — Level 2 is deliberately unimplemented.

    To implement: return {"joint_rarity": {...}, "analogues": [...]} built from
    `state_vector` plus the full observation histories, and render it as a lens beside
    the ledger. The statistical choices it needs — covariance window, shrinkage, the
    degenerate-covariance problem when only two correlated signals are admitted, the
    analogue distance metric and its causality — are the substance of the work and are
    not defaulted here.
    """
    return {"built": False, "seam": LEVEL2_SEAM}


def _is_context_axis(record):
    """The contract's own discriminator: `assumption_monitored` on a context-axis signal
    "must explicitly say 'N/A because ...'" (market-observation-v1.schema.json)."""
    return record["assumption_monitored"].lstrip().upper().startswith("N/A")


def status_of(record):
    signal = record["signal"]
    state = record.get("assumption_state")

    if _is_context_axis(record):
        if state:
            raise ValueError(
                f"{signal}: declares itself a context axis ('N/A because ...') yet carries "
                f"assumption_state. A context axis with a status re-imports the latent state "
                f"the reframe removed — fix the emitter, not the ledger."
            )
        return None, None

    if not state:
        raise ValueError(
            f"{signal}: monitors {record['assumption_monitored']!r} but declares no "
            f"assumption_state, so no {{intact | under_test | violated}} mapping exists. "
            f"That mapping belongs in the signal's charter and its Level-0 emitter, "
            f"pre-committed and dated. The presentation layer will not invent a threshold."
        )
    return state["status"], state["derivation"]


def latest_records(known_at=None):
    """The freshest record per admitted signal that a consumer at `known_at` could hold.

    `known_at` filters on `available_at` FIRST and then takes the current view, which is
    the honest point-in-time query (`observation_history.current_view`). Default None =
    everything in the log.

    `EMITTERS` is the admission registry, so a signal without a published observation
    history cannot reach the ledger by accident — valuation is deliberately absent while
    R9 is open, and credit's one-look is unspent.
    """
    out = {}
    for signal in sorted(EMITTERS):
        log = read_log(log_path(signal))
        if known_at is not None:
            log = [r for r in log if r["available_at"] <= known_at]
        view = current_view(log)
        if not view:
            raise ValueError(f"{signal}: no observation available at {known_at}")
        out[signal] = view[-1]
    return out


def _evidence(record):
    reading, rarity, assessment = record["reading"], record["rarity"], record["assessment"]
    return {
        "signal": record["signal"],
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
            "basis_meaning": BASIS_MEANING[rarity["basis"]],
            "window": rarity["window"],
            "calibration": rarity.get("calibration"),
            "secondary_percentiles": rarity.get("secondary_percentiles", []),
        },
        "trend": record.get("trend"),
        "persistence": (record.get("extreme_conditions") or {}).get("episodes"),
        "confidence": {
            "mechanism_gate": assessment["mechanism"],
            "measurement_validity": assessment["measurement_validity"],
            "investment_usefulness": assessment["investment_usefulness"],
            "evidence_maturity": assessment["evidence_maturity"],
        },
        "maturity": record["maturity"],
        "maturity_note": MATURITY_NOTE.get(record["maturity"], record["maturity"]),
        "cross_signal_relationships": record.get("cross_signal_relationships", []),
    }


def build_ledger(known_at=None):
    records = latest_records(known_at)

    # Validated on the way IN as well as out: a record that cannot pass the closed
    # allowlist must not be rendered, and the log is not assumed clean because it was
    # clean when written.
    for record in records.values():
        validate(record)

    groups = {}
    for signal in sorted(records):
        record = records[signal]
        key = record["assumption_monitored"]
        status, derivation = status_of(record)
        entry = groups.setdefault(key, {
            "assumption": key,
            "kind": "context_axis" if _is_context_axis(record) else "assumption_monitor",
            "status": status,
            "status_derivation": derivation,
            "signals": [],
            "evidence": [],
        })
        if entry["status"] != status:
            # Two signals on one assumption reading different statuses is a real finding,
            # not something to average or arbitrate. D-11 forbids letting either win.
            raise ValueError(
                f"{key!r}: signals disagree on status "
                f"({entry['signals']} say {entry['status']!r}, {signal} says {status!r}). "
                f"Resolve it in the signals' charters, not in the rendering."
            )
        entry["signals"].append(signal)
        entry["evidence"].append(_evidence(record))

    return {
        "spec_version": LEDGER_SPEC_VERSION,
        "known_at": known_at,
        "source": "observations/<signal>/history.ndjson via observation_history.current_view",
        "reading_notes": READING_NOTES,
        # Sorted by assumption text: deterministic, and deliberately not a precedence.
        "level1_assumption_ledger": [groups[k] for k in sorted(groups)],
        "level0_state_vector": [records[s] for s in sorted(records)],
        "level2_context": level2_context(),
    }


# ── rendering ────────────────────────────────────────────────────────────────────
# Follows the vol_read.py idiom: question-led, plain language, teaches how to view the
# number rather than announcing a conclusion.

def _pct(p):
    if p is None:
        return "not available"
    # "52.1th" is jarring; a decimal ordinal takes the suffix of its final digit.
    shown = f"{p * 100:.1f}"
    return shown + {"1": "st", "2": "nd", "3": "rd"}.get(shown[-1], "th") + " percentile"


def _rarity_text(rarity):
    window = rarity["window"]
    scope = rarity["basis"] if window is None else f"{rarity['basis']}, {window} observations"
    return f"{_pct(rarity['level_percentile'])}  [{scope}: {rarity['basis_meaning']}]"


def _reading_text(reading):
    if reading["value"] is None:
        return f"undefined: {reading['undefined_reason']}"
    band = f"  ({reading['context_band']})" if reading.get("context_band") else ""
    return f"{reading['value']} {reading['units']}{band}"


def _trend_text(trend):
    if not trend or trend.get("level_percentile_change") is None:
        return None
    return (
        f"{trend['direction']}: level percentile moved "
        f"{trend['level_percentile_change']:+} over "
        f"{trend['lookback_observations']} observations"
    )


def _persistence_text(ep):
    if not ep or ep.get("current_length") is None:
        return None
    out = f"{ep['current_length']} {ep['length_units']} so far, since {ep['current_start']}"
    span = ep.get("major_episode_median_max")
    if span:
        out += (
            f"; comparable episodes ({ep['major_episode_definition']}) ran "
            f"{span[0]} at the median and {span[1]} at the longest"
        )
    return out


def _status_text(entry):
    if entry["kind"] == "context_axis":
        return "no status by design: a context axis carries a reading, not a status"
    return entry["status"]


def render_text(ledger):
    lines = ["ASSUMPTION LEDGER"]
    for entry in ledger["level1_assumption_ledger"]:
        lines.append("")
        lines.append(f"  ASSUMPTION: {entry['assumption']}")
        lines.append(f"    status:   {_status_text(entry)}")
        for ev in entry["evidence"]:
            lines.append(f"    sensor:   {ev['signal']}  ({ev['clock']} clock)")
            lines.append(f"      reading:  {_reading_text(ev['reading'])}")
            lines.append(f"      rarity:   {_rarity_text(ev['rarity'])}")
            trend = _trend_text(ev["trend"])
            if trend:
                lines.append(f"      trend:    {trend}")
            persistence = _persistence_text(ev["persistence"])
            if persistence:
                lines.append(f"      lasting:  {persistence}")
            c = ev["confidence"]
            lines.append(
                f"      gate:     mechanism {c['mechanism_gate']}  |  measurement validity "
                f"{c['measurement_validity']}  |  usefulness {c['investment_usefulness']}  |  "
                f"evidence maturity {c['evidence_maturity']}"
            )
            lines.append(f"      maturity: {ev['maturity_note']}")
            lines.append(f"      dated:    as_of {ev['as_of']}  |  knowable {ev['available_at']}")
    lines.append("")
    lines.append("  LEVEL 2 (joint rarity + historical analogues): not built. "
                 "Seam: assumption_ledger.level2_context().")
    return "\n".join(lines)


_BODY = "font-family:Helvetica,Arial,sans-serif;color:#1a1a1a;line-height:1.45;max-width:820px"
_CARD = "border:1px solid #d8d8d8;border-radius:4px;padding:14px 18px;margin:0 0 18px 0"
_LABEL = "color:#666;font-variant:small-caps;letter-spacing:0.04em"
_MUTED = "color:#666"
_MONO = "font-family:Consolas,Menlo,monospace"
_PILL_MONITOR = "display:inline-block;padding:2px 9px;border-radius:3px;border:2px solid #1a1a1a;font-weight:bold"
_PILL_AXIS = "display:inline-block;padding:2px 9px;border-radius:3px;border:1px dashed #999;color:#555"
_BADGE_PROD = "display:inline-block;padding:1px 8px;border-radius:3px;background:#eef3ee;border:1px solid #7a9a7a"
_BADGE_RESEARCH = "display:inline-block;padding:1px 8px;border-radius:3px;background:#fdf3e3;border:2px solid #c98a1e;font-weight:bold"


def _esc(value):
    return html.escape(str(value))


def _row(label, value, style=""):
    return (
        f'<tr><td style="{_LABEL};padding:3px 14px 3px 0;vertical-align:top;white-space:nowrap">'
        f"{_esc(label)}</td>"
        f'<td style="padding:3px 0;vertical-align:top;{style}">{_esc(value)}</td></tr>'
    )


def _evidence_html(ev):
    c = ev["confidence"]
    badge = _BADGE_RESEARCH if ev["maturity"] == "research" else _BADGE_PROD
    rows = [
        _row("sensor", f"{ev['signal']}  ({ev['clock']} clock)", _MONO),
        _row("reading", _reading_text(ev["reading"])),
        _row("estimator", ev["reading"]["estimator"], _MUTED),
        _row("rarity", _rarity_text(ev["rarity"])),
    ]
    for sec in ev["reading"]["secondary_readings"]:
        text = (
            f"undefined: {sec['undefined_reason']}" if sec["value"] is None
            else f"{sec['value']} {sec['units']}"
        )
        rows.append(_row(sec["name"], f"{text}  [{sec['estimator']}]"))
    for sec in ev["rarity"]["secondary_percentiles"]:
        rows.append(_row(f"{sec['name']} rarity", f"{_pct(sec['level_percentile'])} ({sec['basis']})"))
    if ev["rarity"]["calibration"]:
        rows.append(_row("calibration", ev["rarity"]["calibration"], _MUTED))
    trend = _trend_text(ev["trend"])
    if trend:
        rows.append(_row("trend", trend))
    persistence = _persistence_text(ev["persistence"])
    if persistence:
        rows.append(_row("lasting", persistence))
    rows.append(_row(
        "confidence",
        f"mechanism gate {c['mechanism_gate']}  |  measurement validity "
        f"{c['measurement_validity']}  |  usefulness {c['investment_usefulness']}  |  "
        f"evidence maturity {c['evidence_maturity']}",
    ))
    rows.append(
        f'<tr><td style="{_LABEL};padding:3px 14px 3px 0;vertical-align:top">maturity</td>'
        f'<td style="padding:3px 0"><span style="{badge}">{_esc(ev["maturity"])}</span> '
        f'<span style="{_MUTED}">{_esc(ev["maturity_note"])}</span></td></tr>'
    )
    rows.append(_row("dated", f"as_of {ev['as_of']}  |  knowable {ev['available_at']}", _MONO))
    for note in ev["cross_signal_relationships"]:
        rows.append(_row("read with", note, _MUTED))
    return '<table style="border-collapse:collapse;width:100%">' + "".join(rows) + "</table>"


def _entry_html(entry):
    monitor = entry["kind"] == "assumption_monitor"
    pill = _PILL_MONITOR if monitor else _PILL_AXIS
    parts = [
        f'<div style="{_CARD}">',
        f'<p style="margin:0 0 8px 0;font-weight:bold">{_esc(entry["assumption"])}</p>',
        f'<p style="margin:0 0 4px 0"><span style="{_LABEL}">status</span>&nbsp;'
        f'<span style="{pill}">{_esc(_status_text(entry))}</span></p>',
    ]
    if entry["status_derivation"]:
        parts.append(
            f'<p style="margin:0 0 10px 0;{_MUTED}">'
            f'<span style="{_LABEL}">derived by</span> {_esc(entry["status_derivation"])}</p>'
        )
    else:
        parts.append(
            f'<p style="margin:0 0 10px 0;{_MUTED}">This signal monitors no market assumption, '
            f"so it carries no status. It is the axis the other readings are read against.</p>"
        )
    parts.extend(_evidence_html(ev) for ev in entry["evidence"])
    parts.append("</div>")
    return "".join(parts)


def render_html(ledger):
    entries = ledger["level1_assumption_ledger"]
    dates = sorted({ev["as_of"] for e in entries for ev in e["evidence"]})
    span = dates[-1] if len(dates) == 1 else f"{dates[0]} to {dates[-1]}"
    notes = "".join(f"<li>{_esc(n)}</li>" for n in ledger["reading_notes"])
    return (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        "<title>Assumption ledger</title></head>"
        f'<body style="{_BODY}">'
        '<h1 style="margin:0 0 2px 0;font-size:20px">Assumption ledger</h1>'
        f'<p style="margin:0 0 14px 0;{_MUTED}">Monitored market assumptions as observed '
        f"on {_esc(span)}. {len(entries)} entries.</p>"
        f'<div style="{_CARD};background:#fafafa"><p style="{_LABEL};margin:0 0 6px 0">'
        "how to read this</p>"
        f'<ul style="margin:0;padding-left:20px">{notes}</ul></div>'
        + "".join(_entry_html(e) for e in entries)
        + f'<div style="{_CARD};background:#fafafa"><p style="{_LABEL};margin:0 0 6px 0">'
        f'level 2</p><p style="margin:0;{_MUTED}">{_esc(LEVEL2_SEAM)}</p></div>'
        f'<p style="{_MUTED};margin:0">Built from {_esc(ledger["source"])}. '
        "This layer presents measurements and their historical context, and goes no further.</p>"
        "</body></html>"
    )


def write_artifacts(ledger, json_out=JSON_OUT, html_out=HTML_OUT):
    json_out.write_text(json.dumps(ledger, indent=2) + "\n", encoding="utf-8", newline="\n")
    html_out.write_text(render_html(ledger), encoding="utf-8", newline="\n")
    return json_out, html_out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument(
        "--known-at", default=None,
        help="ISO instant; keep only observations with available_at <= this "
             "(point-in-time replay). Default: everything in the log.",
    )
    args = ap.parse_args()

    ledger = build_ledger(args.known_at)
    print(render_text(ledger))
    for path in write_artifacts(ledger):
        print(f"\nwrote {path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
