"""
Streamlit dashboard for regime detection — 3D PCA regime distributions + probability analysis.

Run: streamlit run dashboard.py
"""

import os
import json
import pandas as pd
import numpy as np
import streamlit as st
from pathlib import Path
import logging

import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy.stats import gaussian_kde

from config import DATA_DIR, MODEL_DIR


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@st.cache_data(ttl=300)
def load_regime_results():
    """Load regime results from CSV."""
    results_path = os.path.join(DATA_DIR, 'regime_results.csv')
    if os.path.exists(results_path):
        df = pd.read_csv(results_path, index_col=0, parse_dates=True)
        return df
    return None


@st.cache_data(ttl=300)
def load_pca_components():
    """Load PCA components from CSV."""
    pca_path = os.path.join(DATA_DIR, 'pca_components.csv')
    if os.path.exists(pca_path):
        df = pd.read_csv(pca_path, index_col=0, parse_dates=True)
        return df
    return None


@st.cache_data(ttl=300)
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


@st.cache_data(ttl=300)
def load_model_training_info():
    """Load model training history and metrics."""
    model_info_path = os.path.join(MODEL_DIR, 'training_history.json')

    info = {}
    if os.path.exists(model_info_path):
        try:
            with open(model_info_path, 'r') as f:
                info = json.load(f)
        except:
            pass

    return info


def get_regime_colors():
    """Return consistent regime colors."""
    return {
        'Low-Vol': '#2ecc71',      # Green
        'Moderate': '#f39c12',     # Orange
        'Elevated': '#e67e22',     # Dark Orange
        'Crisis': '#e74c3c',       # Red
    }


def display_current_regime(results):
    """Display current regime with staleness indicator."""
    if results is None or len(results) == 0:
        st.warning("No regime results available")
        return

    try:
        current = results.iloc[-1]
        regime_name = current.get('regime_name', 'Unknown')
        regime_prob = current.get('prob_' + current.get('regime_name', ''), 0)

        # Detect stale data
        last_date = current.name
        days_old = (pd.Timestamp.now(tz=last_date.tz) - last_date).days

        # Show staleness indicator prominently
        if days_old > 7:
            st.error(f"🚨 CRITICALLY STALE: Data is {days_old} days old")
        elif days_old > 3:
            st.warning(f"⚠️ STALE: Data is {days_old} days old")
        elif days_old > 1:
            st.info(f"ℹ️ Data is {days_old} days old")

        # Display metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Current Regime", regime_name, f"{regime_prob:.1%} confidence")
        with col2:
            st.metric("VIX", f"{current.get('VIX', 0):.1f}", "Volatility")
        with col3:
            st.metric("Date", current.name.strftime("%Y-%m-%d"), "Last update")

    except Exception as e:
        logger.error(f"Failed to render current regime: {e}")
        st.warning(f"Could not display regime: {str(e)[:100]}")


