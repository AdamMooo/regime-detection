"""PIPE-01: full daily pipeline (no walk-forward) completes in <600s."""
import subprocess
import sys
import time
import pytest
import os


@pytest.mark.slow
def test_pipeline_under_600s():
    t0 = time.perf_counter()
    result = subprocess.run(
        [sys.executable, 'scripts/run.py'],
        capture_output=True,
        cwd=os.getcwd(),
    )
    elapsed = time.perf_counter() - t0
    assert result.returncode == 0, f"Pipeline failed: {result.stderr.decode()[-2000:]}"
    assert elapsed < 600, f"Pipeline took {elapsed:.0f}s (budget: 600s)"
