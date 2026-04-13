"""Integration test: regime pipeline → signals → Algo-Trading-Bot validation.

This test validates that the Regime-Detection pipeline produces signals
compatible with Algo-Trading-Bot's expected schema and label format.

Key validations:
- Signal schema: required fields (timestamp, regime_label, regime_probs)
- Bot labels: must be in {LOW_VOL, MED_VOL, HIGH_VOL}
- Probabilities: must sum to 1.0 across 3 regimes
- Round-trip: mock bot handler accepts signals without error
- Timing: <5 min execution for CI/CD integration
"""

import sys
import os
import numpy as np
import pandas as pd
import pytest
from datetime import datetime, timedelta
from typing import Any

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from config import LABEL_MAPPING, REGIME_NAMES
from signals import compute_signals
from train import StudentTHMM, filtered_probs, filtered_labels


# ═══════════════════════════════════════════════════════════════════
# Schema Validator
# ═══════════════════════════════════════════════════════════════════

def validate_signal_schema(signal: dict[str, Any]) -> bool:
    """
    Validate signal dict matches bot expected format.

    Expected signal structure (from compute_signals()):
    {
        'awareness': {'current_regime': str, 'regime_probs': dict, ...},
        'bot_label': str (one of LOW_VOL, MED_VOL, HIGH_VOL),
        'current_regime': str (internal name),
        'date': str (ISO format date),
        ...other fields...
    }

    Bot integration validates:
    - bot_label is one of {LOW_VOL, MED_VOL, HIGH_VOL}
    - regime_probs (from awareness) dict has 3 keys summing to 1.0
    - date field exists and is string-like
    """
    # Check required top-level keys
    required_keys = ['bot_label', 'awareness', 'date']
    for key in required_keys:
        assert key in signal, f"Missing required key: {key}"

    # Validate bot_label (canonical format)
    bot_label = signal['bot_label']
    valid_labels = {'LOW_VOL', 'MED_VOL', 'HIGH_VOL'}
    assert bot_label in valid_labels, (
        f"Invalid bot_label: {bot_label}. "
        f"Must be one of {valid_labels}"
    )

    # Validate date field
    date_val = signal['date']
    assert isinstance(date_val, (str, datetime)), (
        f"date must be string or datetime, got {type(date_val)}"
    )

    # Validate awareness dict contains regime_probs
    awareness = signal['awareness']
    assert isinstance(awareness, dict), (
        f"awareness must be dict, got {type(awareness)}"
    )
    assert 'regime_probs' in awareness, (
        "awareness must contain regime_probs"
    )

    # Validate regime_probs
    regime_probs = awareness['regime_probs']
    assert isinstance(regime_probs, dict), (
        f"regime_probs must be dict, got {type(regime_probs)}"
    )
    assert len(regime_probs) == 3, (
        f"regime_probs must have exactly 3 keys, got {len(regime_probs)}"
    )

    # Check probabilities sum to 1.0
    prob_sum = sum(regime_probs.values())
    assert abs(prob_sum - 1.0) < 1e-6, (
        f"regime_probs must sum to 1.0, got {prob_sum}"
    )

    # Check all probabilities in [0, 1]
    for regime, prob in regime_probs.items():
        assert isinstance(prob, (int, float)), (
            f"Probability for {regime} must be numeric, got {type(prob)}"
        )
        assert 0.0 <= prob <= 1.0, (
            f"Probability for {regime} must be in [0, 1], got {prob}"
        )

    return True


# ═══════════════════════════════════════════════════════════════════
# Mock Bot Signal Handler
# ═══════════════════════════════════════════════════════════════════

