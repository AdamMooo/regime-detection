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

### Known gap

`observations/<signal>/<as_of>.json` + `MANIFEST.csv` — the append-only point-in-time
history (plan §5.4) — is **not yet written**. Today only the latest observation is emitted
per signal (`results/<signal>_level0.json`). Until the history exists, a consumer cannot
ask "what did we believe on date X, as of time T?", so no backtest can honestly filter on
`available_at` yet.
