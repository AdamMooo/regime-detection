"""Walk-forward validation for HDP-HMM.

TODO: rewrite walk_forward() for the stripped HDP-HMM architecture
(4 features, no PCA, Gaussian emissions, NUTS inference).
The classic HMM walk-forward was removed as part of the architecture simplification.
"""


def walk_forward(*args, **kwargs):
    raise NotImplementedError(
        "walk_forward() must be rewritten for the HDP-HMM architecture. "
        "See architecture_rewrite_plan.md in memory."
    )


__all__ = ['walk_forward']
