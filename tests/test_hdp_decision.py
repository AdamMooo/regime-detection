"""
Tests locking the USE_HDP verdict (script existence, MODEL_CARD section present,
config state matches verdict).

Wave 0: Tests 1 and 2 verify the comparison script exists and is SVI-only.
Tests 3 and 4 fail until Tasks 3 and 4 complete.
"""

from pathlib import Path
import ast


# ===================================================================
# Test 1: Comparison script exists and defines callable main()
# ===================================================================

def test_comparison_script_exists():
    """Comparison script exists and defines a callable main() function."""
    script_path = Path("scripts/analysis/compare_hdp_vs_student.py")
    assert script_path.exists(), (
        f"Compare script not found at {script_path}. "
        "Expected: scripts/analysis/compare_hdp_vs_student.py"
    )

    # Verify main() is defined in the script
    source = script_path.read_text(encoding="utf-8")
    assert "def main(" in source, (
        "compare_hdp_vs_student.py must define a callable main() function. "
        "Found no 'def main(' in the file."
    )

    # Verify __main__ guard
    assert "if __name__ == '__main__':" in source, (
        "compare_hdp_vs_student.py must have an 'if __name__ == \"__main__\":' guard."
    )


# ===================================================================
# Test 2: Script uses inference='svi' and never uses inference='nuts'
# ===================================================================

def test_comparison_script_imports_svi_only():
    """Script contains inference='svi' literal and never references inference='nuts' (D-02 lock)."""
    script_path = Path("scripts/analysis/compare_hdp_vs_student.py")
    assert script_path.exists(), f"Script not found: {script_path}"

    source = script_path.read_text(encoding="utf-8")

    # Must contain the SVI literal (either quote style)
    has_svi = ("inference='svi'" in source) or ('inference="svi"' in source)
    assert has_svi, (
        "compare_hdp_vs_student.py must contain inference='svi' (D-02 lock). "
        "The SVI inference mode must be explicitly specified as a literal, "
        "not passed as a variable."
    )

    # Must NOT contain NUTS inference (D-02 bans NUTS path)
    has_nuts = ("inference='nuts'" in source) or ('inference="nuts"' in source)
    assert not has_nuts, (
        "compare_hdp_vs_student.py must NOT contain inference='nuts'. "
        "D-02 locks inference to SVI only. Remove any NUTS path."
    )


# ===================================================================
# Test 3: MODEL_CARD.md has the Architecture Decision section
# ===================================================================

def test_model_card_has_architecture_decision_section():
    """docs/MODEL_CARD.md contains the 'Model Architecture Decision (Phase 6)' section."""
    model_card_path = Path("docs/MODEL_CARD.md")
    assert model_card_path.exists(), f"MODEL_CARD.md not found at {model_card_path}"

    content = model_card_path.read_text(encoding="utf-8")

    assert "## Model Architecture Decision (Phase 6)" in content, (
        "docs/MODEL_CARD.md must contain a section with the heading "
        "'## Model Architecture Decision (Phase 6)'. "
        "This section is written in Task 3 after the comparison is run."
    )


# ===================================================================
# Test 4: USE_HDP config state matches verdict in tests/_hdp_verdict.txt
# ===================================================================

def test_use_hdp_config_matches_verdict():
    """
    Config state (USE_HDP flag, hdp_hmm.py existence) matches the recorded
    verdict in tests/_hdp_verdict.txt.

    Verdict file must contain exactly one of: 'deleted', 'enabled', 'inconclusive'.

    - 'deleted': USE_HDP must be absent from config.py AND src/core/hdp_hmm.py must not exist
    - 'enabled': USE_HDP = True must be in config.py AND src/core/hdp_hmm.py must exist
    - 'inconclusive': USE_HDP = False must be in config.py AND src/core/hdp_hmm.py must exist
    """
    verdict_path = Path("tests/_hdp_verdict.txt")

    if not verdict_path.exists():
        import pytest
        pytest.fail(
            "tests/_hdp_verdict.txt not yet written. "
            "Run Task 4 (apply verdict) to create this file. "
            "Expected content: 'deleted', 'enabled', or 'inconclusive'."
        )

    verdict = verdict_path.read_text(encoding="utf-8").strip()
    valid_verdicts = {"deleted", "enabled", "inconclusive"}
    assert verdict in valid_verdicts, (
        f"tests/_hdp_verdict.txt contains '{verdict}' but must be one of: "
        f"{valid_verdicts}"
    )

    config_path = Path("src/config.py")
    assert config_path.exists(), "src/config.py not found"
    config_source = config_path.read_text(encoding="utf-8")

    hdp_hmm_path = Path("src/core/hdp_hmm.py")

    if verdict == "deleted":
        # USE_HDP must be absent from config.py
        assert "USE_HDP" not in config_source, (
            "Verdict is 'deleted' but src/config.py still contains 'USE_HDP'. "
            "Remove USE_HDP and all HDP_* symbols from config.py."
        )
        # hdp_hmm.py must not exist
        assert not hdp_hmm_path.exists(), (
            "Verdict is 'deleted' but src/core/hdp_hmm.py still exists. "
            "Delete hdp_hmm.py as part of the deletion branch."
        )

    elif verdict == "enabled":
        # USE_HDP = True must be present
        has_use_hdp_true = "USE_HDP = True" in config_source or "USE_HDP=True" in config_source
        assert has_use_hdp_true, (
            "Verdict is 'enabled' but src/config.py does not have USE_HDP = True. "
            "Set USE_HDP = True in config.py."
        )
        # hdp_hmm.py must exist
        assert hdp_hmm_path.exists(), (
            "Verdict is 'enabled' but src/core/hdp_hmm.py does not exist. "
            "Keep hdp_hmm.py when HDP wins."
        )

    elif verdict == "inconclusive":
        # USE_HDP = False must be present (StudentTHMM remains active)
        has_use_hdp_false = "USE_HDP = False" in config_source or "USE_HDP=False" in config_source
        assert has_use_hdp_false, (
            "Verdict is 'inconclusive' but src/config.py does not have USE_HDP = False. "
            "Keep USE_HDP = False when inconclusive (StudentTHMM remains active)."
        )
        # hdp_hmm.py must exist (not yet deleted; awaiting user decision)
        assert hdp_hmm_path.exists(), (
            "Verdict is 'inconclusive' but src/core/hdp_hmm.py does not exist. "
            "Do not delete hdp_hmm.py when verdict is inconclusive; a user decision is required."
        )
