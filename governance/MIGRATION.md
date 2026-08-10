# MIGRATION — moving the systematic-investing stack to a personal machine

Hard stop on the current machine: **2026-08-25**. Written 2026-08-09, baseline verified same day.
Scope: the three internal repos + these governance docs. **Not** in scope: the `C:\dev` Obsidian
vault, `.config-vault` symlinks, `~/.claude/hooks`, or the GSD install — those are a separate
migration.

---

## 0. The short version

Git already carries almost everything. Verified 2026-08-09: all three repos have a **clean
working tree**, **zero unpushed commits**, **zero stashes**, and **no hardcoded absolute paths**
anywhere in `.py/.yml/.json/.ps1`. GitHub Actions secrets live in GitHub and travel by
themselves.

So the move is: three clones, three venvs, **four secret values**, and **one 9.3 MB data folder**.
Everything else is either in git or regenerable.

The only thing that cannot be copied is the **Questrade refresh token** — see §5.

---

## 1. Prerequisites on the new machine

| Requirement | Value on the old machine | Notes |
|---|---|---|
| Python | **3.13.13** | All three venvs. `runtime.txt` pins `python-3.13` in regime-detection and portfolio-manager; algo-trading-bot has no `runtime.txt` but uses the same interpreter. |
| Git | any recent | |
| GitHub auth | account **`AdamMooo`** | All three repos are already personal-owned — **no repo transfer needed**. Authenticate yourself; do not let an agent do it. |
| Disk | ~2.0 GB | Dominated by `algo-trading-bot/.git` (336 MB) and three ~500 MB venvs. |

**Git identity — decide before your first commit.** The old machine committed with the *work*
email:

```
user.name  = Adam
user.email = Adam.Morris@Purpose.ca
```

These are personal repos. If you want future commits attributed to a personal GitHub identity,
set it on the new machine before committing. Past commits keep the work email; that is cosmetic
and not worth rewriting history over (and §12 of `IMPLEMENTATION-PLAN.md` forbids history
rewrites anyway).

---

## 2. Clone

**Put them wherever you want.** The three repos are the only real units. Nothing depends on a
parent folder, its name, or the three being siblings — no repo imports another, and every
cross-repo document reference is an absolute GitHub URL, not a relative path. On the old machine
they happened to sit under a folder called `systematic-investing-research`; that name carries no
meaning and does not need to be recreated.

Clone **regime-detection first** — it carries this file and the rest of the governance docs.

```powershell
git clone https://github.com/AdamMooo/regime-detection.git
git clone https://github.com/AdamMooo/algo-trading-bot.git      # 336 MB of history — slowest
git clone https://github.com/AdamMooo/portfolio-manager.git
```

---

## 3. The copy manifest — what git does NOT carry

Copy these from the old machine. This is the complete list, verified against disk on 2026-08-09.

| # | Path | Size | Why it isn't in git | If you lose it |
|---|---|---|---|---|
| 1 | `portfolio-manager/.env` | 1.6 KB | secrets (`.gitignore:30`) | Recreate from `.env.example` — 5 keys, see §4 |
| 2 | `regime-detection/.env` | 300 B | secrets (`.gitignore:5`) | Recreate from `.env.example` — 1 key |
| 3 | `regime-detection/data/raw/` | **9.3 MB, 11 files** | ignored raw inputs | **Re-downloadable but painful** — see below |
| 4 | `portfolio-manager/data/` | 52 KB, 5 files | ignored local state | `snapshots.json`, `universe.json`, 3 OHLCV parquets. Regenerates on next run, but you lose snapshot history. |

**Do NOT copy:** `.venv/` (rebuild — it is 1.4 GB of the 2.0 GB and is platform-specific),
`__pycache__/`, `.pytest_cache/`, `.ruff_cache/`, `.coverage`.

**Already in git, no action needed:** `regime-detection/data/processed/` (23 tracked panels +
`MANIFEST.csv`), `algo-trading-bot/outputs/bot_state.json`, `algo-trading-bot/outputs/fred_cache.parquet`,
`backtest/data/*.parquet` price cache, and every `.planning/` directory.

### Why `data/raw/` deserves the copy rather than a re-download

`data/processed/` is tracked, so you only need `data/raw/` to *rebuild* the panels. But four of
the eleven files are **manual portal downloads with no API**, and re-fetching them may not
reproduce the same vintage:

- `ie_data.xls` — Shiller, Yale
- `F-F_International_Indices*.zip` (×2) — Ken French data library
- `ff_25_portfolios_5x5.csv`, `ff_factors_daily.csv` — Ken French
- `bab_monthly.xlsx` — AQR

Provenance is tracked in `data/processed/MANIFEST.csv`. Copying the folder is 9.3 MB and removes
all of this risk. Do that.

### Suggested copy command

Run on the **old** machine, targeting a USB drive or OneDrive folder:

