import pandas as pd
import numpy as np
from src.core.hdp_hmm import fit_hdp_hmm
import matplotlib.pyplot as plt

def fit_toy_sticky_hdp():
    # Load train data
    df = pd.read_csv('data/processed/train.csv', index_col=0, parse_dates=True)
    
    # Use features: tsx_vol, boc_spread, wti_shock
    features = ['tsx_vol', 'boc_spread', 'wti_shock']
    obs = df[features].values
    
    # Fit HDP-HMM with SVI
    svi_result, samples = fit_hdp_hmm(obs, inference='svi')
    
    # Extract regime probabilities
    # For simplicity, take mean posterior for beta (state weights)
    beta_mean = samples['beta'].mean(axis=0)
    print(f"Discovered {np.sum(beta_mean > 0.01)} regimes")
    print(f"Regime weights: {beta_mean}")
    
    # Plot diagnostics
    plt.figure(figsize=(10, 6))
    plt.plot(svi_result.losses)
    plt.title('SVI ELBO Loss')
    plt.xlabel('Step')
    plt.ylabel('Loss')
    plt.savefig('figures/week1_diagnostics.png')
    plt.close()
    
    print("Toy sticky HDP-HMM fitted. Diagnostics saved to figures/week1_diagnostics.png")

if __name__ == '__main__':
    fit_toy_sticky_hdp()