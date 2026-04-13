"""
Streamlit dashboard for regime detection results visualization.

Slim version: Shows regime labels, probabilities, and trust scorecard only.
Analysis and feature diagnostics have been moved to separate analyze_*.py scripts.

Run: streamlit run dashboard.py
"""

import os
import json
import pandas as pd
import numpy as np
import streamlit as st
from pathlib import Path
import re
import logging
import time
import functools

from config import DATA_DIR, MODEL_DIR


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _validate_and_fix_color(color_str: str, fallback: str = '#999999') -> str:
    """
    Validate hex color; if invalid, log warning and return fallback.

    Valid formats:
    - #RRGGBB (6-digit)
    - #RGB (3-digit, expanded to 6)
    - #RRGGBBAA (8-digit with alpha)

    Args:
        color_str: Color string to validate
        fallback: Fallback color if validation fails (default: #999999)

    Returns:
        Validated hex color string
    """
    if not isinstance(color_str, str):
        logger.warning(f"Color is not string: {color_str}, using fallback {fallback}")
        return fallback

    color_str = color_str.strip()

    # 8-digit (with alpha)
    if re.match(r'^#[0-9A-Fa-f]{8}$', color_str):
        return color_str

    # 6-digit
    if re.match(r'^#[0-9A-Fa-f]{6}$', color_str):
        return color_str

    # 3-digit → expand to 6
    if re.match(r'^#[0-9A-Fa-f]{3}$', color_str):
        r, g, b = color_str[1], color_str[2], color_str[3]
        return f'#{r}{r}{g}{g}{b}{b}'

    # Invalid format
    logger.warning(f"Invalid hex color '{color_str}', using fallback {fallback}")
    return fallback


def _validate_data_and_impute(data: pd.DataFrame, data_name: str, strategy: str = 'forward_fill') -> pd.DataFrame:
    """
    Validate data for NaN/missing values. Log warnings if found.
    Impute if strategy='forward_fill', else drop rows with NaN.

    Parameters
    ----------
    data : DataFrame
        Input data to validate
    data_name : str
        Description for logging (e.g., "regime_probs")
    strategy : str
        'forward_fill' or 'drop'

    Returns
    -------
    DataFrame (with missing values handled)
    """
    n_missing = data.isna().sum().sum()
    if n_missing > 0:
        pct_missing = 100 * n_missing / (data.shape[0] * data.shape[1])
        logger.warning(f"{data_name}: {n_missing} missing values ({pct_missing:.1f}%)")

    if strategy == 'forward_fill':
        return data.ffill().bfill()
    else:
        return data.dropna()


