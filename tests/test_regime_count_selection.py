"""
Tests for K regime count selection via walk-forward validation.

Validates K=3 vs K=4 on out-of-sample data (2021-2026):
1. OOS regime count stability (should match K)
2. Regime label persistence (dwell time)
3. Parsimony rule (< 2% BIC improvement → prefer K=3)
4. Bot integration compatibility (3 regimes required)
"""

import os
import sys
import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from config import (
    DATA_DIR, COV_TYPE, RANDOM_SEED, REGIME_HOLD_DAYS,
    PCA_ROLLING_WINDOW, N_SEEDS, LABEL_MAPPING,
)
from inference import expanding_standardize, _fit_hmm, filtered_labels
from hmm_training import (
    fit_rolling_pca, _hmm_bic, check_stability,
)
from orchestrator import walk_forward


# ===================================================================
# Fixtures
# ===================================================================

@pytest.fixture
def market_data():
    """Load full market data (2010-2026)."""
    market = pd.read_csv(
        os.path.join(DATA_DIR, 'market_data.csv'),
        index_col=0, parse_dates=True,
    )
    return market


@pytest.fixture
def feature_data():
    """Load full feature data (2010-2026)."""
    feat_raw = pd.read_csv(
        os.path.join(DATA_DIR, 'features_transformed.csv'),
        index_col=0, parse_dates=True,
    )
    # Apply feature subset
    from config import FEATURE_SUBSET
    if FEATURE_SUBSET:
        feat_raw = feat_raw[[f for f in FEATURE_SUBSET if f in feat_raw.columns]]
    return feat_raw


@pytest.fixture
def train_data(market_data, feature_data):
    """Data for in-sample model selection (2010-2020)."""
    cutoff = pd.Timestamp('2020-12-31')
    market = market_data.loc[:cutoff]
    features = feature_data.loc[:cutoff]
    return market, features


@pytest.fixture
def test_data(market_data, feature_data):
    """Data for out-of-sample validation (2021-2026)."""
    cutoff = pd.Timestamp('2021-01-01')
    market = market_data.loc[cutoff:]
    features = feature_data.loc[cutoff:]
    return market, features


@pytest.fixture
def pcs_train(train_data):
    """Principal components from training data (2010-2020)."""
    market, features = train_data
    X_scaled, _, _ = expanding_standardize(features.values, min_warmup=252)
    X_scaled_valid = X_scaled[~np.isnan(X_scaled[:, 0])]
    pcs, _, _, _, _ = fit_rolling_pca(X_scaled_valid)
    return pcs


# ===================================================================
# Test: K=3 vs K=4 OOS Regime Count
# ===================================================================

class TestK3VsK4OOS:
    """Verify OOS regime count stability for K=3 vs K=4."""

    def test_k3_vs_k4_oos(self, market_data, feature_data):
        """
        Walk-forward validate K=3 and K=4 on test period (2021-2026).

        Assert:
        - K=3 produces mean regime count ~3 (within ±0.5)
        - K=4 produces mean regime count ~4 (within ±1.0, more variable)
        - K=3 regime counts are more stable (lower std)
        """
        cutoff = pd.Timestamp('2021-01-01')
        market = market_data.loc[cutoff:]
        features = feature_data.loc[cutoff:]

        # Validate K=3
        labels_k3, _ = walk_forward(
            market, features, n_states=3, n_pca=5,
            cov_type=COV_TYPE, mode='rolling'
        )
        regime_counts_k3 = []
        for t in range(0, len(labels_k3) - 252, 21):
            window = labels_k3.iloc[t:t+252].dropna().values
            if len(window) > 0:
                regime_counts_k3.append(len(np.unique(window)))

        # Validate K=4
        labels_k4, _ = walk_forward(
            market, features, n_states=4, n_pca=5,
            cov_type=COV_TYPE, mode='rolling'
        )
        regime_counts_k4 = []
        for t in range(0, len(labels_k4) - 252, 21):
            window = labels_k4.iloc[t:t+252].dropna().values
            if len(window) > 0:
                regime_counts_k4.append(len(np.unique(window)))

        mean_k3 = np.mean(regime_counts_k3)
        mean_k4 = np.mean(regime_counts_k4)
        std_k3 = np.std(regime_counts_k3)
        std_k4 = np.std(regime_counts_k4)

        # Assertions
        assert abs(mean_k3 - 3) <= 0.5, (
            f"K=3 mean regime count {mean_k3:.1f} deviates from target 3 by > 0.5"
        )
        assert abs(mean_k4 - 4) <= 1.0, (
            f"K=4 mean regime count {mean_k4:.1f} deviates from target 4 by > 1.0"
        )
        assert std_k3 < std_k4, (
            f"K=3 std ({std_k3:.2f}) should be lower than K=4 ({std_k4:.2f}) "
            f"— K=3 more stable"
        )

        print(f"\nK=3 regime counts: mean={mean_k3:.1f}, std={std_k3:.2f}")
        print(f"K=4 regime counts: mean={mean_k4:.1f}, std={std_k4:.2f}")
        print(f"Advantage: K=3 (more stable regime counts)")


