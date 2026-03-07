"""
sweep 結果から ROI と bet 数の比較表を CSV / Markdown で出力。

入力: outputs/ev_threshold_sweep_summary.json, outputs/topn_sweep_summary.json
出力: outputs/strategy_comparison.csv, docs/ROI_STRATEGY_COMPARISON.md
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

COLUMNS = [
    "strategy",
    "top_n",
    "ev_threshold",
    "mean_roi_selected",
    "median_roi_selected",
    "std_roi_selected",
    "overall_roi_selected",
    "total_selected_bets",
    "mean_selected_bets_per_window",
    "mean_log_loss",
    "mean_brier_score",
]


def load_ev_sweep(output_dir: Path) -> list:
    p = output_dir / "ev_threshold_sweep_summary.json"
    if not p.exists():
        return []
    with open(p, encoding="utf-8") as f:
        data = json.load(f)
    rows = []
    for r in data.get("results", []):
        rows.append({
            "strategy": "top_n_ev",
            "top_n": 5,
            "ev_threshold": r.get("ev_threshold"),
            "mean_roi_selected": r.get("mean_roi_selected"),
            "median_roi_selected": r.get("median_roi_selected"),
            "overall_roi_selected": r.get("overall_roi_selected"),
            "std_roi_selected": r.get("std_roi_selected"),
            "total_selected_bets": r.get("total_selected_bets"),
            "mean_selected_bets_per_window": r.get("mean_selected_bets_per_window"),
            "mean_log_loss": r.get("mean_log_loss"),
            "mean_brier_score": r.get("mean_brier_score"),
        })
    return rows


def load_topn_sweep(output_dir: Path) -> list:
    p = output_dir / "topn_sweep_summary.json"
    if not p.exists():
        return []
    with open(p, encoding="utf-8") as f:
        data = json.load(f)
    ev = data.get("ev_threshold")
    rows = []
    for r in data.get("results", []):
        rows.append({
            "strategy": "top_n_ev",
            "top_n": r.get("top_n"),
            "ev_threshold": ev,
            "mean_roi_selected": r.get("mean_roi_selected"),
            "median_roi_selected": r.get("median_roi_selected"),
            "overall_roi_selected": r.get("overall_roi_selected"),
            "std_roi_selected": r.get("std_roi_selected"),
            "total_selected_bets": r.get("total_selected_bets"),
            "mean_selected_bets_per_window": r.get("mean_selected_bets_per_window"),
            "mean_log_loss": r.get("mean_log_loss"),
            "mean_brier_score": r.get("mean_brier_score"),
        })
    return rows


def to_csv_rows(rows: list) -> list:
    out = []
    for r in rows:
        out.append([r.get(c) for c in COLUMNS])
    return out


def to_markdown_table(rows: list) -> str:
    lines = ["| " + " | ".join(COLUMNS) + " |", "| " + " | ".join("---" for _ in COLUMNS) + " |"]
    for r in rows:
        cells = [str(r.get(c, "")) for c in COLUMNS]
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=Path("outputs"))
    parser.add_argument("--docs-dir", type=Path, default=Path("docs"))
    args = parser.parse_args()

    seen = set()
    rows = []
    for r in load_ev_sweep(args.output_dir) + load_topn_sweep(args.output_dir):
        key = (r.get("strategy"), r.get("top_n"), r.get("ev_threshold"))
        if key in seen:
            continue
        seen.add(key)
        rows.append(r)
    if not rows:
        print("No sweep results found. Run ev_threshold_sweep and/or topn_sweep first.", file=sys.stderr)
        return 1

    csv_path = args.output_dir / "strategy_comparison.csv"
    args.output_dir.mkdir(parents=True, exist_ok=True)
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(COLUMNS)
        w.writerows(to_csv_rows(rows))
    print("Saved", csv_path)

    args.docs_dir.mkdir(parents=True, exist_ok=True)
    md_path = args.docs_dir / "ROI_STRATEGY_COMPARISON.md"
    md_content = "# ROI 戦略比較\n\nsweep 結果の比較表。\n\n" + to_markdown_table(rows) + "\n"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_content)
    print("Saved", md_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
