# Coding Conventions

**Analysis Date:** 2026-05-11

## Naming Patterns

**Files:**
- `snake_case.py` for all modules and scripts
- `src/` package modules use `snake_case` subdirectories

**Functions:**
- `snake_case` function names
- Verb phrases for actions: `fetch_spx_data()`, `apply_threshold_rules()`, `fit_parametric_hmm()`

**Variables:**
- `snake_case` for local variables and DataFrame columns
- Constants in `UPPER_SNAKE_CASE` inside `src/config.py`

**Types:**
- No explicit type aliases detected beyond function signatures in modern Python style

## Code Style

**Formatting:**
- No formal formatter config detected
- Code currently uses standard Python indentation and line breaks

**Linting:**
- No linter configuration detected (`.flake8`, `ruff.toml`, `.pylintrc` absent)

## Import Organization

**Order:**
1. Standard library imports (e.g. `os`, `datetime`)
2. Third-party imports (e.g. `pandas`, `numpyro`, `yfinance`)
3. Local imports from `src.*`

## Error Handling

**Patterns:**
- Limited explicit error handling
- Scripts raise exceptions on data fetch or model failures
- `print()` used for progress and debugging

## Logging

**Framework:**
- None; uses `print()` only

## Comments

**When to Comment:**
- Module docstrings describe script purpose
- Inline comments are minimal and used for simple explanations

**JSDoc/TSDoc:**
- Not used

## Function Design

**Size:**
- Functions are small and task-focused in `src/` (data fetch, baseline apply, model fit)

**Parameters:**
- Optional parameters mostly absent; functions directly read config constants or DataFrame columns

**Return Values:**
- Data-producing functions return `pandas.DataFrame`
- Model functions return model results and/or updated DataFrame

## Module Design

**Exports:**
- No explicit `__all__` declarations
- Public functions are imported directly from modules

**Barrel Files:**
- `src/__init__.py` exists, but `src` is not used as an import package alias in experiments

---

*Convention analysis: 2026-05-11*

---
LINKS:AUTO
