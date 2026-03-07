# モデル改善フェーズ 比較サマリ

calibration・特徴量・モデルの比較基盤と、現時点の結論をまとめる。

## 1. Calibration 比較表

条件: top_n=6, ev_threshold=1.20, n_windows=2（本番は --n-windows 12 推奨）。

| calibration | mean_roi_selected | median_roi_selected | std_roi_selected | overall_roi_selected | total_selected_bets | mean_selected_bets_per_window | mean_log_loss | mean_brier_score |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| none | -26.9 | -26.9 | 5.01 | -27.17 | 4659 | 2329.5 | 4.197415 | 0.947711 |
| sigmoid | -19.72 | -19.72 | 14.07 | -20.39 | 7585 | 3792.5 | 5.230171 | 0.947853 |
| isotonic | -38.5 | -38.5 | 1.99 | -38.56 | 8190 | 4095 | 23.72651 | 0.944274 |

- 詳細: `docs/CALIBRATION_COMPARISON.md` / `outputs/calibration_comparison.csv`

## 2. 特徴量比較表

- current_features: 既存状態ベクトルのみ（KYOTEI_USE_MOTOR_WIN_PROXY=0）
- extended_features: 既存 + モーター勝率代理（KYOTEI_USE_MOTOR_WIN_PROXY=1）

| feature_set | mean_roi_selected | median_roi_selected | std_roi_selected | overall_roi_selected | total_selected_bets | mean_selected_bets_per_window | mean_log_loss | mean_brier_score |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| current_features | -19.72 | -19.72 | 14.07 | -20.39 | 7585 | 3792.5 | 5.230171 | 0.947853 |
| extended_features | -18.23 | -18.23 | 16.19 | -17.55 | 7683 | 3841.5 | 5.252929 | 0.945842 |

- 詳細: `docs/FEATURE_COMPARISON.md` / `outputs/feature_comparison.csv`

## 3. モデル比較表

現状は sklearn のみ実行（lightgbm / xgboost は未導入時スキップ）。導入後は `model_sweep` で自動で追加比較される。

| model_type | label | mean_roi_selected | median_roi_selected | std_roi_selected | overall_roi_selected | total_selected_bets | mean_selected_bets_per_window | mean_log_loss | mean_brier_score |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| sklearn | baseline B (sklearn) | -19.72 | -19.72 | 14.07 | -20.39 | 7585 | 3792.5 | 5.230171 | 0.947853 |

- 詳細: `docs/MODEL_COMPARISON.md` / `outputs/model_comparison.csv`

## 4. 現時点で最も有望な改善方向

（2 window の結果に基づく暫定。n_windows=12 で再実行すると順位が変わる可能性あり。）

1. **Calibration**  
   - **sigmoid** を推奨。mean / overall ROI が none より良く、isotonic は log_loss が極端に悪化しているため避ける。
2. **特徴量**  
   - **extended_features**（モーター勝率代理あり）が、この 2 window では overall_roi が約 3pt 改善（-20.39 → -17.55）。Brier もわずかに改善。まずは extended で n_windows=12 を回して安定性を確認する価値あり。
3. **モデル**  
   - 現状 sklearn のみのため、**LightGBM / XGBoost を導入して model_sweep で追加比較**するのが次の一手。

**まとめ**: 当面は **sigmoid + extended_features + baseline B (sklearn)** をベースにし、**LightGBM/XGBoost の追加**と **n_windows=12 での再評価** で改善余地を確認する。

## 5. 次にやるべきこと

1. **n_windows=12 で再実行**  
   calibration_sweep / feature_sweep / model_sweep を `--n-windows 12` で実行し、上記の傾向が安定するか確認する。
2. **LightGBM / XGBoost の導入**  
   `pip install lightgbm xgboost` のうえ、model_sweep を再実行してモデル比較表を増やす。
3. **特徴量の拡張**  
   会場別成績・コース別成績・直近成績・枠番×会場などは、state_vector と DB スキーマを拡張してから「extended_features」に追加する。
4. **比較の自動化**  
   sweep 実行後に `export_model_improvement_comparisons` を実行し、CSV / docs を更新する。

---

## 実行コマンド一覧

```bash
# Calibration 比較（none / sigmoid / isotonic）
python3 -m kyotei_predictor.tools.calibration_sweep \
  --db-path kyotei_predictor/data/kyotei_races.sqlite \
  --n-windows 12 --output-dir outputs

# 特徴量比較（current / extended）
python3 -m kyotei_predictor.tools.feature_sweep \
  --db-path kyotei_predictor/data/kyotei_races.sqlite \
  --n-windows 12 --output-dir outputs

# モデル比較（sklearn / lightgbm / xgboost）
python3 -m kyotei_predictor.tools.model_sweep \
  --db-path kyotei_predictor/data/kyotei_races.sqlite \
  --n-windows 12 --output-dir outputs

# 比較表のエクスポート（CSV + docs）
python3 -m kyotei_predictor.tools.export_model_improvement_comparisons \
  --output-dir outputs --docs-dir docs
```
