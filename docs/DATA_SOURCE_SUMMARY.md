# データソース現状整理（再現性診断・DB 統一前）

## 要約

| 項目 | 現状 |
|------|------|
| **train data source** | 両対応。`data_source=db` なら DB（repository）。未指定なら JSON 直読（collect_training_data）。 |
| **predict data source** | 両対応。`data_source` / `race_repository` で DB または JSON。未指定なら JSON 直読。 |
| **verify data source** | 両対応。`data_source=db` なら race_data は DB。未指定なら JSON 直読。 |
| **odds data source** | **現状 JSON のみ**。predict は data_dir の odds_data_*.json。verify も data_dir の odds_data_*.json。 |
| **result data source** | verify では「結果」は race_data の着順。よって race_data が DB なら result は実質 DB、JSON なら JSON。 |

## 各レイヤー詳細

- **run_strategy_b**: `data_source` / `db_path` を train / predict / verify にそのまま渡している。未指定時は `data_source or "json"` で conditions に記録。
- **baseline_train_usecase**: `data_source in ("json","db")` なら get_race_data_repository で DB/JSON を取得。それ以外は collect_training_data（JSON 直読）。DB 時は train_manifest の file_paths は取れない（repository はファイルパスを返さない）。
- **baseline_predict_usecase**: レースは repository または JSON 直読。オッズは常に `_attach_odds_to_combinations` で data_dir の odds_data_*.json（load_json）。
- **verify_usecase**: race_data は repository または data_dir の race_data_*.json。オッズは常に `_load_odds_for_race` → data_dir の odds_data_*.json。
- **repository / infrastructure**: DbRaceDataRepository は RaceDB で race のみ取得（load_race, load_races_between, load_races_by_date）。RaceDB には get_odds_json があるがリポジトリ経由では未使用。JsonRaceDataRepository は data_dir の race_data_*.json のみ。

## JSON 混入が残っている箇所（DB 統一対応後）

- **オッズ**: `data_source=db` かつリポジトリに `get_odds` がある場合、predict/verify は DB の odds テーブルを使用。それ以外は従来どおり data_dir の odds_data_*.json。
- **実験で DB 固定にするには**: `--db-path` を指定すると `data_source` 未指定時は自動で `data_source=db` になる。train / predict / verify およびオッズはすべて DB 経由になる（リポジトリの get_odds 実装済み）。
