#!/usr/bin/env python3
"""
5年分データを数回に分けて取得するための仕組み。

- 計画（scripts/fetch_5year_plan.json）に沿って「取得済み月」と「未取得月」を判定
- 既存ファイルは上書きしないので、同じ期間を再実行しても欠けている分だけ取得される
- 欠損レースは retry_missing_races で補完可能

使い方:
  # 進捗確認（どの月が取得済みか・次に取る月）
  python -m kyotei_predictor.tools.batch.fetch_5year_chunked --check

  # 未取得の「次の1ヶ月分」を取得
  python -m kyotei_predictor.tools.batch.fetch_5year_chunked --next 1

  # 未取得の次の3ヶ月分を取得
  python -m kyotei_predictor.tools.batch.fetch_5year_chunked --next 3

  # 指定期間のみ取得（既存はスキップ）
  python -m kyotei_predictor.tools.batch.fetch_5year_chunked --range 2023-01-01 2023-12-31

  # 全計画月の一覧と取得状況
  python -m kyotei_predictor.tools.batch.fetch_5year_chunked --list
"""

import os
import re
import sys
import json
import argparse
from datetime import date, timedelta
from pathlib import Path

# プロジェクトルート（このファイルから逆算）
BATCH_DIR = Path(__file__).resolve().parent
DEFAULT_RAW_DIR = BATCH_DIR.parent.parent / "data" / "raw"
DEFAULT_PLAN_PATH = BATCH_DIR.parent.parent.parent / "scripts" / "fetch_5year_plan.json"

RACE_PATTERN = re.compile(r"race_data_(\d{4}-\d{2}-\d{2})_[A-Z0-9]+_R\d+\.json")


def load_plan(plan_path: Path) -> dict:
    """計画JSONを読み込む"""
    with open(plan_path, encoding="utf-8") as f:
        return json.load(f)


def collect_months_with_data(raw_dir: Path) -> set:
    """
    raw_dir をスキャンし、1件以上 race_data が存在する月（YYYY-MM）の集合を返す。
    月フォルダ直下の race_data_*.json をカウントする。
    """
    found = set()
    if not raw_dir.is_dir():
        return found
    for month_dir in raw_dir.iterdir():
        if not month_dir.is_dir():
            continue
        name = month_dir.name
        if re.match(r"^\d{4}-\d{2}$", name):
            for _ in month_dir.glob("race_data_*.json"):
                found.add(name)
                break
    return found


def get_month_range(ym: str) -> tuple[date, date]:
    """YYYY-MM の月初・月末を返す"""
    y, m = int(ym[:4]), int(ym[5:7])
    first = date(y, m, 1)
    if m == 12:
        last = date(y, 12, 31)
    else:
        last = date(y, m + 1, 1) - timedelta(days=1)
    return first, last


def run_batch_fetch(start_date: date, end_date: date, raw_dir: Path, rate_limit: float = 1.0, race_workers: int = 6, quiet: bool = True) -> int:
    """batch_fetch_all_venues をサブプロセスで実行（--overwrite なし）"""
    import subprocess
    import sys
    cmd = [
        sys.executable,
        "-m", "kyotei_predictor.tools.batch.batch_fetch_all_venues",
        "--start-date", start_date.isoformat(),
        "--end-date", end_date.isoformat(),
        "--stadiums", "ALL",
        "--output-data-dir", str(raw_dir),
        "--rate-limit", str(rate_limit),
        "--race-workers", str(race_workers),
    ]
    if quiet:
        cmd.append("--quiet")
    return subprocess.run(cmd).returncode