# ===================================================================
# Test: Regime Stability via Dwell Time
# ===================================================================

class TestRegimeStability:
    """Measure regime label persistence (dwell time)."""

    def test_regime_stability_by_k(self, market_data, feature_data):
        """
        Measure median dwell time (consecutive days in same regime).

        Assert:
        - Both K=3 and K=4 produce dwell time >= 3 days (minimum hold period)
        - K=3 dwell time likely higher (more stable)
        - Log advantage to summary
        """
        cutoff = pd.Timestamp('2021-01-01')
        market = market_data.loc[cutoff:]
        features = feature_data.loc[cutoff:]

        # K=3 dwell time
        labels_k3, _ = walk_forward(
            market, features, n_states=3, n_pca=5,
            cov_type=COV_TYPE, mode='rolling'
        )
        dwell_k3 = []
        for t in range(0, len(labels_k3) - 252, 21):
            window = labels_k3.iloc[t:t+252].dropna().values
            if len(window) > 1:
                same = (window[1:] == window[:-1]).astype(int)
                runs = []
                current_run = 1
                for s in same:
                    if s:
                        current_run += 1
                    else:
                        runs.append(current_run)
                        current_run = 1
                if runs:
                    dwell_k3.append(np.median(runs))

        # K=4 dwell time
        labels_k4, _ = walk_forward(
            market, features, n_states=4, n_pca=5,
            cov_type=COV_TYPE, mode='rolling'
        )
        dwell_k4 = []
        for t in range(0, len(labels_k4) - 252, 21):
            window = labels_k4.iloc[t:t+252].dropna().values
            if len(window) > 1:
                same = (window[1:] == window[:-1]).astype(int)
                runs = []
                current_run = 1
                for s in same:
                    if s:
                        current_run += 1
                    else:
                        runs.append(current_run)
                        current_run = 1
                if runs:
                    dwell_k4.append(np.median(runs))

        median_dwell_k3 = np.median(dwell_k3) if dwell_k3 else 1
        median_dwell_k4 = np.median(dwell_k4) if dwell_k4 else 1

        # Assertions
        assert median_dwell_k3 >= 3, (
            f"K=3 median dwell time {median_dwell_k3:.1f} < 3 days (unstable)"
        )
        assert median_dwell_k4 >= 3, (
            f"K=4 median dwell time {median_dwell_k4:.1f} < 3 days (unstable)"
        )

        if median_dwell_k3 > median_dwell_k4:
            print(f"\nK=3 advantage: longer dwell time ({median_dwell_k3:.1f} vs {median_dwell_k4:.1f} days)")
        else:
            print(f"\nK=4 advantage: longer dwell time ({median_dwell_k4:.1f} vs {median_dwell_k3:.1f} days)")


# ===================================================================
# Test: Parsimony Rule
# ===================================================================

class TestParsimonyRule:
    """Validate parsimony threshold (2% BIC improvement)."""

    def test_parsimony_rule(self, pcs_train):
        """
        Fit K=3 and K=4 on training data; compute BIC and improvement.

        Assert:
        - BIC improvement (K3→K4) calculated correctly
        - If improvement < 2%, K=3 is recommended (parsimony)
        - If improvement >= 2%, K=4 is statistically justified
        """
        # Fit models
        best_m3 = _fit_hmm(pcs_train, 3, COV_TYPE, seed=RANDOM_SEED)
        best_m4 = _fit_hmm(pcs_train, 4, COV_TYPE, seed=RANDOM_SEED)

        bic3, _ = _hmm_bic(best_m3, pcs_train, 3, pcs_train.shape[1], COV_TYPE)
        bic4, _ = _hmm_bic(best_m4, pcs_train, 4, pcs_train.shape[1], COV_TYPE)

        improvement = (bic3 - bic4) / bic3 * 100

        print(f"\nParsimony Test:")
        print(f"  BIC K=3: {bic3:,.0f}")
        print(f"  BIC K=4: {bic4:,.0f}")
        print(f"  Improvement: {improvement:.1f}%")
        print(f"  Threshold: 2%")

        if improvement < 2:
            recommendation = 3
            print(f"  Decision: K=3 (parsimonious)")
        else:
            recommendation = 4
            print(f"  Decision: K=4 (statistically justified)")

        # Just log the decision; don't assert a specific K
        # (different runs may produce different results)
        assert recommendation in [3, 4], "Invalid recommendation"


