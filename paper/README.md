# Paper — build & editing workflow

LaTeX manuscript for the instrument-first regime paper. Built for **robust AI-human co-editing**:
AI-drafted prose is visually flagged so your review is tractable and git diffs stay clean.

## Build

No LaTeX is installed locally. Two easy options:
- **Overleaf** (recommended): upload the `paper/` folder, set `main.tex` as the root document.
- **Local**: install TeX Live / MiKTeX, then `latexmk -pdf main.tex` (run twice for refs/TODO list).

## The editing conventions (why this is set up the way it is)

**1. Blue text = AI-drafted, not yet yours.** Every AI-written passage is wrapped in `\aidraft{...}`
and renders **blue**. When you rewrite a passage in your own voice, **delete the `\aidraft{` and its
closing `}`** (keep the text) — it turns black. The document is a progress bar: a sea of blue that
becomes black as you approve it. "Black = Adam approved" is the only invariant that matters.

**2. Review mode vs clean mode.** Top of `main.tex`:
- `\reviewtrue` → blue highlighting, margin TODO notes, and a **checklist page** (`\listoftodos`) up front.
- `\reviewfalse` → clean render (no colors, no todos) for reading or submission.

**3. Margin action items.** Three flags, all auto-collected onto the checklist page in review mode:
- `\reviewnote{...}` — a question/decision for you (yellow).
- `\needcite{...}` — a missing or unverified citation (orange).
- `\stub{...}` — a section/paragraph not yet written (red, inline).

**4. Numbers are single-sourced.** Every frozen figure is a macro in `numbers.tex` (e.g. `\feeJMVT`,
`\stabJM`). Edit the number **there**, once, and it updates everywhere. Never hard-code a result in a
section. This ties each number to its `results/*.csv` source (noted in `numbers.tex`).

**5. One sentence per line** (semantic line breaks). Sources look odd but git diffs show you *exactly*
which sentence changed — essential for reviewing edits. Keep this convention when you edit.

## File map

```
main.tex          preamble, review toggle, macros, section \input order
numbers.tex       single source of truth for all frozen figures
refs.bib          bibliography (some fields marked % TODO — verify before submission)
sections/         one file per section (edit in isolation, clean diffs)
  00-abstract  01-intro  02-discipline  03-instrument
  04-race1-exposure  05-race2-covariance  06-race3-margin  07-race4-crossasset
  08-mechanism  09-monitor  10-related  11-discussion  12-reproducibility
tables/           tab-exp1, tab-exp2, tab-exp2-arms (booktabs, numbers from numbers.tex)
```

## Status (2026-07-26)

- **Drafted (blue, ready for your edit):** §1 intro, §2 discipline, §3 instrument, §4–6 the first
  three races, §7 the new cross-asset race, §8 mechanism, §10 related, abstract.
- **Stubs (red `\stub`):** §9 monitor (fill from the Track-C build), §11 discussion (survivor
  hypotheses), §12 reproducibility (exact hashes).
- **Known review flags:** §3 stability-is-under-argued note (the referee's first objection); §1
  Shu–Yu–Mulvey exact-headline `\needcite`; figures not yet inserted (OUTLINE figure plan).

## Provenance

- Planning/structure, figure plan, defensibility requirements: `OUTLINE.md` (kept — it's meta, not
  manuscript). Prose that used to live in `DRAFT-SECTIONS.md` and numbers in `TABLES.md` now live in
  the `.tex` files and `numbers.tex` — those two markdown files are superseded (safe to delete).
