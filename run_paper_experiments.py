"""
Paper experiment runner: collect -> features -> HDP-HMM -> baselines -> LaTeX tables.

Writes results/paper_results.txt with LaTeX-ready tables for:
  Table 1: Regime characteristics (HDP-HMM vs VIX-threshold vs Parametric HMM)
  Table 2: Transition matrix (persistence / stickiness)
  Table 3: Information content regression (R² gain beyond VIX alone)
  Appendix: Posterior diagnostics (effective K, SVI convergence)
"""

import os
import sys
import warnings
import numpy as np
import pandas as pd
from scipy import stats as scipy_stats
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LinearRegression

# Log messages use non-ASCII characters (→, etc.); Windows consoles default
# to cp1252, which can't encode them and crashes the run mid-pipeline.
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

warnings.filterwarnings('ignore')
os.makedirs('results', exist_ok=True)

LOG = open('results/run_log.txt', 'w', buffering=1, encoding='utf-8')

def log(msg):
    print(msg)
    print(msg, file=LOG)

log("=" * 60)
log("REGIME DETECTION — PAPER EXPERIMENTS")
log("=" * 60)


# ===================================================================
# 1. Collect data
# ===================================================================
log("\n[1/6] Collecting data...")
from src.data.collect_macro import fetch_and_save_data
df_raw = fetch_and_save_data()
log(f"  Raw data: {df_raw.shape}  ({df_raw.index[0].date()} to {df_raw.index[-1].date()})")


# ===================================================================
# 2. Feature engineering (expanding standardize)
# ===================================================================
log("\n[2/6] Feature engineering...")
from src.pipeline.stages import stage_features
stage_features(None)

feat_train = pd.read_csv('data/processed/features_train.csv', index_col=0, parse_dates=True).dropna()
feat_test  = pd.read_csv('data/processed/features_test.csv',  index_col=0, parse_dates=True).dropna()
log(f"  Train: {len(feat_train)} rows  |  Test: {len(feat_test)} rows")

# Write Table 0: descriptive stats for the 4 raw (un-standardised) features
raw_train = df_raw[['spy_ret', 'vol_index', 'yield_slope', 'nfci']].reindex(feat_train.index).dropna()
feat_labels = {
    'spy_ret':     r'SPY log return ($r_t$)',
    'vol_index':   r'VIX level ($\sigma^{iv}_t$)',
    'yield_slope': r'Yield slope ($y_t$)',
    'nfci':        r'NFCI ($f_t$)',
}
with open('results/paper_desc_stats.tex', 'w') as _f:
    _f.write(r"\begin{table}[htbp]" + "\n")
    _f.write(r"\centering" + "\n")
    _f.write(r"\caption{Descriptive statistics for the four input features "
             r"(training period, \nTrainStart{}--\nTrainEnd{}, $N=\nTrainDays{}$ trading days). "
             r"SPY log return is the daily log return of the S\&P 500 (\%). "
             r"VIX is the CBOE Volatility Index close. "
             r"Yield slope is the 10y-2y Treasury spread (pp). "
             r"NFCI is the Chicago Fed National Financial Conditions Index.}" + "\n")
    _f.write(r"\label{tab:desc_stats}" + "\n")
    _f.write(r"\begin{tabular}{lrrrrrr}" + "\n")
    _f.write(r"\toprule" + "\n")
    _f.write(r"Feature & Mean & Std & Min & P25 & P75 & Max \\" + "\n")
    _f.write(r"\midrule" + "\n")
    for col, label in feat_labels.items():
        s = raw_train[col]
        _f.write(f"{label} & {s.mean():.3f} & {s.std():.3f} & {s.min():.3f} & "
                 f"{s.quantile(0.25):.3f} & {s.quantile(0.75):.3f} & {s.max():.3f} \\\\\n")
    _f.write(r"\bottomrule" + "\n")
    _f.write(r"\end{tabular}" + "\n")
    _f.write(r"\end{table}" + "\n")
log("  Saved results/paper_desc_stats.tex (Table 0)")