```powershell
$stage = 'D:\stack-migration'    # or your OneDrive path
$src   = 'C:\dev\systematic-investing-research'
New-Item -ItemType Directory -Force "$stage\portfolio-manager\data","$stage\regime-detection" | Out-Null
Copy-Item "$src\portfolio-manager\.env"        "$stage\portfolio-manager\.env"
Copy-Item "$src\regime-detection\.env"         "$stage\regime-detection\.env"
Copy-Item "$src\regime-detection\data\raw"     "$stage\regime-detection\raw" -Recurse
Copy-Item "$src\portfolio-manager\data\*"      "$stage\portfolio-manager\data\" -Recurse
Get-ChildItem $stage -Recurse -File | Measure-Object Length -Sum   # expect ~9.4 MB
```

`.env` files contain live credentials. If you stage them in OneDrive, delete the staging folder
once the new machine is verified.

---

## 4. Secrets

### GitHub Actions secrets — nothing to do

Nine secrets across the three repos live in GitHub, attached to the repos, and survive the
machine change untouched:

| Repo | Secrets |
|---|---|
| `algo-trading-bot` | `ALPACA_API_KEY`, `ALPACA_API_SECRET` |
| `portfolio-manager` | `FRED_API_KEY`, `FINNHUB_API_KEY`, `GMAIL_APP_PASSWORD`, `REPORT_EMAIL`, `QUESTRADE_REFRESH_TOKEN`, `GH_PAT`, `REGIME_REPO_PAT` |

GitHub secrets are **write-only** — you cannot read them back onto the new machine. That only
matters for the Questrade token (§5); the others you hold elsewhere.

### Local `.env` files

`regime-detection/.env` — one key:

```
FRED_API_KEY=      # https://fredaccount.stlouisfed.org/apikeys
```

`portfolio-manager/.env` — five keys (see `portfolio-manager/.env.example` for the annotated
version): `QUESTRADE_REFRESH_TOKEN`, `FRED_API_KEY`, `FINNHUB_API_KEY`, `GMAIL_APP_PASSWORD`,
`REPORT_EMAIL`.

`algo-trading-bot` has **no local `.env`** — its credentials exist only as GitHub secrets, which
is correct while trading is paused. `config.py:12-13` accepts either naming
(`APCA_API_KEY_ID`/`APCA_API_SECRET_KEY` or `ALPACA_API_KEY`/`ALPACA_API_SECRET`) if you ever
need a local one.

---

## 5. The Questrade token — the one genuinely hard step

**This is the only part of the move that cannot be solved by copying a file.**

`portfolio-manager`'s Questrade refresh token is **single-use and rotates on every call**. The
live `daily-report.yml` cron (11:30 UTC, Mon–Fri — the only active schedule in the stack)
consumes it and pushes the rotated value back into the GitHub secret via `gh secret set`
(`daily-report.yml:59-66`). Because GH secrets are write-only, the token now in CI **cannot be
retrieved** for local use.

Good news: you cannot break CI by accident. `src/questrade.py:44-49` has a firm code-level guard
that **refuses** to use CI's token from a local machine unless a dedicated `.env.local` exists:

```
Refusing to use the CI Questrade token locally — it is single-use and a local run
would break the scheduled GitHub Actions email.
```

So the failure mode is not corruption, it is simply that **local report runs are blocked** until
a second token exists. The fix is the standing TODO at `NOTES.md:27`.

### Do this before the move (your hands — do not delegate credential steps)

1. Log in at <https://apphub.questrade.com/UI/UserApps.aspx>.
2. Register a **second** personal app, separate from the one CI uses. Local-only, read-only
   scopes are sufficient for the daily brief.
3. Generate its manual refresh token.
4. On the **new** machine, create `portfolio-manager/.env.local` containing only:
   ```
   QUESTRADE_REFRESH_TOKEN=<the second app's token>
   ```
   `.env.local` is already gitignored (`.gitignore:31`), and `questrade.py::_dotenv_target()`
   rotates into it in preference to `.env` when it exists.

Result — two independent self-rotating tokens, no competition, trap closed permanently:

```
BEFORE   CI ──┐
              ├──▶ ONE token ──▶ local runs blocked by the guard
     local ───┘

AFTER    CI    ──▶ token A  (GitHub secret, self-rotating)
         local ──▶ token B  (.env.local,   self-rotating)
```

If you skip this, the rule on moving day is: **pick one token owner.** Either pause
`daily-report.yml` or never run the report locally. Do not try to share one token.

---

## 6. Environment setup, per repo

Same three commands each time, from inside each repo:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Requirements are pinned hardest in regime-detection (16 lines, exact `==` pins including
`numpy==2.4.3`, `pandas==3.0.1`) and loosest in portfolio-manager (11 lines, `>=` ranges) —
expect portfolio-manager to resolve to newer packages than the old machine had. That is the
existing convention; `requirements.txt` stays (no Poetry/uv migration).

---

## 7. Verification — the acceptance test for the move

Baseline measured on the old machine **2026-08-09, all green**. The move is done when the new
machine reproduces these three numbers:

| Repo | Command (from repo root) | Expected |
|---|---|---|
| `regime-detection` | `pytest` | **42 passed** |
| `algo-trading-bot` | `$env:PYTHONPATH='.'; pytest` | **52 passed** |
| `portfolio-manager` | `pytest tests/` | **103 passed** |

