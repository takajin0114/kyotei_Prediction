# データ読込の JSON → DB 移行方針

**目的**: 学習・検証・比較のレースデータ読込を「JSON 直読」から「repository 経由・DB 対応」へ段階的に移行する方針と使い分けをまとめる。  
**関連**: [DATA_STORAGE_AND_DB.md](DATA_STORAGE_AND_DB.md)（保管と DB スキーマ）、[BASELINE_B_APPROACH.md](BASELINE_B_APPROACH.md)（B案フロー）

---

## 1. 現状の JSON + DB 二重管理の位置づけ

- **サイト取得** → **JSON 保存（raw）** → **DB import** の流れは維持する。
- **JSON** は raw 保管用として残し、取得ツールは従来どおり `race_data_*.json` / `odds_data_*.json` を出力する。
- **DB** は `import_raw_to_db` で JSON から投入し、学習・検証・比較の**主な読込元**として使うことを推奨する。
- 移行は一気に行わず、**読込層の抽象化（repository）** を挟み、`data_source=json` / `data_source=db` で切替可能にしている。

---

## 2. JSON を残す理由（raw 保管）

- 取得パイプライン（batch_fetch 等）の出力形式を変えないため。
- 障害時や手動確認で「生データ」をそのまま参照できるため。
- DB 投入前のバックアップ・再投入の元データとして保持するため。

---

## 3. DB を主読込源にする理由

- ファイル数が増えると `rglob("race_data_*.json")` の走査が重くなる。
- 日付範囲・会場指定が SQL で簡潔に書ける。
- 30日・60日・rolling validation など期間指定の学習・検証を多く回す運用に適する。
- 既存の `RaceDB`（SQLite）と import フローをそのまま再利用できる。

---

## 4. repository 抽象化の方針

- **domain**: `RaceDataRepositoryProtocol` を定義し、以下を約束する。
  - `load_race(race_date, venue, race_number)` → 1 レース分の race_data 辞書
  - `load_races_between(start_date, end_date, max_samples=None)` → 期間内のレースリスト（学習用）
  - `load_races_by_date(race_date, venues=None)` → 指定日の (race_data, venue, race_number) リスト（予測用）
- **infrastructure**: 上記を満たす **JsonRaceDataRepository**（data_dir の JSON 走査）と **DbRaceDataRepository**（RaceDB ラッパー）を実装。
- **usecase**: SQL を書かず、`get_race_data_repository(data_source, data_dir, db_path)` で repository を取得し、そのメソッドだけでデータを取得する。
- **設定**: `config.settings` の `DATA_SOURCE`（環境変数 `KYOTEI_DATA_SOURCE` で上書き）、`DB_PATH`（`KYOTEI_DB_PATH`）で切り替え。

---

## 5. 現時点で DB 対応済みの usecase

| 対象 | data_source=json | data_source=db | 備考 |
|------|------------------|----------------|------|
| **baseline_train_usecase** | ✅（従来通り data_dir 直読も可） | ✅ | `--data-source db` で repository 経由 |
| **baseline_predict_usecase** | ✅ | ✅ | オッズは従来どおり data_dir の JSON |
| **verify_usecase** | ✅ | ✅ | 検証時の race_data を DB から取得可能 |
| **compare_ab_usecase** | ✅ | ✅ | run_verify に data_source を渡す |
| **rolling_validation_windows** | ✅ | ✅ | 環境変数 `KYOTEI_DATA_SOURCE` / `KYOTEI_DB_PATH` で指定 |

---

## 6. 未対応箇所

- **オッズの DB 読込**: 予測・検証時のオッズは現状も `data_dir` の `odds_data_*.json` から読んでいる。オッズも repository 化する場合は別途 interface 拡張が必要。
- **predict_usecase / run_cycle_usecase / prediction_tool**: 現状は JSON または既存の RaceDB 直叩き。必要に応じて repository 経由に寄せる。
- **tools（data_quality_checker, verify_race_data_simple 等）**: 現状は JSON 走査のまま。必要に応じて repository を注入する形で対応可能。

---

## 7. 設定方法

- **環境変数**
  - `KYOTEI_DATA_SOURCE`: `json` または `db`（未設定時は `json`＝従来互換）
  - `KYOTEI_DB_PATH`: DB 利用時の SQLite ファイルパス（相対の場合はプロジェクトルート基準）。未設定時は `config.settings.DB_PATH`（例: `kyotei_predictor/data/kyotei_races.sqlite`）
- **CLI**
  - `baseline_train`: `--data-source json|db`, `--db-path PATH`
  - `baseline_predict`: `--data-source json|db`, `--db-path PATH`
  - `compare_ab`: `--data-source json|db`, `--db-path PATH`
- **rolling_validation_windows**: 引数では渡さず、環境変数 `KYOTEI_DATA_SOURCE` / `KYOTEI_DB_PATH` を参照。

---

## 8. 今後の移行順序（提案）

1. **オッズの repository 化**（必要なら）: OddsDataRepository を追加し、予測・検証で DB からオッズを読む。
2. **predict_usecase / run_cycle_usecase**: レース一覧・1レース取得を repository 経由にし、data_source で切替。
3. **tools 系**: 品質チェック・簡易検証などで「期間指定でレース一覧」が必要な箇所を repository 経由にし、DB で一括取得できるようにする。

---

## 9. 使い分けの目安

| 運用 | 推奨 data_source | 理由 |
|------|-------------------|------|
| 少量データで動作確認 | json | 既存の data_dir だけで完結 |
| 30日・60日・rolling などの長期検証 | db | 日付範囲指定が楽で高速 |
| Colab で学習 | db | Drive に DB 1 ファイルを置く運用が簡単 |
| 新規取得直後でまだ import していない | json | raw の JSON をそのまま使う |
