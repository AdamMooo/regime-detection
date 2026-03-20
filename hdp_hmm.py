"""
Bayesian HDP-HMM with Sticky Transitions and Student-t Emissions.
=================================================================
Supports two inference methods:
  - SVI  (Stochastic Variational Inference) -- fast, recommended for CPU
  - NUTS (Hamiltonian Monte Carlo)          -- gold-standard, slow on CPU

The model auto-discovers the number of regimes via a truncated
stick-breaking prior.

Key features:
  - Stick-breaking GEM(gamma) prior -> global state weights beta
  - Sticky transition rows:  pi_k ~ Dir(alpha*beta + kappa*delta_k)
  - Multivariate Student-t emissions with learnable degrees of freedom
  - Forward algorithm in JAX (jax.lax.scan) for marginalizing discrete states
  - Vectorized model (no Python for-loops) for fast JIT compilation
  - Posterior state probabilities via forward-backward on posterior mean params
"""

import json
import os
import time
import warnings

import jax
import jax.numpy as jnp
import jax.random as jrandom
from jax import lax
from jax.scipy.special import gammaln
import numpy as np
import numpyro
import numpyro.distributions as dist
from numpyro.infer import MCMC, NUTS, SVI, Trace_ELBO, Predictive
from numpyro.infer.autoguide import AutoNormal
from numpyro.infer.initialization import init_to_feasible

from config import (
    RANDOM_SEED, HDP_TRUNCATION, HDP_ALPHA, HDP_KAPPA,
    HDP_INFERENCE, MCMC_NUM_WARMUP, MCMC_NUM_SAMPLES, MCMC_NUM_CHAINS,
    SVI_NUM_STEPS, SVI_LEARNING_RATE, SVI_NUM_SAMPLES,
    T_DF, REGIME_NAMES, MIN_REGIME_OBS, HDP_MAX_REGIMES,
)

# Silence JAX/NumPyro startup noise
warnings.filterwarnings('ignore', message='.*JAX.*')
warnings.filterwarnings('ignore', message='.*jaxlib.*')

# Force CPU backend (avoids GPU search overhead on laptops)
jax.config.update("jax_platform_name", "cpu")
# 64-bit precision for numerical stability in forward algorithm
jax.config.update("jax_enable_x64", True)


# ===================================================================
# Student-t log-pdf (multivariate) in JAX
# ===================================================================

def _diag_mvt_logpdf_batch(X, loc, scale_diag_vec, df):
    """
    Log-pdf of multivariate Student-t with diagonal covariance.
    Vectorized over observations.  Avoids solve_triangular for stability.
    """
    D = loc.shape[0]
    safe_sd = jnp.clip(scale_diag_vec, 1e-6)
    diff = X - loc[None, :]          # (T, D)
    z = diff / safe_sd[None, :]      # (T, D)
    quad = jnp.sum(z ** 2, axis=1)   # (T,)

    log_norm = (
        gammaln((df + D) / 2.0)
        - gammaln(df / 2.0)
        - 0.5 * D * jnp.log(df * jnp.pi)
        - jnp.sum(jnp.log(safe_sd))
    )
    log_kernel = -0.5 * (df + D) * jnp.log1p(quad / df)
    return log_norm + log_kernel


# ===================================================================
# Stick-breaking construction
# ===================================================================

def stick_breaking(v):
    """Convert stick-breaking proportions v ~ Beta to weights beta."""
    one_minus_v = jnp.concatenate([jnp.cumprod(1.0 - v), jnp.array([1.0])])
    prev_remaining = jnp.concatenate([jnp.array([1.0]), one_minus_v[:-1]])
    v_ext = jnp.concatenate([v, jnp.array([1.0])])
    return v_ext * prev_remaining


# ===================================================================
# NumPyro Model (vectorized -- no Python for-loops over K)
# ===================================================================

