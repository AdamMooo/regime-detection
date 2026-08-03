# Signal Declaration — Stock-Bond Correlation (inflation / real-rate, PC2)

> **Retro-fit fit-check, not a new claim.** This declaration fills the frozen template against the built
> stock-bond correlation signal to prove the template accommodates a slow, returns-based correlation-sign
> signal (a genuinely different shape from the fast volatility state model). It records the signal's existing
> status; it asserts no new validation result or SUPPORT claim.

---

## Header block

- **Signal name** — Stock-bond correlation (inflation / real-rate axis, PC2)
- **Assumption monitored** — "bonds hedge equity drawdowns"
- **Native clock / frequency** — monthly (slow)
- **Maturity tag** — research *(DERIVED — Japan/Europe OOS pending per SIG-01)*
- **Spec/template version** — v0.1-draft
- **Dated sign-off** — (blank — not signed; international OOS gate open)

---

## The 8 attributes

### 1. Definition

- **Q1.1 What exactly does the signal measure?** The causal trailing Pearson correlation between equity and
  10-year-bond daily returns (primary window 126d; monthly 24-month read as the honest regime lens). Its SIGN is
  the state: corr < −band → intact (demand-shock world, bonds rally as equities fall); corr > +band → violated
  (supply/inflation world, bonds and equities fall together); |corr| ≤ band → under-test.
- **Q1.2 Which market assumption does it monitor?** "Bonds hedge equity drawdowns" — the header ledger key.

### 2. Mechanism

- **Q2.1 Why should this contain information (survives being known)?** The stock-bond correlation is the
  observable proxy for the nominal-real covariance (the inflation-growth correlation). Whether bonds diversify
  equities is structurally determined by whether shocks are demand-driven (bonds hedge) or supply/inflation-
  driven (bonds co-move). Knowing the current state does not change the underlying macro covariance regime.
- **Q2.2 Risk-premium or risk-management channel?** Risk-management channel — it characterizes whether the
  diversification relationship is currently functioning.

### 3. Measurement

- **Q3.1 Exact causal construction?** `rolling(126).corr` of equity vs 10y-bond daily returns (trailing, no
  look-ahead); monthly 24-month rolling correlation as the slow regime read; expanding-z for "how unusual is
  today's level"; `sign_state` maps the correlation to intact / under_test / violated with a neutral band of
  0.10. Rate-cycle confound handled by reading hedge-behavior-by-state, not average-return-by-state.
- **Q3.2 Data sources + vintage/revision sensitivity?** `assets_daily.csv` (mkt_ret × bond10_ret, 1962+).
  *Not applicable, because* it is built from asset returns — no macro vintage or revision surface.
- **Q3.3 Native clock?** Monthly (the daily 126d series is computed, but the monthly read is the honest regime
  lens — a daily-126d calendar mean hid the 2022 flip).
- **Q3.4 Limitations of the measurement?** Trailing-window lag around fast sign flips (the 2022 flip lesson);
  the neutral band creates an ambiguous "under-test" zone; the correlation sign is slow-moving by construction.

### 4. Historical Context

- **Q4.1 How has it behaved / what regimes identified?** The sign matches the known regimes: 1970s-80s positive
  (supply/inflation), 2000-2021 negative (demand/deflation), 2022+ flip back to positive. Hedge-behavior-by-state
  is monotone through the states (on equity-down days bonds cushioned ≈32% in the intact/negative-corr regime vs
  fell-too ≈57% in the violated/positive-corr regime). Rarity reported as the trailing percentile of 1962-2026.
- **Q4.2 Empirical false-positive / false-negative record?** *Not applicable, because* the signal is a
  descriptive correlation-state characterization, not a discrete-event detector — it produces no
  positive/negative event ledger to tally FP/FN against. The relevant honesty check is the confounded
  average-return-by-state warning (recorded in the script), not an FP/FN count.

### 5. Validation

- **Q5.1 Holds across sub-periods?** Yes — the sign matches across the four episode windows (US 1962-2026), each
  a distinct sub-period.
- **Q5.2 Survives Japan/Europe out-of-hypothesis-sample, or documented failure?** *Not yet run (documented
  pending):* the international OOS confirmation on Japan/Europe requires JGB/Bund series (Phase 2 / SIG-01) and
  has NOT been run. This is the open discipline gap that holds the maturity tag at research.
- **Q5.3 Robust or regime-dependent, confounds ruled out?** The rate-cycle confound is explicitly ruled out
  (hedge-behavior-by-state, not average-return-by-state). Robustness across the non-US panels is the pending
  gate.

### 6. Assumptions

- **Q6.1 What does the signal assume?** Daily equity-bond return comovement proxies the slow nominal-real
  covariance; the correlation SIGN is the economically meaningful state of the hedge relationship.
- **Q6.2 Structural failure modes (declared before testing)?** Neutral-band whipsaw around zero correlation;
  trailing-window lag around fast flips; a structural change in the inflation-growth regime that the trailing
  window is slow to register.

### 7. Confidence (four research-maturity dimensions)

- **measurement quality: H** — causal, from asset returns, no vintage surface, history back to 1962.
- **mechanism support: H** — the nominal-real covariance channel is literature-grounded and durable; passes the
  mechanism gate.
- **evidence robustness: M** — US sub-periods hold and confounds are checked, but international
  out-of-hypothesis-sample confirmation is pending.
- **implementation maturity: M → research** — built and characterized, but the international OOS gap keeps it at
  research; renders as human context only.

> Confidence here states research maturity, not predictive likelihood — it does not mean the signal is more
> likely to be correct or predicts the market.

### 8. Limitations

- **Q8.1 What can it tell us?** The current realized stock-bond correlation state and whether the hedge has
  historically worked in this correlation environment.
- **Q8.2 What can it explicitly NOT tell us?** It does not predict when the correlation sign will flip; it does
  not say whether bonds will hedge the next specific drawdown; it is not a return forecast.
- **Q8.3 Per-signal boundary.** This reading names the monitored market assumption ("bonds hedge equity
  drawdowns") and STOPS. It implies no action.

---

## Level 0 record

```
{
  signal:               "stockbond_corr_pc2",
  assumption_monitored: "bonds hedge equity drawdowns",
  reading:              "<current state + 126d/63d/252d corr from results/stockbond_corr.csv>",
  rarity:               "<trailing percentile of 1962-2026, expanding-z level>",
  clock:                "monthly",
  confidence: {
     measurement_quality:    "H",
     mechanism_support:      "H",
     evidence_robustness:    "M",
     implementation_maturity:"M"
  },
  maturity:             "research",
  spec_version:         "v0.1-draft"
}
```

---

## Versioned-amendment candidates (template NOT edited here)

- **None required for fit.** Every attribute filled cleanly, including the two genuine forced
  `Not applicable, because …` answers (Q3.2 vintage, Q4.2 FP/FN) — which is the template working as designed for
  a returns-based descriptive-state signal. The only cross-signal note is the shared clock-vocabulary amendment
  candidate already recorded in the volatility declaration (a MINOR additive tempo field); it is not blocking.

---
<!-- LINKS:AUTO -->
## Related
**Project:** [[_planning/regime-detection/ROADMAP|ROADMAP]] · [[_planning/regime-detection/STATE|STATE]] · [[regime-detection/regime-detection|Hub]]
<!-- LINKS:END -->
