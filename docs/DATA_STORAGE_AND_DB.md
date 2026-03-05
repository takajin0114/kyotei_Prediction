# データ保管と DB 化

**目的**: レース・オッズデータの保管を JSON ファイルから SQLite DB へ移行する方針と設計を整理する。  
**最終更新**: 2026-03

---

## 1. 背景と方針

### 1.1 現状（JSON ファイル）

- **保管場所**: `kyotei_predictor/data/raw/YYYY-MM/`
- **形式**: `race_data_YYYY-MM-DD_会場名_Rn.json` と `odds_data_YYYY-MM-DD_会場名_Rn.json` のペア
- **学習**: データディレクトリを走査し、ペアが揃ったレースだけを読み込んでエピソード化（[LEARNING_INPUT_OUTPUT.md](LEARNING_INPUT_OUTPUT.md) 参照）

### 1.2 DB 化する理由

| 観点 | JSON のまま | DB（SQLite） |
|------|-------------|--------------|
| データ数増加 | 5年分で 25万ファイル超 → 走査・open が重い | 1 DB ファイルで済み、インデックスで必要な範囲だけ取得 |
| 条件指定 | 日付・会場で「該当ファイル一覧」を毎回組み立てる必要 | SQL で日付範囲・会場・欠損有無を指定できる |
| 学習の試行 | 年月や会場を変えるたびにファイル列挙ロジックと整合を取る必要 | 同じクエリで条件だけ変えればよい |
| race + odds の対応 | ファイル名で対応付けして自前で読む | テーブル JOIN で一括取得可能 |

データ量の増加と学習実験の繰り返しを考えると、**SQLite で DB 化する方針**とする。

### 1.3 採用する DB

- **SQLite** を採用する。
  - サーバー不要・1 ファイルで完結（例: `kyotei_predictor/data/kyotei_races.sqlite`）
  - Colab では Drive に DB ファイルを置いてマウントするだけで利用可能
  - 既存の「JSON を raw に保存」する取得フローは維持し、**JSON → DB への投入**を別ツールで行う（取得と保管形式を切り離す）

---

## 2. スキーマ方針（案）

### 2.1 テーブル構成

- **races**: 1 レース 1 行。日付・会場・レース番号をキーに、レース情報・出走表・結果を JSON カラムまたは正規化カラムで保持。
- **odds**: 1 レース 1 行（races と 1:1）。3連単 120 通りを JSON で保持するか、別テーブルで正規化するかは実装時に決定。
- **race_canceled**: 中止レースは「日付・会場・R番号」のみ記録し、学習では除外する。

学習で必要な項目は [LEARNING_INPUT_OUTPUT.md](LEARNING_INPUT_OUTPUT.md) の「race_data_*.json / odds_data_*.json で参照している項目」に合わせる。

### 2.2 キー・インデックス

- **主キー**: `(race_date, stadium, race_number)` で一意。
- **インデックス**: 学習時の絞り込み用に `race_date`（日付範囲）、`stadium`（会場）にインデックスを張る。

### 2.3 保管場所

- **DB ファイル**: `kyotei_predictor/data/kyotei_races.sqlite`（または設定で変更可能とする）。
- `.gitignore` で除外する（raw と同様、中身は手元で用意）。

---

## 3. 移行・運用の流れ（予定）

1. **取得は従来どおり JSON で出力**  
   `batch_fetch_all_venues.py` は引き続き `data/raw/YYYY-MM/` に JSON を保存する。
2. **JSON → DB 投入ツールを用意**  
   指定した `data_dir`（raw）を走査し、`race_data_*` と `odds_data_*` のペアを DB に挿入・更新する。既存 DB がある場合は upsert で追記。
3. **学習の入力オプションを拡張**  
   - 従来: `--data-dir kyotei_predictor/data/raw` で JSON ディレクトリを指定。
   - 追加: `--data-source db --db-path kyotei_predictor/data/kyotei_races.sqlite` のように DB を指定可能にする。  
   学習パイプラインは「データソースが DB の場合は SQL でレース一覧を取得し、1 レースずつ state/報酬用のデータを読みに行く」ようにする。
4. **Colab**  
   Drive に `kyotei_races.sqlite` を置き、ノートブックで `DATA_SOURCE = 'db'` と `DB_PATH` を設定して `scripts/run_colab_learning_cycle.py` を実行する。詳細は [Colab 学習の準備](guides/colab_learning_prep.md) を参照。

### 3.1 コマンド例

- **JSON → DB 投入**（プロジェクトルートで実行）:
  ```bash
  python -m kyotei_predictor.tools.storage.import_raw_to_db --raw-dir kyotei_predictor/data/raw --db-path kyotei_predictor/data/kyotei_races.sqlite
  ```
  `--dry-run` を付けると投入せずに対象ファイル数だけ表示する。

- **最適化を DB で行う**:
  ```bash
  python -m kyotei_predictor.tools.optimization.optimize_graduated_reward --data-source db --db-path kyotei_predictor/data/kyotei_races.sqlite --year-month 2025-01
  ```
  `--db-path` を省略した場合は `kyotei_predictor/data/kyotei_races.sqlite` をデフォルトで使用する。