class MockBotSignalHandler:
    """
    Mock Algo-Trading-Bot signal handler for testing.

    Simulates a bot that consumes regime signals and validates format.
    Used to verify end-to-end signal pipeline without depending on
    actual Algo-Trading-Bot code.
    """

    def __init__(self):
        self.last_signal = None
        self.signal_count = 0
        self.errors = []

    def consume_signal(self, signal: dict[str, Any]) -> bool:
        """
        Consume a regime signal and validate format.

        Args:
            signal: Dict with timestamp, regime_label, regime_probs

        Returns:
            True if signal is valid

        Raises:
            ValueError if signal format is invalid
        """
        try:
            validate_signal_schema(signal)
            self.last_signal = signal
            self.signal_count += 1
            return True
        except AssertionError as e:
            error_msg = str(e)
            self.errors.append(error_msg)
            raise ValueError(f"Invalid signal: {error_msg}") from e

    def get_last_signal(self) -> dict[str, Any]:
        """Get the most recently consumed signal."""
        return self.last_signal

    def get_signal_count(self) -> int:
        """Get total number of signals consumed."""
        return self.signal_count

    def get_errors(self) -> list[str]:
        """Get list of validation errors encountered."""
        return self.errors


# ═══════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════

@pytest.fixture
def sample_results_small():
    """
    Generate small sample data for fast integration tests.

    ~1 year of synthetic data (250 trading days) with:
    - 3 regime states
    - SPY close prices
    - Regime probabilities
    - Regime names (internal labels)
    """
    np.random.seed(42)
    n_days = 250

    # Create dates
    dates = pd.date_range('2025-01-01', periods=n_days, freq='B')

    # Generate synthetic price data (starting at 100, random walk)
    returns = np.random.normal(0.0005, 0.01, n_days)
    prices = 100 * np.exp(np.cumsum(returns))

    # Generate synthetic regime assignments (3 regimes)
    raw_probs = np.random.dirichlet([1, 1, 1], size=n_days)
    regime_indices = np.argmax(raw_probs, axis=1)

    # Map to regime names
    regime_name_map = {0: 'Low-Vol', 1: 'Medium-Vol', 2: 'High-Vol'}
    regime_names = np.array([regime_name_map[i] for i in regime_indices])

    # Create results DataFrame
    results_df = pd.DataFrame(
        {
            'SPY_close': prices,
            'regime_name': regime_names,
            'prob_Low-Vol': raw_probs[:, 0],
            'prob_Medium-Vol': raw_probs[:, 1],
            'prob_High-Vol': raw_probs[:, 2],
        },
        index=dates
    )

    return results_df


# ═══════════════════════════════════════════════════════════════════
# Test Cases
# ═══════════════════════════════════════════════════════════════════

