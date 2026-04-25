# Deferred Items — Phase 07 Plan 03

## Pre-existing Issues (Out of Scope)

1. **test_dashboard_refactor.py::TestDashboardLoading::test_dashboard_loads_regime_results**
   - `ModuleNotFoundError: No module named 'dashboard'`
   - Pre-existing failure on base commit cd07baa
   - Not caused by Plan 07-03 changes

2. **test_regime_results_schema.py — prob_Moderate-Vol vs prob_Medium-Vol mismatch**
   - Test expects `prob_Moderate-Vol` but actual model output uses `prob_Medium-Vol`
   - config.py REGIME_NAMES for K=3 is `['Low-Vol', 'Medium-Vol', 'High-Vol']`
   - Plan spec used "Moderate-Vol" but production data uses "Medium-Vol"
   - Pre-existing naming drift; not introduced by Plan 07-03
   - Fix would require either: updating test to check `prob_Medium-Vol`, or
     renaming regime in config (would break downstream consumers)
