"""
calibration / feature / model の比較 JSON を読み、CSV と Markdown を出力する。

入力: outputs/calibration_comparison_summary.json, feature_comparison_summary.json, model_comparison_summary.json
出力: outputs/calibration_comparison.csv, feature_comparison.csv, model_comparison.csv
      docs/CALIBRATION_COMPARISON.md, docs/FEATURE_COMPARISON.md, docs/MODEL_COMPARISON.md
"""

import argparse
import csv
import json
import sys
from pathlib import Path

_THIS_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _THIS_DIR.parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

METRIC_COLUMNS = [
    "mean_roi_selected",
    "median_roi_selected",
    "std_roi_selected",
    "overall_roi_selected",
    "total_selected_bets",
    "mean_selected_bets_per_window",
    "mean_log_loss",
    "mean_brier_score",
]


def _load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _key_col(name: str) -> str:
    if "calibration" in name.lower():
        return "calibration"
    if "feature" in name.lower():
        return "feature_set"
    if "model" in name.lower():
        return "model_type"
    return "variant"


def _rows_from_results(results: list, key_col: str, label_col: str = None) -> list:
    out = []
    for r in results:
        row = {key_col: r.get(key_col, r.get("model_label", ""))}
        if label_col and r.get(label_col):
            row["label"] = r.get(label_col)
        for c in METRIC_COLUMNS:
            row[c] = r.get(c)
        out.append(row)
    return out


def _to_csv(path: Path, rows: list, key_col: str) -> None:
    if not rows:
        return
    cols = [key_col] + METRIC_COLUMNS
    if any(r.get("label") for r in rows):
        cols = [key_col, "label"] + METRIC_COLUMNS
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k) for k in cols})
    print("Saved", path)


def _to_md_table(rows: list, key_col: str, title: str) -> str:
    if not rows:
        return f"# {title}\n\n(no data)\n"
    cols = [key_col] + METRIC_COLUMNS
    if any(r.get("label") for r in rows):
        cols = [key_col, "label"] + METRIC_COLUMNS
    lines = [f"# {title}\n", "| " + " | ".join(cols) + " |", "| " + " | ".join("---" for _ in cols) + " |"]
    for r in rows:
        cells = [str(r.get(c, "")) for c in cols]
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=Path("outputs"))
    parser.add_argument("--docs-dir", type=Path, default=Path("docs"))
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    args.docs_dir.mkdir(parents=True, exist_ok=True)

    # Calibration
    cal = _load_json(args.output_dir / "calibration_comparison_summary.json")
    if cal.get("results"):
        key_col = "calibration"
        rows = _rows_from_results(cal["results"], key_col)
        _to_csv(args.output_dir / "calibration_comparison.csv", rows, key_col)
        with open(args.docs_dir / "CALIBRATION_COMPARISON.md", "w", encoding="utf-8") as f:
            f.write(_to_md_table(rows, key_col, "Calibration 比較") + f"\n(n_windows={cal.get('n_windows', '')})\n")
        print("Saved docs/CALIBRATION_COMPARISON.md")

    # Feature
    feat = _load_json(args.output_dir / "feature_comparison_summary.json")
    if feat.get("results"):
        key_col = "feature_set"
        rows = _rows_from_results(feat["results"], key_col)
        _to_csv(args.output_dir / "feature_comparison.csv", rows, key_col)
        with open(args.docs_dir / "FEATURE_COMPARISON.md", "w", encoding="utf-8") as f:
            f.write(_to_md_table(rows, key_col, "特徴量セット比較") + f"\n(n_windows={feat.get('n_windows', '')})\n")
        print("Saved docs/FEATURE_COMPARISON.md")

    # Model
    mod = _load_json(args.output_dir / "model_comparison_summary.json")
    if mod.get("results"):
        key_col = "model_type"
        rows = _rows_from_results(mod["results"], key_col, "model_label")
        _to_csv(args.output_dir / "model_comparison.csv", rows, key_col)
        with open(args.docs_dir / "MODEL_COMPARISON.md", "w", encoding="utf-8") as f:
            f.write(_to_md_table(rows, key_col, "モデル比較") + f"\n(n_windows={mod.get('n_windows', '')})\n")
        print("Saved docs/MODEL_COMPARISON.md")

    if not cal.get("results") and not feat.get("results") and not mod.get("results"):
        print("No comparison JSONs found. Run calibration_sweep, feature_sweep, model_sweep first.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
