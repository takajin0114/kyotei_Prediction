# B案ベースライン（最小比較用モデル）

A案（PPO）と同じ検証基盤で比較するための、最小ベースラインモデルの説明です。

---

## 1. B案ベースラインの目的

- **A/B 比較**: A案（強化学習 PPO）と同一の verify / betting / ROI 評価に流し、性能を比較する。
- **高性能化は目的にしない**: 30分程度で動く最小構成を優先する。
- **B案の土台**: 将来「予測モデルと買い目選定の分離」「ROI 重視の改善」へ進むときのベースラインとする。

---

## 2. 実装範囲（現在）

- **モデル**: sklearn（RandomForest）をデフォルト。**LightGBM / XGBoost** を `--model-type` で指定可能（未導入時は sklearn にフォールバック）。
- **入力**: 既存の状態ベクトル（`build_race_state_vector`）をそのまま利用。
- **出力**: A案と同一形式の予測 JSON。**selected_bets** を `--include-selected-bets` で付与可能（betting_selector を再利用）。
- **学習**: 着順入りの `race_data_*.json` から状態ベクトルと正解 3連単クラスを集め、学習・モデル保存（種別は .meta.json に保存）。
- **予測**: 学習済みモデルと `race_data_*.json` から、レースごとに 120 クラススコアを出力し、`all_combinations` に整形。
- **CLI**: `baseline_train` / `baseline_predict` / **compare_ab**（A案・B案を同一条件で検証し結果を並べる）。
- **TODO**: 1着/2着/3着確率モデル、EV 本格導入は今後の発展とする。

---

## 3. A案との違い

| 項目 | A案（PPO） | B案ベースライン |
|------|------------|------------------|
| モデル | 強化学習（stable-baselines3 PPO） | 教師あり分類（RandomForest） |
| 学習 | 環境との相互作用・報酬設計 | 着順入りデータの正解ラベル |
| 予測出力形式 | 同一（all_combinations, probability, rank） | 同一（互換） |
| 検証 | verify_predictions | 同じ verify_predictions |
| 買い目選定 | betting_selector（single / top_n / ev 等） | 同じ betting_selector |

---

## 4. 何を予測しているか

- **タスク**: 3連単 120 通り（1-2-3, 1-2-4, …）の「簡易スコア」を出力する多クラス分類。
- **正解ラベル**: 学習時は `race_data` の着順（race_records）から 1-2-3 着の艇番を取り、その 3連単をクラスラベルとする。
- **予測時**: 状態ベクトルを入力に `predict_proba` で 120 クラスのスコアを出し、確率降順で rank 1..120 を付与。`expected_value` は最小実装では 0 固定（将来オッズと組み合わせて EV 計算可能）。

---

## 5. 既存 verify / betting との接続方法

1. **予測出力**: `run_baseline_predict` の戻り値（または `predictions_baseline_YYYY-MM-DD.json`）は、A案の `predictions_YYYY-MM-DD.json` と同じ構造を持つ。
   - `predictions[].venue`, `race_number`, `all_combinations`
   - `all_combinations[]`: `combination`, `probability`, `expected_value`, `rank`
2. **検証**: `python -m kyotei_predictor.tools.verify_predictions --prediction outputs/predictions_baseline_2024-05-01.json --data-dir kyotei_predictor/data/test_raw` で、A案と同様に的中率・回収率を算出できる。
3. **selected_bets の付与**: B案予測に既存の betting_selector を適用し、`evaluation_mode=selected_bets` で検証できる。
   - 予測時に `--include-selected-bets` を付けると、improvement_config の strategy（または `--strategy`）に従って各レースに `selected_bets` を付与する。
   - 戦略は **single** / **top_n** / **threshold** / **ev** を利用可能（A案と同じ）。
   - 保存された JSON を `verify_predictions --evaluation-mode selected_bets` に渡すと、selected_bets ベースの ROI を算出できる。

---

