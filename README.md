# Regime Detection

**Market regime detection via a statistical jump model — validated as an instrument, tested for decision value.**

A K=2 weighted statistical jump model (Bemporad/Boyd 2018; Nystrup et al. 2020–21; Shu/Yu/Mulvey 2024) fit to Ken French daily market data (1926+), run under strict preregistration and causal discipline. The program builds a market risk-state label, validates it to an unusually high measurement standard, and then — under preregistered, one-look, exposure-matched tests — asks whether that label has economic *decision* value at a daily horizon.

The short answer, and the thesis: **measurement validity ≠ decision value.** The label is an exceptional *instrument* (100.0% stability under ±2y training-window shifts, vs 80.9% for the retired v1 HMM ensemble). But every economic use tested so far is dominated by a simpler reactive estimator — vol targeting for exposure, EWMA for covariance — unified by one mechanism: causal filters lag the regime by 5–20 days, and at a daily horizon that lag erases the edge. This is a comparative-negative result, held to a higher standard than the source literature (which omits exposure-matched nulls and a reactive incumbent).

---

## What's proven, parked, and killed

| Layer | Result | Status |
|---|---|---|
| **Instrument** (measurement) | K=2 label, causal forward filter, 100.0% ±2y stability; 15/18 −15% bears caught, 20d median lag | ✅ Validated |
| **Chapter 1** — regime overlay vs buy-and-hold | "Switching beats B&H" is an exposure artifact (fee inside every null band); vol targeting dominates the overlay (−256 bps, CI excl. 0) | ✅ Closed (one-look spent) |
| **Chapter 2** — state-conditional covariance (ERC) | NULL: +2.8 bps vs unconditional twin (inside all bands), loses −29 bps to a plain EWMA-covariance twin | ✅ Closed (one-look spent) |
| **Probability layer** — confidence margin | KILLED: the filter's evidence margin loses to plain EWMA-vol on Brier *and* AUC across all 8 synthetic DGP cells | ❌ Killed |
| **Chapter 3** — graded state-conditioned exposure dial | Runner + prereg built; the one-look is deliberately **not spent** (scarce, irreversible) | ⏸ Parked |
| **Monitor** (Layer 2 nowcast) | Spec'd claim-by-claim (`MONITOR-VALIDATION-SPEC.md`); `monitor_gate.py` not yet built | 🔨 In build |

Full parked/killed ledger and program framing: `PROGRAM.md`.

---

## What's here

All code is flat in `scripts/` (there is no `src/` package):

**Core pipeline**
- `jumpmodel.py` — estimator: return-only causal features (downside-deviation halflife-10, Sortino halflife-20/60), exact DP state assignment (k=2/k=3 fast paths, verified vs brute force), sparse feature-weighted fit, causal DP-endpoint filter (never smoothed)
- `walkforward.py` — shared expanding walk-forward (annual refits, λ selected causally by 8y-validation Sharpe); imported byte-identically by the synthetic battery and the real runner so the two cannot drift
- `backtest.py` — strategy construction (next-close delay, costs), VT/SMA200/B&H baselines, FKO (Fleming–Kirby–Ostdiek 2001) utility fee, paired stationary bootstrap (Politis–Romano 1994)

**Data**
- `build_panel.py` — French daily panel + SPY cross-check → `data/processed/market_daily.csv` (public Dartmouth URL + yfinance; **no API key**)
- `build_assets.py` — chapter-2 bond/gold assets (this is the only script that needs a FRED key)

**Preregistered batteries (one-looks spent — frozen evidence in `results/`)**
- `run_backtest.py` — chapter-1 battery; refuses to run without `--confirm-frozen`
- `run_allocation.py` + `allocation.py` — chapter-2 ERC allocation battery
- `synthetic_validation.py` — capability battery on simulated panels with known truth (incl. oracle and oracle-lag ceilings)

**Live + reporting**
- `live_label.py` — SPY-splice live tail so the frozen protocol runs to today (French publishes 1–2 months lagged; splice gate corr ≥0.98)
- `build_report.py` — regenerates `results/report.html`, the living program report (status tiles, claims-vs-honest-bar ladder, sensor section)

**Gates & probes** (rerunnable): `calibration_gate.py` (the killed probability layer's reproduction path), `explore_k3.py` (K=3 severity-ladder probe), `validate_sensor.py` (label vs ex-post bear datings).

The primary visual is **`results/report.html`** — open it directly. There is no `figures/` directory yet (figure export is a pending paper task).

---

## Quickstart

Python 3.13 (see `runtime.txt`).

```bash
python -m venv .venv
.venv\Scripts\activate            # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

The frozen chapter-1/2 evidence and the current label are already tracked in `results/` and `data/processed/` — a fresh clone can read every headline number and open `results/report.html` with no network and no keys.

To rebuild the data panel from source (needs network — public Dartmouth French URL + yfinance, no key):

```bash
python scripts/build_panel.py
```

A FRED key (`cp .env.example .env`, set `FRED_API_KEY`) is required **only** for `build_assets.py` (the chapter-2 assets), not for the core pipeline.

```bash
pytest                            # jump-model + backtest test suites
python scripts/live_label.py      # refresh the label's live tail to today
python scripts/build_report.py    # regenerate results/report.html
```

The preregistered batteries (`run_backtest.py`, `run_allocation.py`) are **one-look experiments whose looks are already spent** — they require `--confirm-frozen` and are not meant to be casually rerun. See `CLAUDE.md` and `PROGRAM.md` for the discipline.

---

## Method & discipline (why this is more than a fitted model)

- **Estimator:** statistical jump model — a k-means-like objective plus a jump penalty λ on state changes that enforces persistence, the field's answer to the HMM over-segmentation failure mode. λ=0 recovers k-means; λ→∞ collapses to one state.
- **Causal by construction:** forward filtering only (no smoothed/backtracked labels), expanding windows, parameters frozen per refit. Mechanically unit-tested — perturbing a future value provably cannot change any past state. This is the primary guard against the look-ahead bias that inflates most published regime backtests.
- **Preregistration in git history:** the freeze commit precedes the run; one look per chapter; exposure-matched null bands; reactive co-primary baselines. The protocol is stricter than the papers it engages.

Canonical references: Bemporad/Boyd (2018) and Nystrup–Lindström–Madsen (2020) for the jump model; Nystrup–Kolm–Lindström (2021) for the sparse variant; Shu–Yu–Mulvey (2024) for the regime-allocation application; Hamilton (1989) for the Markov-switching lineage; Moreira–Muir (2017) vs Cederburg et al. (2020) for the vol-managed debate this result speaks to.

---

## History

The v1 program (a sticky HDP-HMM plus four successor formulations, five preregistered nulls) converged and is sealed at git tag `v1-convergence`; its narrative lives in `RESEARCH-RECORD.md` (newest-first) and its code in `archive/research-v1/`. The v2 jump-model program described above superseded it on 2026-07-23.