# ===================================================================
# 3. HDP-HMM training
# ===================================================================
log("\n[3/6] Training HDP-HMM (SVI, 4000 steps — takes a few minutes)...")
from src.core.hdp_hmm import (
    fit_hdp_hmm, posterior_mean_params, get_labels_and_probs,
    label_regimes_hdp, effective_K, get_transition_matrix, mcmc_diagnostics,
)

obs_train = feat_train.values
hdp_result, hdp_samples = fit_hdp_hmm(obs_train, inference='svi')
hdp_params   = posterior_mean_params(hdp_samples)
hdp_labels_raw, hdp_filt, hdp_smooth, hdp_active = get_labels_and_probs(obs_train, hdp_params)

eff_k_mean, eff_k_std, eff_k_mode = effective_K(hdp_samples)
log(f"  Effective K (raw): mean={eff_k_mean:.1f}, mode={eff_k_mode}")
log(f"  Active states (raw): {hdp_active}")

# --- Merge K raw states to 3 canonical regimes by VIX rank ---
# Sort all discovered states ascending by mean VIX, partition into thirds.
# NOTE: min(int(i*3/K_eff), 2) only fills all 3 groups when K_eff >= 3 --
# below that, "High-Vol" silently never gets assigned. Fail loudly instead.
vix_train = df_raw['vol_index'].reindex(feat_train.index).values
spy_train = df_raw['spy_ret'].reindex(feat_train.index).values

K_eff = len(hdp_active)
assert K_eff >= 3, (
    f"HDP pruned to only {K_eff} active state(s) -- cannot map to 3 canonical "
    f"regimes (Low/Moderate/High-Vol). Rerun with a different seed/kappa, or "
    f"handle K_eff<3 explicitly before merging."
)
mean_vix_per_state = {
    s: float(vix_train[hdp_labels_raw == s].mean()) if (hdp_labels_raw == s).sum() > 0 else 0.0
    for s in range(K_eff)
}
sorted_by_vix = sorted(range(K_eff), key=mean_vix_per_state.get)
state_to_regime = {s: min(int(i * 3 / K_eff), 2) for i, s in enumerate(sorted_by_vix)}

hdp_labels   = np.array([state_to_regime[l] for l in hdp_labels_raw])
hdp_name_map = {0: 'Low-Vol', 1: 'Moderate-Vol', 2: 'High-Vol'}

# Empirical transition matrix on merged labels
hdp_trans = np.zeros((3, 3))
for t in range(1, len(hdp_labels)):
    hdp_trans[hdp_labels[t-1], hdp_labels[t]] += 1
row_sums = hdp_trans.sum(axis=1, keepdims=True)
hdp_trans = hdp_trans / np.where(row_sums > 0, row_sums, 1.0)

hdp_vols = {k: float(np.std(spy_train[hdp_labels == k]) * np.sqrt(252) * 100)
            for k in range(3) if (hdp_labels == k).sum() > 0}
hdp_diag = mcmc_diagnostics(hdp_result, hdp_samples)

log(f"  VIX rank map (raw state → regime): {state_to_regime}")
log(f"  Distribution: { {hdp_name_map[k]: int((hdp_labels==k).sum()) for k in range(3)} }")
log(f"  Mean VIX: { {hdp_name_map[k]: round(float(vix_train[hdp_labels==k].mean()),1) for k in range(3)} }")


# ===================================================================
# 4. Threshold baseline
# ===================================================================
log("\n[4/6] Threshold baseline...")
from src.baselines.threshold_rules import apply_threshold_rules

df_train_raw = df_raw.loc[feat_train.index].copy()
df_train_raw = apply_threshold_rules(df_train_raw)
thresh_labels = df_train_raw['threshold_regime'].values
thresh_name_map = {0: 'Low-Vol', 1: 'Moderate-Vol', 2: 'High-Vol'}
log(f"  Threshold distribution: {pd.Series(thresh_labels).value_counts().to_dict()}")


# ===================================================================
# 5. Parametric HMM baseline
# ===================================================================
log("\n[5/6] Parametric HMM baseline...")
from src.baselines.parametric_hmm import (
    fit_parametric_hmm, get_filtered_states, relabel_by_vix,
)

X_raw_train = df_raw[['spy_ret', 'vol_index', 'yield_slope', 'nfci']].reindex(feat_train.index).dropna().values
scaler = StandardScaler().fit(X_raw_train)
X_scaled_train = scaler.transform(X_raw_train)