def profile_render_time(func):
    """Decorator to profile rendering time."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - start
        logger.info(f"{func.__name__} render time: {elapsed:.2f}s")
        return result
    return wrapper


def load_regime_results():
    """Load regime results from CSV."""
    results_path = os.path.join(DATA_DIR, 'regime_results.csv')
    if os.path.exists(results_path):
        df = pd.read_csv(results_path, index_col=0, parse_dates=True)
        return df
    return None


def load_trust_scorecard():
    """Load trust scorecard from JSON."""
    scorecard_path = os.path.join(DATA_DIR, 'trust_scorecard.json')
    if os.path.exists(scorecard_path):
        try:
            with open(scorecard_path, 'r') as f:
                return json.load(f)
        except:
            return None
    return None


def display_current_regime(results):
    """Display current regime label with confidence."""
    if results is None or len(results) == 0:
        st.warning("No regime results available")
        return

    try:
        current = results.iloc[-1]
        regime_name = current.get('regime_name', 'Unknown')
        regime_prob = current.get('regime_prob', 0)

        # Color code by regime
        regime_colors = {
            'Low-Vol': '#2ecc71',      # Green
            'Medium-Vol': '#f39c12',   # Orange
            'High-Vol': '#e74c3c',     # Red
        }
        color = _validate_and_fix_color(regime_colors.get(regime_name, '#95a5a6'))

        # Display in columns
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(
                "Current Regime",
                regime_name,
                f"{regime_prob:.1%} confidence"
            )
        with col2:
            st.metric(
                "VIX",
                f"{current.get('VIX', 0):.1f}",
                "Market volatility index"
            )
        with col3:
            st.metric(
                "Date",
                current.name.strftime("%Y-%m-%d"),
                "Most recent trading day"
            )
    except Exception as e:
        logger.error(f"Failed to render current regime display: {e}")
        st.warning(f"Could not display current regime: {str(e)[:100]}")


def display_regime_probabilities(results):
    """Display regime probability time series."""
    if results is None or len(results) == 0:
        return

    try:
        # Extract probability columns
        prob_cols = [c for c in results.columns if c.startswith('prob_')]
        if not prob_cols:
            st.warning("No probability data available")
            return

        st.subheader("Regime Probabilities Over Time")

        # Validate and impute missing data
        prob_df = results[prob_cols].copy()
        prob_df = _validate_data_and_impute(prob_df, "regime_probabilities", strategy='forward_fill')
        prob_df.columns = [c.replace('prob_', 'Regime ') for c in prob_cols]

        st.line_chart(prob_df)

        # Show summary statistics
        with st.expander("Probability Statistics"):
            st.dataframe(prob_df.describe())
    except Exception as e:
        logger.error(f"Failed to render regime probabilities: {e}")
        st.warning(f"Could not render probability chart: {str(e)[:100]}")


def display_trust_scorecard(scorecard):
    """Display trust scorecard (validation results)."""
    if scorecard is None:
        st.info("No trust scorecard available")
        return

    st.subheader("Trust Scorecard")
    st.write("Regime detection validation checks:")

    # Display checks as table
    checks = scorecard.get('checks', {})
    check_data = []

    for check_name, result in checks.items():
        status = "✓ PASS" if result.get('passed', False) else "✗ FAIL"
        message = result.get('message', '')
        check_data.append({
            'Check': check_name,
            'Status': status,
            'Details': message
        })

    if check_data:
        st.dataframe(pd.DataFrame(check_data), use_container_width=True)
    else:
        st.info("No validation checks recorded")

    # Overall summary
    overall_passed = scorecard.get('all_passed', False)
    if overall_passed:
        st.success("✓ All validation checks passed")
    else:
        st.warning("⚠ Some validation checks failed")


def display_recent_regime_switches(results):
    """Display recent regime switches (dates and transitions)."""
    if results is None or len(results) < 2:
        return

    try:
        st.subheader("Recent Regime Switches")

        # Find regime changes
        regime_col = 'regime_name' if 'regime_name' in results.columns else results.columns[0]
        regimes = results[regime_col]

        switches = []
        for i in range(1, len(regimes)):
            if regimes.iloc[i] != regimes.iloc[i - 1]:
                switches.append({
                    'Date': results.index[i].strftime("%Y-%m-%d"),
                    'From': regimes.iloc[i - 1],
                    'To': regimes.iloc[i],
                })

        # Show last 10 switches
        if switches:
            switches_df = pd.DataFrame(switches[-10:])
            st.dataframe(switches_df, use_container_width=True)
        else:
            st.info("No regime switches detected in recent data")
    except Exception as e:
        logger.error(f"Failed to render regime switches: {e}")
        st.warning(f"Could not display regime switches: {str(e)[:100]}")


@profile_render_time
def main():
    """Main dashboard application with error boundary."""
    try:
        st.set_page_config(
            page_title="Regime Detection Dashboard",
            page_icon="📊",
            layout="wide"
        )

        st.title("Regime Detection Dashboard")
        st.write("Real-time market regime detection and validation.")

        # Load data
        results = load_regime_results()
        scorecard = load_trust_scorecard()

        if results is None:
            st.error("❌ No regime results found. Run 'python run.py' to generate results.")
            return

        # Display sections
        st.divider()
        display_current_regime(results)

        st.divider()
        display_regime_probabilities(results)

        st.divider()
        display_trust_scorecard(scorecard)

        st.divider()
        display_recent_regime_switches(results)

        # Footer
        st.divider()
        st.caption(
            "Analysis scripts available: "
            "`python analyze_feature_importance.py`, "
            "`python analyze_regime_characterization.py`, "
            "`python analyze_signal_quality.py`"
        )
    except Exception as e:
        logger.error(f"Dashboard rendering failed: {e}", exc_info=True)
        st.error(f"Dashboard rendering error: {str(e)[:200]}. Check logs for details.")


if __name__ == '__main__':
    main()
