# Phase 1 Plan 03: Unified Signal-Admission Model — Summary

Documentation revision replacing the four-dimension confidence model with a unified signal-admission model
(binary mechanism prerequisite gate + three non-compensatory graded axes + a DERIVED maturity tag), and
recording that code-level boundary enforcement is part of the architecture. No code this pass; framework NOT
frozen (no sign-off filled).

## The model change

| Old four-dim confidence | Unified admission model |
|---|---|
| measurement quality | → **measurement validity** (axis) |
| mechanism support (graded H/M/L) | → **mechanism prerequisite gate** (graded → **binary** pass/rejected) |
| evidence robustness | → **evidence maturity** (axis) |
| implementation maturity | → **DROPPED** — becomes the DERIVED maturity tag (was circular) |
| *(new)* | → **investment usefulness** (important question + unique information; static, per-signal) |

- Three axes are **orthogonal and non-compensatory** (a high axis never offsets a low one).
- Maturity tag DERIVED from {mechanism = pass · three axes · dated sign-off · answerable investor-question}.
- Production bar: measurement ≥ M · usefulness = H · evidence maturity = H (incl. Japan/Europe OOS) · sign-off ·
  a clear "why does this deserve to be in front of an investor?".
- `current-relevance` / `regime-relevance` / `portfolio-relevance` stay DROPPED (predictive framing). Investment
  usefulness is explicitly NOT their replacement — it is a one-time admission judgment, never a per-reading score.

## Files changed (atomic commits by file-group)

- `framework/signal-output-spec.md` — §1 rewritten (gate + three axes, disclaimer reframed to "earned its
  place"); §2 maturity now DERIVED (implementation-maturity dropped); §3 adds the four-dim→unified supersession
  mapping; §4.1 Level-0 `confidence{}` → closed `assessment{}` block; §4.2 ledger row → admission assessment;
  §4.3 analogues "occurred before / observed outcomes, never will-happen-again" sentence; new §4.6 code-level
  enforcement pointer.
- `framework/signal-spec-template.md` — attribute 7 renamed "Admission Assessment" (Q7.1 = gate + three axes);
  new Q1.5 (unique information, universal-required); header maturity note re-derived; new header "Investor
  question (production bar)" field; D-05 reconciliation table updated.
- `framework/validation-standards.md` — §(b) mechanism gate = binary admission prerequisite; new §(l) Signal
  admission gate; new §(m) Boundary enforcement is executable; §(h) confidence note reframed; checklist
  attribute 7 relabeled.
- `framework/examples/{volatility,stock-bond-corr}-signal-declaration.md` — attribute 7 + Level-0 `assessment{}`
  block; Q1.5 + investor-question added; volatility keeps the RF production-vs-OOS tension (reworded to
  "evidence maturity"); stock-bond stays research (evidence maturity = M).
- `REGIME-SENSOR-ARCHITECTURE.md` — "three confidence dimensions" section replaced by the admission-model summary
  + rescored scorecard (mechanism gate + three axes); Level-0 field set + line-9/line-44 references updated; new
  "Boundary enforcement is executable" note. Observatory / one-way-boundary / glossary sections untouched.
- `01-CONTEXT.md` — added **D-17** (unified admission model) and **D-18** (code-level boundary enforcement is
  architecture).
- `SIGNOFF-CHECKLIST.md` — A1 rescoped to the three axes; A2 reworded; added **ADM** + **ENF**; old **D-06 swap**
  marked RESOLVED/superseded by ADM; dated sign-off lines updated. Still NOT SIGNED.
- `NOTES.md` — Phase-1 framework bullet + NEXT ACTION reflect the admission model, code-enforcement, and the new
  sign-off item set (A1/A2/A3/RF/OBS/ADM/ENF).

## Boundary audit

Reviewed-grep run on every touched file. Every forbidden-vocabulary hit sits inside a prohibition / boundary /
glossary / supersession statement, or is the legitimate descriptive signal name "Volatility / risk-off". No
allocation / decision / composite field introduced as a live field, value, or instruction.

## Deviations from plan

- **[Rule 3 — consistency]** Aligned the §4.2 Level-1 ledger row (`· confidence}` → `· the admission
  assessment}`) so no live "confidence" field contradicts the unified model. Small surgical edit; not in the
  explicit §4.1 scope but required for internal consistency.

## Not done (by design / out of scope)

- `ROADMAP.md` SC#3 and `STATE.md` decision-log still carry stale "three/four confidence dimensions" text. Left
  untouched per the established "upstream docs stale, not silently rewritten" discipline (research A5); the
  §3 supersession record documents the drift; patch is Adam's optional follow-up post-sign-off.
- The schema allowlist + boundary-audit test are documented as architecture (D-18) but built in the next
  (code) pass.

## Self-Check: PASSED

- `01-03-SUMMARY.md` created.
- All 8 file-groups edited; `assessment{}` block present in output-spec + both examples; D-17/D-18 in CONTEXT;
  ADM + ENF in SIGNOFF; A1 rescoped to three axes.
- Nothing frozen to v1.0 (sign-off lines blank).

---
<!-- LINKS:AUTO -->
## Related
**Project:** [[_planning/regime-detection/ROADMAP|ROADMAP]] · [[_planning/regime-detection/STATE|STATE]] · [[regime-detection/regime-detection|Hub]]
**Phase siblings:**
- [[_planning/regime-detection/phases/01-signal-framework/01-01-PLAN|01-01-PLAN]]
- [[_planning/regime-detection/phases/01-signal-framework/01-01-SUMMARY|01-01-SUMMARY]]
- [[_planning/regime-detection/phases/01-signal-framework/01-02-PLAN|01-02-PLAN]]
- [[_planning/regime-detection/phases/01-signal-framework/01-02-SUMMARY|01-02-SUMMARY]]
- [[_planning/regime-detection/phases/01-signal-framework/01-CONTEXT|01-CONTEXT]]
- [[_planning/regime-detection/phases/01-signal-framework/01-RESEARCH|01-RESEARCH]]
- [[_planning/regime-detection/phases/01-signal-framework/01-VERIFICATION|01-VERIFICATION]]

<!-- LINKS:END -->