param_model = fit_parametric_hmm(X_scaled_train, n_restarts=10)
param_states, param_probs = get_filtered_states(param_model, X_scaled_train)
param_name_map = relabel_by_vix(param_model, X_scaled_train, df_raw['vol_index'].reindex(feat_train.index).values)
log(f"  Parametric HMM distribution: {pd.Series([param_name_map[s] for s in param_states]).value_counts().to_dict()}")


# ===================================================================
# 6. Compute paper statistics
# ===================================================================
log("\n[6/6] Computing paper statistics...")

# Align returns and VIX to train index
spy_ret_s  = df_raw['spy_ret'].reindex(feat_train.index)
vol_s      = df_raw['vol_index'].reindex(feat_train.index)

def regime_stats(labels, name_map, spy_ret, vix, model_name):
    """Compute within-regime statistics for Table 1."""
    rows = []
    T = len(labels)
    for r in sorted(name_map.keys()):
        name = name_map[r]
        mask = labels == r
        n = mask.sum()
        if n < 5:
            continue
        ret = spy_ret[mask]
        ret_ann  = float(ret.mean() * 252 * 100)   # annualized %
        vol_ann  = float(ret.std() * np.sqrt(252) * 100)
        sharpe   = ret_ann / vol_ann if vol_ann > 0 else np.nan
        vix_mean = float(vix[mask].mean())

        # Dwell time (mean days per spell)
        label_arr = np.asarray(labels)
        spells = []
        in_spell = False
        count = 0
        for t in range(T):
            if label_arr[t] == r:
                in_spell = True
                count += 1
            else:
                if in_spell:
                    spells.append(count)
                    in_spell = False
                    count = 0
        if in_spell:
            spells.append(count)
        dwell = float(np.mean(spells)) if spells else 0.0

        rows.append({
            'Model':   model_name,
            'Regime':  name,
            'N':       n,
            'Pct':     n / T * 100,
            'AnnRet':  ret_ann,
            'AnnVol':  vol_ann,
            'Sharpe':  sharpe,
            'VIX':     vix_mean,
            'Dwell':   dwell,
        })
    return rows


all_rows = []
all_rows += regime_stats(hdp_labels,    hdp_name_map,    spy_ret_s.values, vol_s.values, 'HDP-HMM')
all_rows += regime_stats(thresh_labels, thresh_name_map, spy_ret_s.values, vol_s.values, 'VIX Threshold')
all_rows += regime_stats(param_states,  param_name_map,  spy_ret_s.values, vol_s.values, 'Param HMM')
stats_df = pd.DataFrame(all_rows)


def information_content_regression(spy_ret, vix, labels_dict, fwd_days=5):
    """Table 3: R² gain from regime dummies beyond VIX alone."""
    n = len(spy_ret)
    fwd_ret = pd.Series(spy_ret).shift(-fwd_days).values
    valid = ~np.isnan(fwd_ret)

    X_vix    = vix[valid].reshape(-1, 1)
    y        = fwd_ret[valid]

    results = {}

    # Baseline: VIX only
    m = LinearRegression().fit(X_vix, y)
    r2_vix = m.score(X_vix, y)
    results['VIX only'] = r2_vix

    # VIX + regime dummies for each model
    for model_name, labels in labels_dict.items():
        K = len(np.unique(labels))
        dummies = pd.get_dummies(labels[valid], prefix='regime', drop_first=True).values
        X_full = np.hstack([X_vix, dummies])
        m2 = LinearRegression().fit(X_full, y)
        r2_full = m2.score(X_full, y)
        results[model_name] = r2_full

    return r2_vix, results


r2_vix, r2_results = information_content_regression(
    spy_ret_s.values, vol_s.values,
    {'HDP-HMM': hdp_labels, 'VIX Threshold': thresh_labels, 'Param HMM': param_states}
)


# ===================================================================
# Table 4: Volatility-targeting backtest
# ===================================================================

