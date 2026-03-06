# B案ベースライン（最小比較用モデル）

A案（PPO）と同じ検証基盤で比較するための、最小ベースラインモデルの説明です。

---

## 1. B案ベースラインの目的

- **A/B 比較**: A案（強化学習 PPO）と同一の verify / betting / ROI 評価に流し、性能を比較する。
- **高性能化は目的にしない**: 30分程度で動く最小構成を優先する。
- **B案の土台**: 将来「予測モデルと買い目選定の分離」「ROI 重視の改善」へ進むときのベースラインとする。

---

## 2. 今回の実装範囲

- **モデル**: scikit-learn の RandomForestClassifier（3連単 120 クラスの多クラス分類）。
- **入力**: 既存の状態ベクトル（`build_race_state_vector`）をそのまま利用。
- **出力**: A案と同一形式の予測 JSON（`prediction_date`, `predictions[].venue`, `race_number`, `all_combinations`）。
- **学習**: 着順入りの `race_data_*.json` から状態ベクトルと正解 3連単クラスを集め、学習・モデル保存。
- **予測**: 学習済みモデルと `race_data_*.json` から、レースごとに 120 クラススコアを出力し、`all_combinations` に整形。
- **CLI**: `baseline_train` / `baseline_predict` の 2 本。
- **TODO**: LightGBM / XGBoost への差し替え、1着/2着/3着確率モデル、EV 本格導入は今後の発展とする。

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
3. **買い目選定**: 予測 JSON に `selected_bets` を付与する場合は、既存の `betting_selector`（single / top_n / threshold / ev）をそのまま使える。B案側で `include_selected_bets` 相当の処理を追加すれば、検証で `evaluation_mode=selected_bets` も利用可能。

---

## 6. 実行例

```bash
# 学習（着順入り race_data_*.json が data_dir にあること）
python -m kyotei_predictor.cli.baseline_train \
  --data-dir kyotei_predictor/data/test_raw \
  --model-path outputs/baseline_b_model.joblib \
  --max-samples 3000

# 予測
python -m kyotei_predictor.cli.baseline_predict \
  --predict-date 2024-05-01 \
  --data-dir kyotei_predictor/data/test_raw \
  --output outputs/predictions_baseline_2024-05-01.json

# 検証（A案と同じコマンド）
python -m kyotei_predictor.tools.verify_predictions \
  --prediction outputs/predictions_baseline_2024-05-01.json \
  --data-dir kyotei_predictor/data/test_raw
```

---

## 7. 今後の発展

- **1着/2着/3着確率モデル**: 3連単 120 クラスではなく、1着・2着・3着を別々のモデルで予測し、その積で 3連単確率を構成する。
- **EV 本格導入**: オッズと組み合わせて期待値を計算し、`expected_value` を出力し、betting strategy=ev で比較する。
- **A/B 比較自動化**: 同一日・同一データで A案と B案の予測を実行し、verify 結果（ROI, hit_rate）を自動で並べてレポートする。
- **LightGBM / XGBoost**: `create_baseline_model(use_sklearn=False)` で差し替え可能な構造にしてある。依存を追加したうえで、同じ fit / predict_proba インターフェースで利用する。
