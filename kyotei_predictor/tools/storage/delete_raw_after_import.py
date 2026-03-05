"""
DB 投入済みの raw 配下 JSON を削除する CLI。

DB に存在する (race_date, stadium, race_number) のペアに対応する
race_data_*.json / odds_data_*.json だけを削除する（DB に無いファイルは残す）。

使い方:
  # 削除対象の確認のみ（実際には削除しない）
  python -m kyotei_predictor.tools.storage.delete_raw_after_import --raw-dir kyotei_predictor/data/raw --db-path kyotei_predictor/data/kyotei_races.sqlite --dry-run

  # 実際に削除する（--yes 必須）
  python -m kyotei_predictor.tools.storage.delete_raw_after_import --raw-dir kyotei_predictor/data/raw --db-path kyotei_predictor/data/kyotei_races.sqlite --yes
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from kyotei_predictor.data.race_db import RaceDB, DEFAULT_DB_PATH

RACE_PATTERN = re.compile(r"race_data_(\d{4}-\d{2}-\d{2})_([A-Z0-9]+)_R(\d{1,2})\.json")
ODDS_PATTERN = re.compile(r"odds_data_(\d{4}-\d{2}-\d{2})_([A-Z0-9]+)_R(\d{1,2})\.json")


def find_pairs(raw_dir: str) -> list[tuple[str, str, int, str, str]]:
    """raw_dir 以下を走査し、(race_date, stadium, race_number, race_path, odds_path) のペア一覧を返す。"""
    raw_path = Path(raw_dir)
    if not raw_path.is_dir():
        return []

    race_files: dict[tuple[str, str, int], str] = {}
    odds_files: dict[tuple[str, str, int], str] = {}

    for path in raw_path.rglob("*.json"):
        name = path.name
        if name.startswith("race_data_") and name.endswith(".json"):
            m = RACE_PATTERN.match(name)
            if m:
                date_s, stadium, num_s = m.groups()
                race_files[(date_s, stadium, int(num_s))] = str(path.resolve())
        elif name.startswith("odds_data_") and name.endswith(".json"):
            m = ODDS_PATTERN.match(name)
            if m:
                date_s, stadium, num_s = m.groups()
                odds_files[(date_s, stadium, int(num_s))] = str(path.resolve())

    pairs = []
    for key in race_files:
        if key in odds_files:
            pairs.append((key[0], key[1], key[2], race_files[key], odds_files[key]))
    return sorted(pairs, key=lambda x: (x[0], x[1], x[2]))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="DB 投入済みの raw 配下 JSON（race_data_*.json / odds_data_*.json）を削除する"
    )
    parser.add_argument(
        "--raw-dir",
        type=str,
        default=os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "raw"),
        help="raw ディレクトリ（サブディレクトリも検索）",
    )
    parser.add_argument("--db-path", type=str, default=DEFAULT_DB_PATH, help="SQLite DB ファイルパス")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="削除せずに対象ファイル数とパス例だけ表示",
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="実際にファイルを削除する（指定しない場合は削除しない）",
    )
    args = parser.parse_args()

    raw_dir = os.path.abspath(args.raw_dir)
    if not os.path.isdir(raw_dir):
        print(f"[ERROR] ディレクトリが存在しません: {raw_dir}")
        return 1

    pairs = find_pairs(raw_dir)
    if not pairs:
        print(f"[INFO] raw にペアが 1 件もありません: {raw_dir}")
        return 0

    db = RaceDB(args.db_path)
    db_pairs_set = set(db.get_race_odds_pairs())
    db.close()

    to_delete: list[tuple[str, str]] = []
    for race_date, stadium, race_number, race_path, odds_path in pairs:
        key = (race_date, stadium, race_number)
        if key in db_pairs_set:
            to_delete.append((race_path, odds_path))

    if not to_delete:
        print("[INFO] DB に存在するペアに対応する JSON が raw にありません（削除対象 0 件）")
        return 0

    # 削除するファイルパスを一意に（同じパスが複数回出ないように）
    paths_to_remove = set()
    for rp, op in to_delete:
        paths_to_remove.add(rp)
        paths_to_remove.add(op)

    print(f"[INFO] 削除対象: {len(to_delete)} ペア（ファイル {len(paths_to_remove)} 件）")
    if to_delete:
        r0, o0 = to_delete[0]
        print(f"[INFO] 例: {r0}")
        print(f"       {o0}")

    if args.dry_run:
        print("[INFO] --dry-run のため削除しません")
        return 0

    if not args.yes:
        print("[INFO] 実際に削除するには --yes を付けて再実行してください")
        return 0

    removed = 0
    errors = 0
    for path in paths_to_remove:
        try:
            os.remove(path)
            removed += 1
            if removed % 5000 == 0:
                print(f"[INFO] 削除済み: {removed} 件")
        except OSError as e:
            errors += 1
            print(f"[WARN] 削除失敗 {path}: {e}")

    print(f"[INFO] 完了: 削除 {removed} 件, エラー {errors} 件")
    return 0 if errors == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
