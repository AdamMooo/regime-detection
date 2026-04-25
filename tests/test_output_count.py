"""PIPE-02: exactly 2 HTML files exist in figures/ after a run; stable across 2 runs."""
import subprocess
import glob
import os
import pytest


@pytest.mark.slow
def test_exactly_two_html_files_after_two_runs():
    for _ in range(2):
        subprocess.run(['python', 'scripts/run.py'], check=True)
    html_files = glob.glob(os.path.join('figures', '*.html'))
    assert len(html_files) == 2, f"Expected 2 HTML files, found {len(html_files)}: {html_files}"
    names = {os.path.basename(f) for f in html_files}
    assert names == {'dashboard.html', 'feature_analysis.html'}, f"Got {names}"