def hdp_hmm_model(obs, K_max=HDP_TRUNCATION):
    """
    Sticky HDP-HMM with Student-t emissions.
    Discrete states are marginalized via the forward algorithm.
    """
    T_len, D = obs.shape

    # --- Global state weights via stick-breaking ---
    # Gamma(0.5, 2.0) prior on alpha_dp: mean=0.25, concentrates mass
    # on fewer states (lower alpha -> sparser stick-breaking)
    alpha_dp = numpyro.sample('alpha_dp', dist.Gamma(0.5, 2.0))
    v_raw = numpyro.sample(
        'v_raw',
        dist.Beta(1.0, alpha_dp).expand([K_max - 1]).to_event(1),
    )
    beta = numpyro.deterministic('beta', stick_breaking(v_raw))

    # --- Sticky transition matrix (vectorized) ---
    kappa = numpyro.sample('kappa', dist.Gamma(2.0, 0.2))
    alpha_trans = numpyro.sample('alpha_trans', dist.Gamma(1.0, 1.0))

    # Concentration: alpha * beta + kappa * I (sticky diagonal)
    conc_matrix = alpha_trans * beta[None, :] + kappa * jnp.eye(K_max)  # type: ignore[index]
    conc_matrix = jnp.clip(conc_matrix, 1e-6)
    trans_matrix = numpyro.sample(
        'trans_matrix', dist.Dirichlet(conc_matrix).to_event(1),
    )

    # --- Initial state distribution ---
    init_probs = numpyro.deterministic('init_probs', beta)

    # --- Emission parameters ---
    locs = numpyro.sample(
        'locs',
        dist.Normal(0.0, 3.0).expand([K_max, D]).to_event(2),
    )
    scale_diag = numpyro.sample(
        'scale_diag',
        dist.HalfCauchy(2.0).expand([K_max, D]).to_event(2),
    )
    df_raw = numpyro.sample(
        'df_raw',
        dist.Gamma(2.0, 0.1).expand([K_max]).to_event(1),
    )
    df = numpyro.deterministic('df', df_raw + 2.0)

    # --- Emission log-likelihoods (vectorized over states) ---
    def _single_state_ll(loc_k, sd_k, df_k):
        return _diag_mvt_logpdf_batch(obs, loc_k, sd_k, df_k)

    log_lik = jax.vmap(_single_state_ll)(locs, scale_diag, df).T  # (T, K)

    # --- Forward algorithm (marginalize discrete states via scan) ---
    log_trans = jnp.log(trans_matrix + 1e-30)
    log_init = jnp.log(init_probs + 1e-30)

    def _forward_step(log_alpha_prev, log_lik_t):
        log_alpha_pred = jax.nn.logsumexp(
            log_alpha_prev[:, None] + log_trans, axis=0,
        )
        log_alpha_new = log_alpha_pred + log_lik_t
        log_norm = jax.nn.logsumexp(log_alpha_new)
        return log_alpha_new - log_norm, log_norm

    log_alpha_0 = log_init + log_lik[0]
    log_norm_0 = jax.nn.logsumexp(log_alpha_0)
    log_alpha_0 = log_alpha_0 - log_norm_0

    _, log_norms = lax.scan(_forward_step, log_alpha_0, log_lik[1:])
    total_ll = log_norm_0 + jnp.sum(log_norms)
    numpyro.factor('log_likelihood', total_ll)


# ===================================================================
# Inference
# ===================================================================

def fit_hdp_hmm(pcs, K_max=HDP_TRUNCATION, inference=HDP_INFERENCE,
                seed=RANDOM_SEED):
    """
    Run inference for the HDP-HMM model.

    Returns
    -------
    result   : SVIRunResult or MCMC object
    samples  : dict of posterior samples (numpy arrays)
    """
    obs = jnp.array(pcs, dtype=jnp.float64)
    if inference == 'svi':
        return _fit_svi(obs, K_max, seed)
    else:
        return _fit_nuts(obs, K_max, seed)


