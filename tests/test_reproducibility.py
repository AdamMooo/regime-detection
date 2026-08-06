"""Reproducibility guarantees.

Every test here exists because the corresponding failure ACTUALLY HAPPENED in
this repo (2026-08-06):

  - `arch` and `matplotlib` were imported but absent from requirements.txt, so a
    fresh clone could not run the volatility signal at all.
  - `results/vol_descriptors.csv` was committed without the half_life columns its
    own producer emits — a result artifact that silently disagreed with the code
    claiming to produce it.
  - `causal.assert_causal` existed but nothing forced a new signal to use it.

Point-in-time honesty is this repo's entire value proposition; "we were careful"
is not a guarantee, a failing test is.
"""

import ast
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

SCRIPTS = sorted((ROOT / "scripts").glob("*.py"))

# import name -> distribution name on PyPI
IMPORT_ALIASES = {"sklearn": "scikit-learn", "yaml": "pyyaml", "PIL": "pillow", "dotenv": "python-dotenv"}


def _declared_requirements() -> set[str]:
    out = set()
    for raw in (ROOT / "requirements.txt").read_text(encoding="utf-8").splitlines():
        line = raw.split("#")[0].strip()
        if not line:
            continue
        for sep in ("==", ">=", "<=", "~=", ">", "<"):
            if sep in line:
                line = line.split(sep)[0]
                break
        out.add(line.strip().lower())
    return out


def _third_party_imports() -> dict[str, set[str]]:
    """Top-level third-party modules imported by scripts/, mapped to who imports them."""
    local = {p.stem for p in SCRIPTS}
    found: dict[str, set[str]] = {}
    for path in SCRIPTS:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [a.name.split(".")[0] for a in node.names]
            elif isinstance(node, ast.ImportFrom):
                names = [node.module.split(".")[0]] if node.module and node.level == 0 else []
            else:
                continue
            for name in names:
                if name in sys.stdlib_module_names or name in local:
                    continue
                found.setdefault(name, set()).add(path.name)
    return found


def test_every_third_party_import_is_declared():
    """A fresh clone must be able to run what the docs say to run."""
    declared = _declared_requirements()
    missing = {
        mod: sorted(users)
        for mod, users in _third_party_imports().items()
        if IMPORT_ALIASES.get(mod, mod).lower() not in declared
    }
    assert not missing, f"imported but not in requirements.txt: {missing}"


def test_vol_descriptor_artifact_matches_its_producer():
    """The committed CSV must carry the columns its producer actually emits.
    Catches a stale artifact left behind when a descriptor is added."""
    import vol_descriptors

    committed = pd.read_csv(ROOT / "results" / "vol_descriptors.csv", nrows=5)
    produced = vol_descriptors.build(vol_descriptors.load_returns().tail(1500))
    missing = set(produced.columns) - set(committed.columns)
    assert not missing, (
        f"results/vol_descriptors.csv is STALE — missing {sorted(missing)}. "
        "Rerun `python scripts/vol_descriptors.py` and commit the artifact."
    )


def test_level0_record_is_schema_valid():
    """The emitted signal record must satisfy the closed Level-0 allowlist."""
    import json

    from signal_output_schema import validate

    path = ROOT / "results" / "vol_level0.json"
    assert path.exists(), "results/vol_level0.json missing — run scripts/vol_level0.py"
    validate(json.loads(path.read_text(encoding="utf-8")))


def test_data_manifest_covers_every_processed_panel():
    """Every panel a result can be built from must have a recorded hash + span."""
    manifest_path = ROOT / "data" / "processed" / "MANIFEST.csv"
    assert manifest_path.exists(), "run scripts/data_manifest.py"
    listed = set(pd.read_csv(manifest_path)["file"])
    on_disk = {p.name for p in (ROOT / "data" / "processed").glob("*.csv")} - {"MANIFEST.csv"}
    assert not on_disk - listed, f"undocumented data panels: {sorted(on_disk - listed)}"


# Modules exposing a signal `build()` that are NOT under the causal guard, with
# the reason. Anything else defining `build()` must be covered in test_causal.py.
# Empty is the correct state — an entry here is a debt, not a design.
CAUSAL_GUARD_EXCEPTIONS: dict[str, str] = {}
CAUSALLY_GUARDED = {"vol_descriptors", "stockbond_corr"}


def test_every_signal_build_is_under_the_causal_guard():
    """A new signal must not be able to skip assert_causal by omission.

    Enforcement is structural (D-18): if you add a module with a `build()`, this
    fails until it is either guarded in test_causal.py or explicitly excepted.
    """
    unguarded = []
    for path in SCRIPTS:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        has_build = any(
            isinstance(n, ast.FunctionDef) and n.name == "build" for n in tree.body
        )
        if has_build and path.stem not in CAUSALLY_GUARDED | set(CAUSAL_GUARD_EXCEPTIONS):
            unguarded.append(path.stem)
    assert not unguarded, (
        f"signal build() not covered by assert_causal: {unguarded}. "
        "Add a case to tests/test_causal.py, or document an exception."
    )


@pytest.mark.parametrize("stem", sorted(CAUSALLY_GUARDED))
def test_guard_registry_is_not_stale(stem):
    """The registry must not name modules that no longer exist."""
    assert (ROOT / "scripts" / f"{stem}.py").exists()
