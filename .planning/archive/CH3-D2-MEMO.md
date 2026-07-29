# D2 Memo — Is Episode Age the Right Next Hypothesis?

Status: research memo, 2026-07-23. Requested by Adam before the D2 ruling and Rev-3
freeze. No prereg changes, no runs. Question: should M2 (episode age/hazard) enter
chapter 3, or is age an ex-post descriptive coordinate that will not survive
conditioning on VT and strict OOS testing?

## 1. What is actually established (Adam's five claims)

1. K=3 states statistically stable — ESTABLISHED (probe: 1.000 agreement, both ±2y shifts).
2. K=3 = severity tiers, not phase labels — ESTABLISHED at the descriptive level (state
   moments are vol tiers; rebound-heavy state = majority state; loading is phase-tilted
   beyond a matched vol threshold, but no state IS a phase).
3. Episode age carries information about future returns/risk — SUGGESTED ONLY
   (episode_anatomy age profile; descriptive, overlapping windows, ~20 effective episodes
   in the sweet-zone bins, era-concentrated, bins read off the full-sample curve).
4. Age adds information BEYOND (sigma-hat, S) — NOT ESTABLISHED. Nothing run so far
   conditions the age effect on the vol path.
5. That increment survives costs/OOS as a decision improvement — NOT ESTABLISHED.

The probe resolved M3. It supplied ZERO new evidence about age. Any D2 ruling that
upgrades M2 must therefore rest on evidence that predates Rev 1 — i.e., on the anatomy
alone, which is claim-3-level.

## 2. The economics: what would have to be TRUE for tau to matter beyond sigma-hat

The math (I(R_{t+h}; tau | sigma-hat, S) > 0) only has content if some economic process
makes duration informative given current risk. Two candidate mechanisms, both with
literature standing:

- **Slow-moving capital / liquidity-provision timing** (Duffie 2010 AFA address;
  Grossman-Miller 1988; Nagel 2012 "Evaporating Liquidity", RFS 25(7)): after a shock,
  forced deleveraging exhausts itself and liquidity providers arrive with delay; the
  returns to bearing risk are concentrated in the weeks after the shock and DECAY.
  CAVEAT (verified against the source, 2026-07-23): Nagel's liquidity-provision returns
  are highly predictable with the VIX LEVEL — so this premium is at least partly a level
  story that sigma-hat conditioning may already span; the delay/sequence component
  (Duffie) is the only part tau can uniquely claim. Strengthens the case that the
  reactive/vol-conditioned race (§4b) is mandatory, not optional.
- **Duration as Bayesian learning about shock type** (duration-dependent regime
  switching: Maheu-McCurdy 2000 JBES; Lunde-Timmermann 2004; hidden semi-Markov models:
  Bulla-Bulla 2006): a mixture of technical corrections (die young) and fundamental
  repricings (grind on) makes survival itself informative — the longer stress lasts, the
  more likely it is fundamental, the worse the conditional risk/reward. Formally: M2
  asserts the regime process is SEMI-MARKOV (dwell-time-dependent), while the JM/HMM
  class assumes geometric (memoryless) dwell. The anatomy's non-monotone hazard is a
  descriptive rejection of memorylessness. This is the standard-literature framing of
  the whole hypothesis, and it is testable on the LABEL SEQUENCE ALONE.
  CAVEAT (external check, 2026-07-23): the SIGN of duration dependence is CONTESTED in
  this literature — Maheu-McCurdy find declining hazards in both bull and bear markets,
  while Cochran-Defina, Ohn-Taylor-Pagan, and Harman-Zuehlke find positive duration
  dependence on similar US data. The field disagrees about the very object M2 conditions
  on; sensitivity to bull/bear dating method is a known cause. External precedent FOR
  the state-is-not-the-phase idea: a five-state hidden semi-Markov model finds "not all
  bull and bear markets are alike" (Risk Management, 2022 — 3 bull + 2 bear states);
  post-crash vol relaxation also has documented structure (Omori-law power-law decay,
  Lillo-Mantegna) — though that structure is computable from the vol series itself,
  i.e., reactive.

The counter-story (why tau may be already-in-VT):

- tau is strongly correlated with the SHAPE of the vol path: early episode = vol rising,
  sweet zone = vol has peaked and is mean-reverting, grind = vol elevated again.
  w = sigma*/sigma-hat already re-levers mechanically as vol falls off the peak — VT
  partially HARVESTS the exhaustion premium without knowing tau. Moreira-Muir 2017 works
  precisely because premia lag vol; some of the "age effect" is that lag wearing a new
  coordinate. The testable residual claim is only the increment AFTER the vol path is
  conditioned on.
- The reactive-age degeneracy: tau is computed from the label, the label from returns.
  "Days since a plain sigma-hat trigger" (tau_vol) is a two-line incumbent. If
  E[R | tau_JM] ~= E[R | tau_vol], the JM contributes nothing to the duration story and
  an age chapter is really a vol-machinery chapter.

## 3. Why the anatomy bins cannot become a strategy

The 6-42d sweet zone was identified by inspecting the full forward-return curve —
garden of forking paths. Effective sample is ~20 episodes (not 332 days: overlapping
21d windows within clustered episodes). The 127+ grind bin is 5 episodes, two eras.
The prereg's Rev-1 cure (frozen LOW-dimensional monotone/unimodal h(tau), parameters fit
per refit on training data only) prevents bin-mining at run time, but it cannot cure the
fact that the HYPOTHESIS was selected on the same panel the one look would score.

## 4. What can validate/kill claims 3-4 WITHOUT spending the look

In rough order of value per unit of contamination risk:

- (a) **Planted-effect synthetic capability test** (chapter-1 idiom: oracle/lag
  decomposition). Simulate semi-Markov panels with a KNOWN duration-dependent Sharpe
  profile; verify the g(S, tau) machinery harvests it net of costs at realistic detection
  lag, and measure the minimum effect size the design can detect. If the pipeline cannot
  recover a planted tau effect of plausible magnitude, chapter-3-with-M2 is underpowered
  and should not be run. Zero real-data contact.
- (b) **Reactive-age race, descriptive, US** (already-inspected data; no new look):
  compute tau_vol (days since sigma-hat crossed a frozen threshold) and compare age
  profiles E[R_fwd | tau_JM] vs E[R_fwd | tau_vol], plus the age profile within
  sigma-hat level bands (the poor man's conditioning for claim 4). If JM-age collapses
  onto vol-age, M2's delta is dead on arrival.
- (c) **Era-split robustness of the existing age profile** (1990-2007 vs 2008-2026):
  costs nothing, uses only already-described data; kills the hypothesis early if the
  sweet zone is one era's artifact.
- (d) **Label-only semi-Markov test**: duration-dependence of the exit hazard on the
  label sequence alone (no returns touched) — instrument work, fully clean.
- (e) **International panels: DO NOT SCREEN.** Using Japan/Germany/UK now to check the
  age profile would partially spend the designated out-of-hypothesis-sample confirmation
  set. Recommendation: preserve all three; (a)-(d) provide the pre-freeze screening.

## 5. The D2 recommendation, revisited

There is also a design problem with putting M2 into chapter 3 at all, independent of
validation status: **it breaks single-delta.** A3 = VT x g(S, tau) differs from A2 = VT
by TWO conceptual ingredients (the state dial AND the age modulation). A positive would
be unattributable; a null would be ambiguous between "state adds nothing" and "age
spoiled the map." Chapter 3's boxed question — does the STATE improve exposure beyond
VT — is answered by the two-point hard-label dial alone.

The state-only dial also has its own honest economic content (it is not a re-run of
chapter 1): S is a persistence-filtered DOWNSIDE-vol threshold, so its delta vs
sigma-hat is hysteresis — VT re-levers into every vol lull inside a grind; g_stress < 1
says "stay cautious through in-episode lulls." That is a real, falsifiable mechanism
(the fee, if any, should concentrate on within-episode vol-lull days), and it gives the
expected-null a clean reading: even hysteresis on top of VT adds nothing at daily cadence.

**Recommendation:**

- **D2 = registered null branch for chapter 3**: A3 = VT x g(S), two-point hard label
  (single free parameter g_stress, fit per refit on training data), registered prior =
  interpolates to VT / null. Single-delta preserved; this IS the original boxed question.
- **M2 is deferred to a chapter-4 candidate** with its own prereg, gated on passing
  (a)-(d) above, with tau_vol (reactive age) as the mandatory co-incumbent and
  Japan/Germany/UK preserved for confirmation. If (b)/(c) kill the age effect
  descriptively, we saved the look; if they don't, chapter 4 starts from a validated
  mechanism instead of an attractive table.

Deviation note (defensibility): this deviates from the Rev-1 conditional rule's letter
(neg-M3 -> M2). The deviation is PRE-FREEZE, moves toward the more conservative branch,
and uses no information about age that arrived after the rule was written (the probe
said nothing about age). The rule's purpose — preventing a post-hoc CHOICE between M2
and M3 after seeing which looked better — is not implicated: M3 died on its own terms,
and M2 is not being promoted on new evidence but demoted on design logic. Recorded here
precisely so a referee can check that reasoning.

## 6. What this means operationally (if Adam concurs)

1. Rev 3 freeze: D2 = registered null; A3 = two-point hard-label dial; everything else
   unchanged (D1 daily, D3 w_max=1.0, arms/falsifiers/metrics as Rev 2).
2. Cooling-off: overnight gap, named+dated sign-off, one look. Expected null; completes
   the negative paper's arc (binary overlay failed; graded probability layer failed its
   gate; the hard dial is the last coherent daily-cadence use).
3. In parallel (no look, no prereg needed yet): screens (a)-(d) for the M2/chapter-4
   decision. International panels remain untouched.

## 7. External validation (2026-07-23 search — sources verified, not repo-internal)

- Maheu-McCurdy duration-dependent switching and Lunde-Timmermann bull/bear duration:
  verified; NEW information: the sign of duration dependence is contested across authors
  (declining vs positive hazards on similar data) — folded into §2 as a caveat. Their
  "best gains come at the start of a bull market" independently echoes our young-bull
  honeymoon (Sharpe 1.29).
- Nagel 2012 RFS verified; nuance folded into §2: liquidity-provision returns load on
  the VIX LEVEL, so part of the "post-shock premium" is vol-spanned — raises the bar for
  claim 4 exactly where the memo already put the burden (the tau_vol race).
- HSMM/semi-Markov in finance verified (Bulla-Bulla 2006 CSDA; five-state HSMM "not all
  bull and bear markets are alike," Risk Management 2022; robust HSMM estimation, Annals
  of OR 2024) — the model-class framing of M2 is standard and current.
- NOT FOUND in the searched literature: any direct test of "stress-episode age adds
  information beyond current volatility" as an exposure input. Claim 4 is APPARENTLY
  UNDEREXPLORED (Adam's wording, 2026-07-23 — a statement about our search, not a novelty
  claim) — which cuts both ways: no external validation exists to borrow, and no external
  refutation either.

---
<!-- LINKS:AUTO -->
## Related
**Project:** [[regime-detection/regime-detection|Hub]]
<!-- LINKS:END -->