def _fit_svi(obs, K_max, seed):
    """SVI -- fast variational inference for CPU."""
    rng_key = jrandom.PRNGKey(seed)
    guide = AutoNormal(hdp_hmm_model, init_loc_fn=init_to_feasible)
    optimizer = numpyro.optim.Adam(step_size=SVI_LEARNING_RATE)
    svi = SVI(hdp_hmm_model, guide, optimizer, loss=Trace_ELBO())

    print(f"\nBayesian HDP-HMM via SVI (K_max={K_max}, "
          f"{SVI_NUM_STEPS} steps, lr={SVI_LEARNING_RATE}):")
    print("  JAX compiling model (one-time cost)...")

    t0 = time.time()
    svi_result = svi.run(rng_key, SVI_NUM_STEPS, obs, K_max=K_max,
                         progress_bar=True)
    elapsed = time.time() - t0

    final_loss = float(svi_result.losses[-1])
    print(f"  Done in {elapsed:.0f}s  |  Final ELBO loss: {final_loss:.1f}")

    # --- SVI convergence check ---
    losses = np.array(svi_result.losses)
    tail = losses[-200:]
    early = losses[-400:-200] if len(losses) >= 400 else losses[:len(losses)//2]
    if len(early) > 0:
        rel_change = abs(tail.mean() - early.mean()) / (abs(early.mean()) + 1e-8)
        if rel_change > 0.05:
            warnings.warn(
                f"SVI may not have converged: relative ELBO change in last "
                f"400 steps = {rel_change:.3f} (> 0.05). Consider more steps."
            )

    # Draw posterior samples from trained guide
    rng_key2 = jrandom.PRNGKey(seed + 1)
    predictive = Predictive(guide, params=svi_result.params,
                            num_samples=SVI_NUM_SAMPLES)
    raw_samples = predictive(rng_key2, obs, K_max=K_max)
    samples = {k: np.array(v) for k, v in raw_samples.items()}

    # Compute deterministic sites the guide doesn't produce
    if 'beta' not in samples:
        v = jnp.array(samples['v_raw'])
        samples['beta'] = np.array(jax.vmap(stick_breaking)(v))
    if 'df' not in samples:
        samples['df'] = np.array(samples['df_raw']) + 2.0
    if 'init_probs' not in samples:
        samples['init_probs'] = samples['beta'].copy()

    return svi_result, samples


def _fit_nuts(obs, K_max, seed):
    """NUTS MCMC -- gold-standard, best run overnight on CPU."""
    rng_key = jrandom.PRNGKey(seed)
    kernel = NUTS(
        hdp_hmm_model,
        target_accept_prob=0.8,
        max_tree_depth=8,
    )
    mcmc = MCMC(
        kernel,
        num_warmup=MCMC_NUM_WARMUP,
        num_samples=MCMC_NUM_SAMPLES,
        num_chains=MCMC_NUM_CHAINS,
        progress_bar=True,
    )

    print(f"\nBayesian HDP-HMM via NUTS (K_max={K_max}, "
          f"{MCMC_NUM_WARMUP} warmup + {MCMC_NUM_SAMPLES} x {MCMC_NUM_CHAINS} chains):")
    print("  JAX compiling model (one-time cost)...")

    t0 = time.time()
    mcmc.run(rng_key, obs, K_max=K_max)
    elapsed = time.time() - t0
    print(f"  Done in {elapsed:.0f}s")

    # --- Convergence diagnostics ---
    if MCMC_NUM_CHAINS > 1:
        from numpyro.diagnostics import summary
        diag = summary(mcmc.get_samples(group_by_chain=True))
        bad_rhat, low_ess = [], []
        for param_name, stats in diag.items():
            rh = stats.get('r_hat')
            ess = stats.get('n_eff')
            if rh is not None and np.any(rh > 1.05):
                bad_rhat.append((param_name, float(np.max(rh))))
            if ess is not None and np.any(ess < 100):
                low_ess.append((param_name, float(np.min(ess))))
        if bad_rhat:
            warnings.warn(
                f"MCMC convergence issue: R-hat > 1.05 for "
                f"{[f'{n}={v:.3f}' for n, v in bad_rhat[:5]]}. "
                f"Consider more warmup or thinning."
            )
        if low_ess:
            warnings.warn(
                f"Low effective sample size (< 100) for "
                f"{[f'{n}={v:.0f}' for n, v in low_ess[:5]]}. "
                f"Consider more samples or thinning."
            )

    samples = {k: np.array(v) for k, v in mcmc.get_samples().items()}

    # Ensure deterministic sites are present
    if 'beta' not in samples:
        v = jnp.array(samples['v_raw'])
        samples['beta'] = np.array(jax.vmap(stick_breaking)(v))
    if 'df' not in samples:
        samples['df'] = np.array(samples['df_raw']) + 2.0
    if 'init_probs' not in samples:
        samples['init_probs'] = samples['beta'].copy()

    return mcmc, samples


# ===================================================================
# Post-processing
# ===================================================================

def effective_K(samples, threshold=0.01):
    """Count active states from posterior beta weights."""
    beta = np.array(samples['beta'])
    K_per_sample = (beta > threshold).sum(axis=1)
    from collections import Counter
    counts = Counter(K_per_sample.tolist())
    mode_K = counts.most_common(1)[0][0]
    return float(K_per_sample.mean()), float(K_per_sample.std()), int(mode_K)


def posterior_mean_params(samples, K_max=HDP_TRUNCATION):
    """Extract posterior-mean parameters for forward-backward decoding."""
    beta = np.array(samples['beta']).mean(axis=0)
    init_probs = beta / beta.sum()
    trans_matrix = np.array(samples['trans_matrix']).mean(axis=0)
    locs = np.array(samples['locs']).mean(axis=0)
    scale_diag = np.array(samples['scale_diag']).mean(axis=0)
    df = np.array(samples['df']).mean(axis=0)

    return {
        'beta': beta,
        'trans_matrix': trans_matrix,
        'init_probs': init_probs,
        'locs': locs,
        'scale_diag': scale_diag,
        'df': df,
        'K_max': K_max,
    }


def forward_backward_numpy(obs, params):
    """
    Forward-backward on posterior-mean params (numpy, no JAX needed).
    Returns filtered P(s_t | x_{1:t}) and smoothed P(s_t | x_{1:T}).
    """
    T_len, D = obs.shape
    K = params['K_max']
    trans = params['trans_matrix']
    locs = params['locs']
    scale_diag = params['scale_diag']
    df_arr = params['df']
    init = params['init_probs']

    from scipy.stats import t as t_dist
    log_lik = np.zeros((T_len, K))
    for k in range(K):
        for d in range(D):
            log_lik[:, k] += t_dist.logpdf(
                obs[:, d], df=df_arr[k],
                loc=locs[k, d], scale=scale_diag[k, d],
            )

    log_trans = np.log(trans + 1e-300)
    log_init = np.log(init + 1e-300)

    # Forward pass
    log_alpha = np.zeros((T_len, K))
    log_alpha[0] = log_init + log_lik[0]
    log_alpha[0] -= _logsumexp(log_alpha[0])

    for t in range(1, T_len):
        for j in range(K):
            log_alpha[t, j] = _logsumexp(
                log_alpha[t - 1] + log_trans[:, j]
            ) + log_lik[t, j]
        log_alpha[t] -= _logsumexp(log_alpha[t])

    filtered = np.exp(log_alpha)
    filtered /= filtered.sum(axis=1, keepdims=True)

    # Backward pass
    log_beta = np.zeros((T_len, K))
    for t in range(T_len - 2, -1, -1):
        for j in range(K):
            log_beta[t, j] = _logsumexp(
                log_trans[j, :] + log_lik[t + 1] + log_beta[t + 1]
            )
        log_beta[t] -= _logsumexp(log_beta[t])

    # Smoothed = normalized(alpha * beta)
    log_gamma = log_alpha + log_beta
    log_gamma -= _logsumexp_2d(log_gamma)
    smoothed = np.exp(log_gamma)
    smoothed /= smoothed.sum(axis=1, keepdims=True)

    return filtered, smoothed


def _logsumexp(a):
    """Numerically stable log-sum-exp for 1D array."""
    a = np.asarray(a, dtype=np.float64)
    c = a.max()
    if not np.isfinite(c):
        return -np.inf
    return c + np.log(np.sum(np.exp(a - c)))


def _logsumexp_2d(a):
    """Per-row logsumexp for 2D array."""
    c = a.max(axis=1, keepdims=True)
    return c + np.log(np.sum(np.exp(a - c), axis=1, keepdims=True))


def prune_states(params, filtered, threshold=0.08):
    """Identify active states: must have meaningful beta weight AND occupy days."""
    beta = params['beta']
    T_len = filtered.shape[0]
    max_assignments = filtered.argmax(axis=1)
    active = []
    for k in range(params['K_max']):
        n_assigned = (max_assignments == k).sum()
        # Keep state only if it has real weight AND is assigned to enough days
        if beta[k] > threshold and n_assigned > max(T_len * 0.01, 10):
            active.append(k)
    # Fallback: if nothing passes, keep top states by beta weight
    if len(active) < 2:
        ranked = np.argsort(-beta)
        active = sorted(ranked[:3].tolist())
    print(f"  Pruning: {len(active)} active states from {params['K_max']} truncation")
    for k in range(params['K_max']):
        n_assigned = (max_assignments == k).sum()
        tag = ' <-- ACTIVE' if k in active else ''
        print(f"    state {k}: beta={beta[k]:.4f}, days={n_assigned}{tag}")
    return active


def get_labels_and_probs(obs, params, hold_days=3):
    """
    Compute regime labels and probabilities from posterior-mean params.

    Returns: labels, filt_probs, smooth_probs, active_states
    """
    filtered, smoothed = forward_backward_numpy(obs, params)
    active = prune_states(params, filtered)

    filt_active = filtered[:, active]
    filt_active /= filt_active.sum(axis=1, keepdims=True)
    smooth_active = smoothed[:, active]
    smooth_active /= smooth_active.sum(axis=1, keepdims=True)

    raw = filt_active.argmax(axis=1)
    labels = _apply_hysteresis(raw, hold_days) if hold_days > 1 else raw

    return labels, filt_active, smooth_active, active


def _apply_hysteresis(raw, hold_days):
    """Apply hold-days hysteresis to prevent regime flicker."""
    out = np.empty_like(raw)
    out[0] = raw[0]
    pending = raw[0]
    streak = 0
    for t in range(1, len(raw)):
        if raw[t] == out[t - 1]:
            out[t] = out[t - 1]
            pending = out[t]
            streak = 0
        elif raw[t] == pending:
            streak += 1
            if streak >= hold_days:
                out[t] = pending
                streak = 0
            else:
                out[t] = out[t - 1]
        else:
            pending = raw[t]
            streak = 1
            out[t] = out[t - 1]
    return out


def merge_similar_states(labels, filt_probs, params, active_states,
                         max_regimes=HDP_MAX_REGIMES):
    """
    Iteratively merge closest pair of states (by emission location)
    until at most max_regimes remain.
    Returns: (new_labels, K_new, new_active_list)
    """
    from scipy.spatial.distance import pdist, squareform

    # Work with local-indexed labels (0..len(active)-1)
    cur_active = list(active_states)
    # Map: local idx -> set of original active indices that got merged here
    groups = {i: {a} for i, a in enumerate(cur_active)}
    cur_labels = labels.copy()

    while len(groups) > max_regimes:
        idxs = sorted(groups.keys())
        locs = params['locs'][[cur_active[i] for i in idxs]]
        if len(locs) <= 1:
            break
        dists = squareform(pdist(locs, 'euclidean'))
        np.fill_diagonal(dists, np.inf)
        pi, pj = np.unravel_index(dists.argmin(), dists.shape)
        # Map back to group keys
        ki, kj = idxs[pi], idxs[pj]
        # Merge kj into ki
        groups[ki] |= groups[kj]
        cur_labels[cur_labels == kj] = ki
        del groups[kj]

    # Re-index to 0..K_new-1
    final_keys = sorted(groups.keys())
    remap = {old: new for new, old in enumerate(final_keys)}
    final_labels = np.array([remap[l] for l in cur_labels])
    # Pick representative active state for each group (highest beta weight)
    new_active = []
    for k in final_keys:
        members = list(groups[k])
        best = max(members, key=lambda a: params['beta'][a])
        new_active.append(best)

    return final_labels, len(new_active), new_active


def label_regimes_hdp(labels, active_states, vix_values):
    """Assign interpretive regime names sorted by VIX mean."""
    K_eff = len(active_states)
    regime_vix = {}
    for i in range(K_eff):
        mask = (labels == i)
        regime_vix[i] = float(vix_values[mask].mean()) if mask.sum() > 0 else 0.0

    sorted_by_vix = sorted(regime_vix, key=lambda k: regime_vix[k])

    names = REGIME_NAMES.get(K_eff)
    if names is None:
        # Always produce meaningful names for any K
        _ALL_NAMES = ['Low-Vol', 'Moderate', 'Elevated', 'High-Vol', 'Stressed', 'Crisis']
        if K_eff <= len(_ALL_NAMES):
            # Evenly space through the name ladder
            idxs = np.linspace(0, len(_ALL_NAMES) - 1, K_eff, dtype=int)
            names = [_ALL_NAMES[i] for i in idxs]
        else:
            names = _ALL_NAMES + [f'Regime-{i}' for i in range(K_eff - len(_ALL_NAMES))]

    return {sorted_by_vix[i]: names[i] for i in range(K_eff)}


# ===================================================================
# Diagnostics (handles both SVI and NUTS)
# ===================================================================

def mcmc_diagnostics(result, samples):
    """Print and return diagnostic summary. Works with MCMC or SVI results."""
    if isinstance(result, MCMC):
        return _nuts_diagnostics(result, samples)
    else:
        return _svi_diagnostics(result, samples)


def _svi_diagnostics(svi_result, samples):
    """SVI diagnostics: ELBO convergence check."""
    losses = np.array(svi_result.losses)
    final = float(losses[-1])
    n = len(losses)
    early_avg = float(losses[:max(1, n // 10)].mean())
    late_avg = float(losses[-max(1, n // 10):].mean())
    converged = late_avg < early_avg

    print("\nSVI Diagnostics:")
    print(f"  Final ELBO loss: {final:.1f}")
    print(f"  Early avg: {early_avg:.1f}  ->  Late avg: {late_avg:.1f}")
    print(f"  Converged: {'Yes' if converged else 'WARNING -- may need more steps'}")

    return {
        'inference': 'svi',
        'final_elbo': final,
        'converged': converged,
        'n_steps': n,
    }


def _nuts_diagnostics(mcmc, samples):
    """NUTS diagnostics: R-hat, ESS, divergences."""
    n_divergences = 0
    if hasattr(mcmc, '_states'):
        for chain_state in mcmc._states.values():
            if hasattr(chain_state, 'diverging'):
                n_divergences += int(chain_state.diverging.sum())

    from numpyro.diagnostics import summary as numpyro_summary
    site_summary = numpyro_summary(samples, group_by_chain=False)

    key_params = ['alpha_dp', 'kappa', 'alpha_trans']
    r_hats, ess_vals = [], []

    print("\nNUTS Diagnostics:")
    print(f"  Divergences: {n_divergences}")

    for name in key_params:
        if name in site_summary:
            info = site_summary[name]
            rh = info.get('r_hat', np.nan)
            ess = info.get('n_eff', np.nan)
            if np.ndim(rh) > 0:
                rh, ess = np.nanmax(rh), np.nanmin(ess)
            r_hats.append(rh)
            ess_vals.append(ess)
            print(f"  {name}: R-hat={rh:.3f}, ESS={ess:.0f}")

    if 'beta' in site_summary:
        beta_rhat = site_summary['beta'].get('r_hat', np.nan)
        if np.ndim(beta_rhat) > 0:
            beta_rhat = np.nanmax(beta_rhat)
        print(f"  beta (max R-hat): {beta_rhat:.3f}")
        r_hats.append(beta_rhat)

    max_rhat = max(r_hats) if r_hats else np.nan
    min_ess = min(ess_vals) if ess_vals else np.nan
    print(f"  Max R-hat: {max_rhat:.3f} {'(OK)' if max_rhat < 1.05 else '(WARNING)'}")
    print(f"  Min ESS:   {min_ess:.0f} {'(OK)' if min_ess > 100 else '(WARNING)'}")

    return {
        'inference': 'nuts',
        'n_divergences': n_divergences,
        'max_r_hat': float(max_rhat) if np.isfinite(max_rhat) else None,
        'min_ess': float(min_ess) if np.isfinite(min_ess) else None,
    }


# ===================================================================
# Save / Load
# ===================================================================

def save_hdp_results(model_dir, result, samples, params, diagnostics,
                     effective_k_info, data_info):
    """Save HDP-HMM results with full metadata."""
    import joblib

    os.makedirs(model_dir, exist_ok=True)

    params_save = {k: v.tolist() if hasattr(v, 'tolist') else v
                   for k, v in params.items()}
    joblib.dump(params_save, os.path.join(model_dir, 'hdp_params.pkl'))

    # Save posterior samples (skip huge arrays)
    samples_np = {k: np.array(v) for k, v in samples.items()
                  if np.array(v).nbytes < 50_000_000}
    joblib.dump(samples_np, os.path.join(model_dir, 'hdp_samples.pkl'))

    inference_type = diagnostics.get('inference', 'unknown')
    # Per-state beta weights and emission means for inspecting state distinctness
    beta_weights = params.get('beta', np.array([]))
    per_state = []
    for k in range(len(beta_weights)):
        entry = {'state': k, 'beta': float(beta_weights[k])}
        if 'locs' in params and k < len(params['locs']):
            entry['mean_emission'] = [float(v) for v in params['locs'][k]]
        per_state.append(entry)

    metadata = {
        'model_type': f'HDP-HMM (Bayesian, {inference_type.upper()})',
        'K_max': params.get('K_max', HDP_TRUNCATION),
        'effective_K_mean': effective_k_info[0],
        'effective_K_std': effective_k_info[1],
        'effective_K_mode': effective_k_info[2],
        'diagnostics': diagnostics,
        'data': data_info,
        'per_state_detail': per_state,
    }
    with open(os.path.join(model_dir, 'hdp_metadata.json'), 'w') as f:
        json.dump(metadata, f, indent=2, default=str)


# ===================================================================
# Transition matrix extraction
# ===================================================================

def get_transition_matrix(params, active_states):
    """Extract transition matrix restricted to active states."""
    full_trans = params['trans_matrix']
    sub = full_trans[np.ix_(active_states, active_states)]
    row_sums = sub.sum(axis=1, keepdims=True)
    row_sums = np.where(row_sums > 0, row_sums, 1.0)
    return sub / row_sums


# ===================================================================
# HDP stability check
# ===================================================================

def hdp_stability_check(samples, obs, n_draws=10, seed=42):
    """Check label agreement across posterior samples (no re-inference).

    Draws n_draws sets of parameters from the posterior samples,
    runs forward decoding on each, and measures pairwise label agreement.

    Returns
    -------
    dict with 'mean_agreement', 'n_draws', 'per_draw_effective_k'
    """
    rng = np.random.RandomState(seed)
    n_posterior = len(samples['beta'])
    draw_indices = rng.choice(n_posterior, size=min(n_draws, n_posterior), replace=False)

    all_labels = []
    effective_ks = []

    for idx in draw_indices:
        # Extract single posterior sample as params dict
        params_i = {
            'beta': samples['beta'][idx],
            'trans_matrix': samples['trans_matrix'][idx],
            'init_probs': samples['beta'][idx] / samples['beta'][idx].sum(),
            'locs': samples['locs'][idx],
            'scale_diag': samples['scale_diag'][idx],
            'df': samples['df'][idx],
            'K_max': len(samples['beta'][idx]),
        }

        # Forward pass only (fast)
        filtered, _ = forward_backward_numpy(obs, params_i)
        labels_i = filtered.argmax(axis=1)
        all_labels.append(labels_i)

        # Effective K for this draw
        effective_ks.append(len(np.unique(labels_i)))

    # Pairwise agreement (mode-based: find best permutation alignment)
    agreements = []
    for i in range(len(all_labels)):
        for j in range(i + 1, len(all_labels)):
            # Simple agreement: fraction of matching labels
            # (without permutation alignment, since state indices may differ)
            # Use maximum overlap across simple relabeling
            a = all_labels[i]
            b = all_labels[j]
            states_a = np.unique(a)
            states_b = np.unique(b)

            # Build contingency and find best greedy mapping
            best_match = 0
            mapping = {}
            used_b = set()
            for sa in states_a:
                mask_a = (a == sa)
                best_overlap = 0
                best_sb = None
                for sb in states_b:
                    if sb in used_b:
                        continue
                    overlap = np.sum(mask_a & (b == sb))
                    if overlap > best_overlap:
                        best_overlap = overlap
                        best_sb = sb
                if best_sb is not None:
                    mapping[sa] = best_sb
                    used_b.add(best_sb)
                    best_match += best_overlap

            agreement = best_match / len(a) if len(a) > 0 else 0
            agreements.append(agreement)

    mean_agreement = float(np.mean(agreements)) if agreements else 1.0

    return {
        'mean_agreement': mean_agreement,
        'n_draws': len(all_labels),
        'per_draw_effective_k': effective_ks,
        'mean_effective_k': float(np.mean(effective_ks)),
    }


# ===================================================================
# Adapter (compatibility with hmmlearn interface)
# ===================================================================

class HDPModelAdapter:
    """Wraps HDP-HMM results to match hmmlearn GaussianHMM interface."""

    def __init__(self, params, active_states, labels, filtered_probs):
        self.params = params
        self.active_states = active_states
        self.n_components = len(active_states)
        self._labels = labels
        self._filtered_probs = filtered_probs

        self.transmat_ = get_transition_matrix(params, active_states)
        self.startprob_ = params['init_probs'][active_states]
        self.startprob_ /= self.startprob_.sum()
        self.means_ = params['locs'][active_states]
        sd = params['scale_diag'][active_states]
        self.covars_ = np.array([np.diag(sd[k] ** 2)
                                 for k in range(self.n_components)])

    def predict(self, X=None):
        return self._labels

    def predict_proba(self, X=None):
        return self._filtered_probs

    def score(self, X):
        return 0.0

    def _compute_log_likelihood(self, X):
        from scipy.stats import t as t_dist
        T_len, D = X.shape
        K = self.n_components
        log_lik = np.zeros((T_len, K))
        for ki, k_orig in enumerate(self.active_states):
            for d in range(D):
                log_lik[:, ki] += t_dist.logpdf(
                    X[:, d],
                    df=self.params['df'][k_orig],
                    loc=self.params['locs'][k_orig, d],
                    scale=self.params['scale_diag'][k_orig, d],
                )
        return log_lik
