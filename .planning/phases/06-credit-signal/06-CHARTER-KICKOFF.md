# Credit Signal (Excess Bond Premium) — Charter Kickoff (warm-start)

**Status: warm-start scaffold, 2026-08-05. NOT a charter, NOT signed off.** Scope confirmed by Adam 2026-08-05:
**FULL keep — EBP-residual only** (raw spreads are redundant with vol). Data pulled this session.

## Stage-0 Relevance Gate (default = NO)

- **G1 — investment question:** are bond investors demanding unusual compensation beyond expected default — is
  credit-market risk appetite tightening ahead of the broader market?
- **G2 — why it matters:** the excess bond premium leads risk-off by ~1–2 years via a credit-supply / intermediary
  channel — a genuine early read no coincident stress gauge provides.
- **G3 — unique information:** **the residual only.** Raw credit spreads are ~85% shared with VIX (redundant);
  the EBP (spread purged of expected default) is the thin, orthogonal, *leading* part.
- **G4 — leave-one-out:** removing it loses the leading credit-supply signal ("credit conditions are benign").
- **G5 — ex-ante prior:** strong (Gilchrist-Zakrajšek 2012; López-Salido-Stein-Zakrajšek 2017).

**Gate verdict: PASS — EBP residual, not raw spreads.**

## Header (draft)

- **Signal name** — Credit (excess bond premium)
- **Assumption monitored** — *"credit conditions are benign — bond investors aren't demanding unusual compensation."*
- **Native clock** — slow, LEADING (~1–2yr)
- **Scope** — FULL (EBP residual only)
- **Maturity** — DERIVED, unset (pre-validation)

## Mechanism (sketch — gates the charter)

Risk-premium / credit-supply channel. EBP reflects bond-investor risk appetite and intermediary balance-sheet
capacity beyond compensation for expected default; a contraction in credit supply precedes real-economy and
market weakness. Survives being known because it is a risk-premium, not an arbitrage. Refs above.

## Measurement + data (pulled this session — `scripts/build_credit.py`)

- **EBP (the signal):** Fed FEDS-Notes published monthly series → `data/processed/credit_monthly.csv`
  (cols `gz_spread`, `ebp`, `est_prob`; 1973–present; latest EBP ≈ −0.30). **PIT hazard: the series is restated
  each month** — snapshot vintages for strict PIT, or treat as a near-real-time smoothed read (document the
  choice).
- **Daily OAS proxies** (market prices, unrevised/PIT): ICE BofA IG/HY OAS + Baa−10y → `credit_daily.csv`
  (1986+) — context/robustness, NOT the primary object.

## Orthogonality standing

STRONG — thin, leading residual. Raw spreads dropped as redundant.

## Open for the full charter (next session)

Published-EBP vs the restatement/PIT concern; confound-check the lead; the international-OOS problem (a comparable
JGB/Bund EBP is hard — flag as a documented limitation, possibly US-only with a stated caveat). V/R with Adam.

---
<!-- LINKS:AUTO -->
## Related
**Project:** [[_planning/regime-detection/ROADMAP|ROADMAP]] · [[_planning/regime-detection/STATE|STATE]] · [[regime-detection/regime-detection|Hub]]
<!-- LINKS:END -->