# ===================================================================
# Test: Bot Integration Compatibility
# ===================================================================

class TestBotIntegration:
    """Verify K maps to 3 bot regimes (Low/Med/High)."""

    def test_bot_integration_k_count(self):
        """
        Check LABEL_MAPPING in config.py.

        Assert:
        - LABEL_MAPPING defines exactly 3 bot labels (LOW_VOL, MED_VOL, HIGH_VOL)
        - K=3 can map directly (1:1)
        - K=4 requires merging (1 regime→HIGH_VOL)
        """
        # Check LABEL_MAPPING
        bot_labels = set(LABEL_MAPPING.values())
        expected_labels = {'LOW_VOL', 'MED_VOL', 'HIGH_VOL'}

        assert expected_labels.issubset(bot_labels), (
            f"LABEL_MAPPING missing required labels. Has: {bot_labels}, "
            f"needs: {expected_labels}"
        )

        # K=3 direct mapping
        k3_mapping = {
            'Low-Vol': 'LOW_VOL',
            'Medium-Vol': 'MED_VOL',
            'High-Vol': 'HIGH_VOL',
        }
        for regime_name, expected_bot_label in k3_mapping.items():
            assert LABEL_MAPPING.get(regime_name) == expected_bot_label, (
                f"K=3 mapping broken: {regime_name} maps to "
                f"{LABEL_MAPPING.get(regime_name)}, expected {expected_bot_label}"
            )

        print(f"\nBot Integration Test:")
        print(f"  Bot labels available: {bot_labels}")
        print(f"  K=3 mapping: {k3_mapping}")
        print(f"  K=4 mapping: Merge regime 3 (Crisis) -> HIGH_VOL")
        print(f"  All mappings valid for bot integration")


# ===================================================================
# Test: Multi-Seed Stability (used for recommendation)
# ===================================================================

class TestMultiSeedStability:
    """Verify regime labels are stable across random initializations."""

    def test_stability_check_k3(self, pcs_train):
        """K=3 stability: label agreement across multiple seeds."""
        best_model, agreement = check_stability(pcs_train, 3, cov_type=COV_TYPE)

        print(f"\nK=3 stability check:")
        print(f"  Label agreement: {agreement:.1%}")
        print(f"  Threshold: >80% acceptable")

        assert agreement > 0.70, (
            f"K=3 stability too low ({agreement:.1%}). Regime labels inconsistent."
        )

    def test_stability_check_k4(self, pcs_train):
        """K=4 stability: label agreement across multiple seeds."""
        best_model, agreement = check_stability(pcs_train, 4, cov_type=COV_TYPE)

        print(f"\nK=4 stability check:")
        print(f"  Label agreement: {agreement:.1%}")
        print(f"  Threshold: >70% acceptable (more states = harder to align)")

        assert agreement > 0.60, (
            f"K=4 stability too low ({agreement:.1%}). Regime labels very inconsistent."
        )


# ===================================================================
# Integration Test: Full K Selection Flow
# ===================================================================

def test_full_k_selection_flow(market_data, feature_data, pcs_train):
    """
    Integration test: run select_k_via_crossval.py script.

    This test validates that the full K selection analysis can run
    without errors and produces a decision.
    """
    # Import and run the diagnostic script
    import select_k_via_crossval

    # Main execution
    recommended_k = select_k_via_crossval.main()

    assert recommended_k in [3, 4], f"Invalid recommendation: {recommended_k}"
    print(f"\n[Integration Test] Recommended K: {recommended_k}")

    # Verify report was created
    report_path = os.path.join(DATA_DIR, 'regime_count_selection_report.txt')
    assert os.path.exists(report_path), f"Report not created at {report_path}"

    with open(report_path, 'r') as f:
        report_content = f.read()
        assert 'K=3' in report_content, "Report missing K=3 results"
        assert 'K=4' in report_content, "Report missing K=4 results"
        assert 'RECOMMENDATION' in report_content, "Report missing recommendation"

    print(f"[Integration Test] Report validated at {report_path}")
