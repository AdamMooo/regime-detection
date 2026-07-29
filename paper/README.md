# Paper — one file, one process

**The paper is `main.tex`** — a single self-contained LaTeX file (preamble + number macros +
all sections + tables inlined). No modular scaffold, no build script: edit one file, compile
one file. (Collapsed from the old 15-file modular layout 2026-07-29 — "one paper, simpler
process." The section boundaries survive as `% >>> begin sections/…` comments if you ever want
to split again.)

## Build

No LaTeX installed locally. Either:
- **Overleaf** (recommended): upload `paper/`, set `main.tex` as root.
- **Local**: TeX Live / MiKTeX, then `latexmk -pdf main.tex` (run twice for refs + the TODO list).

## Editing conventions

- **Blue text = AI-drafted, not yet yours.** Wrapped in `\aidraft{...}`. Rewrite it in your voice,
  delete the `\aidraft{` + closing `}` (keep the text) → it turns black = approved. The doc is a
  progress bar: blue → black.
- **Review toggle** (top of `main.tex`): `\reviewtrue` shows blue + margin TODOs + a checklist page;
  `\reviewfalse` = clean submission render.
- **Margin flags** (auto-collected on the checklist page): `\reviewnote{}` (decision for you),
  `\needcite{}` (missing citation), `\stub{}` (not yet written).
- **Numbers single-sourced** as macros in the preamble (e.g. `\feeJMVT`, `\stabJM`) — edit once,
  updates everywhere; never hard-code a result.
- **One sentence per line** (semantic line breaks) so git diffs show exactly which sentence changed.

## Status — WORKING DRAFT, not done

Drafted (blue): abstract, §1–8, §10. Stubs: §9 monitor, §11 discussion, §12 reproducibility.

What's left (was `OUTLINE.md`'s next-actions, folded here):
1. **Fold in the two new nulls** — Path-B cross-asset timing (loses to VT at every exposure) and
   the dispersion 4th-feature lead that **failed international confirmation** (Japan +154d, Europe
   +94d; the clean "candidate that didn't survive out-of-sample" story). Both in RESEARCH-RECORD
   2026-07-29.
2. **§3 instrument** — the stability-is-under-argued objection (pair every stability number with a
   skill number; harden the perturbation; add a deterministic vol-threshold baseline).
3. **§1 intro** — quote Shu–Yu–Mulvey's exact baselines; resolve the `\needcite`.
4. **Wire `refs.bib`** — no `\bibliography` in `main.tex` yet; citations aren't live.
5. **Figures** — export from the report machinery to `paper/fig/`.
6. **Exact-numbers appendix** — from `stage1.csv`, `allocation_summary.csv`, `sensor_validation.csv`.
