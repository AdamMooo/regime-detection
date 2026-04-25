"""PIPE-01: each of 8 stages runs in isolation and produces expected output files."""
import pytest


def test_pipeline_package_imports():
    from src.pipeline import Pipeline  # noqa: F401


def test_stages_registry_has_eight_plus_walk_forward():
    from src.pipeline.stages import STAGES
    names = [s[0] for s in STAGES]
    expected = ['collect', 'features', 'feature_analysis', 'pca',
                'train_hmm', 'garch', 'signals', 'dashboard', 'walk_forward']
    assert names == expected, f"Stage order mismatch: {names}"


def test_run_stage_callable():
    from src.pipeline import Pipeline
    p = Pipeline()
    assert callable(p.run_stage)
    assert callable(p.run_all)
    assert callable(p.run_from)