def vol_target_backtest(spy_ret, vol_estimate, target_vol_pct=15.0, max_leverage=1.5):
    """Scale daily SPY exposure by target_vol / current_vol_estimate.

    Parameters
    ----------
    spy_ret       : array (T,) daily log returns
    vol_estimate  : array (T,) annualized vol estimate for each day (%)
    target_vol_pct: float — target annualized portfolio vol (%)
    max_leverage  : float — cap on position size

    Returns dict of performance metrics.
    """
    vol_est = np.where(vol_estimate > 1e-6, vol_estimate, target_vol_pct)
    sizes   = np.clip(target_vol_pct / vol_est, 0.0, max_leverage)
    port    = spy_ret * sizes

    ann_ret  = float(port.mean() * 252 * 100)
    ann_vol  = float(port.std() * np.sqrt(252) * 100)
    sharpe   = ann_ret / ann_vol if ann_vol > 0 else np.nan
    cum      = np.cumprod(1 + port)
    roll_max = np.maximum.accumulate(cum)
    drawdown = (cum - roll_max) / roll_max
    max_dd   = float(drawdown.min() * 100)

    # Turnover: fraction of days position size changes meaningfully (>1%)
    size_changes = np.abs(np.diff(sizes))
    turnover_annual = float((size_changes > 0.01).mean() * 252)

    return {
        'Ann. Ret (%)':  ann_ret,
        'Ann. Vol (%)':  ann_vol,
        'Sharpe':        sharpe,
        'Max DD (%)':    max_dd,
        'Rebalances/yr': turnover_annual,
    }


spy_arr = spy_ret_s.values
vix_arr = vol_s.values
T       = len(spy_arr)

# Strategy 1: Buy and hold
bh_ret  = float(spy_arr.mean() * 252 * 100)
bh_vol  = float(spy_arr.std() * np.sqrt(252) * 100)
bh_shr  = bh_ret / bh_vol
bh_cum  = np.cumprod(1 + spy_arr)
bh_roll = np.maximum.accumulate(bh_cum)
bh_dd   = float(((bh_cum - bh_roll) / bh_roll).min() * 100)
bh_results = {'Ann. Ret (%)': bh_ret, 'Ann. Vol (%)': bh_vol,
              'Sharpe': bh_shr, 'Max DD (%)': bh_dd, 'Rebalances/yr': 0.0}

# Strategy 2: Vol-target using 30-day realized vol (lagged 1 day to avoid lookahead)
rv30 = pd.Series(spy_arr).rolling(30).std().shift(1).bfill().values * np.sqrt(252) * 100
rv_results = vol_target_backtest(spy_arr, rv30)

# Strategy 3: Vol-target using HDP regime vol (causal -- point-in-time
# per-regime vol, no full-sample lookahead; see src.core.inference)
from src.core.inference import expanding_regime_vol
hdp_vol_series = expanding_regime_vol(spy_arr, hdp_labels, n_regimes=3)
hdp_bt_results = vol_target_backtest(spy_arr, hdp_vol_series)

# Strategy 4: Vol-target using VIX-threshold regime vol (same causal estimator)
thresh_vol_series = expanding_regime_vol(spy_arr, thresh_labels, n_regimes=3)
thresh_bt_results = vol_target_backtest(spy_arr, thresh_vol_series)

backtest_rows = {
    'Buy \\& Hold':       bh_results,
    'Vol-Target (RV30)': rv_results,
    'Vol-Target (HDP)':  hdp_bt_results,
}
log("\nBacktest results (15% vol target, 1.5x max leverage):")
for name, res in backtest_rows.items():
    log(f"  {name:<25s}  Sharpe={res['Sharpe']:.3f}  MaxDD={res['Max DD (%)']:.1f}%  "
        f"Rebal={res['Rebalances/yr']:.0f}/yr")


# ===================================================================
# Save intermediates for figure generation
# ===================================================================
log("\nSaving regime labels and backtest series to results/...")

# Backtest cumulative return series (for equity curve figure)
bh_cum  = np.cumprod(1 + spy_arr)

rv30    = pd.Series(spy_arr).rolling(30).std().shift(1).bfill().values * np.sqrt(252) * 100
rv_sizes = np.clip(15.0 / np.where(rv30 > 1e-6, rv30, 15.0), 0.0, 1.5)
rv_cum  = np.cumprod(1 + spy_arr * rv_sizes)

