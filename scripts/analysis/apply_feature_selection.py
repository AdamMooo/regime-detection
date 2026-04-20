"""Apply Phase 5 walk-forward selection result to src/config.py::FEATURE_SUBSET.

Reads data/walk_forward_selection_result.json produced by
scripts/analysis/walk_forward_feature_selection.py, expands the selected
sections into their member features via SECTION_MAP, and rewrites the
FEATURE_SUBSET block in src/config.py with the old block preserved as a
comment.

Idempotent: if the file already contains a `# Phase 5 replaced:` marker,
the script refuses to run unless --force is passed.

Run:
    python -m scripts.analysis.apply_feature_selection            # live edit
    python -m scripts.analysis.apply_feature_selection --dry-run  # preview only
    python -m scripts.analysis.apply_feature_selection --force    # re-apply
"""

import argparse
import json
import re
import sys
from datetime import datetime

from src.features.features import SECTION_MAP, CURATED_FEATURES


PHASE5_MARKER = "# Phase 5 replaced:"
FEATURE_SUBSET_RE = re.compile(
    r"(^FEATURE_SUBSET\s*=\s*\[)(.*?)(^\])",
    re.MULTILINE | re.DOTALL,
)


def _expand_sections(selected: list) -> list:
    """Expand section names to member features via SECTION_MAP.

    Preserves order: sections in the order given, features in SECTION_MAP order,
    de-duplicated (first occurrence wins).
    """
    seen: set = set()
    out: list = []
    for section in selected:
        if section not in SECTION_MAP:
            raise ValueError(f"Unknown section in selection result: {section!r}")
        for feat in SECTION_MAP[section]:
            if feat in seen:
                continue
            if feat not in CURATED_FEATURES:
                raise ValueError(
                    f"Section {section!r} references feature {feat!r} not in CURATED_FEATURES"
                )
            seen.add(feat)
            out.append(feat)
    return out


def _build_new_block(new_features: list, selected_sections: list) -> str:
    """Build the replacement text for the FEATURE_SUBSET assignment."""
    date = datetime.now().strftime('%Y-%m-%d')
    sections_str = ', '.join(selected_sections)
    lines = [
        f"# Phase 5 selected on {date}: walk-forward section selection",
        f"# Source: data/walk_forward_selection_result.json",
        f"# Selected sections (>=60% fold stability): {sections_str}",
        "FEATURE_SUBSET = [",
    ]
    for feat in new_features:
        lines.append(f"    '{feat}',")
    lines.append("]")
    return "\n".join(lines)


def apply_feature_selection(result_path: str, config_path: str,
                            dry_run: bool = False, force: bool = False) -> dict:
    """Apply walk-forward selection result to config.py. Returns a summary dict."""
    # 1. Load selection result
    with open(result_path) as fh:
        result = json.load(fh)
    selected_sections = result.get('selected', [])
    if not selected_sections:
        raise ValueError(
            f"{result_path} has empty 'selected' list — nothing to apply")

    # 2. Expand sections to features
    new_features = _expand_sections(selected_sections)

    # 3. Read current config
    with open(config_path, encoding='utf-8') as fh:
        config_src = fh.read()

    # 4. Idempotency check
    if PHASE5_MARKER in config_src and not force:
        print(f"[apply] {config_path} already contains '{PHASE5_MARKER}' — "
              "refusing to re-apply. Pass --force to override.")
        return {
            'status': 'skipped',
            'reason': 'already-applied',
            'new_features': new_features,
            'selected_sections': selected_sections,
        }

    # 5. Locate existing FEATURE_SUBSET block
    match = FEATURE_SUBSET_RE.search(config_src)
    if match is None:
        raise RuntimeError(
            f"Could not locate FEATURE_SUBSET block in {config_path}")

    old_block = match.group(0)

    # 6. Build the commented-out old block + new block
    commented_old = "\n".join(
        (PHASE5_MARKER if i == 0 else "#") + " " + line
        for i, line in enumerate(old_block.splitlines())
    )
    new_block = _build_new_block(new_features, selected_sections)
    replacement = commented_old + "\n" + new_block

    # 7. Perform replacement
    new_src = config_src[:match.start()] + replacement + config_src[match.end():]

    n_old = old_block.count("'")
    summary = {
        'status': 'dry-run' if dry_run else 'applied',
        'new_features': new_features,
        'selected_sections': selected_sections,
        'n_features_old': n_old // 2,  # each feature name has 2 quotes
        'n_features_new': len(new_features),
    }

    if dry_run:
        print("=" * 70)
        print("DRY RUN — would replace:")
        print("=" * 70)
        print(old_block)
        print("-" * 70)
        print("with:")
        print("-" * 70)
        print(replacement)
        print("=" * 70)
        return summary

    with open(config_path, 'w', encoding='utf-8') as fh:
        fh.write(new_src)
    print(f"[apply] Updated {config_path}")
    print(f"[apply] New FEATURE_SUBSET has {len(new_features)} features: {new_features}")
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--result', default='data/walk_forward_selection_result.json')
    parser.add_argument('--config', default='src/config.py')
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--force', action='store_true')
    args = parser.parse_args()

    summary = apply_feature_selection(
        result_path=args.result,
        config_path=args.config,
        dry_run=args.dry_run,
        force=args.force,
    )
    print(f"\nResult: {summary['status']}")


if __name__ == '__main__':
    main()
