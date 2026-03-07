# 再現性診断の使い方

主戦略（run_strategy_b）の **「同じ条件なら同じ結果」** を確認し、ROI ブレの原因を切り分けるための手順です。

## 目的

- 同条件で再実行したら同じ結果になることを確認する
- 2 回の run の違いを説明できるようにする
- 学習データと verify 対象の実態を見えるようにする

## 1. 実行ごとに保存されるもの

`run_strategy_b` 実行後、次のファイルが出力されます。

| 出力 | 内容 |
|------|------|
| `strategy_b_summary_<predict_date>.json` | 実行条件（conditions）と検証サマリ（summary）。再現性切り分けの基準。 |
| `train_file_manifest.json` | 学習に使ったファイルパス一覧・件数・日付範囲（モデルと同じディレクトリ） |
| `verify_details_<predict_date>.json` | 検証の前提条件（評価レース数・スキップ理由・1日ごと bet 件数）とレース別詳細 |

summary JSON の `conditions` には次が含まれます。

- `run_id`, `train_start`, `train_end`, `predict_date`, `model`, `calibration`, `strategy`, `top_n`, `ev_threshold`, `evaluation_mode`, `seed`
- `max_samples`, `sample_mode`, `data_source`, `data_dir`
- `train_sample_count`, `train_file_count`, `train_first_date`, `train_last_date`, `train_file_manifest_path`, `train_file_manifest_hash`
- `predict_race_count`, `odds_missing_count`, `selected_bets_count`, `total_bet_selected`, `total_payout_selected`, `roi_selected`
- `git_commit_hash`, `model_path`, `verify_details_path`, `verify_details_hash`, `summary_created_at`

## 2. 再現実行の手順（同じ結果を出す）

同じ条件で再実行するには、少なくとも以下を揃えます。

1. **seed**  
   `--seed 42` のように固定（未指定時は 42）。
2. **学習期間**  
   `--train-start`, `--train-end` を同じに。
3. **学習サンプル**  
   `--max-samples`, `--sample-mode` を同じに（`sample_mode=random` のときは seed も同じに）。
4. **データ**  
   同じ `--data-dir`（および `--data-source`）で、同じ期間の race_data / odds_data が入っていること。
5. **予測日**  
   `--predict-date` を同じに。

例（CLI）:

```bash
python -m kyotei_predictor.cli.run_strategy_b \
  --train-start 2024-01-01 --train-end 2024-05-31 \
  --predict-date 2024-06-01 \
  --data-dir /path/to/raw \
  --seed 42 \
  --max-samples 50000 \
  --sample-mode head
```

同じ条件で 2 回実行し、2 つの summary JSON を比較します。

## 2.1 実験パターン別コマンド例

以下は **ROI 不安定の原因切り分け** 用に、比較しやすい実行パターンです。`DATA_DIR` と `PREDICT_DATE` は環境に合わせて置き換えてください。

### パターン 1: 同一条件で 2 回実行（完全再現の確認）

```bash
export DATA_DIR="kyotei_predictor/data/raw"
export PREDICT_DATE="2024-06-01"

# 1 回目 → outputs/strategy_b/strategy_b_summary_${PREDICT_DATE}.json
python -m kyotei_predictor.cli.run_strategy_b \
  --train-start 2024-01-01 --train-end 2024-05-31 \
  --predict-date "$PREDICT_DATE" --data-dir "$DATA_DIR" \
  --seed 42 --max-samples 50000 --sample-mode head

# 2 回目 → 別ディレクトリに保存して比較（または上書きして summary を比較）
python -m kyotei_predictor.cli.run_strategy_b \
  --train-start 2024-01-01 --train-end 2024-05-31 \
  --predict-date "$PREDICT_DATE" --data-dir "$DATA_DIR" \
  --seed 42 --max-samples 50000 --sample-mode head \
  --output outputs/strategy_b_run2

# 比較（差分がなければ再現できている）
python -m kyotei_predictor.cli.compare_run_summaries \
  outputs/strategy_b/strategy_b_summary_${PREDICT_DATE}.json \
  outputs/strategy_b_run2/strategy_b_summary_${PREDICT_DATE}.json --diff-only
```

### パターン 2: sample_mode=head で実行

```bash
python -m kyotei_predictor.cli.run_strategy_b \
  --train-start 2024-01-01 --train-end 2024-05-31 \
  --predict-date "$PREDICT_DATE" --data-dir "$DATA_DIR" \
  --seed 42 --max-samples 50000 --sample-mode head \
  --output outputs/strategy_b_head
```

### パターン 3: sample_mode=random で実行

```bash
python -m kyotei_predictor.cli.run_strategy_b \
  --train-start 2024-01-01 --train-end 2024-05-31 \
  --predict-date "$PREDICT_DATE" --data-dir "$DATA_DIR" \
  --seed 42 --max-samples 50000 --sample-mode random \
  --output outputs/strategy_b_random
```

### パターン 4: sample_mode=all で実行

```bash
python -m kyotei_predictor.cli.run_strategy_b \
  --train-start 2024-01-01 --train-end 2024-05-31 \
  --predict-date "$PREDICT_DATE" --data-dir "$DATA_DIR" \
  --seed 42 --sample-mode all \
  --output outputs/strategy_b_all
```

### head / random / all の 3 本を比較する例

