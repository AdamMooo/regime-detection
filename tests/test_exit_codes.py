"""PIPE-01: forcing a stage failure produces exit code 1 (no silent swallow)."""
import subprocess
import pytest
import os


@pytest.mark.slow
def test_stage_failure_returns_exit_1(tmp_path, monkeypatch):
    # Force a stage failure by corrupting an input path via env var override.
    env = os.environ.copy()
    env['GSD_FORCE_STAGE_FAIL'] = 'features'  # runner honors this test hook
    result = subprocess.run(
        ['python', 'scripts/run.py'],
        capture_output=True, env=env,
    )
    assert result.returncode == 1, (
        f"Expected exit 1 on forced failure, got {result.returncode}. "
        f"stderr: {result.stderr.decode()[-1000:]}"
    )
