# Experiment: EXP-0006 XGBoost Strategy Grid and Bet Sizing

## experiment id

EXP-0006

## purpose

XGBoost を固定し、top_n_ev の top_n × ev_threshold 2次元最適化、bet sizing 比較、xgboost vs lightgbm 再比較を行う。

## ev_threshold_only の不採用根拠

- EXP-0005 で ev_threshold_only を 1.05〜1.25 で sweep した結果、**全条件で -48.95% 〜 -51.35%** と top_n_ev より大幅悪化。
- top_n を外すと購入点数が増え、fixed stake では損失が拡大。よって **「top_n を外す」は現時点では不採用（reject）**。

## configuration

- model: XGBoost（grid / bet sizing）、XGBoost vs LightGBM（モデル比較）
- calibration: sigmoid
- features: extended_features
- strategy: top_n_ev
- top_n: 3, 5, 6, 8
- ev_threshold: 1.05, 1.10, 1.15, 1.20, 1.25
- n_windows: 12（要再実行時は --n-windows 12）
- seed: 42

## results

### Task1: top_n × ev_threshold grid

（outputs/exp0006_xgb_strategy_grid_and_bet_sizing.json の grid を参照）

- 最良: top_n=3, ev_threshold=1.25 で overall_roi_selected が最良（実行条件により変動）。
- 各セルで overall_roi_selected, mean_roi_selected, median_roi_selected, std_roi_selected, total_selected_bets, profit, max_drawdown を出力。

### Task2: bet sizing comparison

最良 (top_n, ev_threshold) 条件で同一 bet 列に対し以下を比較:

| bet_sizing | overall_roi_selected | max_drawdown | Notes |
|------------|---------------------|--------------|-------|
| fixed | （JSON 参照） | - | 基準 |
| half_kelly | （JSON 参照） | - | 変動大の可能性 |
| capped_kelly_0.02 | （JSON 参照） | - | cap 2% |
| capped_kelly_0.05 | （JSON 参照） | - | cap 5% |

### Task3: model comparison (xgboost vs lightgbm)

最良 (top_n, ev) 条件で同指標を比較:

- overall_roi_selected
- mean_roi_selected
- std_roi_selected
- total_selected_bets
- mean_log_loss
- mean_brier_score

## decision

- **adopt**: Task1 で最良だった (top_n, ev_threshold) を次基準とする。
- **hold**: ev_threshold_only（不採用根拠は上記）。
- **reject**: top_n 廃止（ev_threshold_only で悪化のため）。