```powershell
# run all three at once — $parent is wherever YOU put the clones; no layout is assumed
$parent = 'C:\code'      # <- set this to your own location
foreach ($r in @('regime-detection','algo-trading-bot','portfolio-manager')) {
  Push-Location (Join-Path $parent $r)
  $env:PYTHONPATH = '.'
  & ".\.venv\Scripts\python.exe" -m pytest -q --no-header 2>&1 | Select-Object -Last 1
  Pop-Location
}
```

Then two smoke checks that exercise the copied data and secrets — run each from its own repo root:

```powershell
# algo: must exit without trading (the strategy slot is deliberately empty — D-1)
$env:PYTHONPATH='.'; python main.py --dry-run

# portfolio-manager: exercises .env.local, FRED and Questrade
python scripts\daily_report.py --dry-run     # confirm the flag name against the script first
```

`main.py --dry-run` exiting without placing orders is the **correct** outcome, not a failure —
the bot has no validated strategy by design (`IMPLEMENTATION-PLAN.md` §3.5).

---

## 8. What keeps running during and after the move

GitHub Actions are machine-independent, so the move does not interrupt them:

| Workflow | Schedule | State |
|---|---|---|
| `portfolio-manager/daily-report.yml` | `30 11 * * 1-5` | **LIVE** — keeps emailing throughout. The only active cron. |
| `portfolio-manager/weekly-regime-brief.yml` | commented | parked until content lands |
| `algo-trading-bot/trading.yml` | all crons commented | **paused 2026-08-09** (Step 0a). Resume = uncomment. `workflow_dispatch` still works. |
| `algo-trading-bot/ci.yml`, `regime-detection/tests.yml` | on push | unaffected |

**Nothing needs switching off for the move.** The old machine can go dark without stopping the
daily brief.

---

## 9. Known drift to be aware of on a fresh clone

Found while preparing this document. None blocks the migration; all would confuse a fresh setup.

### Fixed 2026-08-09

| Location | Issue |
|---|---|
| `algo-trading-bot/CLAUDE.md` "First-time setup" / "Running" | Told a fresh clone to run `python -m regime.train`, `python -m backtest.regime_replay` and `scripts/daily_regime_report.py` — **all three deleted** in the strip-down (`9f6e4a28`). A fresh setup following them failed at step one. Rewritten. |
| `regime-detection/CLAUDE.md:73` | Claimed "26 passing"; actual is **42**. Corrected — this closes the `IMPLEMENTATION-PLAN.md` §10 "test counts not verified" item for all three repos (42 / 52 / 103, measured). |
| 15 references to `../IMPLEMENTATION-PLAN.md` etc. across both consumer repos | Would have dangled after the governance docs moved. All rewritten to `../regime-detection/governance/…`, depth-corrected (`.planning/STATE.md` was already off by one level before the move). |

### Found and deliberately NOT fixed — the top follow-up

**`algo-trading-bot/CLAUDE.md` describes a repository that no longer exists.** Its pause block
says *"Everything below this block describes the repo as it is TODAY, pre-strip-down… it will be
rewritten when the strip-down lands."* **The strip-down landed** (`9f6e4a28`, −15,382 lines), so
roughly 200 lines of that file now document deleted code as current: the 2-HMM ensemble and its
feature table, `RegimeEnsemble.combine()`, the gauge/report boundary rules, regime-conditional
cadence, and the equal-weight-with-HIGH_VOL-top-N sizing that D-1 removed from the live path.

This is the single highest-value thing to fix before the machine change. It is not a migration
blocker — nothing breaks — but it is the file every future session reads first, and after the move
it will confidently describe machinery that isn't there. `IMPLEMENTATION-PLAN.md` §10 already
carries the row ("rewrite the framing section around the six monetization questions"); it was not
completed in Step 0b.

`algo-trading-bot/README.md` is the same problem in the public-facing doc, and arguably worse: its
directory tree and command list still document `regime_detector.py`, `regime_replay.py`,
`daily_regime_report.py`, `rank_model_candidates.py` and `outputs/models/` — every one deleted.

(An earlier revision of this section claimed `outputs/models/FROZEN.md` still carried a stale
reference. It does not exist at all — the whole directory was deleted in the strip-down and is
recoverable at `b1f3fa3e`. The hub file `algo-trading-bot.md:27` still cites it.)

---

## 10. Checklist

Before 2026-08-25, on the old machine:

- [ ] `git status` clean and `git push` current in all three repos (verified clean 2026-08-09)
- [ ] Second Questrade app registered, token in hand (§5)
- [ ] Copy manifest staged — 4 items, ~9.4 MB (§3)
- [ ] Governance docs pushed inside `regime-detection` (done 2026-08-09)

On the new machine:

- [ ] Python 3.13 installed; git identity set (§1)
- [ ] Three clones as siblings (§2)
- [ ] Copy manifest restored (§3)
- [ ] `.env.local` created with the second app's token (§5)
- [ ] Three venvs built (§6)
- [ ] **42 / 52 / 103 tests green** (§7)
- [ ] `main.py --dry-run` exits without trading (§7)
- [ ] One successful local `daily_report.py` run
- [ ] Staging folder with `.env` files deleted