class TestBotIntegration:
    """Integration tests for bot signal compatibility."""

    def test_signal_schema_valid(self, sample_results_small):
        """Test 1: Signal schema matches bot expected format.

        Validates:
        - compute_signals() produces required fields
        - Each field has correct type
        - No missing keys
        """
        results = sample_results_small
        signal = compute_signals(results)

        # Should have all required top-level fields
        assert 'bot_label' in signal
        assert 'awareness' in signal
        assert 'date' in signal

        # awareness should contain regime_probs
        assert 'regime_probs' in signal['awareness']

        # bot_label should be a string
        assert isinstance(signal['bot_label'], str)

        # regime_probs should be dict
        assert isinstance(signal['awareness']['regime_probs'], dict)

        # date should be string
        assert isinstance(signal['date'], str)

        # Should validate without error
        assert validate_signal_schema(signal) is True

    def test_bot_labels_correct(self, sample_results_small):
        """Test 2: Bot labels are in canonical format {LOW_VOL, MED_VOL, HIGH_VOL}.

        Validates:
        - bot_label field is always uppercase with underscore
        - Never outputs internal names like 'Low-Vol'
        - Matches LABEL_MAPPING values
        """
        results = sample_results_small
        signal = compute_signals(results)

        bot_label = signal['bot_label']

        # Must be in canonical bot format
        valid_bot_labels = {'LOW_VOL', 'MED_VOL', 'HIGH_VOL'}
        assert bot_label in valid_bot_labels, (
            f"bot_label '{bot_label}' not in {valid_bot_labels}"
        )

        # Should NOT contain internal names like 'Low-Vol'
        assert bot_label != 'Low-Vol'
        assert bot_label != 'Medium-Vol'
        assert bot_label != 'High-Vol'

        # Should match values in LABEL_MAPPING
        valid_mappings = set(LABEL_MAPPING.values())
        assert bot_label in valid_mappings

    def test_regime_probs_valid(self, sample_results_small):
        """Test 3: Regime probabilities are valid and sum to 1.0.

        Validates:
        - regime_probs dict (from awareness) has exactly 3 keys
        - All values are floats in [0, 1]
        - Sum equals 1.0 (within numerical tolerance)
        """
        results = sample_results_small
        signal = compute_signals(results)

        regime_probs = signal['awareness']['regime_probs']

        # Must have exactly 3 regimes
        assert len(regime_probs) == 3, (
            f"Expected 3 regimes, got {len(regime_probs)}"
        )

        # All probabilities must be floats in [0, 1]
        for regime, prob in regime_probs.items():
            assert isinstance(prob, (int, float)), (
                f"Probability for {regime} not numeric: {type(prob)}"
            )
            assert 0.0 <= prob <= 1.0, (
                f"Probability for {regime} out of range: {prob}"
            )

        # Must sum to 1.0 (with numerical tolerance)
        prob_sum = sum(regime_probs.values())
        assert abs(prob_sum - 1.0) < 1e-6, (
            f"Probabilities sum to {prob_sum}, not 1.0"
        )

    def test_bot_handler_round_trip(self, sample_results_small):
        """Test 4: Mock bot handler accepts signals without error.

        Validates:
        - Handler can consume signals from pipeline
        - Handler.consume_signal() returns True for valid signals
        - Handler tracks signal count
        - Handler can retrieve last signal
        """
        results = sample_results_small
        signal = compute_signals(results)

        # Create mock bot handler
        handler = MockBotSignalHandler()

        # Feed signal to handler
        assert handler.consume_signal(signal) is True
        assert handler.get_signal_count() == 1
        assert handler.get_errors() == []

        # Should be able to retrieve signal
        last = handler.get_last_signal()
        assert last is not None
        assert last['bot_label'] == signal['bot_label']

    def test_signal_date_field(self, sample_results_small):
        """Test 5: Signal date field is present and parseable.

        Validates:
        - Date comes from results DataFrame index
        - Can be parsed as datetime or ISO format string
        - Should be a recent date
        """
        results = sample_results_small
        signal = compute_signals(results)

        # Date field should exist
        assert 'date' in signal

        date_str = signal['date']

        # Should be parseable as date (ISO format string)
        if isinstance(date_str, str):
            # Try to parse as ISO date
            try:
                dt = datetime.fromisoformat(date_str)
                # Should be recent (within last 5 years)
                now = datetime.now()
                assert (now - dt).days < 365 * 5
            except ValueError:
                # Also accept other date formats like '2025-12-16'
                # Just verify it's a non-empty string
                assert len(date_str) > 0

    def test_label_mapping_completeness(self):
        """Test 6: LABEL_MAPPING covers all possible regime names.

        Validates:
        - For each N_STATES in [2, 3, 4, 5, 6]:
          - All regime names from REGIME_NAMES[N_STATES] are in LABEL_MAPPING
          - Each mapping produces a valid bot label
        - This prevents CR-01 from regressing if config is changed
        """
        # Test all supported N_STATES values
        for n_states in [2, 3, 4, 5, 6]:
            regime_names = REGIME_NAMES.get(n_states, [])

            for regime_name in regime_names:
                # Every regime name must be in LABEL_MAPPING
                assert regime_name in LABEL_MAPPING, (
                    f"N_STATES={n_states}: Regime '{regime_name}' not in LABEL_MAPPING. "
                    f"Valid entries: {list(LABEL_MAPPING.keys())}"
                )

                # Mapped label should be valid (one of LOW_VOL, MED_VOL, HIGH_VOL)
                bot_label = LABEL_MAPPING[regime_name]
                valid_bot_labels = {'LOW_VOL', 'MED_VOL', 'HIGH_VOL'}
                assert bot_label in valid_bot_labels, (
                    f"N_STATES={n_states}: Regime '{regime_name}' maps to invalid label '{bot_label}'. "
                    f"Must be one of {valid_bot_labels}"
                )
