"""Step 3 (NO look — descriptive spanning characterization; FACTOR-MODEL-DIRECTION §5-6).

Builds the regime factor REG (both FMP constructions) on the FF 25 size/BE-ME portfolios and asks
whether REG is SPANNED by Mkt/SMB/HML + BAB. The honest prior (§5): SPANNED — our label is a
market-downside-vol transform, so a regime-beta spread most likely re-loads the low-vol/BAB axis.

DISCIPLINE — READ BEFORE INTERPRETING OUTPUT:
  * Spanned (|t_alpha_nw| < 3, or alpha ~ 0)  => CLOSED cheaply. "Regime is the vol/BAB axis in the
    cross-section." This is the expected, clean result.
  * An UNSPANNED alpha here is NOT a SUPPORT claim. It only triggers the Step-4 protocol: freeze a
    prereg (spanning + Sh^2 + GRS + sign + international confirmation), overnight cooling-off, an
    explicit dated sign-off, THEN the single look. Nothing here spends that look.
  * Economic sign gate: a genuine regime risk factor is a HEDGE => its premium (mean REG) must be
    NEGATIVE. A POSITIVE premium is a timing artifact (the Case-B trap), not a priced factor.
"""

from pathlib import Path

import numpy as np
import pandas as pd

import sys
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from factor_tests import factor_spanning_nw, max_sharpe2
from regime_factor import beta_sort_factor, mimicking_factor, regime_innovation

WINDOW = 60
ANN = np.sqrt(12.0)


def load():
    panel = pd.read_csv(ROOT / "data/processed/factor_test_monthly.csv", index_col=0, parse_dates=True)
    reg = pd.read_csv(ROOT / "data/processed/regime_monthly.csv", index_col=0, parse_dates=True)
    bab = pd.read_csv(ROOT / "data/processed/bab_monthly.csv", index_col=0, parse_dates=True)
    df = panel.join(reg[["stress_eom"]], how="inner").join(bab[["bab_us"]], how="inner").dropna(
        subset=["bab_us", "stress_eom"])
    return df


def spanning_row(name, reg, ctrl_ff3, ctrl_ff3_bab):
    ok = np.isfinite(reg) & np.all(np.isfinite(ctrl_ff3_bab), axis=1)
    r = reg[ok]
    ff3 = factor_spanning_nw(r, ctrl_ff3[ok], lags=6)
    ff3b = factor_spanning_nw(r, ctrl_ff3_bab[ok], lags=6)
    sh2_base = max_sharpe2(ctrl_ff3_bab[ok])
    sh2_aug = max_sharpe2(np.column_stack([ctrl_ff3_bab[ok], r]))
    corr_bab = float(np.corrcoef(r, ctrl_ff3_bab[ok][:, -1])[0, 1])
    return dict(
        construction=name, n=int(ok.sum()),
        mean_mo=float(r.mean()), sharpe_ann=float(r.mean() / r.std() * ANN),
        corr_bab=corr_bab,
        alpha_ff3_mo=ff3["alpha"], t_ff3_nw=ff3["t_alpha_nw"], r2_ff3=ff3["r2"],
        alpha_ff3bab_mo=ff3b["alpha"], t_ff3bab_nw=ff3b["t_alpha_nw"],
        t_ff3bab_ols=ff3b["t_alpha_ols"], r2_ff3bab=ff3b["r2"],
        dSh2=sh2_aug - sh2_base, dSharpe_ann=float(np.sqrt(max(sh2_aug, 0)) - np.sqrt(max(sh2_base, 0))) * ANN,
    )


def main():
    df = load()
    port_cols = [c for c in df.columns if len(c) == 4 and c[0] == "s" and c[2] == "v"]
    R = (df[port_cols].to_numpy() - df["rf"].to_numpy()[:, None])          # excess returns 25 assets
    innov = regime_innovation(df["stress_eom"].to_numpy(), "diff")
    ctrl_ff3 = df[["mkt_rf", "smb", "hml"]].to_numpy()
    ctrl_ff3_bab = df[["mkt_rf", "smb", "hml", "bab_us"]].to_numpy()

    reg_beta = beta_sort_factor(R, innov, window=WINDOW, frac=0.3)["reg"]
    reg_mim = mimicking_factor(R, innov, window=WINDOW)["reg"]

    rows = [
        spanning_row("beta_sort", reg_beta, ctrl_ff3, ctrl_ff3_bab),
        spanning_row("mimicking", reg_mim, ctrl_ff3, ctrl_ff3_bab),
    ]
    out = pd.DataFrame(rows).set_index("construction")
    out.to_csv(ROOT / "results/regime_spanning.csv")

    pd.set_option("display.width", 200, "display.max_columns", 30)
    print(f"sample {df.index.min().date()}..{df.index.max().date()}  window={WINDOW}mo\n")
    print(out.round(4).T.to_string())
    print("\n--- reading (per discipline banner in this file) ---")
    for _, r in out.reset_index().iterrows():
        spanned = abs(r["t_ff3bab_nw"]) < 3
        sign = "NEGATIVE (hedge, correct)" if r["mean_mo"] < 0 else "POSITIVE (timing-artifact flag)"
        verdict = ("SPANNED by FF3+BAB -> CLOSED cheaply" if spanned
                   else "UNSPANNED alpha -> Step-4 protocol ONLY (NOT support)")
        print(f"  {r['construction']:10s}: alpha_nw t={r['t_ff3bab_nw']:+.2f}  mean sign {sign}  =>  {verdict}")


if __name__ == "__main__":
    main()
