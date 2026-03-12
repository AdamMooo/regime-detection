
import numpy as np
import pandas as pd

T_SCORE_WINDOW = 10  # More sensitive window

def t_score(series, window):
    """Calculate rolling t-score for tail risk."""
    mean = series.rolling(window).mean()
    std = series.rolling(window).std()
    tscore = (series - mean) / (std / np.sqrt(window))
    return tscore

def compute_geometry(market):
    log_vix = np.log(market['vix'])
    log_hy  = np.log(market['hy_spread'])
    geom = pd.DataFrame(index=market.index)
    geom['t_vix'] = t_score(log_vix, T_SCORE_WINDOW)
    geom['t_hy'] = t_score(log_hy, T_SCORE_WINDOW)
    return geom


def plot_regime_geometry(market, labels, name_map):
    colors = {'Low-Risk': 'green', 'Elevated-Risk': 'gold'}
    colors['Crisis'] = 'red'
