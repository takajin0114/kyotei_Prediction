# Next Tasks

新しいモデル比較を始める前に、[leaderboard](../../experiments/leaderboard.md) と [open_questions](../../experiments/open_questions.md) を確認すること。

## Priority 1

- Strategy B pipeline stabilization

## Priority 2

- 特徴量見直し（venue/recent の正規化・重み）、または rolling validation automation

## Priority 3

- **実施済み**: LightGBM / XGBoost model sweep。EXP-0005 で XGBoost が最良 ROI。次基準候補として adopt

## Priority 4

- XGBoost をデフォルトモデルとして運用検討

## Priority 5

- ranking probability model
  - P(1st)
  - P(2nd | 1st)
  - P(3rd | 1st, 2nd)

## Priority 6

- feature engineering
  - **実施済み**: feature_set 明示引数化、meta.json に feature_set 保存、予測時 mismatch 警告、DB 由来 recent_form / venue_course の v2 実装、train/predict への racer_history_cache 接続
  - **実施済み**: n_windows=12 で extended_features と extended_features_v2 を正式比較。EXP-0004 で hold 判断（v2 ROI 悪化）
  - course × venue performance のさらなる拡張は任意
