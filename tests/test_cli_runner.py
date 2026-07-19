import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import run as cli


def test_cli_help_works():
    repo = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        [sys.executable, 'scripts/run.py', '--help'],
        cwd=repo,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0
    assert 'usage:' in result.stdout.lower()


def test_regime_classifier_uses_current_vix_thresholds():
    assert cli.classify_regime_from_vix(10.0) == 'Low-Vol'
    assert cli.classify_regime_from_vix(18.8) == 'Moderate-Vol'
    assert cli.classify_regime_from_vix(25.0) == 'High-Vol'
