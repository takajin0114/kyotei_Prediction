# 再現性診断 実験実行レポート

実施日: 2026-03-07  
データソース: **DB のみ**（JSON 直読みは使用していない）

---

## 1. DB 存在確認結果

| 項目 | 結果 |
|------|------|
| **DB path** | `kyotei_predictor/data/kyotei_races.sqlite` |
| **tables** | `races`, `odds`, `race_canceled` |
| **races_count** | 60,027 |
| **odds_count** | 60,027 |
| **date_range** | 2025-01-01 ～ 2026-02-23 |

- DB ファイルは存在し、races / odds の両方にレコードあり。
- 想定パス `kyotei_predictor/data/kyotei_races.sqlite` をそのまま使用。

---

## 2. DB を使う実行経路確認（Task 1）

`--db-path` を指定すると `run_strategy_b_usecase` 内で `data_source = "db"` が設定され、train / predict / verify にそのまま渡される。

| 項目 | 経路 |
|------|------|
| **train data source** | `data_source=db` → `get_race_data_repository("db")` → `load_races_between`。DB のみ。 |
| **predict data source** | `data_source=db` → 同様に repository → `load_races_by_date`。DB のみ。 |
| **verify data source** | `data_source=db` → repository → `load_race`。DB のみ。 |
| **odds data source** | repository に `get_odds` あり → DB の `get_odds_json`。DB のみ。 |
| **result data source** | verify の結果は race_data の着順。race が DB なので実質 DB。 |

- JSON 直読みは、`--db-path` を指定しない場合のみ使われる。今回の実験では `--db-path` を指定しているため、全経路で DB のみ使用。

---

## 3. DB 構造（参照）

- **races**: `(race_date, stadium, race_number)` 主キー、`race_json` (TEXT) で race_data を保存。
- **odds**: 同上、`odds_json` (TEXT) で odds_data を保存。
- **race_canceled**: 中止レースの (race_date, stadium, race_number)。

---

## 4. 実行コマンド一覧

いずれも `--db-path kyotei_predictor/data/kyotei_races.sqlite` を指定。学習期間 2025-01-01～2025-05-31、予測日 2025-06-01。

```bash
export DB_PATH="kyotei_predictor/data/kyotei_races.sqlite"
export DATA_DIR="kyotei_predictor/data/raw"
export PREDICT_DATE="2025-06-01"

# run A
python -m kyotei_predictor.cli.run_strategy_b \
  --train-start 2025-01-01 --train-end 2025-05-31 --predict-date "$PREDICT_DATE" \
  --data-dir "$DATA_DIR" --db-path "$DB_PATH" \
  --seed 42 --max-samples 50000 --sample-mode head --output outputs/runA

# run B（同一条件）
python -m kyotei_predictor.cli.run_strategy_b \
  --train-start 2025-01-01 --train-end 2025-05-31 --predict-date "$PREDICT_DATE" \
  --data-dir "$DATA_DIR" --db-path "$DB_PATH" \
  --seed 42 --max-samples 50000 --sample-mode head --output outputs/runB

# sample_mode=head
python -m kyotei_predictor.cli.run_strategy_b \
  --train-start 2025-01-01 --train-end 2025-05-31 --predict-date "$PREDICT_DATE" \
  --data-dir "$DATA_DIR" --db-path "$DB_PATH" \
  --seed 42 --max-samples 50000 --sample-mode head --output outputs/head

# sample_mode=random
python -m kyotei_predictor.cli.run_strategy_b \
  --train-start 2025-01-01 --train-end 2025-05-31 --predict-date "$PREDICT_DATE" \
  --data-dir "$DATA_DIR" --db-path "$DB_PATH" \
  --seed 42 --max-samples 50000 --sample-mode random --output outputs/random

# sample_mode=all
python -m kyotei_predictor.cli.run_strategy_b \
  --train-start 2025-01-01 --train-end 2025-05-31 --predict-date "$PREDICT_DATE" \
  --data-dir "$DATA_DIR" --db-path "$DB_PATH" \
  --seed 42 --sample-mode all --output outputs/all
```

---

## 5. 各 run の比較表

| 項目 | runA | runB | head | random | all |
|------|------|------|------|--------|-----|
| data_source | db | db | db | db | db |
| db_path | kyotei_races.sqlite | 同左 | 同左 | 同左 | 同左 |
| train_sample_count | 22416 | 22416 | 22416 | 22416 | 22416 |
| train_file_manifest_hash | None | None | None | None | None |
| verify_details_hash | 49a1cafac36cc07e | 同左 | 同左 | 同左 | 同左 |
| selected_bets_count | 504 | 504 | 504 | 504 | 504 |
| selected_bets_total_count | 504 | 504 | 504 | 504 | 504 |
| total_bet_selected | 50400.0 | 50400.0 | 50400.0 | 50400.0 | 50400.0 |
| total_payout_selected | 46450.0 | 46450.0 | 46450.0 | 46450.0 | 46450.0 |
| roi_selected | 92.16 | 92.16 | 92.16 | 92.16 | 92.16 |
| odds_missing_count | 0 | 0 | 0 | 0 | 0 |
| skip_reasons | すべて 0 | 同左 | 同左 | 同左 | 同左 |