thresh_sizes = np.clip(15.0 / np.where(thresh_vol_series > 1e-6, thresh_vol_series, 15.0), 0.0, 1.5)
thresh_cum   = np.cumprod(1 + spy_arr * thresh_sizes)

hdp_sizes = np.clip(15.0 / np.where(hdp_vol_series > 1e-6, hdp_vol_series, 15.0), 0.0, 1.5)
hdp_cum   = np.cumprod(1 + spy_arr * hdp_sizes)

labels_df = pd.DataFrame({
    'date':          feat_train.index,
    'spy_ret':       spy_arr,
    'vol_index':     vol_s.values,
    'hdp_regime':    [hdp_name_map[l]    for l in hdp_labels],
    'thresh_regime': [thresh_name_map[l] for l in thresh_labels],
    'param_regime':  [param_name_map[s]  for s in param_states],
    'cum_bh':        bh_cum,
    'cum_rv30':      rv_cum,
    'cum_vix_thr':   thresh_cum,
    'cum_hdp':       hdp_cum,
})
labels_df.to_csv('results/regime_labels_train.csv', index=False)

trans_df = pd.DataFrame(
    hdp_trans,
    index=['Low-Vol', 'Moderate-Vol', 'High-Vol'],
    columns=['Low-Vol', 'Moderate-Vol', 'High-Vol'],
)
trans_df.to_csv('results/transition_matrix.csv')
log("  Saved results/regime_labels_train.csv and results/transition_matrix.csv")


# ===================================================================
# LaTeX output
# ===================================================================
log("\nWriting LaTeX output to results/ ...")

# paper_results.txt stays for backward compat — full file (macros + tables)
OUT   = open('results/paper_results.txt', 'w')
MACRO = open('results/paper_macros.tex', 'w')   # \newcommand only → preamble
TABLE = open('results/paper_tables.tex', 'w')   # table envs only → Results section

def tex(s, dest='tables'):
    """Write to paper_results.txt always; also route to the split files."""
    OUT.write(s + '\n')
    if dest == 'macros':
        MACRO.write(s + '\n')
    else:
        TABLE.write(s + '\n')

tex("% ================================================================")
tex("% AUTO-GENERATED PAPER RESULTS — regime-detection/run_paper_experiments.py")
tex(f"% Generated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}")
tex(f"% Train: {feat_train.index[0].date()} to {feat_train.index[-1].date()}  ({len(feat_train)} trading days)")
tex("% ================================================================\n")


# --- Table 1: Regime Characteristics ---
tex("% ---- TABLE 1: REGIME CHARACTERISTICS ----\n")
tex(r"\begin{table}[htbp]")
tex(r"\centering")
tex(r"\caption{Within-regime characteristics (in-sample training period). "
    r"Ann. Ret and Ann. Vol are annualized (\%). "
    r"Sharpe = Ann. Ret / Ann. Vol. Dwell = mean consecutive days in regime.}")
tex(r"\label{tab:regime_chars}")
tex(r"\begin{tabular}{llrrrrrrrr}")
tex(r"\toprule")
tex(r"Model & Regime & N & \% & Ann. Ret & Ann. Vol & Sharpe & Avg VIX & Dwell \\")
tex(r"\midrule")

current_model = None
for _, row in stats_df.iterrows():
    if row['Model'] != current_model:
        if current_model is not None:
            tex(r"\addlinespace")
        current_model = row['Model']
    tex(f"{row['Model']} & {row['Regime']} & {int(row['N'])} & "
        f"{row['Pct']:.1f}\\% & "
        f"{row['AnnRet']:+.2f} & {row['AnnVol']:.2f} & "
        f"{row['Sharpe']:+.2f} & {row['VIX']:.1f} & {row['Dwell']:.1f} \\\\")

tex(r"\bottomrule")
tex(r"\end{tabular}")
tex(r"\end{table}")
tex("")


# --- Table 2: Transition Matrix (HDP-HMM) ---
tex("% ---- TABLE 2: TRANSITION MATRIX (HDP-HMM) ----\n")
K_eff = 3
state_names = ['Low-Vol', 'Moderate-Vol', 'High-Vol']

