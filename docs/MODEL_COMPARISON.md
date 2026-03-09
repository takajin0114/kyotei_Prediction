# モデル比較

条件: extended_features + sigmoid, top_n=6, ev_threshold=1.20, n_windows=12。

| model_type | label | mean_roi_selected | median_roi_selected | std_roi_selected | overall_roi_selected | total_selected_bets | mean_selected_bets_per_window | mean_log_loss | mean_brier_score |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| sklearn | baseline B (sklearn) | -31.86 | -33.91 | 12.92 | -31.81 | 46878 | 3906.5 | 5.371836 | 0.937577 |

(n_windows=12)

## 最有力モデル（現時点）

- **選定**: baseline B (sklearn)
- **理由**: 上記条件で sklearn のみ実行済み。LightGBM / XGBoost は実行環境に OpenMP (libomp) が必要で、未導入の場合は model_sweep がスキップする。Mac では `brew install libomp` のうえで model_sweep を再実行すると 3 モデル比較が可能。
- **評価指標**: overall_roi_selected, mean_roi_selected, std_roi_selected, total_selected_bets, mean_log_loss, mean_brier_score で比較。

## EXP-0006 strategy grid とモデル再比較

- scripts/exp0006_xgb_topn_threshold_grid.py で top_n × ev_threshold grid（XGBoost）と bet sizing 比較、xgboost vs lightgbm 再比較を実施。結果は outputs/exp0006_xgb_strategy_grid_and_bet_sizing.json。ev_threshold_only は reject（ROI 大幅悪化）。