- 差分が出たのは **run_id** と **summary_created_at** のみ（runA vs runB）。
- head / random / all 間の差分は **sample_mode** のラベルと run_id・summary_created_at のみで、数値・hash はすべて同一。

※ DB 経路では `_collect_training_data_from_repository` が sample_mode / seed を受け取っておらず、取得順・件数が同一のため、head・random・all で同じ学習データ・同じ結果になっている。

---

## 6. 分析整理

1. **runA / runB が一致したか**  
   **一致した。** 差分は run_id と summary_created_at のみ。data_source, db_path, train_sample_count, verify_details_hash, selected_bets_count, total_bet_selected, total_payout_selected, roi_selected はすべて同一。

2. **head / random / all で train_file_manifest_hash がどう違うか**  
   **差なし。** DB 経路では train_file_manifest を出力しておらず、いずれも None。また DB では sample_mode に依存する処理がなく、学習データ・結果とも同一。

3. **roi_selected の変化**  
   **変化なし。** 全 run で 92.16%。

4. **selected_bets_total_count の差**  
   **差なし。** 全 run で 504。

5. **skip_reasons の差**  
   **差なし。** 全 run で odds_missing / prediction_missing / no_ev_candidate / result_missing とも 0。

6. **odds_missing の差**  
   **差なし。** 全 run で odds_missing_count 0。DB にオッズが揃っているため。

---

## 7. 原因候補の優先順位

今回の実験では **DB 統一・同一条件で完全再現** し、head/random/all でも数値・hash はすべて同一だった。そのうえで、一般的な「ROI がブレる原因」の切り分け用に優先順位を整理した。

### 1. 最有力原因（今回の実験では未発生）

- **非決定性（乱数・時刻依存）**
  - **根拠**: 同一条件で run_id 以外が一致すれば再現性は取れている。runA/runB で一致したため、今回の経路では非決定性の影響は見られなかった。
  - **該当 run**: 特になし（runA vs runB は一致）。
  - **次アクション**: 今後別環境で runA/runB が一致しない場合は、seed の伝播・時刻依存コードの有無を確認する。

### 2. 次点原因（今回の実験では未発生）

- **データソースの混在（JSON と DB）**
  - **根拠**: DB のみに統一した今回、全 run で data_source=db かつ同一 db_path で結果が揃った。
  - **該当 run**: 特になし。
  - **次アクション**: 再現性診断では常に `--db-path` を指定し、conditions の data_source / db_path を compare_run_summaries で確認する。

- **サンプル切り出し（head / random / all）**
  - **根拠**: JSON 経路では sample_mode で先頭 N 件・ランダム・全件が変わるが、**DB 経路では repository が sample_mode を受け取っておらず、全 run で同じ 22416 件・同じ順序**。そのため今回の DB 実験では head/random/all で差は出なかった。
  - **該当 run**: head / random / all（いずれも同じ結果）。
  - **次アクション**: JSON で head と all の差を確認したい場合は、JSON 経路で同様の実験を行う。DB で sample_mode を効かせる場合は、`_collect_training_data_from_repository` に sample_mode / seed を渡し、取得順・件数を変える実装を検討する。

### 3. 低優先原因（今回の実験では未発生）

- **verify 条件の差（odds_missing / no_ev_candidate）**
  - **根拠**: 全 run で odds_missing_count=0、skip_reasons も 0。オッズ・結果が DB で揃っているため。
  - **該当 run**: 特になし。
  - **次アクション**: 別データで odds_missing や no_ev_candidate が増えた run と比較する場合は、compare_run_summaries の skip_reasons / odds_missing_count を確認する。

- **bet 数が少なすぎることによる ROI 分散**
  - **根拠**: 今回 selected_bets_total_count=504 と十分あり、全 run で同一。
  - **該当 run**: 特になし。
  - **次アクション**: 日をまたいだ検証や、bet 数が極端に少ない run では、ROI の信頼区間を考慮する。

---

## 8. 次にやるべきアクション

1. **DB を正とした再現性診断のルール化**  
   実験時は常に `--db-path` を指定し、compare_run_summaries で data_source / db_path が同一であることを確認する。

2. **DB 経路での sample_mode の扱い**  
   head/random/all の差を DB でも見たい場合は、`baseline_train_usecase` の `_collect_training_data_from_repository` に sample_mode と seed を渡し、取得順のシャッフルや打ち切りを変える実装を検討する。

3. **train_file_manifest の DB 対応（任意）**  
   DB 経路でも「どの race_date/stadium/race_number を何件使ったか」を manifest 相当で記録し、train_file_manifest_hash を出せるようにすると、今後の切り分けがしやすい。

4. **別日・別期間での再現性確認**  
   2025-06-01 以外の predict_date や、別の train 期間でも runA/runB を実行し、同様に一致するか確認する。

---

## 補足: 実行時のコード修正

- **CalibratedClassifierCV**: sklearn 1.8 で `cv="prefit"` が廃止されているため、既に fit 済みのモデルを `FrozenEstimator` でラップし、`CalibratedClassifierCV(estimator=frozen, method=calib, cv=None)` でキャリブレーションするように `baseline_train_usecase.py` を修正した。挙動は「学習データのみでキャリブレーション」のまま。
