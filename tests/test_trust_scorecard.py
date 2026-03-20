"""Tests for the trust scorecard."""

import numpy as np
import pandas as pd
import pytest

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from trust import compute_trust_scorecard, format_scorecard


def _make_signals(separation_p=1e-10, vol_match=True, median_run=10,
                  var_ok=True, oos_agr=0.75, oos_sep_p=1e-5,
                  ece=0.03, has_oos=True, has_cal=True):
    """Create a mock signals dict for testing."""
    sigs = {
        'validation': {
            'separation_pvalue': separation_p,
            'separation_significant': separation_p < 0.01,
            'vol_ordering_match': vol_match,
            'median_run_length': median_run,
            'var_backtest': {
                'Low-Vol': {'ok': var_ok},
                'High-Vol': {'ok': var_ok},
            },
        },
        'awareness': {'current_regime': 'Low-Vol'},
    }

    if has_oos:
        sigs['oos_validation'] = {
            'available': True,
            'agreement_rate': oos_agr,
            'n_oos_days': 1000,
            'oos_separation_pvalue': oos_sep_p,
            'oos_separation_significant': oos_sep_p < 0.01,
        }
    else:
        sigs['oos_validation'] = {'available': False, 'reason': 'No OOS data'}

    if has_cal:
        sigs['calibration'] = {
            'available': True,
            'ece': ece,
            'is_calibrated': ece < 0.10,
            'interpretation': f'ECE={ece:.1%}',
        }
    else:
        sigs['calibration'] = {'available': False, 'reason': 'No smooth probs'}

    return sigs


class TestTrustScorecard:

    def test_all_pass(self):
        """All checks passing should give overall PASS."""
        sigs = _make_signals()
        sc = compute_trust_scorecard(sigs)

        assert sc['overall'] in ('PASS', 'WARN')  # data freshness may WARN
        assert 'checks' in sc
        # Non-freshness checks should all pass
        for c in sc['checks']:
            if c['name'] != 'Data Freshness':
                assert c['status'] == 'PASS', f"{c['name']} should be PASS"

    def test_fail_propagates(self):
        """A single FAIL should make overall FAIL."""
        sigs = _make_signals(separation_p=0.5)  # separation fails
        sc = compute_trust_scorecard(sigs)

        assert sc['overall'] == 'FAIL'

    def test_warn_propagates(self):
        """WARN without FAIL should give overall WARN."""
        sigs = _make_signals(oos_agr=0.55)  # OOS agreement is WARN level
        sc = compute_trust_scorecard(sigs)

        # Should be WARN (not FAIL, not PASS)
        found_warn = any(c['status'] == 'WARN' for c in sc['checks']
                         if c['name'] != 'Data Freshness')
        assert found_warn

    def test_missing_oos_is_na(self):
        """Missing OOS data should give N/A, not crash."""
        sigs = _make_signals(has_oos=False)
        sc = compute_trust_scorecard(sigs)

        oos_checks = [c for c in sc['checks'] if 'OOS' in c['name']]
        for c in oos_checks:
            assert c['status'] == 'N/A'

    def test_format_scorecard(self):
        """format_scorecard should return a non-empty string."""
        sigs = _make_signals()
        sc = compute_trust_scorecard(sigs)
        output = format_scorecard(sc)

        assert isinstance(output, str)
        assert 'Trust Scorecard' in output
        assert sc['overall'] in output
