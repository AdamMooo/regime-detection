# Signal Declaration — Volatility / Risk-Off (jump-model instrument)

> **Retro-fit fit-check, not a new claim.** This declaration fills the frozen template against the
> already-shipped volatility / jump-model signal to prove the template accommodates a fast, return-derived
> state model. It records the signal's existing status; it asserts no new validation result or SUPPORT claim.

---

## Header block

- **Signal name** — Volatility / risk-off (statistical jump-model instrument)
- **Assumption monitored** — "the market is in its normal low-stress operating range"
- **Native clock / frequency** — daily (fast)
- **Maturity tag** — production *(DERIVED — see attribute 5 + attribute 7 §implementation maturity)*
- **Spec/template version** — v0.1-draft
- **Dated sign-off** — (blank — the shipped signal predates this framework; not re-signed here)

---

## The 8 attributes

### 1. Definition

- **Q1.1 What exactly does the signal measure?** A two-state (calm / stressed) volatility-regime label produced
  by a statistical jump model (Bemporad 2018; Nystrup 2020) over return-derived features. State 0 = calm/bull,
  state 1 = stressed/bear, by the downside-deviation sort convention in `jumpmodel.py`.
- **Q1.2 Which market assumption does it monitor?** "The market is in its normal low-stress operating range" —
  the header ledger key.

### 2. Mechanism

- **Q2.1 Why should this contain information (survives being known)?** Volatility clusters and persists — the
  most robust stylized fact in asset pricing (ARCH/GARCH lineage). A risk-off state observed today tends to
  persist tomorrow because the volatility-generating process is autocorrelated; knowing the state does not
  arbitrage away the persistence.
- **Q2.2 Risk-premium or risk-management channel?** Risk-management channel — it characterizes the current
  volatility environment, not a harvested premium.

### 3. Measurement

- **Q3.1 Exact causal construction?** EWM downside deviation (halflife 10d) + EWM Sortino ratios (halflives 20d,
  60d), all causal (EWMs look back only); jump model minimizes squared feature distance + a switch penalty λ via
  exact DP state assignment. Live label splices live SPY onto the French market panel (`live_label.py`), with a
  splice-gate correlation health check.
- **Q3.2 Data sources + vintage/revision sensitivity?** Asset returns (SPY / French market panel). *Not
  applicable, because* it is built from asset returns — no macro vintage or revision surface. Splice-gate health
  (`splice_corr`, `agreement_with_frozen`) monitors live-panel drift instead.
- **Q3.3 Native clock?** Daily.
- **Q3.4 Limitations of the measurement?** A vol-state instrument, not a bear detector: multi-week detection lag;
  historically misses fast crashes with no volatility build-up (e.g. 1998, 2018-Q4).

### 4. Historical Context

- **Q4.1 How has it behaved / what regimes identified?** Separates persistent calm from persistent stressed
  volatility regimes; 30 completed episodes in history, empirical median dwell ≈ 61.5 trading days, very high
  day-to-day persistence (p_stay ≈ 0.995). Monthly timeline in `results/regime_card.json`.
- **Q4.2 Empirical false-positive / false-negative record?** Scored by `validate_sensor.py` vs
  Lunde-Timmermann ex-post bear dating on the frozen chapter-1 OOS labels: LT15 detected 15/18 (median lag 20d);
  LT20 detected 9/11 (median lag 56d). False negatives concentrate in fast crashes; the lag is the systematic
  error.

### 5. Validation

- **Q5.1 Holds across sub-periods?** Yes — the label is validated on the frozen chapter-1 out-of-sample period
  and its persistence/skill statistics are stable across it.
- **Q5.2 Survives Japan/Europe out-of-hypothesis-sample, or documented failure?** *Partial / by-reference:*
  volatility clustering is a documented universal stylized fact across international equity markets, and the
  instrument's own OOS was the frozen chapter-1 US labels + Lunde-Timmermann scoring. A literal Japan/Europe
  panel replication of this specific instrument was not separately run — see the versioned-amendment candidate
  below (this tension between the derivation rule and the shipped production tag is flagged for sign-off).
- **Q5.3 Robust or regime-dependent, confounds ruled out?** Robust — the persistence property is not
  regime-conditional; the splice-gate rules out the live-panel-drift confound.

### 6. Assumptions

- **Q6.1 What does the signal assume?** Volatility regimes persist; return-derived downside-deviation / Sortino
  features capture the risk-off state; the live SPY splice stays aligned with the French panel.
- **Q6.2 Structural failure modes (declared before testing)?** Fast crashes with no volatility build-up (jump
  risk) → detection lag; splice drift breaking the live-to-frozen alignment; a structural break in volatility
  dynamics that the fitted centers no longer describe.

### 7. Confidence (four research-maturity dimensions)

- **measurement quality: H** — causal, from asset returns, no vintage surface, full history.
- **mechanism support: H** — volatility persistence is a durable, literature-grounded risk-management channel;
  passes the mechanism gate.
- **evidence robustness: H** — stable across the frozen chapter-1 OOS; property is a universal stylized fact
  (see the Q5.2 caveat / amendment candidate).
- **implementation maturity: H → production** — built, validated, failure-mapped, shipped, and consumed by a
  separate downstream repo via `results/regime_card.json`.

> Confidence here states research maturity, not predictive likelihood — it does not mean the signal is more
> likely to be correct or predicts the market.

### 8. Limitations

- **Q8.1 What can it tell us?** Whether the market is currently in a persistent elevated-volatility / risk-off
  state, and how the current run compares to historical episodes.
- **Q8.2 What can it explicitly NOT tell us?** It does not predict when the state will flip; it does not catch
  fast crashes early; it is not a bear-market predictor and not a return forecast.
- **Q8.3 Per-signal boundary.** This reading names the monitored market assumption ("the market is in its normal
  low-stress operating range") and STOPS. It implies no action.

---

## Level 0 record

```
{
  signal:               "volatility_riskoff_jumpmodel",
  assumption_monitored: "the market is in its normal low-stress operating range",
  reading:              "CALM (state 0), 95 days in",
  rarity:               "53rd percentile of 30 completed episodes (dwell length)",
  clock:                "daily",
  confidence: {
     measurement_quality:    "H",
     mechanism_support:      "H",
     evidence_robustness:    "H",
     implementation_maturity:"H"
  },
  maturity:             "production",
  spec_version:         "v0.1-draft"
}
```

---

## Versioned-amendment candidates (template NOT edited here)

- **Clock vocabulary.** The template enumerates daily / weekly / monthly / structural; the ledger also uses a
  qualitative fast/slow tempo descriptor. A MINOR additive amendment could add an optional tempo field. Low
  priority — daily fills cleanly.
- **Production tag vs literal Japan/Europe OOS.** The maturity derivation rule (`signal-output-spec.md` §2)
  requires evidence robustness = H via international out-of-hypothesis-sample confirmation, but this shipped
  signal's production status rests on frozen-US OOS + the universal vol-persistence stylized fact rather than a
  literal Japan/Europe panel run. Either the rule needs a "universal-stylized-fact" clause or the signal needs
  the explicit panel run — surfaced for sign-off (see `SIGNOFF-CHECKLIST.md`).

---
<!-- LINKS:AUTO -->
## Related
**Project:** [[_planning/regime-detection/ROADMAP|ROADMAP]] · [[_planning/regime-detection/STATE|STATE]] · [[regime-detection/regime-detection|Hub]]
<!-- LINKS:END -->
