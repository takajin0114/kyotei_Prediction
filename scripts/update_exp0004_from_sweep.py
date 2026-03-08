#!/usr/bin/env python3
"""
feature_sweep の outputs/feature_comparison_summary.json を読み、
experiments/logs/EXP-0004_n12_extended_features_v2_formal_comparison.md の
比較表・解釈・結論を更新する。

用法:
  python scripts/update_exp0004_from_sweep.py [--output-dir outputs]
"""

import argparse
import json
import re
from pathlib import Path

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--output-dir", type=Path, default=Path("outputs"))
    ap.add_argument("--exp-path", type=Path, default=Path("experiments/logs/EXP-0004_n12_extended_features_v2_formal_comparison.md"))
    args = ap.parse_args()
    summary_path = args.output_dir / "feature_comparison_summary.json"
    exp_path = args.exp_path
    if not summary_path.exists():
        print(f"Not found: {summary_path}")
        return 1
    if not exp_path.exists():
        print(f"Not found: {exp_path}")
        return 1
    with open(summary_path) as f:
        data = json.load(f)
    results = data.get("results", [])
    ext = [r for r in results if r.get("feature_set") == "extended_features"]
    v2 = [r for r in results if r.get("feature_set") == "extended_features_v2"]
    if not ext or not v2:
        print("Need extended_features and extended_features_v2 in results")
        return 1
    ext, v2 = ext[0], v2[0]
    n_w = data.get("n_windows") or ext.get("n_windows") or ext.get("number_of_windows")
    if n_w != 12:
        print(f"Warning: n_windows={n_w} (expected 12)")
    # Build table rows
    def row(r):
        return (
            f"| {r.get('feature_set','')} | {r.get('overall_roi_selected','')} | "
            f"{r.get('mean_roi_selected','')} | {r.get('median_roi_selected','')} | "
            f"{r.get('std_roi_selected','')} | {r.get('total_selected_bets','')} | "
            f"{r.get('mean_log_loss','')} | {r.get('mean_brier_score','')} |"
        )
    new_table = (
        "| feature_set | overall_roi_selected | mean_roi_selected | median_roi_selected | "
        "std_roi_selected | total_selected_bets | mean_log_loss | mean_brier_score |\n"
        "|-------------|---------------------|-------------------|---------------------|"
        "------------------|---------------------|---------------|------------------|\n"
        + row(ext) + "\n"
        + row(v2) + "\n"
    )
    # decision: adopt if v2 overall_roi > ext overall_roi (higher is better)
    ext_roi = ext.get("overall_roi_selected")
    v2_roi = v2.get("overall_roi_selected")
    if ext_roi is not None and v2_roi is not None:
        decision = "adopt" if v2_roi > ext_roi else "hold"
    else:
        decision = "TBD"
    content = exp_path.read_text(encoding="utf-8")
    # Replace table block
    old_table = """| feature_set | overall_roi_selected | mean_roi_selected | median_roi_selected | std_roi_selected | total_selected_bets | mean_log_loss | mean_brier_score |
|-------------|---------------------|-------------------|---------------------|------------------|---------------------|---------------|------------------|
| extended_features | TBD | TBD | TBD | TBD | TBD | TBD | TBD |
| extended_features_v2 | TBD | TBD | TBD | TBD | TBD | TBD | TBD |"""
    if old_table in content:
        content = content.replace(old_table, new_table.rstrip())
    # Replace decision line
    content = content.replace("- **decision**: TBD（adopt / hold）", f"- **decision**: {decision}")
    exp_path.write_text(content, encoding="utf-8")
    print(f"Updated {exp_path}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