def main() -> None:
    parser = argparse.ArgumentParser(
        description="5年分データを数回に分けて取得（計画に基づく進捗確認・チャンク取得）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--raw-dir",
        type=str,
        default=os.environ.get("KYOTEI_RAW_DATA_DIR", str(DEFAULT_RAW_DIR)),
        help="rawデータのディレクトリ",
    )
    parser.add_argument(
        "--plan",
        type=str,
        default=str(DEFAULT_PLAN_PATH),
        help="取得計画JSONのパス（scripts/fetch_5year_plan.json）",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="進捗確認のみ。取得済み月・未取得月・次に取る範囲を表示",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="全計画月の一覧と取得状況を表示",
    )
    parser.add_argument(
        "--next",
        type=int,
        metavar="N",
        help="未取得の「次のNヶ月分」を取得する（既存はスキップ）",
    )
    parser.add_argument(
        "--range",
        nargs=2,
        metavar=("START", "END"),
        help="指定期間を取得（例: --range 2023-01-01 2023-12-31）。既存はスキップ",
    )
    parser.add_argument(
        "--rate-limit",
        type=float,
        default=1.0,
        help="batch_fetch のレート制限秒数",
    )
    parser.add_argument(
        "--race-workers",
        type=int,
        default=6,
        help="batch_fetch のレース並列数",
    )
    parser.add_argument(
        "--no-quiet",
        action="store_true",
        help="batch_fetch の進捗を通常表示",
    )
    args = parser.parse_args()

    raw_dir = Path(args.raw_dir)
    plan_path = Path(args.plan)
    if not plan_path.is_file():
        print(f"計画ファイルが見つかりません: {plan_path}")
        return

    plan = load_plan(plan_path)
    months_planned = plan.get("months", [])
    if not months_planned:
        print("計画に months がありません")
        return

    done_months = collect_months_with_data(raw_dir)
    missing_months = [m for m in months_planned if m not in done_months]

    # --list: 全月の状況
    if args.list:
        print(f"対象ディレクトリ: {raw_dir}")
        print(f"計画: {plan.get('start_date')} ～ {plan.get('end_date')} ({len(months_planned)}ヶ月)")
        print()
        for ym in months_planned:
            status = "取得済" if ym in done_months else "未取得"
            print(f"  {ym}  {status}")
        print()
        print(f"取得済: {len(done_months)}ヶ月  未取得: {len(missing_months)}ヶ月")
        return

    # --check: 進捗と次に取る範囲の提案
    if args.check:
        print(f"対象ディレクトリ: {raw_dir}")
        print(f"計画: {len(months_planned)}ヶ月（{months_planned[0]} ～ {months_planned[-1]}）")
        print(f"取得済: {len(done_months)}ヶ月  未取得: {len(missing_months)}ヶ月")
        if done_months:
            done_sorted = sorted(done_months)
            print(f"取得済み月: {done_sorted[0]} ～ {done_sorted[-1]}")
        if missing_months:
            print(f"未取得月（先頭5件）: {missing_months[:5]}")
            first_missing = missing_months[0]
            start, end = get_month_range(first_missing)
            print(f"\n次に取得する場合の例:")
            print(f"  --next 1   # 未取得の1ヶ月分（{first_missing}）")
            if len(missing_months) >= 3:
                start3 = get_month_range(missing_months[0])[0]
                end3 = get_month_range(missing_months[2])[1]
                print(f"  --next 3   # 未取得の3ヶ月分（{start3.isoformat()} ～ {end3.isoformat()}）")
            print(f"  --range {start.isoformat()} {end.isoformat()}   # 指定月のみ")
        return

    # --next N: 未取得の次のNヶ月を取得
    if args.next is not None:
        n = max(1, args.next)
        if not missing_months:
            print("未取得の月はありません。")
            return
        to_fetch = missing_months[:n]
        start_date = get_month_range(to_fetch[0])[0]
        end_date = get_month_range(to_fetch[-1])[1]
        print(f"取得対象: {to_fetch[0]} ～ {to_fetch[-1]}（{len(to_fetch)}ヶ月）")
        print(f"期間: {start_date.isoformat()} ～ {end_date.isoformat()}")
        print("既存ファイルはスキップし、欠けている分のみ取得します。")
        rc = run_batch_fetch(
            start_date, end_date, raw_dir,
            rate_limit=args.rate_limit,
            race_workers=args.race_workers,
            quiet=not args.no_quiet,
        )
        if rc == 0:
            print("\n取得完了。欠損がある場合は retry_missing_races で補完できます。")
        sys.exit(rc)

    # --range START END: 指定期間を取得
    if args.range:
        start_s, end_s = args.range[0], args.range[1]
        try:
            start_date = date.fromisoformat(start_s)
            end_date = date.fromisoformat(end_s)
        except ValueError as e:
            print(f"日付形式エラー: {e}  (YYYY-MM-DD)")
            return
        if start_date > end_date:
            print("開始日は終了日以前にしてください。")
            return
        print(f"取得期間: {start_date.isoformat()} ～ {end_date.isoformat()}")
        print("既存ファイルはスキップし、欠けている分のみ取得します。")
        rc = run_batch_fetch(
            start_date, end_date, raw_dir,
            rate_limit=args.rate_limit,
            race_workers=args.race_workers,
            quiet=not args.no_quiet,
        )
        if rc == 0:
            print("\n取得完了。欠損がある場合は retry_missing_races で補完できます。")
        sys.exit(rc)

    # いずれのオプションもない場合は --check と同様
    parser.print_help()
    print("\n例: 進捗確認 → python -m kyotei_predictor.tools.batch.fetch_5year_chunked --check")


if __name__ == "__main__":
    main()