## 6. モデル種別（LightGBM / XGBoost / sklearn）

- **切替条件**: `--model-type sklearn`（デフォルト）/ `lightgbm` / `xgboost` で学習時に指定。lightgbm または xgboost が未導入の場合は **sklearn にフォールバック** する。
- **保存**: 使用したモデル種別は `モデルパス.meta.json` に保存され、予測結果の `model_info.backend` に含まれる。
- **学習例**: `python -m kyotei_predictor.cli.baseline_train --model-type lightgbm ...`

---

## 7. 実行例

```bash
# 学習（着順入り race_data_*.json が data_dir にあること）
python -m kyotei_predictor.cli.baseline_train \
  --data-dir kyotei_predictor/data/test_raw \
  --model-path outputs/baseline_b_model.joblib \
  --max-samples 3000

# 予測（selected_bets 付きで保存する場合）
python -m kyotei_predictor.cli.baseline_predict \
  --prediction-date 2024-05-01 \
  --data-dir kyotei_predictor/data/test_raw \
  --output outputs/predictions_baseline_2024-05-01.json \
  --include-selected-bets --strategy top_n --top-n 3

# 検証（first_only: 1位のみ100円）
python -m kyotei_predictor.tools.verify_predictions \
  --prediction outputs/predictions_baseline_2024-05-01.json \
  --data-dir kyotei_predictor/data/test_raw

# 検証（selected_bets: 付与した買い目で ROI）
python -m kyotei_predictor.tools.verify_predictions \
  --prediction outputs/predictions_baseline_2024-05-01.json \
  --data-dir kyotei_predictor/data/test_raw \
  --evaluation-mode selected_bets

# A/B比較（同一 data-dir / evaluation-mode で A と B の結果を並べる）
python -m kyotei_predictor.cli.compare_ab \
  --prediction-a outputs/predictions_2024-05-01.json \
  --prediction-b outputs/predictions_baseline_2024-05-01.json \
  --data-dir kyotei_predictor/data/test_raw \
  --evaluation-mode first_only \
  --output outputs/compare_ab.json
```

---

## 8. 比較時に揃えるべき条件

A案と B案を同条件で比較するときは、以下を揃える。

| 項目 | 説明 |
|------|------|
| **date / data** | 同じ予測日・同じ `data_dir` の race_data / odds_data を使う |
| **betting_strategy** | 両方に selected_bets を付与する場合は、同じ strategy（single / top_n / threshold / ev）とパラメータ（top_n, score_threshold, ev_threshold）を使う |
| **evaluation_mode** | 検証時に同じ first_only または selected_bets を指定する |
| **ROI 解釈** | first_only は「1位予想に100円ずつ」の ROI。selected_bets は「付与した買い目に100円ずつ」の ROI。比較時はどちらか一方で統一する。 |

**ROI 解釈時の注意**: 買い目数が増えると total_bet が増え、ROI の意味が変わる。A/B で「同じ betting_strategy・同じ evaluation_mode」にそろえたうえで、hit_rate と roi_pct の両方を見ること。

---

## 9. 今後の発展

- **1着/2着/3着確率モデル**: 3連単 120 クラスではなく、1着・2着・3着を別々のモデルで予測し、その積で 3連単確率を構成する。
- **EV 本格導入**: オッズと組み合わせて期待値を計算し、`expected_value` を出力し、betting strategy=ev で比較する。
- **A/B 比較の拡張**: 同一日・同一データで A/B を実行するスクリプトを用意し、compare_ab の前段で予測を自動実行するオプションを追加する。

---

## 最終出力（Sprint サマリ）

### Baseline B Summary

B案ベースラインは、A案（PPO）と同じ verify / betting / ROI 基盤で比較するための**最小比較用モデル**として追加済みである。

