# Research Charter Template

**Template version: v0.1-draft**

The research charter is the pre-registration front-matter subset of the 8-attribute signal spec
(`signal-spec-template.md`). It is written and dated **BEFORE any implementation**. No signal (Phases 2–10)
is implemented before its charter exists — see `validation-standards.md` §Charter before implementation.

The charter is the registered-report Stage-1 artifact: it is frozen before the validation look and answers
exactly the six questions below, in order. It maps onto template attributes 1 / 2 / 5 / 6 / 8. Carries the
same semver version line as the spec it precedes.

---

## Header

- **Signal name** —
- **Assumption monitored** —
- **Charter/spec version** — semver (e.g. `v0.1-draft`)
- **Charter dated** — the date this charter was frozen (before implementation)

---

## The six charter questions

### 1. What question does the signal answer?

Maps to spec attribute 1 (Definition).

### 2. What market assumption does it monitor?

The ledger key. Maps to spec attribute 1 / header.

### 3. What mechanism supports it — why does it survive being known?

The written structural reason (risk-premium or risk-management channel). Maps to spec attribute 2 and is
gated by `validation-standards.md` §The mechanism gate.

### 4. What evidence would validate it?

The descriptive property to test, including the out-of-hypothesis-sample (Japan / Europe) confirmation bar.
Maps to spec attribute 5.

### 5. What would falsify it?

The declared-before-testing structural failure modes and the specific results that would kill the signal.
Maps to spec attribute 6.

### 6. What does it explicitly NOT claim?

The per-signal boundary statement: it names a monitored market assumption and STOPS; it implies no action.
Maps to spec attribute 8.

---
<!-- LINKS:AUTO -->
## Related
**Project:** [[_planning/regime-detection/ROADMAP|ROADMAP]] · [[_planning/regime-detection/STATE|STATE]] · [[regime-detection/regime-detection|Hub]]
<!-- LINKS:END -->
