"""
raw 配下の race_data_*.json / odds_data_*.json を SQLite DB に投入する CLI。

使い方:
  python -m kyotei_predictor.tools.storage.import_raw_to_db --raw-dir kyotei_predictor/data/raw
  python -m kyotei_predictor.tools.storage.import_raw_to_db --raw-dir kyotei_predictor/data/raw --db-path kyotei_predictor/data/kyotei_races.sqlite
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

# プロジェクトルートをパスに追加（raw 指定が相対のとき用）
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from kyotei_predictor.data.race_db import RaceDB, DEFAULT_DB_PATH

# race_data_YYYY-MM-DD_VENUE_Rn.json から (date, venue, n) を抽出
RACE_PATTERN = re.compile(r"race_data_(\d{4}-\d{2}-\d{2})_([A-Z0-9]+)_R(\d{1,2})\.json")


def find_pairs(raw_dir: str) -> list[tuple[str, str, str, str]]:
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
            # odds_data_YYYY-MM-DD_VENUE_Rn.json
            m = re.match(r"odds_data_(\d{4}-\d{2}-\d{2})_([A-Z0-9]+)_R(\d{1,2})\.json", name)
            if m:
                date_s, stadium, num_s = m.groups()
                odds_files[(date_s, stadium, int(num_s))] = str(path.resolve())

    pairs = []
    for key in race_files:
        if key in odds_files:
            pairs.append((key[0], key[1], key[2], race_files[key], odds_files[key]))
    return sorted(pairs, key=lambda x: (x[0], x[1], x[2]))


def main() -> int:
    parser = argparse.ArgumentParser(description="raw 配下の JSON を SQLite DB に投入する")
    parser.add_argument(
        "--raw-dir",
        type=str,
        default=os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "raw"),
        help="race_data_*.json / odds_data_*.json が入っているディレクトリ（サブディレクトリも検索）",
    )
    parser.add_argument("--db-path", type=str, default=DEFAULT_DB_PATH, help="SQLite DB ファイルパス")
    parser.add_argument("--dry-run", action="store_true", help="投入せずにペア数と件数だけ表示")
    args = parser.parse_args()

    raw_dir = os.path.abspath(args.raw_dir)
    if not os.path.isdir(raw_dir):
        print(f"[ERROR] ディレクトリが存在しません: {raw_dir}")
        return 1

    pairs = find_pairs(raw_dir)
    if not pairs:
        print(f"[WARN] ペアが 1 件も見つかりませんでした: {raw_dir}")
        return 0

    print(f"[INFO] ペア数: {len(pairs)} 件（race + odds が揃ったレース）")
    if args.dry_run:
        print("[INFO] --dry-run のため投入しません")
        return 0

    db = RaceDB(args.db_path)
    db.create_tables()

    inserted = 0
    errors = 0
    for race_date, stadium, race_number, race_path, odds_path in pairs:
        try:
            with open(race_path, "r", encoding="utf-8") as f:
                race_data = json.load(f)
            with open(odds_path, "r", encoding="utf-8") as f:
                odds_data = json.load(f)
            db.insert_race(race_date, stadium, race_number, race_data)
            db.insert_odds(race_date, stadium, race_number, odds_data)
            inserted += 1
            if inserted % 5000 == 0:
                print(f"[INFO] 投入済み: {inserted} 件")
        except Exception as e:
            errors += 1
            if errors <= 5:
                print(f"[WARN] 投入失敗 {race_date} {stadium} R{race_number}: {e}")

    pair_count = db.count_pairs()
    db.close()
    print(f"[INFO] 完了: 投入 {inserted} 件, エラー {errors} 件")
    print(f"[INFO] DB: {os.path.abspath(args.db_path)}, ペア数: {pair_count}")
    return 0 if errors == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
