"""
Feature diagnostics: interactive HTML report with correlation heatmap,
distribution histograms, time-series explorer, and summary statistics.
Replaces the old static matplotlib PNG with a single feature_analysis.html.
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go          # type: ignore[import-untyped]
from plotly.subplots import make_subplots  # type: ignore[import-untyped]
import os

from config import DATA_DIR, FIGURE_DIR

# ── Dark theme (matches main dashboard) ───────────────────────────
_BG       = '#0d1117'
_PAPER    = '#161b22'
_GRID     = '#21262d'
_TEXT     = '#c9d1d9'
_ACCENT   = '#58a6ff'

_LAYOUT = dict(
    paper_bgcolor=_PAPER, plot_bgcolor=_BG,
    font=dict(color=_TEXT, size=11),
    margin=dict(l=60, r=30, t=50, b=50),
)


def _build_correlation_heatmap(features: pd.DataFrame) -> go.Figure:
    """Interactive correlation matrix with hover values."""
    corr = features.corr()
    fig = go.Figure(go.Heatmap(
        z=corr.values, x=corr.columns, y=corr.columns,
        colorscale='RdBu_r', zmid=0, zmin=-1, zmax=1,
        text=np.round(corr.values, 2), texttemplate='%{text}',
        textfont=dict(size=7),
        hovertemplate='%{x} vs %{y}: %{z:.3f}<extra></extra>',
    ))
    fig.update_layout(
        **_LAYOUT, title='Feature Correlation Matrix',
        height=max(500, 18 * len(corr.columns)),
        width=max(600, 18 * len(corr.columns)),
        xaxis=dict(tickfont=dict(size=8), tickangle=45),
        yaxis=dict(tickfont=dict(size=8), autorange='reversed'),
    )
    return fig


def _build_distributions(features: pd.DataFrame) -> go.Figure:
    """Histogram grid for all features."""
    cols = list(features.columns)
    n = len(cols)
    ncols = min(4, n)
    nrows = (n + ncols - 1) // ncols

    fig = make_subplots(rows=nrows, cols=ncols,
                        subplot_titles=cols,
                        vertical_spacing=0.04,
                        horizontal_spacing=0.05)

    for i, col in enumerate(cols):
        r, c = divmod(i, ncols)
        data = features[col].dropna()
        fig.add_trace(
            go.Histogram(x=data, nbinsx=60, marker_color=_ACCENT,
                         opacity=0.8, showlegend=False,
                         hovertemplate=f'{col}: %{{x:.3f}}<br>count: %{{y}}<extra></extra>'),
            row=r + 1, col=c + 1,
        )
        # Median line
        med = float(data.median())
        fig.add_vline(x=med, line_dash='dash', line_color='#f0883e',
                      line_width=1, row=r + 1, col=c + 1)

    fig.update_layout(
        **_LAYOUT,
        title='Feature Distributions (orange = median)',
        height=220 * nrows,
        showlegend=False,
    )
    fig.update_xaxes(gridcolor=_GRID, tickfont=dict(size=7))
    fig.update_yaxes(gridcolor=_GRID, tickfont=dict(size=7))
    return fig


def _build_timeseries(features: pd.DataFrame) -> go.Figure:
    """Dropdown-selectable time series for each feature."""
    cols = list(features.columns)
    fig = go.Figure()

    for i, col in enumerate(cols):
        fig.add_trace(go.Scatter(
            x=features.index, y=features[col],
            mode='lines', name=col, visible=(i == 0),
            line=dict(width=1, color=_ACCENT),
            hovertemplate=f'{col}: %{{y:.4f}}<extra></extra>',
        ))

    buttons = []
    for i, col in enumerate(cols):
        vis = [False] * len(cols)
        vis[i] = True
        buttons.append(dict(label=col, method='update',
                            args=[{'visible': vis},
                                  {'title': f'Feature: {col}'}]))

    fig.update_layout(
        **_LAYOUT,
        title=f'Feature: {cols[0]}',
        updatemenus=[dict(
            buttons=buttons, direction='down',
            showactive=True, x=0.01, xanchor='left',
            y=1.15, yanchor='top',
            bgcolor='#21262d', font=dict(color=_TEXT, size=10),
        )],
        xaxis=dict(gridcolor=_GRID),
        yaxis=dict(gridcolor=_GRID),
        height=450,
    )
    return fig


def _build_stats_table(features: pd.DataFrame) -> go.Figure:
    """Summary statistics table."""
    desc = features.describe().T
    desc['skew'] = features.skew()
    desc['kurt'] = features.kurtosis()
    desc = desc[['count', 'mean', 'std', 'min', '25%', '50%', '75%', 'max', 'skew', 'kurt']]

    fig = go.Figure(go.Table(
        header=dict(
            values=['Feature'] + [str(c) for c in desc.columns],
            fill_color='#21262d', font=dict(color=_TEXT, size=10),
            align='left',
        ),
        cells=dict(
            values=[desc.index] + [desc[c].round(4) for c in desc.columns],
            fill_color=_BG, font=dict(color=_TEXT, size=9),
            align='left',
        ),
    ))
    fig.update_layout(
        **_LAYOUT, title='Summary Statistics',
        height=max(400, 28 * len(desc) + 80),
    )
    return fig


def _write_analysis_html(corr_fig, dist_fig, ts_fig, stats_fig, path: str):
    """Write tabbed HTML with all four panels."""
    tabs = [
        ('Correlations', corr_fig),
        ('Distributions', dist_fig),
        ('Time Series', ts_fig),
        ('Statistics', stats_fig),
    ]

    tab_btns = ''
    tab_divs = ''
    for i, (name, fig) in enumerate(tabs):
        active = ' active' if i == 0 else ''
        display = 'block' if i == 0 else 'none'
        html_content = fig.to_html(full_html=False, include_plotlyjs=False)
        tab_btns += f'<button class="tab-btn{active}" onclick="showTab({i})">{name}</button>\n'
        tab_divs += f'<div class="tab-content" id="tab-{i}" style="display:{display}">{html_content}</div>\n'

    html = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<title>Feature Analysis</title>
<script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ background:{_BG}; color:{_TEXT}; font-family:system-ui,-apple-system,sans-serif; }}
  .header {{ padding:18px 24px; background:{_PAPER}; border-bottom:1px solid {_GRID}; }}
  .header h1 {{ font-size:20px; font-weight:600; }}
  .header p {{ font-size:12px; color:#8b949e; margin-top:4px; }}
  .tab-bar {{ display:flex; gap:2px; padding:8px 24px; background:{_PAPER};
              border-bottom:1px solid {_GRID}; flex-wrap:wrap; }}
  .tab-btn {{ padding:8px 18px; border:none; border-radius:6px 6px 0 0;
              background:transparent; color:#8b949e; cursor:pointer; font-size:13px; }}
  .tab-btn:hover {{ color:{_TEXT}; background:#21262d; }}
  .tab-btn.active {{ color:{_TEXT}; background:{_BG}; font-weight:600;
                     border-bottom:2px solid {_ACCENT}; }}
  .content {{ padding:16px 24px; }}
</style>
<script>
function showTab(idx) {{
  document.querySelectorAll('.tab-content').forEach((d,i) => d.style.display = i===idx ? 'block' : 'none');
  document.querySelectorAll('.tab-btn').forEach((b,i) => b.classList.toggle('active', i===idx));
  window.dispatchEvent(new Event('resize'));
}}
</script>
</head><body>
<div class="header">
  <h1>Feature Analysis Report</h1>
  <p>{len(tabs)} panels &bull; Generated by analyze.py</p>
</div>
<div class="tab-bar">{tab_btns}</div>
<div class="content">{tab_divs}</div>
</body></html>"""

    with open(path, 'w', encoding='utf-8') as fh:
        fh.write(html)


def analyze():
    os.makedirs(FIGURE_DIR, exist_ok=True)

    market = pd.read_csv(os.path.join(DATA_DIR, 'market_data.csv'),
                         index_col=0, parse_dates=True)

    feat_path = os.path.join(DATA_DIR, 'features_raw.csv')
    if not os.path.exists(feat_path):
        print("No features_raw.csv found — run 'python run.py features' first.")
        return market

    features = pd.read_csv(feat_path, index_col=0, parse_dates=True)

    print(f"{len(market)} days  |  Missing: {market.isnull().sum().sum()}")
    print(f"Features: {features.shape[1]} x {features.shape[0]}")

    corr_fig  = _build_correlation_heatmap(features)
    dist_fig  = _build_distributions(features)
    ts_fig    = _build_timeseries(features)
    stats_fig = _build_stats_table(features)

    out_path = os.path.join(FIGURE_DIR, 'feature_analysis.html')
    _write_analysis_html(corr_fig, dist_fig, ts_fig, stats_fig, out_path)
    print(f"Feature analysis saved: {out_path}")

    return market


if __name__ == '__main__':
    analyze()