tex(r"\begin{table}[htbp]")
tex(r"\centering")
tex(r"\caption{HDP-HMM transition matrix (posterior mean). "
    r"High diagonal entries confirm regime persistence (sticky transitions).}")
tex(r"\label{tab:transition}")

col_spec = "l" + "r" * K_eff
tex(r"\begin{tabular}{" + col_spec + "}")
tex(r"\toprule")
header = "From $\\backslash$ To & " + " & ".join(state_names) + r" \\"
tex(header)
tex(r"\midrule")
for i in range(K_eff):
    row_name = state_names[i]
    cells = " & ".join(f"{hdp_trans[i, j]:.3f}" for j in range(K_eff))
    tex(f"{row_name} & {cells} \\\\")
tex(r"\bottomrule")
tex(r"\end{tabular}")
tex(r"\end{table}")
tex("")


# --- Table 3: Information Content ---
tex("% ---- TABLE 3: INFORMATION CONTENT REGRESSION ----\n")
tex(r"\begin{table}[htbp]")
tex(r"\centering")
tex(r"\caption{Information content of regime labels beyond VIX. "
    r"Dependent variable: 5-day forward SPY log return. "
    r"Columns show $R^2$ from OLS regression on (i) VIX alone, "
    r"(ii) VIX + regime dummies. $\Delta R^2$ is the improvement.}")
tex(r"\label{tab:info_content}")
tex(r"\begin{tabular}{lrrr}")
tex(r"\toprule")
tex(r"Model & $R^2$ (VIX only) & $R^2$ (+ Regimes) & $\Delta R^2$ \\")
tex(r"\midrule")
for model_name, r2_full in r2_results.items():
    if model_name == 'VIX only':
        continue
    delta = r2_full - r2_vix
    tex(f"{model_name} & {r2_vix:.4f} & {r2_full:.4f} & {delta:+.4f} \\\\")
tex(r"\bottomrule")
tex(r"\end{tabular}")
tex(r"\end{table}")
tex("")


# --- Table 4: Backtest ---
tex("% ---- TABLE 4: VOLATILITY-TARGETING BACKTEST ----\n")
tex(r"\begin{table}[htbp]")
tex(r"\centering")
tex(r"\caption{Volatility-targeting backtest (in-sample, \nTrainStart{}--\nTrainEnd{}). "
    r"All strategies target 15\% annualized portfolio volatility, capped at $1.5\times$ "
    r"exposure. RV30 = 30-day lagged realized volatility. "
    r"Rebalances/yr = mean annual position changes.}")
tex(r"\label{tab:backtest}")
tex(r"\begin{tabular}{lrrrrrr}")
tex(r"\toprule")
tex(r"Strategy & Ann.\ Ret (\%) & Ann.\ Vol (\%) & Sharpe & Max DD (\%) & Rebal./yr \\")
tex(r"\midrule")
for strat_name, res in backtest_rows.items():
    tex(f"{strat_name} & {res['Ann. Ret (%)']:.2f} & {res['Ann. Vol (%)']:.2f} & "
        f"{res['Sharpe']:.3f} & {res['Max DD (%)']:.1f} & {res['Rebalances/yr']:.0f} \\\\")
tex(r"\bottomrule")
tex(r"\end{tabular}")
tex(r"\end{table}")
tex("")

# Inline backtest numbers — macros → preamble
hdp_bt = backtest_rows['Vol-Target (HDP)']
bh_bt  = backtest_rows['Buy \\& Hold']
rv_bt  = backtest_rows['Vol-Target (RV30)']
tex(f"\\newcommand{{\\nBHSharpe}}{{{bh_bt['Sharpe']:.3f}}}", 'macros')
tex(f"\\newcommand{{\\nBHMaxDD}}{{{bh_bt['Max DD (%)']:.1f}\\%}}", 'macros')
tex(f"\\newcommand{{\\nRVSharpe}}{{{rv_bt['Sharpe']:.3f}}}", 'macros')
tex(f"\\newcommand{{\\nHDPBTSharpe}}{{{hdp_bt['Sharpe']:.3f}}}", 'macros')
tex(f"\\newcommand{{\\nHDPBTMaxDD}}{{{hdp_bt['Max DD (%)']:.1f}\\%}}", 'macros')
tex(f"\\newcommand{{\\nHDPRebalPerYear}}{{{hdp_bt['Rebalances/yr']:.0f}}}", 'macros')
tex(f"\\newcommand{{\\nRVRebalPerYear}}{{{rv_bt['Rebalances/yr']:.0f}}}", 'macros')
tex("", 'macros')