- **学習**: 着順入りの `race_data_*.json` から状態ベクトルと 3連単クラスを集め、軽量分類器を学習してモデル保存。
- **予測**: 学習済みモデルで 120 クラススコアを出力し、A案と同一形式（`all_combinations`, `probability`, `rank`）の JSON を生成。オプションで `selected_bets` を付与可能。
- **検証**: 既存の `verify_predictions` にそのまま渡して ROI / hit_rate を算出可能。A案と同条件で比較するための `compare_ab` CLI も利用可能。

### Model Choice

- **採用**: デフォルトは **scikit-learn の RandomForestClassifier**。オプションで **LightGBM** または **XGBoost** を `--model-type` で指定可能。
- **理由**: 依存が少なく 30 分で動く最小構成を優先。LightGBM / XGBoost は未導入時は sklearn にフォールバックするため、環境に依存せず動作する。
- **LightGBM でない場合**: 将来差し替える場合は、`create_baseline_model(model_type="lightgbm")` を指定するだけでよい。fit / predict_proba / save-load のインターフェースは共通。

### Changed Files（B案ベースライン追加時の対象）

| ファイル | 目的 |
|----------|------|
| `application/baseline_train_usecase.py` | 学習データ収集・学習実行・モデル保存 |
| `application/baseline_predict_usecase.py` | 予測実行・A案互換形式・selected_bets 付与 |
| `infrastructure/baseline_model_runner.py` | モデル生成（sklearn/LGB/XGB）、predict_proba、all_combinations 整形 |
| `infrastructure/baseline_model_repository.py` | モデル保存・読込・.meta.json で種別管理 |
| `cli/baseline_train.py` | 学習 CLI |
| `cli/baseline_predict.py` | 予測 CLI |
| `docs/BASELINE_B_APPROACH.md` | B案の目的・範囲・実行例・接続方法 |
| `tests/test_baseline_b.py` | 学習・予測・selected_bets の軽量テスト |

### How It Connects

- **betting**: B案の予測 JSON は `all_combinations` に probability / rank を持つ。既存の `betting_selector`（single / top_n / threshold / ev）をそのまま適用でき、`--include-selected-bets` で `selected_bets` を付与する。
- **verify**: `verify_predictions --prediction <B案JSON> --data-dir <同一data_dir>` で、A案と同様に first_only または selected_bets で ROI / hit_rate を算出する。
- **ROI**: 同じ data_dir・同じ evaluation_mode・同じ betting_strategy に揃えれば、A案と B案の ROI を同条件で比較できる。

### Validation

- **学習**: `baseline_train` で data_dir に着順入り race_data があればモデルが保存される。テストでは `run_baseline_train` を小規模パラメータで実行して成功することを確認。
- **予測**: 保存したモデルで `run_baseline_predict` を実行し、`predictions[].all_combinations` に 120 件の combination / probability / rank が含まれることを確認。
- **検証**: 出力 JSON を `verify_predictions` に渡し、エラーなく hit_rate / roi_pct が算出されることを確認。`test_baseline_predict_with_selected_bets` で selected_bets 付与を検証。

### How to Run

- **学習**: `python -m kyotei_predictor.cli.baseline_train --data-dir <data_dir> --model-path outputs/baseline_b_model.joblib [--model-type lightgbm]`
- **予測**: `python -m kyotei_predictor.cli.baseline_predict --prediction-date YYYY-MM-DD --data-dir <data_dir> [--include-selected-bets --strategy top_n --top-n 3]`
- **検証**: `python -m kyotei_predictor.tools.verify_predictions --prediction outputs/predictions_baseline_YYYY-MM-DD.json --data-dir <data_dir> [--evaluation-mode selected_bets]`

### Next Steps

1. **実データで A/B 比較**: 同一日・同一 data_dir で A案と B案の予測を取得し、`compare_ab` で ROI / hit_rate を比較する。
2. **B案のモデル・特徴量改善**: 1着/2着/3着確率モデルや特徴量拡張で予測精度を上げる。
3. **EV 本格化**: オッズと組み合わせて expected_value を計算し、strategy=ev で検証可能にする。
