# Tail / Jump Signal — Charter Kickoff (warm-start)

**Status: warm-start scaffold, 2026-08-05. NOT a charter, NOT signed off.** Scope confirmed by Adam 2026-08-05:
**FULL keep — options-implied** (realized-jump/bipower is data-gated and out of scope). Data pulled this session.
**Update: no longer data-gated** — the free options-implied lens closes the gap the ROADMAP flagged.

## Stage-0 Relevance Gate (default = NO)

- **G1 — investment question:** is the market pricing an unusual left-tail / jump risk — is the shape of the
  return distribution abnormal, separate from its width (vol)?
- **G2 — why it matters:** priced jump/tail risk carries its own risk premium with time-variation volatility
  cannot explain; it is the "shape not magnitude" dimension.
- **G3 — unique information:** STRONG and separately priced (Bollerslev-Todorov 2011; Kelly-Jiang 2014 ≈5.4%/yr).
  Distinct from vol (magnitude), inflation, valuation, concentration.
- **G4 — leave-one-out:** removing it leaves the observatory blind to "the distribution is its normal shape."
- **G5 — ex-ante prior:** strong (jump-risk-premium literature).

**Gate verdict: PASS.**

## Header (draft)

- **Signal name** — Tail / jump risk (options-implied)
- **Assumption monitored** — *"the return distribution is its normal shape — tails aren't unusually priced."*
- **Native clock** — fast, shape-not-magnitude
- **Scope** — FULL, options-implied (SKEW + VIX term structure); realized-jump/bipower EXCLUDED (data-gated)
- **Maturity** — DERIVED, unset (pre-validation)

## Mechanism (sketch — gates the charter)

Risk-premium channel. The risk-neutral distribution prices left-tail/jump risk with its own dynamics; the jump
premium is compensated separately from diffusive vol. Survives being known because it is a priced risk, not an
arbitrage. Refs above.

## Measurement + data (pulled this session — `scripts/build_tail.py`)

- **CBOE SKEW** (risk-neutral 30d skewness of S&P 500; fat-left-tail pricing), 1990+ → `data/processed/tail_daily.csv`
  (latest ≈ 126).
- **VIX term structure** (`VIX9D`/`VIX`/`VIX3M`) → `term_slope = VIX3M/VIX − 1` (inversion = near-term tail fear;
  latest ≈ +0.17, normal upward). PIT-clean (same-day option quotes).
- **Excluded (data-gated):** high-frequency realized-jump / bipower variation — the free long intraday source
  (Oxford-Man Realized Library) closed 2022; a daily-return jump approximation is the only free fallback and is
  out of the warm-start scope.
- **Caveat:** CBOE re-based the SKEW / term-structure methodology over time — the long series is continuous but
  not perfectly methodology-homogeneous; document before any SUPPORT claim.

## Orthogonality standing

STRONG, separately priced (own time-variation vol can't explain).

## Open for the full charter (next session)

SKEW methodology homogeneity + the known critiques of SKEW's informativeness; SKEW vs term-slope as the primary
object; the international-OOS problem (intl options-implied tail data is hard — flag). V/R with Adam.

---
<!-- LINKS:AUTO -->
## Related
**Project:** [[_planning/regime-detection/ROADMAP|ROADMAP]] · [[_planning/regime-detection/STATE|STATE]] · [[regime-detection/regime-detection|Hub]]
<!-- LINKS:END -->
