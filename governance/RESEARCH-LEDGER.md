# RESEARCH LEDGER

Every hypothesis tested across the three internal repositories, and what happened to it.

**Purpose:** prevent rediscovering the same idea six months later because nobody remembers why
it failed. **Read this before proposing a new signal, model, or strategy.** Eight of the
entries below are documented nulls — that is the point of the file.

Created 2026-08-09, seeded from `CROSS-REPO-AUDIT-2026-08-09.md`. No findings invented; every
row is transcribed from evidence already recorded in the repos.

**ID space:** `MI-*` regime-detection · `ALGO-*` algo-trading-bot · `PM-*` portfolio-manager.
**Status:** `IDEA · TESTING · PROMISING · VALIDATING · VALIDATED · REJECTED · DEPRECATED · REDUNDANT`

> **Location is not ownership.** This file lives in `regime-detection/governance/` for one
> reason only: the workspace root is not a git repository, so a root-level ledger had no
> version history and no way to survive a machine migration (decided 2026-08-09, superseding
> `IMPLEMENTATION-PLAN.md` §9's "accept vault-only history"). **regime-detection does not own
> the `ALGO-*` or `PM-*` entries.** Each repository owns its own rows; this is a shared index
> that happens to be stored in the one repo guaranteed to be present. Do not infer any
> architectural relationship from the path, and do not let regime-detection code read this file.

> **Note on deleted code.** Several `ALGO-*` entries reference code deleted from the working
> tree on 2026-08-09 (the market-understanding strip-down). The code is recoverable from git
> history at commit `b1f3fa3e~1`. **The findings below are the durable artifact — not the
> implementations.** That is why they are written out in full here.

---

## Market Intelligence — `regime-detection`

| ID | Hypothesis | Test | Result | Status | Reason | Date |
|---|---|---|---|---|---|---|
| MI-001 | A K=2 jump-model state label reads volatility better than a plain causal threshold | Exposure-matched head-to-head at both bear datings (`results/detector_benchmark.csv`) | Threshold + hysteresis matched or beat it on precision, recall and BAC, with shorter detection lag | **REJECTED** | Thresholding destroys the graded information in σ. `results/regime_card.json` parked as a consequence | 2026-08-04 |
| MI-002 | Volatility descriptors (level · rarity · drift · GARCH half-life) are a usable production signal | Frozen one-look, `scripts/validate_vol.py` → `results/vol_validation.txt` | Signed off; maturity `production` | **VALIDATED** | Mechanism pass; measurement validity / investment usefulness / evidence maturity all H | 2026-08-06 |
| MI-003 | Stock-bond correlation state describes whether bonds hedge equity drawdowns | Hedge-behavior-by-state, US 1962–2026 | Monotone through states: bonds cushioned 32% of equity-down days in the negative-corr regime vs fell-too 57% in the positive-corr regime | **VALIDATING** | Japan/Europe out-of-hypothesis-sample confirmation owed before SUPPORT. Note: average-return-by-state was **confounded by the rate cycle** — hedge behavior is the honest metric | 2026-08-06 |
| MI-004 | The jump-model regime is a priced cross-sectional factor | REG on FF 25 size/BE-ME, spanning-regressed on FF3 and FF3+BAB, Newey-West(6); two FMP constructions | Constructions **disagree**: beta-sort α t=−1.30, mimicking-portfolio α t=−2.09 | **TESTING** (ambiguous) | Escalated to a Step-4 preregistered confirmatory test. An earlier "spanned, closed cheaply" verdict was **retracted** as an over-claim (wrong significance bar, misread negative α, uninterpretable ΔSh², under-controlled axis) | 2026-07-30 |
| MI-005 | State-conditional covariance adds allocation value | Fee-equivalent comparison vs a reactive EWMA covariance | fee_A +2.8 inside all bands; reactive EWMA beats it outright (fee_B −29.1) | **REJECTED** | The risk-stabilization mechanism exists (F2 clear), but reactive estimation harvests it better | 2026-07-23 |
| MI-006 | Cross-asset defensive rotation timing adds value beyond exposure | Matched vol-target comparison | Null — timing adds no return or Sharpe beyond exposure; a matched vol-target matches or beats its drawdown protection | **REJECTED** | Exposure artifact. Chapter 1 reconfirmed for the third time | 2026-07-26 |
| MI-007 | The absorption ratio is an admissible diversification signal | Signal declaration + validation | Dropped | **REJECTED** | `archive/dropped-signals/05-ABSORPTION-DROPPED.md` | — |
| MI-008 | Funding stress is an admissible signal | Signal declaration + validation | Dropped | **REJECTED** | `archive/dropped-signals/07-FUNDING-DROPPED.md` | — |

---

## Algo Trading — `algo-trading-bot`

| ID | Hypothesis | Test | Result | Status | Reason | Date |
|---|---|---|---|---|---|---|
| ALGO-001 | A regime-aware cross-sectional ML ranker produces tradable alpha | Backtest, then de-leaked | IC 0.082 → 0.018; Sharpe 1.93 → **−0.02** | **REJECTED** | Lookahead leak. The entire apparent edge was the leak | — |
| ALGO-002 | The jump penalty λ yields a sticky, economically meaningful macro regime | Persistence sweep (spike 002) | Validated, but narrowly | **VALIDATED** (narrow) | It is a **credit-crisis detector**: nailed the GFC, caught COVID late, missed 2022. ~2 episodes in 21 years — the GFC dominates the sample | 2026-06-12 |
| ALGO-003 | The macro regime carries information volatility cannot see | Orthogonality / lead-lag at every λ (spike 003) | Regime **lags** vol at every λ; 100% overlap | **REJECTED** | Discretizing kills the lead. **Fitting a regime on an asset's own returns just rediscovers vol** | 2026-06-12 |
| ALGO-004 | A damped macro overlay beats vol-target-alone after costs | Decision gate (spike 004) | Never run | **REJECTED** (not run) | Pre-determined by ALGO-003: the overlay acts only on already-de-risked days, so it cannot improve risk-adjusted return. Verdict accepted rather than spending the test | 2026-06-12 |
| ALGO-005 | MacroHMM states track forward risk | Out-of-sample replacement test | Window-dependent (transmat diagonal ~0.999 → locks into its start state); "Contraction" fwd-63d +3.0% ≈ "Expansion" +3.2%; a market-priced risk-appetite replacement went +1.55% in-sample → **+0.37% OOS** | **REJECTED** | States do not order forward returns. Model + 4 artifacts deleted | 2026-06-16 |
| ALGO-006 | The 2-HMM gauge detects volatility | Hermetic forward-RV eval (`backtest/regime_vol_eval.py`) | Forward RV monotonic LOW < MED < HIGH; HIGH/LOW ratio 2.2× / 1.9× / 1.6× at 5/21/63d; AUC 0.77–0.81 | **VALIDATED** as a *nowcaster* | An excellent volatility **nowcaster**, explicitly **not a forecaster**. Never demonstrated to be monetizable — it was never put through a monetization test | 2026-06-16 |
| ALGO-007 | A paper-faithful 3-state directional detector (Gupta et al. 2025) beats oracle-label baselines | Two-fold walk-forward with locked Fold-1 gates and one-shot Fold-2 confirmation | **Never completed.** Milestone v9 marked complete at 4/5 phases; Phase 59 never started; working tree diverged 2026-07-09 | **DEPRECATED** | No verdict was ever reached. Deleted from the Algo repo 2026-08-09 as market *understanding*, which the monetization layer does not own. **If the question is still open it belongs in `regime-detection` under a fresh charter — but note MI-001 already retired the labelled-state framing on published evidence** | 2026-08-09 |
| ALGO-008 | 12-1 / 6-1 risk-adjusted momentum ranks an 8-ETF universe well enough to monetize | — | **Never tested** | **IDEA** | `strategy/ev_ranker.py` ran in the live path for months without ever clearing an admission gate — no OOS test, no cost analysis, no ledger entry. Unwired from live 2026-08-09; retained as a candidate | 2026-08-09 |
| ALGO-009 | *(defect, not a hypothesis)* The frozen 2-HMM gauge was fed valid features | Discovered during the Step-0b documentation audit | Artifacts frozen **2026-06-16** against the 16-ETF universe; `493cba43` (**2026-07-21**) cut `ETF_UNIVERSE` to 8; `regime/data.py:191-192` computed `pct_above_{50,200}ma` from `ETF_UNIVERSE`, and `pct_above_200ma` was BreadthHMM's **primary relabeling anchor** | **REJECTED** (invalidated) | The scaler and label map stayed frozen to a 16-name distribution while the input became an 8-name one. **Every regime label from 2026-07-21 onward is suspect, including those the live bot traded on through 2026-07-27.** Same failure class as the 2026-06-16 live feature-degradation bug, in a new form. Not fixed — the gauge was deleted instead | 2026-08-09 |

### Standing lessons for anyone proposing a regime/state idea here

1. **A regime fitted on an asset's own returns rediscovers volatility** (ALGO-003). If the
   proposal cannot state what it sees that vol cannot, it is redundant before it is written.
2. **Discretizing a continuous state destroys information** (MI-001, ALGO-003). A threshold has
   to earn its place against the continuous reading plus hysteresis, and so far it never has.
3. **State detection quality is not monetization** (ALGO-006). The gauge is a genuinely good
   volatility nowcaster and was still never shown to make money.
4. **Frozen artifacts silently rot when their inputs move** (ALGO-009). Any frozen model needs
   a test pinning the distribution of its inputs, not just its own checksums.
5. **Market-state modelling does not belong in the Algo repo at all.** That is the architectural
   conclusion these five entries add up to.

---

## Portfolio Management — `portfolio-manager`

| ID | Hypothesis | Test | Result | Status | Reason | Date |
|---|---|---|---|---|---|---|
| PM-001 | An MVO optimizer / recommender / rebalancer belongs in the governance engine | — | Retired | **DEPRECATED** | The security-selection paradigm was abandoned. `ARCHITECTURE.md` "Do NOT rebuild" — Quarter-Kelly sizing, the ~70-name TSX universe, the factor library, the in-repo regime detector | 2026-08-02 |

---

## External-origin findings

Recorded as context only. A finding from outside the internal stack carries **no internal ID**
and is not a signal here until re-tested under `regime-detection`'s charter (mechanism gate,
preregistration, cooling-off, dated sign-off).

| Origin | Finding | Result | Note |
|---|---|---|---|
| `vol-diagnostics` | Timing covered-call writing off the VRP level produces a forward-return edge | **REJECTED**, p = 0.74 | The prescriptive language was removed from that product as a result (`engine/report/card_model.py:474-481`). Not an internal signal | 2026-07-27 |

---

## How to add an entry

Append a row. Keep it to one line per hypothesis; put detail in the repo that owns it.

A hypothesis reaching **VALIDATED** in the `ALGO-*` table is the **only** path into the live
trading path — and it enters as a named strategy component, never as a raw Market Intelligence
field. See `IMPLEMENTATION-PLAN.md` §3.6 (admission gate) and §7 (consumer rules).

`REJECTED` and `DEPRECATED` rows are never deleted. They are the most valuable rows here.