```bash
python -m kyotei_predictor.cli.compare_run_summaries \
  outputs/strategy_b_head/strategy_b_summary_${PREDICT_DATE}.json \
  outputs/strategy_b_random/strategy_b_summary_${PREDICT_DATE}.json --diff-only

python -m kyotei_predictor.cli.compare_run_summaries \
  outputs/strategy_b_head/strategy_b_summary_${PREDICT_DATE}.json \
  outputs/strategy_b_all/strategy_b_summary_${PREDICT_DATE}.json --diff-only
```

## 3. 2 回の run の違いを比較する

`compare_run_summaries` で 2 つの summary JSON を比較し、差分がある項目だけを確認できます。

```bash
# 全項目表示
python -m kyotei_predictor.cli.compare_run_summaries \
  outputs/strategy_b/strategy_b_summary_2024-06-01.json \
  outputs2/strategy_b/strategy_b_summary_2024-06-01.json

# 差分がある項目だけ表示
python -m kyotei_predictor.cli.compare_run_summaries \
  summary_a.json summary_b.json --diff-only
```

比較対象（conditions）: `train_start`, `train_end`, `seed`, `max_samples`, `sample_mode`, `train_sample_count`, `train_file_count`, `train_first_date`, `train_last_date`, `train_file_manifest_hash`, `verify_details_hash`, `odds_missing_count`, `selected_bets_count`, `total_bet_selected`, `total_payout_selected`, `roi_selected` など。

比較対象（summary 側）: `skip_reasons`, `bets_per_date`, `selected_bets_total_count`, `races_with_selected_bets`, `odds_missing_count` も比較可能。`--show-json-diff` で JSON 差分を表示できる。

## 4. 学習データの実態を確認する

- **ログ**  
  学習時には `[train_manifest]` で次のログが出ます。  
  `file_count`, `sample_count`, `first_date`, `last_date`, `max_samples_reached`, `files_head`, `files_tail`
- **train_file_manifest.json**  
  モデル保存先と同じディレクトリに出力されます。summary の `conditions.train_file_manifest_path` からパスを参照できます。  
  中身: 使用ファイルパス一覧・件数・日付範囲・`max_samples_reached`・`sample_mode`。

「train_start〜train_end のつもりで、実際にどのファイルを何件使ったか」をここで確認できます。

## 5. verify の前提条件を確認する

- **summary のキー**  
  `evaluated_race_count`, `races_with_predictions`, `races_with_odds`, `races_with_selected_bets`, `skipped_race_count`, `skip_reasons`（`odds_missing`, `result_missing`, `no_ev_candidate`）, `selected_bets_total_count`, `bets_per_date`
- **verify_details_<date>.json**  
  上記に加え、レース別の詳細（`details`）が入っています。  
  「なぜ bet 数が減ったか」をレース単位で追いやすくするためのものです。

## 6. 次に確認すべきポイント

- **seed**  
  全経路（run_strategy_b → baseline_train → モデル・キャリブレーション）で同じ seed が渡っているか。summary とモデルの `.meta.json` に `seed` が保存されているか。
- **データ差分**  
  同じ `train_start`/`train_end` でも、ファイル追加・削除で `train_file_count` や `train_first_date`/`train_last_date` が変わっていないか。`train_file_manifest.json` 同士の差分。
- **verify 条件**  
  `odds_missing_count` や `skip_reasons` が run 間で違っていないか。オッズ欠損や「selected_bets が 0 のレース」が増えていないか。
- **sample_mode / max_samples**  
  `head` だとファイル順に依存するため、ファイル集合が変わると先頭 N 件の内容が変わります。`random`（seed 固定）や `all` で切り分け可能です。

## 7. ROI 不安定原因の切り分け手順

診断実行と `compare_run_summaries` の結果から、次の判断基準で原因を切り分けてください。

| 現象 | 判断 | 次の確認 |
|------|------|----------|
| **同一条件で summary が一致しない** | **非決定性**（乱数・順序・時刻依存など） | `seed` 固定・`train_file_manifest_hash` / `verify_details_hash` が同一か。2 回実行で conditions の hash が同じか。 |
| **head と all で大きく差が出る** | **サンプル切り出し**（先頭 N 件の偏り） | `train_file_manifest.json` の `file_paths` 先頭と `sample_mode`。`sample_mode=random`（seed 固定）でも差があればデータ依存。 |
| **odds_missing / no_ev_candidate の差が大きい** | **verify 条件の差分**（オッズ欠損・EV 候補の有無） | `verify_details_*.json` の `skip_reasons`・`skipped_race_identifiers`。オッズファイル有無・予測の selected_bets 有無。 |
| **bet 数が少なすぎる** | **ROI 分散**（母数が少なく変動が大きい） | `selected_bets_total_count`・`races_with_selected_bets`。日をまたいだ検証や bet 数を増やす設定の検討。 |

実行手順の流れ: [2.1 実験パターン別コマンド例](#21-実験パターン別コマンド例) で同一条件 2 回・head/random/all を実行 → `compare_run_summaries`（必要なら `--show-json-diff`）で差分確認 → 上表で原因を当てる。

---

関連: [RUN_VERIFICATION.md](RUN_VERIFICATION.md), [STRATEGY_B_OPERATION.md](STRATEGY_B_OPERATION.md)
