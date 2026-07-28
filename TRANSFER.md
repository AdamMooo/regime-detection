# Transfer to Personal Computer — Unified Briefs Projects

Moving `regime-detection`, `vol-diagnostics`, `portfolio-manager` from the work laptop to a
personal machine. **Channel: git only** (USB blocked, no Claude artifact — nothing tied to the
work Claude account). All three remotes are personal GitHub (`AdamMooo/*`).

Delete this file after the move is confirmed.

---

## Transparency verdict (audited 2026-07-27)

- **No LLM / Claude / Anthropic dependency** in any of the three. No Anthropic key needed. The
  `.claude/` folders and `CLAUDE.md` are editor scaffolding; code runs without them.
- **No workplace services.** No internal Purpose API, no corporate AWS, no `@purpose.ca`.
- The only "corporate-looking" infra (vol-diagnostics Oracle box `40.233.113.63` + OCI bucket)
  is a **personal** Oracle Cloud free-tier account, and is optional for a local run.
- All email → personal Gmail (`adam.morris0201@gmail.com`). All data sources public/free.
- `.planning/` and `CLAUDE.md` are **tracked** in all three → GSD state + Obsidian hubs travel
  via git. Only `.claude/` (Claude Code local toggles) is gitignored in vol-diagnostics /
  portfolio-manager — re-established by the personal config-vault, not a loss.

---

## PART A — do on the WORK computer (before it's "moved")

### regime-detection
- [ ] Commit + push `scripts/regime_signal.py` (the regime-signal scaffold; `persistence_gauge()`
      still `TODO(human)`).
- [ ] Decide on untracked `paper/full-draft.tex` — commit if wanted, else it stays behind.
- [ ] Commit + push this `TRANSFER.md`.
- [ ] (Hygiene) Rotate the FRED key committed in `.env:3` — it's a free key, not work-bound, but
      exposed on disk. Can also be done personal-side.

### vol-diagnostics
- [ ] **Push the 5 unpushed commits** (GSD milestone/roadmap state — lost if not pushed).
- [ ] Decide on modified `scripts/update.sh` — commit if the change is wanted.
- [ ] The two `out_preview_*.html` are disposable dry-run outputs — ignore/delete.
- [ ] **Back up `out/` history to OCI** so the personal machine can restore it:
      `python -m engine.backup_to_oci` (or trust the last daily GitHub Actions run, which does this).
      `out/` is gitignored, so this is the ONLY way the accrued history crosses.

### portfolio-manager
- [ ] **Push the 2 unpushed commits** (docs/GSD state).
- [ ] Tree is otherwise clean — nothing else to stage.

### Cross-cutting
- [ ] Confirm each `git push` succeeded (all three remotes are `AdamMooo/*`).
- [ ] Note which personal accounts own the API keys you'll regenerate on the other side
      (FRED, Finnhub — free; Questrade; Gmail app password; OCI). Do NOT git your `.env` files —
      recreate them personally.

---

## PART B — do on the PERSONAL computer (after clone)

### Per repo
- [ ] `git clone` all three from personal GitHub; venv per repo; `pip install -r requirements.txt`.
- [ ] Recreate each `.env` from `.env.example` with personal keys.
- [ ] **regime-detection:** run the data fetch (`scripts/build_panel.py`, `build_assets.py`) to
      regenerate the gitignored `data/` CSVs (public French/FRED/yfinance). Finish
      `persistence_gauge()` in `regime_signal.py`.
- [ ] **vol-diagnostics:** `python -m engine.restore_from_oci` to pull `out/` history (or cold-start
      and re-accrue). Delete stray `.streamlit/secrets.toml`. Swap/blank the hardcoded Oracle IP if
      not self-hosting.
- [ ] **portfolio-manager:** generate a **fresh Questrade refresh token** (old one expires); add a
      Gmail app password if you want email; fix WSL `/home/adam` paths in `scripts/run_report.sh` +
      `setup_task.ps1` if scheduling locally.

### Obsidian + GSD workflow wiring (personal vault)
- [ ] Clone the repos into the personal vault root so Obsidian indexes them.
- [ ] Add each project's hub to the personal `INDEX.md` (vault-level; doesn't travel with the repo).
- [ ] Re-establish the `.config-vault` symlink for each repo's `.claude/` via the personal
      `link.ps1` (the work symlinks don't cross).
- [ ] Run the personal `gsd-hub-sync` to rebuild the `_planning/{project}/` live mirror hardlinks.
- [ ] `.planning/` content itself already arrived via git — this step only re-wires the vault-level
      surfaces around it.

### Optional — automation
- [ ] If re-hosting on personal GitHub Actions: re-add the workflow secrets (SMTP/Gmail, Questrade
      + `GH_PAT`, OCI) under the personal account, or delete the workflows and schedule locally.

---

## What travels vs. what you rebuild

| | Travels via git | Rebuilt on personal (gitignored) |
|---|---|---|
| regime-detection | all code, `.planning/`, `CLAUDE.md`, hub | `data/` CSVs (refetch), `.env` |
| vol-diagnostics | all code, `.planning/`, `CLAUDE.md`, GH workflow | `out/` history (OCI restore), `.env`, `.claude/` |
| portfolio-manager | all code, `.planning/`, `CLAUDE.md`, GH workflow | `.env` (fresh Questrade token), `.claude/` |