- **直接訓練を DB で行う**:
  ```bash
  python -m kyotei_predictor.tools.batch.train_with_graduated_reward --data-source db --db-path kyotei_predictor/data/kyotei_races.sqlite --year-month 2025-01 --total-timesteps 500000
  ```
  `--db-path` を省略した場合も上記と同様にデフォルトの DB パスを使用する。

- **DB 投入後に raw の JSON を削除する**（ディスク節約用）:
  ```bash
  # 削除対象の確認のみ
  python -m kyotei_predictor.tools.storage.delete_raw_after_import --raw-dir kyotei_predictor/data/raw --db-path kyotei_predictor/data/kyotei_races.sqlite --dry-run

  # 実際に削除（DB に存在するペアに対応する JSON のみ削除）
  python -m kyotei_predictor.tools.storage.delete_raw_after_import --raw-dir kyotei_predictor/data/raw --db-path kyotei_predictor/data/kyotei_races.sqlite --yes
  ```
  DB に無いペアのファイルは残るため、投入漏れがあっても安全。

---

## 4. 各処理とデータソース（一覧）

DB に入れたレースデータで動かせる処理と、現状ファイル（raw）のみの処理を整理する。

### 4.1 データの流れ

```
[取得] batch_fetch_* → data/raw/YYYY-MM/*.json
         ↓
[投入] import_raw_to_db → kyotei_predictor/data/kyotei_races.sqlite
         ↓
[利用] 学習・検証など（下記のとおり DB / file のどちらかまたは両方対応）
```

### 4.2 処理ごとのデータソース

| 処理 | モジュール・エントリ | データソース | 備考 |
|------|----------------------|--------------|------|
| **学習（最適化）** | `optimize_graduated_reward.py` | **file / db** | `--data-source db --db-path ...` で DB 使用。デフォルトは file。 |
| **学習（直接訓練）** | `train_with_graduated_reward.py` | **file / db** | `--data-source db --db-path ... --year-month YYYY-MM` で DB 使用。 |
| **強化学習環境** | `KyoteiEnvManager`（pipelines/kyotei_env.py） | **file / db** | `data_source="db"`, `db_path=...` で DB から `get_race_json` / `get_odds_json` を使用。 |
| **JSON→DB 投入** | `import_raw_to_db.py` | raw → DB | 入力は raw の JSON。出力は SQLite。 |
| **投入済み raw 削除** | `delete_raw_after_import.py` | DB 参照 + raw | DB に存在するペアに対応する raw の JSON を削除。 |
| **予測（CLI）** | `prediction_tool.py` | **file のみ** | `get_race_data_paths` は raw の JSON ファイルを glob。DB から読むモードは未実装。 |
| **予測検証** | `verify_predictions.py` | **file のみ** | 予測結果と data_dir の JSON を照合。 |
| **データ品質チェック** | `data_quality_checker.py` | **file のみ** | raw ディレクトリを走査。 |
| **取得済み一覧** | `list_fetched_data_summary.py` | **file のみ** | raw のファイル名から集計。 |

### 4.3 DB を使うときの共通ポイント

- **DB ファイル**: デフォルトは `kyotei_predictor/data/kyotei_races.sqlite`。`--db-path` で変更可能。
- **スキーマ**: `data/race_db.py` の `RaceDB`（races / odds / race_canceled）。`get_race_odds_pairs(year_month=...)` で学習用ペア一覧を取得。
- **年月フィルタ**: 学習・最適化では `--year-month 2025-01` のように指定すると、その月のデータだけを使う。

---

## 5. 関連ドキュメント

| ドキュメント | 内容 |
|--------------|------|
| [LEARNING_INPUT_OUTPUT.md](LEARNING_INPUT_OUTPUT.md) | 学習のインプット（現状は JSON のパス・必須項目）。DB 対応後は「データソース: ファイル or DB」を追記予定。 |
| [LEARNING_AND_PREDICTION_STATUS.md](LEARNING_AND_PREDICTION_STATUS.md) | 学習・予測の手順。データまわりに「DB 保管」を追記予定。 |
| [guides/processing_flow.md](guides/processing_flow.md) | 取得→保管→学習の流れ。保管先を「raw のほか DB を利用可能」と記載予定。 |
| [RACE_DATA_FETCH_OVERVIEW.md](RACE_DATA_FETCH_OVERVIEW.md) | 取得処理の概要。取得結果は従来どおり JSON；DB は別ツールで投入。 |

---

## 6. 実装フェーズ（目安）

| フェーズ | 内容 |
|----------|------|
| **ドキュメント整理** | 本ドキュメントと既存ドキュメントの参照を整える（済）。 |
| **スキーマ確定・DB 作成** | 上記スキーマで SQLite の DDL と作成スクリプトを用意する。 |
| **JSON → DB 投入** | raw 配下の JSON を読んで DB に投入する CLI/スクリプトを実装する。 |
| **学習の DB 対応** | 学習エントリ（optimize_graduated_reward 等）で `--data-source db` を指定したときに DB からレースを取得するようにする。 |
| **運用** | 取得は JSON → 必要に応じて JSON を DB に投入 → 学習は DB を参照、という流れで運用する。 |

以上のとおり、DB 化は「データ数の増加と学習のしやすさ」を目的に進める。