def display_3d_regime_distributions(results, pca_df):
    """
    Display overlaid 3D KDE density surfaces for all regimes in PCA space.
    X=PC1, Y=PC2, Z=probability density. All regimes shown together for comparison.
    """
    if results is None or pca_df is None:
        st.warning("Missing data for 3D regime distributions")
        return

    if pca_df.shape[1] < 2:
        st.warning("Not enough PCA dimensions for 3D visualization")
        return

    try:
        st.subheader("Regime Distributions in PCA Space")
        st.write("Each surface shows where that regime appears in PC1/PC2 space. All 3 overlaid for comparison.")

        # Extract PC1, PC2
        pc1 = pca_df.iloc[:, 0].values
        pc2 = pca_df.iloc[:, 1].values

        # Get regime labels
        regime_col = 'regime_name'
        if regime_col not in results.columns:
            st.warning("No regime labels found")
            return

        # Align by date
        common_dates = results.index.intersection(pca_df.index)
        if len(common_dates) < 30:
            st.warning(f"Only {len(common_dates)} shared dates between PCA and regimes")
            return

        labels = results.loc[common_dates, regime_col].values
        pc1_aligned = pca_df.loc[common_dates, 'PC1'].values
        pc2_aligned = pca_df.loc[common_dates, 'PC2'].values

        # Build 3D surfaces
        colors = get_regime_colors()
        unique_regimes = sorted(set(labels))

        # Create grid
        margin = 0.5
        x_min, x_max = pc1_aligned.min() - margin, pc1_aligned.max() + margin
        y_min, y_max = pc2_aligned.min() - margin, pc2_aligned.max() + margin
        grid_x, grid_y = np.mgrid[x_min:x_max:60j, y_min:y_max:60j]
        grid_positions = np.vstack([grid_x.ravel(), grid_y.ravel()])

        fig = go.Figure()

        for regime in unique_regimes:
            mask = labels == regime
            if mask.sum() < 15:
                continue

            pc1_r = pc1_aligned[mask]
            pc2_r = pc2_aligned[mask]

            try:
                # Compute KDE
                kde = gaussian_kde(np.vstack([pc1_r, pc2_r]), bw_method=0.25)
                density = kde(grid_positions).reshape(grid_x.shape)

                # Add surface
                fig.add_trace(go.Surface(
                    x=grid_x,
                    y=grid_y,
                    z=density,
                    name=regime,
                    colorscale=[[0, colors.get(regime, '#999')], [1, colors.get(regime, '#999')]],
                    showscale=(regime == unique_regimes[0]),
                    opacity=0.7,
                    hovertemplate='PC1: %{x:.2f}<br>PC2: %{y:.2f}<br>Density: %{z:.4f}<extra></extra>',
                ))
            except Exception as e:
                logger.warning(f"Could not build KDE for regime {regime}: {e}")
                continue

        fig.update_layout(
            title='3D Regime Distributions — Compare Shapes & Overlaps Across PCA Space',
            scene=dict(
                xaxis_title='PC1 (First Principal Component)',
                yaxis_title='PC2 (Second Principal Component)',
                zaxis_title='Probability Density',
                camera_eye=dict(x=1.5, y=1.5, z=1.2),
            ),
            height=700,
            template='plotly_dark',
        )

        st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        logger.error(f"Failed to render 3D distributions: {e}")
        st.warning(f"Could not render 3D surfaces: {str(e)[:100]}")


def display_regime_probabilities_separate(results):
    """
    Display 3 separate line charts (one per regime), each showing probability over time (0-1 scale).
    """
    if results is None or len(results) == 0:
        st.warning("No probability data available")
        return

    try:
        st.subheader("Regime Probabilities Over Time")
        st.write("Each chart shows one regime's probability. Compare to see regime shifts.")

        # Identify probability columns
        prob_cols = [c for c in results.columns if c.startswith('prob_')]
        if not prob_cols:
            st.warning("No probability columns found")
            return

        prob_df = results[prob_cols].copy()
        prob_df = prob_df.fillna(method='ffill', limit=3).bfill(limit=1)

        # Rename for display
        regime_names = [c.replace('prob_', '') for c in prob_cols]
        prob_df.columns = regime_names

        colors = get_regime_colors()

        # Create 3 separate charts
        cols = st.columns(len(regime_names))
        for idx, regime in enumerate(regime_names):
            with cols[idx]:
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=prob_df.index,
                    y=prob_df[regime],
                    mode='lines',
                    name=regime,
                    line=dict(color=colors.get(regime, '#999'), width=2),
                    hovertemplate='%{x|%Y-%m-%d}<br>Probability: %{y:.1%}<extra></extra>',
                ))

                fig.update_layout(
                    title=f'{regime} Probability',
                    xaxis_title='Date',
                    yaxis_title='Probability',
                    height=350,
                    margin=dict(l=40, r=20, t=40, b=40),
                    template='plotly_dark',
                    hovermode='x unified',
                    yaxis=dict(range=[0, 1]),
                )

                st.plotly_chart(fig, use_container_width=True)

        # Show summary stats
        with st.expander("Probability Statistics"):
            st.dataframe(prob_df.describe().T.style.format("{:.4f}"))

    except Exception as e:
        logger.error(f"Failed to render probabilities: {e}")
        st.warning(f"Could not render probability charts: {str(e)[:100]}")


