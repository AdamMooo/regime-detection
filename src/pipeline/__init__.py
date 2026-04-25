"""Pipeline package — orchestration layer for the daily HDP-HMM regime detection run.

Satisfies PIPE-01, PIPE-02, PIPE-03 (via runner + stages + schema enrichment in signals).
"""
from src.pipeline.runner import Pipeline

__all__ = ['Pipeline']
