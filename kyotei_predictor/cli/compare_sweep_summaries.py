"""
sweep 結果 JSON を読み、表形式で表示する簡易 CLI。

使い方:
  python -m kyotei_predictor.cli.compare_sweep_summaries --output-dir outputs
  python -m kyotei_predictor.cli.compare_sweep_summaries outputs/ev_threshold_sweep_summary.json
  python -m kyotei_predictor.cli.compare_sweep_summaries outputs/topn_sweep_summary.json
"""

import argparse
import json
import sys
from pathlib import Path


def _table(rows: list, headers: list, col_widths: list = None) -> str:
    if not rows:
        return "(no rows)"
    if col_widths is None:
        col_widths = [max(len(str(r.get(h, ""))) for r in rows) for h in headers]
        for i, h in enumerate(headers):
            col_widths[i] = max(col_widths[i], len(h))
    fmt = "  ".join(f"{{:{w}}}" for w in col_widths)
    lines = [fmt.format(*headers)]
    lines.append("  ".join("-" * w for w in col_widths))
    for r in rows:
        cells = [str(r.get(h, "")) for h in headers]
        lines.append(fmt.format(*cells))
    return "\n".join(lines)


def show_ev_sweep(path: Path) -> None:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    results = data.get("results", [])
    if not results:
        print("(empty results)")
        return
    headers = ["ev_threshold", "mean_roi_selected", "overall_roi_selected", "std_roi_selected", "total_selected_bets", "mean_selected_bets_per_window"]
    print("EV threshold sweep:", path)
    print(_table(results, headers))
    print()


def show_topn_sweep(path: Path) -> None:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    results = data.get("results", [])
    if not results:
        print("(empty results)")
        return
    headers = ["top_n", "mean_roi_selected", "overall_roi_selected", "std_roi_selected", "total_selected_bets", "mean_selected_bets_per_window"]
    print("top_n sweep:", path)
    print(_table(results, headers))
    print()


def main() -> int:
    parser = argparse.ArgumentParser(description="View sweep summaries as tables")
    parser.add_argument("paths", nargs="*", type=Path, help="JSON paths or leave empty to use --output-dir")
    parser.add_argument("--output-dir", type=Path, default=Path("outputs"))
    args = parser.parse_args()

    if args.paths:
        for p in args.paths:
            if not p.exists():
                print("Not found:", p, file=sys.stderr)
                continue
            name = p.name.lower()
            if "ev_threshold" in name:
                show_ev_sweep(p)
            elif "topn" in name:
                show_topn_sweep(p)
            else:
                print("Unknown file:", p, file=sys.stderr)
        return 0

    out = args.output_dir
    if (out / "ev_threshold_sweep_summary.json").exists():
        show_ev_sweep(out / "ev_threshold_sweep_summary.json")
    if (out / "topn_sweep_summary.json").exists():
        show_topn_sweep(out / "topn_sweep_summary.json")
    if not (out / "ev_threshold_sweep_summary.json").exists() and not (out / "topn_sweep_summary.json").exists():
        print("No sweep JSONs in", out, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