# --- Appendix: Posterior Diagnostics (comments only, no dest needed) ---
tex("% ---- APPENDIX: POSTERIOR DIAGNOSTICS ----\n")
tex("% Paste into diagnostics section or footnote.\n")
tex(f"% Effective K (raw, pre-merge): mean={eff_k_mean:.1f}, std={eff_k_std:.1f}, mode={eff_k_mode}")
tex(f"% Merged to K=3 for tables using merge_similar_states()")
tex(f"% SVI steps:    4000")
tex(f"% SVI converged: {hdp_diag.get('converged', 'N/A')}")
tex(f"% Final ELBO:   {hdp_diag.get('final_elbo', 'N/A'):.1f}" if isinstance(hdp_diag.get('final_elbo'), float) else "% Final ELBO: see run_log.txt")
tex(f"% Active states (post-merge to 3): Low-Vol, Moderate-Vol, High-Vol")
tex(f"% Realized vol by regime: { {hdp_name_map[k]: round(hdp_vols[k],1) for k in range(3) if k in hdp_vols} } (annualized %)")
tex("")


# --- Inline numbers for paper body — macros → preamble ---
tex("% ---- INLINE NUMBERS FOR PAPER BODY ----\n", 'macros')
hdp_rows = stats_df[stats_df['Model'] == 'HDP-HMM'].copy()
seen = set()
for _, row in hdp_rows.iterrows():
    label = row['Regime'].replace('-', '').replace(' ', '')
    if label in seen:
        continue
    seen.add(label)
    tex(f"\\newcommand{{\\n{label}Days}}{{{int(row['N'])}}}", 'macros')
    tex(f"\\newcommand{{\\n{label}Pct}}{{{row['Pct']:.1f}\\%}}", 'macros')
    tex(f"\\newcommand{{\\n{label}AnnRet}}{{{row['AnnRet']:+.2f}}}", 'macros')
    tex(f"\\newcommand{{\\n{label}AnnVol}}{{{row['AnnVol']:.2f}}}", 'macros')
    tex(f"\\newcommand{{\\n{label}Sharpe}}{{{row['Sharpe']:+.2f}}}", 'macros')
    tex(f"\\newcommand{{\\n{label}VIX}}{{{row['VIX']:.1f}}}", 'macros')
    tex(f"\\newcommand{{\\n{label}Dwell}}{{{row['Dwell']:.1f}}}", 'macros')
    tex("", 'macros')
tex(f"\\newcommand{{\\nEffKRaw}}{{{eff_k_mode}}}", 'macros')
tex(f"\\newcommand{{\\nEffKMerged}}{{3}}", 'macros')
tex(f"\\newcommand{{\\nTrainDays}}{{{len(feat_train)}}}", 'macros')
tex(f"\\newcommand{{\\nTrainStart}}{{{feat_train.index[0].strftime('%B %Y')}}}", 'macros')
tex(f"\\newcommand{{\\nTrainEnd}}{{{feat_train.index[-1].strftime('%B %Y')}}}", 'macros')
tex(f"\\newcommand{{\\nRsqVIX}}{{{r2_vix:.4f}}}", 'macros')
r2_hdp = r2_results.get('HDP-HMM', None)
if r2_hdp is not None:
    tex(f"\\newcommand{{\\nRsqHDP}}{{{r2_hdp:.4f}}}", 'macros')
    tex(f"\\newcommand{{\\nDeltaRsqHDP}}{{{r2_hdp - r2_vix:+.4f}}}", 'macros')

OUT.close()
MACRO.close()
TABLE.close()
log("Done. Written: results/paper_results.txt, results/paper_macros.tex, results/paper_tables.tex")
log("             + results/regime_labels_train.csv, results/transition_matrix.csv")
LOG.close()