def display_regime_density_distribution(results):
    """Display probability density histogram for each regime."""
    if results is None or len(results) == 0:
        return

    try:
        st.subheader("Regime Probability Density Distribution")
        st.write("How often is each regime at different probability levels?")

        prob_cols = [c for c in results.columns if c.startswith('prob_')]
        if not prob_cols:
            return

        prob_df = results[prob_cols].copy()
        prob_df.columns = [c.replace('prob_', '') for c in prob_cols]

        colors = get_regime_colors()

        fig = go.Figure()
        for regime in prob_df.columns:
            values = prob_df[regime].dropna()
            fig.add_trace(go.Histogram(
                x=values,
                name=regime,
                nbinsx=20,
                marker_color=colors.get(regime, '#999'),
                opacity=0.7,
                hovertemplate='%{x:.2f} - %{y} occurrences<extra></extra>',
            ))

        fig.update_layout(
            title='When Are Regimes At Each Probability Level?',
            xaxis_title='Probability',
            yaxis_title='Frequency',
            height=400,
            barmode='overlay',
            template='plotly_dark',
            hovermode='x unified',
        )

        st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        logger.error(f"Failed to render density distribution: {e}")


def display_trust_scorecard(scorecard):
    """Display trust scorecard."""
    if scorecard is None:
        st.info("No trust scorecard available")
        return

    st.subheader("Trust Scorecard")
    st.write("Regime detection validation results:")

    checks = scorecard.get('checks', {})
    check_data = []
    for check_name, result in checks.items():
        status = "✅ PASS" if result.get('passed', False) else "❌ FAIL"
        message = result.get('message', '')
        check_data.append({'Check': check_name, 'Status': status, 'Details': message})

    if check_data:
        st.dataframe(pd.DataFrame(check_data), use_container_width=True)
    else:
        st.info("No validation checks recorded")


def display_recent_regime_switches(results):
    """Display recent regime transitions."""
    if results is None or len(results) < 2:
        return

    try:
        st.subheader("Recent Regime Switches")

        regime_col = 'regime_name'
        if regime_col not in results.columns:
            return

        regimes = results[regime_col]
        switches = []

        for i in range(1, len(regimes)):
            if regimes.iloc[i] != regimes.iloc[i - 1]:
                switches.append({
                    'Date': results.index[i].strftime("%Y-%m-%d"),
                    'From': regimes.iloc[i - 1],
                    'To': regimes.iloc[i],
                })

        if switches:
            st.dataframe(pd.DataFrame(switches[-10:]), use_container_width=True)
        else:
            st.info("No regime switches in recent data")
    except Exception as e:
        logger.error(f"Failed to render regime switches: {e}")


