# Project Status

現在のプロジェクト状態。

- **メイン戦略**: Strategy B（baseline B + sigmoid + top_n_ev, top_n=6, ev_threshold=1.20）
- **データ**: DB を唯一の正（`kyotei_predictor/data/kyotei_races.sqlite`）。JSON 直読みは使わない。
- **評価**: rolling validation（n_windows=12）、extended_features、sigmoid calibration。
- **モデル比較**: sklearn / LightGBM / XGBoost の比較基盤あり。LightGBM/XGBoost は環境に libomp が必要。
- **成果物**: docs/MODEL_COMPARISON.md、docs/ROI_EVALUATION_N12_SUMMARY.md、outputs/*.json（gitignore）。

更新日: プロジェクトのマイルストーンごとに更新する。
