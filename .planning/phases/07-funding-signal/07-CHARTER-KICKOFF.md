# Funding-Stress Signal — Charter Kickoff (warm-start)

**Status: warm-start scaffold, 2026-08-05. NOT a charter, NOT signed off.** Scope confirmed by Adam 2026-08-05:
**NARROW keep — binary tail-only flag** (decouples only in 2008/2020). Fold-into-Tail is an open possibility.
Data pulled this session.

## Stage-0 Relevance Gate (default = NO)

- **G1 — investment question:** are funding markets functioning, or is there acute secured/unsecured funding
  stress right now?
- **G2 — why it matters:** funding seizures are the mechanism of the worst tail events (2008, 2020) — an
  intermediary-constraint channel that turns a drawdown into a spiral.
- **G3 — unique information:** **tail-only.** In normal times funding stress is redundant with vol; it carries
  distinct information only when it decouples in a crisis.
- **G4 — leave-one-out:** removing it loses a tail-specific flag — but its everyday value is ~zero, so it is a
  flag, not a continuous signal, and possibly belongs *inside* the Tail signal.
- **G5 — ex-ante prior:** moderate (2008/2020 decoupling is well documented; no single seminal construction).

**Gate verdict: CONDITIONAL PASS — narrow binary flag. Reassess vs folding into Tail during the charter.**

## Header (draft)

- **Signal name** — Funding stress
- **Assumption monitored** — *"funding markets function."*
- **Native clock** — fast, tail-only
- **Scope** — NARROW (binary flag)
- **Maturity** — DERIVED, unset (pre-validation)

## Mechanism (sketch — gates the charter)

Risk-management / tail channel. When intermediaries cannot fund positions, forced deleveraging amplifies
drawdowns. Not a return-timing edge; a tail-conditioning flag.

## Measurement + data (pulled this session — `scripts/build_funding.py`)

- FRED financial-stress indices with funding components → `data/processed/funding_weekly.csv` (`STLFSI4`, `NFCI`;
  1971+). **Preferred strict-PIT source = OFR FSI funding sub-index (financialresearch.gov) — wire later;**
  NFCI/STLFSI are *revised*, document it.
- Long spreads → `funding_daily.csv`: CP−bill (`DCPN3M` − `DTB3`, late-1990s+) and SOFR−EFFR (2018+).
- **Structural hazard:** the LIBOR→SOFR transition (TED spread discontinued 2022; no clean free LIBOR-OIS
  history) means any hand-built spread is spliced across incompatible rates — document the break; cross-currency
  basis is infeasible free (drop).

## Orthogonality standing

PARTIAL, tail-only. A narrow flag by design.

## Open for the full charter (next session)

Binary-threshold pre-registration; whether it is genuinely distinct from the Tail signal or should fold into it;
the LIBOR→SOFR splice. V/R with Adam.

---
<!-- LINKS:AUTO -->
## Related
**Project:** [[_planning/regime-detection/ROADMAP|ROADMAP]] · [[_planning/regime-detection/STATE|STATE]] · [[regime-detection/regime-detection|Hub]]
<!-- LINKS:END -->
