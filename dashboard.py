"""
Clean regime detection dashboard (K=3 + GARCH VaR + Statistics)

Run: streamlit run dashboard.py
"""

import os
import pandas as pd
import numpy as np
import streamlit as st
from pathlib import Path
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from config import DATA_DIR, MODEL_DIR

# --- Page setup ---
st.set_page_config(page_title="Regime Detection", layout="wide")
st.title("Market Regime Detection & Risk Management")
st.caption("K=3 regimes | GARCH-conditional VaR | Phase 2.5+ validation")

# --- Load data ---
@st.cache_data(ttl=300)
def load_data():
    results_path = os.path.join(DATA_DIR, 'regime_results.csv')
    pca_path = os.path.join(DATA_DIR, 'pca_components.csv')

    results = pd.read_csv(results_path, index_col=0, parse_dates=True) if os.path.exists(results_path) else None
    pca = pd.read_csv(pca_path, index_col=0, parse_dates=True) if os.path.exists(pca_path) else None

    return results, pca

results, pca = load_data()

if results is None:
    st.error("No data. Run: python run.py all")
    st.stop()

# --- SECTION 1: Current Regime (Top) ---
st.markdown("## Current Regime")
col1, col2, col3, col4 = st.columns(4)

current = results.iloc[-1]
regime_name = current['regime']
regime_prob = current.get('regime_prob', 0)
vix = current['VIX']
garch_var = current.get('garch_var_95', np.nan)
last_date = current.name

with col1:
    st.metric("Regime", regime_name)
with col2:
    st.metric("Confidence", f"{regime_prob:.1%}")
with col3:
    st.metric("VIX", f"{vix:.1f}")
with col4:
    if not np.isnan(garch_var):
        st.metric("GARCH VaR (95%)", f"{garch_var:.2%}")
    else:
        st.metric("GARCH VaR (95%)", "N/A")

st.caption(f"Last update: {last_date.strftime('%Y-%m-%d')}")

# --- SECTION 2: Regime Statistics Table ---
st.markdown("## Regime Statistics (Full Sample)")

regime_stats = []
for regime in sorted(results['regime'].unique()):
    regime_data = results[results['regime'] == regime]
    regime_stats.append({
        'Regime': regime,
        'Days': len(regime_data),
        'Freq %': f"{len(regime_data)/len(results)*100:.1f}%",
        'Avg VIX': f"{regime_data['VIX'].mean():.1f}",
        'Avg GARCH VaR': f"{regime_data['garch_var_95'].mean():.2%}",
        'Persistence %': f"{regime_data['persist_pct'].mean():.1f}%",
        'Avg Duration': f"{regime_data['dwell_time'].mean():.1f} days",
    })

stats_df = pd.DataFrame(regime_stats)
st.dataframe(stats_df, use_container_width=True, hide_index=True)

# --- SECTION 3: Two Charts Side-by-Side ---
col_left, col_right = st.columns(2)

# Chart 1: Regime Probabilities Over Time
with col_left:
    st.markdown("### Regime Probabilities Over Time")

    fig_probs = go.Figure()
    for regime in sorted(results['regime'].unique()):
        prob_col = f'prob_{regime}'
        if prob_col in results.columns:
            fig_probs.add_trace(go.Scatter(
                x=results.index, y=results[prob_col],
                name=regime, mode='lines', hovertemplate='%{y:.2%}'
            ))

    fig_probs.update_layout(
        height=400,
        hovermode='x unified',
        yaxis_title='Probability',
        yaxis=dict(range=[0, 1.05]),
        margin=dict(l=0, r=0, t=0, b=0),
    )
    st.plotly_chart(fig_probs, use_container_width=True, key="probs")

# Chart 2: GARCH VaR Over Time
with col_right:
    st.markdown("### GARCH VaR Over Time (by Regime)")

    fig_var = go.Figure()
    colors = {'Low-Vol': '#2ecc71', 'Medium-Vol': '#f39c12', 'High-Vol': '#e74c3c'}

    for regime in sorted(results['regime'].unique()):
        regime_data = results[results['regime'] == regime]
        fig_var.add_trace(go.Scatter(
            x=regime_data.index, y=regime_data['garch_var_95'],
            name=regime, mode='markers',
            marker=dict(color=colors.get(regime, '#95a5a6'), size=3, opacity=0.6),
            hovertemplate='%{y:.2%}'
        ))

    fig_var.update_layout(
        height=400,
        hovermode='x unified',
        yaxis_title='VaR (95% CI)',
        margin=dict(l=0, r=0, t=0, b=0),
    )
    st.plotly_chart(fig_var, use_container_width=True, key="var")

# --- SECTION 4: Recent Regime Switches ---
st.markdown("## Recent Regime Switches (Last 10)")

recent_switches = []
prev_regime = None

for idx, row in results.iterrows():
    curr_regime = row['regime']
    if prev_regime is not None and prev_regime != curr_regime:
        recent_switches.append({
            'Date': idx.strftime('%Y-%m-%d'),
            'From': prev_regime,
            'To': curr_regime,
        })
    prev_regime = curr_regime

recent_df = pd.DataFrame(recent_switches[-10:])
if len(recent_df) > 0:
    st.dataframe(recent_df, use_container_width=True, hide_index=True)
else:
    st.info("No regime switches in dataset")

# --- SECTION 5: 3D PCA Scatter ---
if pca is not None and len(pca.columns) >= 3:
    st.markdown("## 3D PCA Space (All Regimes)")

    # Prepare 3D scatter
    fig_3d = go.Figure()
    colors = {'Low-Vol': '#2ecc71', 'Medium-Vol': '#f39c12', 'High-Vol': '#e74c3c'}

    for regime in sorted(results['regime'].unique()):
        regime_mask = results['regime'] == regime
        regime_indices = regime_mask.index[regime_mask].tolist()

        pca_subset = pca.loc[pca.index.isin(regime_indices)]

        fig_3d.add_trace(go.Scatter3d(
            x=pca_subset.iloc[:, 0],
            y=pca_subset.iloc[:, 1],
            z=pca_subset.iloc[:, 2],
            name=regime,
            mode='markers',
            marker=dict(
                size=2,
                color=colors.get(regime, '#95a5a6'),
                opacity=0.5
            ),
            hovertemplate='PC1: %{x:.2f}<br>PC2: %{y:.2f}<br>PC3: %{z:.2f}'
        ))

    fig_3d.update_layout(
        scene=dict(
            xaxis_title='PC1 (47%)',
            yaxis_title='PC2 (26%)',
            zaxis_title='PC3 (15%)',
            camera=dict(eye=dict(x=1.5, y=1.5, z=1.3))
        ),
        height=600,
        margin=dict(l=0, r=0, t=0, b=0),
    )
    st.plotly_chart(fig_3d, use_container_width=True, key="3d")

# --- Footer ---
st.markdown("---")
st.markdown("""
**Model Info:**
- K=3 regimes (Low-Vol, Medium-Vol, High-Vol)
- GARCH-conditional VaR (passes Kupiec + Christoffersen tests)
- 6-feature set (VRP, VIX, SPY_skew20, SPY_TLT_corr63, lev_effect20, rv_ratio_10_63)
- Phase 2.5 production validation complete

**Next Phase (3.1):**
- Feature diversification: reduce correlated vol signals
- Add cross-asset + macro indicators
""")
