# Diversification / Absorption Signal — Charter Kickoff (warm-start)

**Status: warm-start scaffold, 2026-08-05. NOT a charter, NOT signed off.** Scope confirmed by Adam 2026-08-05:
**NARROW keep — lead-only.** This is the curse-of-dimensionality watch signal: it partially collapses onto vol
and earns a slot ONLY if its lead survives.

## Stage-0 Relevance Gate (default = NO)

- **G1 — investment question:** are cross-asset returns compressing onto a single factor — is diversification
  quietly failing *before* it shows up in volatility?
- **G2 — why it matters:** when everything loads on one factor, diversification fails exactly when it is needed;
  the absorption ratio rises ahead of realized turbulence.
- **G3 — unique information:** **partial.** The absorption ratio *is* a component of index vol; its only
  orthogonal content is the **lead** (it moves before vol does).
- **G4 — leave-one-out:** removing it loses an early-warning lead on correlation compression — but ONLY if that
  lead is real. If the lead fails, this signal is redundant with vol and should be dropped.
- **G5 — ex-ante prior:** moderate (Kritzman-Li-Page-Rigobon 2010; the identity σ_index ≈ σ̄·√ρ̄ ties it to vol).

**Gate verdict: CONDITIONAL PASS — narrow, lead-only. Kill if the lead does not survive causally + OOS.**

## Header (draft)

- **Signal name** — Diversification / correlation (absorption ratio)
- **Assumption monitored** — *"diversification is intact (cross-asset correlations haven't compressed onto one factor)."*
- **Native clock** — slow
- **Scope** — NARROW (lead-only)
- **Maturity** — DERIVED, unset (pre-validation)

## Mechanism (sketch — gates the charter)

Risk-management channel. Absorption ratio = fraction of total variance explained by the top principal components
of a trailing asset-return covariance (Kritzman et al. 2010). Rising AR = the market is becoming a one-factor
system = fragile. Survives being known because it describes the covariance structure, not a tradeable edge.

## Measurement + data (no new fetch)

Pure PCA of a trailing covariance matrix of `assets_daily.csv` (and/or the 10/48 French industry return series) —
strictly causal on a trailing window, no look-ahead. **Pre-register the window length and n-components before the
look** (researcher degrees of freedom). No external data.

## Orthogonality standing

PARTIAL — a factor of index vol that LEADS it. **The lead is the entire justification.** Held to the exact bar
that killed the dispersion-lead candidate (a US-only lead that failed to generalize: Japan +154d, Europe +94d).

## Open for the full charter (next session)

Does the lead survive causally and replicate on Japan/Europe? If not → DROP (do not keep a second reading of the
vol axis). Window/n-components pre-registration. V/R conditions with Adam.

---
<!-- LINKS:AUTO -->
## Related
**Project:** [[_planning/regime-detection/ROADMAP|ROADMAP]] · [[_planning/regime-detection/STATE|STATE]] · [[regime-detection/regime-detection|Hub]]
<!-- LINKS:END -->
