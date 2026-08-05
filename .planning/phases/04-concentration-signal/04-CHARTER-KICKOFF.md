# Concentration Signal — Charter Kickoff (warm-start)

**Status: warm-start scaffold, 2026-08-05. NOT a charter, NOT signed off.** Pre-registration front-matter to
red-pen before the full charter is written (D-15). Scope confirmed by Adam 2026-08-05: **FULL keep,
proxy-scoped.** Data uses an existing panel (no new fetch).

## Stage-0 Relevance Gate (default = NO)

- **G1 — investment question:** is the market's leadership narrowing into a few names — is breadth/diversification
  eroding structurally, independent of how volatile it is?
- **G2 — why it matters:** concentration decouples from volatility (index HHI was at multi-decade highs in a
  *low*-vol regime) and leads tail loss; a narrow market is fragile in a way vol does not reveal.
- **G3 — unique information:** a cross-sectional/compositional dimension none of vol (PC1), inflation (PC2), or
  valuation carry.
- **G4 — leave-one-out:** removing it leaves the observatory blind to "the index isn't dependent on a few names."
- **G5 — ex-ante prior:** strong (random-matrix / HHI evidence; the "Magnificent-7" concentration literature).

**Gate verdict: PASS.**

## Header (draft)

- **Signal name** — Concentration
- **Assumption monitored** — *"the index isn't dependent on a few names."*
- **Native clock** — slow / structural
- **Scope** — FULL, **proxy-scoped** (see measurement)
- **Maturity** — DERIVED, unset (pre-validation)

## Mechanism (sketch — gates the charter)

Risk-management channel. A market whose returns are driven by a handful of names carries undiversified
idiosyncratic risk the aggregate index level hides; this is a compositional fact, not a mispricing, so it is
not arbitraged away by being known. Reference: Meucci 2009 (effective-N); random-matrix theory (Laloux 1999).

## Measurement + data (no new fetch)

- **Honest constraint (data scout, 2026-08-05):** a *true* top-N weight / cap-HHI needs historical index
  constituents — paywalled and survivorship-prone on free data. **Do not fake it with today's membership.**
- **Free, long, PIT proxy:** Ken French **value-weighted − equal-weighted** return spread (VW = `mkt_ret`,
  EW = mean of the 10 industry return series already in `assets_daily.csv`). VW leading EW ⇒ leadership narrowing
  into the largest names. Daily back to 1926. The charter must state plainly that the **observable is a
  leadership/breadth proxy**, not a literal cap-HHI.

## Orthogonality standing

STRONG (decouples from vol; leads VaR). Not a curse-of-dimensionality risk.

## Open for the full charter (next session)

Whether the VW−EW proxy adequately stands in for concentration (vs an unobtainable true HHI); the lead property;
confound-check; Japan/Europe OOS (French intl return series). V/R conditions to be worked with Adam + a data look.

---
<!-- LINKS:AUTO -->
## Related
**Project:** [[_planning/regime-detection/ROADMAP|ROADMAP]] · [[_planning/regime-detection/STATE|STATE]] · [[regime-detection/regime-detection|Hub]]
<!-- LINKS:END -->
