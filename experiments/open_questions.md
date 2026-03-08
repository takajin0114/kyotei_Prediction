# Open Questions

現在の未解決課題を記録する。

## Q1

120 class classification のままでよいか。それとも順位確率分解（P(1着)、P(2着|1着)、P(3着|1着,2着)）へ移行すべきか。

## Q2

ROI 改善に最も効く特徴量は何か。

- venue performance
- course performance
- recent form
- motor trend
- relative race strength

（extended_features_v2 で motor_trend / relative_race_strength に加え、DB 由来の recent_form・venue_course を実装済み。EXP-0004: n_windows=12 で正式比較済み → extended_features_v2 は extended_features より ROI 悪化（-33.76% vs -27.7%）のため hold。）

## Q3

EV strategy の改善余地はどこか。

- conservative EV
- odds bucket threshold
- Kelly fraction
- portfolio control

## Q4

LightGBM / XGBoost は baseline を上回れるか。

## Q5

戦略調整ではなく確率モデル改善が主因か。
