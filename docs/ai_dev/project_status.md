# Project Status

現在のプロジェクト状態。

- **メイン戦略**: Strategy B（baseline B + sigmoid + top_n_ev, top_n=6, ev_threshold=1.20）
- **データ**: DB を唯一の正（`kyotei_predictor/data/kyotei_races.sqlite`）。JSON 直読みは使わない。
- **評価**: rolling validation（n_windows=12）、extended_features、sigmoid calibration。extended_features_v2 は n12 正式比較で ROI 悪化のため hold。
- **特徴量セット**: train / predict / rolling validation / feature_sweep で **feature_set を明示引数**で指定可能。優先順位は「明示引数 > 環境変数 KYOTEI_FEATURE_SET > デフォルト」。学習時に使った feature_set は **meta.json に保存**され、予測時に不一致の場合は **warning** を出す。
  - `current_features` / `extended_features` / `extended_features_v2`
  - v2 は DB 由来の **recent_form**（直近N走の平均着順・1着率・3着内率）と **venue_course**（当該場成績）を実装済み。motor_trend・relative_race_strength は extended ベース。リーク防止のため「対象レース以前の履歴のみ」使用。
- **モデル比較**: sklearn / LightGBM / XGBoost を rolling validation で比較可能。EXP-0005 で XGBoost が最良 ROI（-20.7%）。LightGBM/XGBoost は環境に libomp が必要（brew install libomp）。
- **成果物**: docs/MODEL_COMPARISON.md、docs/ROI_EVALUATION_N12_SUMMARY.md、outputs/*.json（gitignore）。rolling validation の summary は model_type / feature_set / n_windows / overall_roi_selected 等の標準キーで統一。

- **EXP-0005 ev_threshold_sweep**: status: completed。purpose: EV threshold optimization（ev_threshold_only 戦略で 1.05〜1.25 を比較）。Kelly capped 実装済み（bet_size = bankroll * min(kelly, 0.05)）。

更新日: プロジェクトのマイルストーンごとに更新する。
