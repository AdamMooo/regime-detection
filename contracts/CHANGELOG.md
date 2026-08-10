# Observation contract — changelog

`market-observation-v1.schema.json` is the canonical, language-neutral contract for market
observation records produced by this repository. Consumers **vendor** a pinned copy plus a
sha256 assertion; they do not import Python from here. Drift therefore shows up as a red
test in the consumer, not as a runtime mismatch.

Distribution is deliberate duplication made safe by a checksum. A shared package would
couple three release cycles, which is the thing the three-repo architecture exists to
prevent.

## Compatibility rules

- **Additive, optional fields** → same version.
- **A new required field, a removed field, a narrowed enum, or any change that makes a
  previously-valid record invalid** → new major version and a new file. `v1` is never
  edited in place once a consumer has vendored it.
- `spec_version` inside a record is a `const`. A record always states which contract it
  was written against.

## 1.0 — 2026-08-09

First published version. Implements the interface design in
[IMPLEMENTATION-PLAN.md §5](../governance/IMPLEMENTATION-PLAN.md).

**Point-in-time identity.** `as_of` (the date described) and `available_at` (the instant
computable) are both required, and neither is derivable from the other. Backtests filter
on `available_at`. For revised series it is first-print availability, never the revision
timestamp. Per-source lag policy lives in `scripts/data_vintage.py` so it can be reviewed
rather than buried.

**`rarity.basis` is an enum, not prose.** `expanding` · `trailing_fixed` (requires
`window`) · `full_sample` (`window` must be null). A percentile without its reference
distribution is uninterpretable, and the three are not comparable — this resolves the
cross-repo audit's D2 finding at the interface.

**`full_sample` cannot be `production`.** Enforced structurally in both validators. A
full-sample rank embeds the future distribution in a past reading, so it leaks; the
schema refuses to let such a measurement claim production maturity. Same treatment for
`assessment.mechanism = rejected`.

**Closed allowlists throughout** (`additionalProperties: false` at every level). This,
not the denylist, is the real enforcement: a decision field renamed to something benign
is rejected for being *unknown*. Every numeric leaf carries `units`, which removes the
natural shape a smuggled weight would take.

**`maturity` is the only behaviour-bearing field**, asserted by a test that fails if a
new enumerated top-level field appears.

### Amendments to the plan's §5.2 sketch, made while migrating the live emitters

Both were forced by real records and are flagged for review rather than absorbed silently:

1. **`reading` is `{value, units, estimator}` plus optional `secondary_readings[]`.** The
   plan sketched a single flat reading, but the live signals carry genuine extra
   descriptors (volatility's GARCH shock half-life, stock-bond's z-score). Free-form
   per-signal keys would be unparseable for a consumer; dropping them would lose real
   information. Secondary readings keep them, each with its own units.

2. **`assumption_state {status, derivation}` added, nested and optional.** Assumption-monitor
   signals legitimately carry `intact` / `under_test` / `violated`. It is nested so that
   `maturity` remains the only *top-level* behaviour-bearing field, `derivation` is
   mandatory so the label is always reproducible from `reading.value`, and the contract
   states that consumers may not branch on it. This answers the repo's standing objection
   that one word destroys graded information: the label adds no axis, only convenience.

### Amendment to the plan's §5.4 layout — the point-in-time history

**Shipped** as `observations/<signal>/history.ndjson` + `MANIFEST.csv`, written by
`scripts/observation_history.py`. Volatility (1,187 records, 1927-07-30 → 2026-05-29)
and stock-bond correlation (750 records, 1963-12-31 → 2026-05-31). Valuation is
deliberately absent while its R9 disposition is open — publishing an observation
record for it would pre-empt a decision that is Adam's.

The plan specified one JSON file per `as_of`. Two problems with that, both found while
implementing it, so the layout changed and the reasons are recorded here rather than
absorbed silently:

1. **It cannot express its own correction model.** §5.4 says a correction is "a new
   record with a later `available_at`" — but a path keyed on `as_of` alone holds
   exactly one record, so the first correction must either overwrite (destroying the
   append-only guarantee stated in the same paragraph) or have nowhere to go.
2. **Daily granularity is redundant, 22× over.** Volatility has 25,938 `as_of` dates
   but only **1,187 distinct `available_at` vintages** — Ken French publishes monthly,
   so every day in a month shares one publication instant. A consumer's only
   legitimate filter is `available_at <= T`, under which vintage-mates are
   indistinguishable. 26k files / ~52MB bought no answerable question.

So: **one NDJSON log per signal, appended to, never rewritten.** Emission is on the
vintage grid — the freshest `as_of` per publication instant, which is what a consumer
standing at that instant could actually have read. Each line is canonical JSON (sorted
keys, tight separators) so `sha256(line)` equals both the `MANIFEST.csv` hash and the
hash `supersedes` cites; the manifest is a regenerated index, the log is the artifact.
A record whose `(as_of, available_at)` is already present with different content is
**refused**, which is the guarantee the log exists for.

`MANIFEST.csv` carries one column beyond the plan's four: **`provenance`**
(`reconstructed` | `live`). It marks a distinction that would otherwise be silent —
see below.

### These records are RECONSTRUCTIONS, not contemporaneous prints

Nobody was running this pipeline in 1927. Every backfilled record answers a
counterfactual: *if this signal, as specified and signed off today, had been running
from the start, what would it have read at each vintage?* The two halves have
different standing and a consumer must not conflate them:

- **Causal and honestly point-in-time — every data-derived number.** Each record is
  built by the live `build_record()` on `df.loc[:as_of]`, so one code path produces
  the history and the live reading, and nothing after `as_of` is in scope. A test
  asserts reading and rarity equal the committed descriptor at every `as_of`, which
  is what carries `assert_causal`'s upstream guarantee through the slice.
- **Not point-in-time — the specification.** Estimator, assessment axes, `maturity`,
  calibration prose. A 1930 record carries a maturity derived from a 2026-08-06
  sign-off.

The second is unavoidable — it is true of any backtest of a signal designed today —
but stating it is not optional, because a consumer reading `maturity: production` on
a 1930 row would otherwise believe it was earned then.

### Two live defects the backfill exposed

Both were latent in the emitters and would have fired on any short panel, not only in
backfill — a newly launched signal or a short regional history would have hit them:

1. **`trend.level_percentile_change` was NaN during burn-in**, which serializes as
   bare `NaN` — invalid strict JSON that no non-Python consumer can parse — and
   `direction` reported `"flat"`, asserting flatness the data does not support. Now
   `null` for both, and `canonical_bytes` uses `allow_nan=False` so the failure is
   loud rather than silent.
2. **`stockbond_level0` dropped on `corr` alone**, so a record could be emitted
   during the rarity burn-in with `level_pctile` NaN — where every comparison in
   `_band()` is False and it silently returned `"very high"`. `level_pctile` is now in
   the dropna, which is also what D-02b requires: no status without the number *and*
   its rarity.
