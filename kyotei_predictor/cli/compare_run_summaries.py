"""
2 回の run の summary JSON を比較し、再現性切り分けに使う差分を表示する。

使い方:
  python -m kyotei_predictor.cli.compare_run_summaries summary_a.json summary_b.json
  python -m kyotei_predictor.cli.compare_run_summaries summary_a.json summary_b.json --diff-only
  python -m kyotei_predictor.cli.compare_run_summaries summary_a.json summary_b.json --show-json-diff
"""

import argparse
import difflib
import json
import sys
from pathlib import Path

# 比較対象キー（conditions）
COMPARE_KEYS = [
    "run_id",
    "train_start",
    "train_end",
    "predict_date",
    "model",
    "calibration",
    "strategy",
    "top_n",
    "ev_threshold",
    "evaluation_mode",
    "seed",
    "max_samples",
    "sample_mode",
    "data_source",
    "data_dir",
    "train_sample_count",
    "train_file_count",
    "train_first_date",
    "train_last_date",
    "train_file_manifest_hash",
    "verify_details_hash",
    "predict_race_count",
    "odds_missing_count",
    "selected_bets_count",
    "total_bet_selected",
    "total_payout_selected",
    "roi_selected",
    "git_commit_hash",
    "summary_created_at",
]

# summary 側の比較対象キー（conditions に無いものを summary から取得）
SUMMARY_COMPARE_KEYS = [
    "skip_reasons",
    "bets_per_date",
    "selected_bets_total_count",
    "races_with_selected_bets",
    "odds_missing_count",
]


def load_full(path: Path) -> dict:
    """summary JSON を読み、{ conditions, summary } を含む辞書を返す。"""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_conditions(data: dict) -> dict:
    return data.get("conditions", data)


def get_summary(data: dict) -> dict:
    return data.get("summary", {})


def _json_lines(obj) -> list:
    return json.dumps(obj, ensure_ascii=False, indent=2).splitlines(keepends=True)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="2 つの strategy_b summary JSON を比較し、再現性切り分け用の差分を表示する"
    )
    parser.add_argument("summary_a", type=Path, help="1 つ目の summary JSON パス")
    parser.add_argument("summary_b", type=Path, help="2 つ目の summary JSON パス")
    parser.add_argument(
        "--diff-only",
        action="store_true",
        help="差分がある項目だけ表示する",
    )
    parser.add_argument(
        "--show-json-diff",
        action="store_true",
        help="差分がある項目について JSON の unified diff を表示する",
    )
    args = parser.parse_args()

    if not args.summary_a.exists():
        print(f"エラー: ファイルがありません: {args.summary_a}")
        return 1
    if not args.summary_b.exists():
        print(f"エラー: ファイルがありません: {args.summary_b}")
        return 1

    data_a = load_full(args.summary_a)
    data_b = load_full(args.summary_b)
    cond_a = get_conditions(data_a)
    cond_b = get_conditions(data_b)
    sum_a = get_summary(data_a)
    sum_b = get_summary(data_b)

    print(f"--- A: {args.summary_a}")
    print(f"--- B: {args.summary_b}")
    print()

    def _source_a(key: str):
        return cond_a.get(key) if key in COMPARE_KEYS else sum_a.get(key)

    def _source_b(key: str):
        return cond_b.get(key) if key in COMPARE_KEYS else sum_b.get(key)

    all_keys = list(COMPARE_KEYS) + [k for k in SUMMARY_COMPARE_KEYS if k not in COMPARE_KEYS]
    for key in all_keys:
        va = _source_a(key)
        vb = _source_b(key)
        if key not in cond_a and key not in cond_b and key not in sum_a and key not in sum_b:
            continue
        if args.diff_only and va == vb:
            continue
        a_str = json.dumps(va, ensure_ascii=False) if va is not None else "(なし)"
        b_str = json.dumps(vb, ensure_ascii=False) if vb is not None else "(なし)"
        diff_mark = " ***" if va != vb else ""
        label = "[summary]" if key in SUMMARY_COMPARE_KEYS and key not in COMPARE_KEYS else ""
        print(f"  {key}{label}:")
        print(f"    A: {a_str}{diff_mark}")
        print(f"    B: {b_str}{diff_mark}")
        if args.show_json_diff and va != vb and (va is not None or vb is not None):
            a_lines = _json_lines(va) if va is not None else ["(なし)\n"]
            b_lines = _json_lines(vb) if vb is not None else ["(なし)\n"]
            for line in difflib.unified_diff(
                a_lines, b_lines, fromfile="A", tofile="B", lineterm=""
            ):
                print("    " + line.rstrip())
        print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