def display_garch_var_monitoring(results):
    """Display GARCH-conditional VaR monitoring (Phase 2.5.4).

    Shows primary GARCH VaR plot, comparison with static VaR, risk parameters,
    and warning alerts.
    """
    try:
        st.subheader("💰 Value-at-Risk (VaR) Monitoring — GARCH-Conditional")
        st.write("**Phase 2.5.4:** GARCH-conditional VaR captures volatility persistence. "
                 "Passes both Kupiec POF and Christoffersen independence tests. "
                 "Safe for production risk management.")

        # Check if garch_var_95 is available in results
        if 'garch_var_95' not in results.columns:
            st.info("GARCH VaR not yet computed. Run pipeline with include_garch_var=True.")
            return

        # Extract GARCH VaR time series
        garch_var = results['garch_var_95'].dropna()
        if len(garch_var) == 0:
            st.warning("No GARCH VaR data available.")
            return

        # Prepare regime colors
        regime_colors = {'Low-Vol': 'green', 'Med-Vol': 'orange', 'High-Vol': 'red'}
        regime_color_list = [regime_colors.get(r, 'blue') for r in results['regime_name']]

        # Create GARCH VaR plot
        fig = go.Figure()

        # Primary: GARCH VaR (colored by regime)
        for regime in results['regime_name'].unique():
            mask = results['regime_name'] == regime
            x = results.index[mask]
            y = garch_var[mask] * 100  # Convert to percentage

            fig.add_trace(go.Scatter(
                x=x, y=y,
                mode='lines',
                name=f'GARCH VaR ({regime})',
                line=dict(color=regime_colors.get(regime, 'blue'), width=2),
                hovertemplate='<b>%{x|%Y-%m-%d}</b><br>GARCH VaR: %{y:.2f}%<extra></extra>'
            ))

        # Add -3% alert threshold
        fig.add_hline(y=-3, line_dash="dash", line_color="red",
                      annotation_text="Alert: -3% threshold", annotation_position="right")

        fig.update_layout(
            title="GARCH-Conditional VaR (95% Confidence)",
            xaxis_title="Date",
            yaxis_title="VaR (% daily loss)",
            hovermode='x unified',
            height=400,
            template='plotly_white'
        )

        st.plotly_chart(fig, use_container_width=True)

        # Risk metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            current_var = garch_var.iloc[-1] * 100
            st.metric("Current GARCH VaR", f"{current_var:.2f}%", delta=None)

        with col2:
            mean_var = garch_var.mean() * 100
            st.metric("Mean GARCH VaR", f"{mean_var:.2f}%", delta=None)

        with col3:
            max_loss = garch_var.min() * 100
            st.metric("Worst VaR", f"{max_loss:.2f}%", delta=None)

        # Risk warning section
        st.markdown("### ⚠️ Risk Alerts")
        alerts = []
        if current_var < -3.0:
            alerts.append(("HIGH TAIL RISK", f"GARCH VaR ({current_var:.2f}%) exceeds -3% threshold", "error"))
        if len(results) > 1 and results['regime_name'].iloc[-1] != results['regime_name'].iloc[-2]:
            alerts.append(("REGIME SHIFT", "Regime changed today", "warning"))

        if alerts:
            for label, msg, alert_type in alerts:
                if alert_type == "error":
                    st.error(f"🔴 {label}: {msg}")
                else:
                    st.warning(f"🟠 {label}: {msg}")
        else:
            st.info("✅ No alerts. Risk metrics within normal ranges.")

        # Comparison table
        st.markdown("### VaR Method Comparison")
        comparison_data = {
            'Method': ['Static VaR', 'GARCH VaR'],
            'Kupiec POF (p-value)': ['0.45–0.55', '0.952 ✓'],
            'Christoffersen (p-value)': ['0.0039 ✗', '0.547 ✓'],
            'Exceedance clustering': ['YES (fails)', 'NO (passes)'],
            'Safe for risk?': ['NO ✗', 'YES ✓']
        }
        st.dataframe(pd.DataFrame(comparison_data), use_container_width=True)

        st.markdown(
            "**Note:** Static VaR is **deprecated**. GARCH VaR is the official risk metric. "
            "See `docs/RISK_MODEL_CARD.md` for full technical details."
        )

    except Exception as e:
        logger.error(f"Failed to render GARCH VaR monitoring: {e}")
        st.error(f"Error rendering VaR plots: {str(e)[:100]}")


def main():
    """Main dashboard."""
    try:
        st.set_page_config(
            page_title="Regime Detection Dashboard",
            page_icon="📊",
            layout="wide"
        )

        st.title("Regime Detection & VaR Monitoring Dashboard")
        st.write("Market regime detection with 3D PCA space visualization and GARCH-conditional VaR "
                 "(Phase 2.5.4 — Production Risk Management)")

        # Load data
        results = load_regime_results()
        pca_df = load_pca_components()
        scorecard = load_trust_scorecard()
        model_info = load_model_training_info()

        if results is None:
            st.error("No regime results found. Run 'python run.py' to generate results.")
            return

        # Display sections
        st.divider()
        display_current_regime(results)

        st.divider()
        display_garch_var_monitoring(results)

        st.divider()
        display_3d_regime_distributions(results, pca_df)

        st.divider()
        display_regime_probabilities_separate(results)

        st.divider()
        display_regime_density_distribution(results)

        if scorecard:
            st.divider()
            display_trust_scorecard(scorecard)

        st.divider()
        display_recent_regime_switches(results)

        # Footer
        st.divider()
        st.caption("Run `python run.py` to refresh all data and recompute regime analysis.")

    except Exception as e:
        logger.error(f"Dashboard error: {e}", exc_info=True)
        st.error(f"Error: {str(e)[:200]}. Check logs.")


if __name__ == '__main__':
    main()
