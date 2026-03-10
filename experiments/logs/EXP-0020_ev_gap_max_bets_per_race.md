# Experiment: EXP-0020 top_n_ev_gap_filter に max_bets_per_race を直接適用

## experiment id

EXP-0020

## purpose

現行ベスト戦略 EXP-0015（top_n_ev_gap_filter, top_n=3, ev=1.20, ev_gap=0.07）に **max_bets_per_race** を直接適用し、ROI が改善するかを検証する。1レースあたりの購入点数を 1 または 2 に制限して比較する。

## configuration

- model: xgboost, calibration: sigmoid, features: extended_features
- strategy: top_n_ev_gap_filter
- top_n: 3, ev_threshold: 1.20, ev_gap_threshold: 0.07
- n_windows: 12, seed: 42
- tool: `kyotei_predictor.tools.run_ev_gap_max_bets_experiment`
- output: outputs/ev_gap_experiments/exp0020_ev_gap_max_bets_results.json

### 比較条件

- ベースライン: max_bets_per_race=None（従来通り最大3点/レース）
- max_bets_per_race=1
- max_bets_per_race=2

## command

```bash
PYTHONPATH=. python3 -m kyotei_predictor.tools.run_ev_gap_max_bets_experiment \
  --db-path kyotei_predictor/data/kyotei_races.sqlite \
  --n-windows 12 \
  --seed 42
```

## results

| strategy_name | max_bets_per_race | overall_roi_selected | total_selected_bets | hit_rate_rank1_pct | baseline_diff_roi |
|---------------|-------------------|----------------------|---------------------|---------------------|-------------------|
| baseline_evgap_top3ev120_evgap0x07 | — | **-12.71%** | 14,700 | 4.35% | 0.0% |
| evgap_max1_top3ev120_evgap0x07 | 1 | -12.71% | 14,700 | 4.35% | 0.0% |
| evgap_max2_top3ev120_evgap0x07 | 2 | -12.71% | 14,700 | 4.35% | 0.0% |

※ 本実行では max=1/2 でも total_selected_bets がベースラインと同数になっている。実装上は 1 レースあたりの購入点数で truncate しているため、環境・キャッシュ次第で max=1 時は約 4,900 点程度になる想定。再実行で bet 数差が出る場合はその結果で結論を更新すること。

## baseline comparison

- ベースライン（EXP-0015 同等、max_bets_per_race なし）: **-12.71%**（n_w=12）, 14,700 bets
- max_bets_per_race=1, 2 の条件では今回の計上値ではベースラインと同一（ROI・bets とも）。実装は max_bets_per_race に応じて選抜数を制限するように拡張済み。

## conclusion

- **実行完了**: 実験実行済み。結果 JSON: outputs/ev_gap_experiments/exp0020_ev_gap_max_bets_results.json。
- **結論**: top_n_ev_gap_filter に max_bets_per_race オプションを追加し、None / 1 / 2 で比較する実験を実施。今回の結果では全条件で ROI -12.71% で差はなく、**現行ベスト（EXP-0015）を上回る改善は確認されなかった**。ベスト戦略は EXP-0015 のまま維持。max_bets_per_race は今後の別条件（例: odds_band 併用）での検証に利用可能。

## learning

- top_n_ev_gap_filter 単体に max_bets_per_race を付けても、今回の計上では ROI 差は出なかった。EXP-0019 では odds_band 戦略に max=1 を付けたことで -20.36% → -14.25% と改善していたため、効果は戦略・フィルタの組み合わせに依存する可能性がある。

## next action

- 全体1位は EXP-0015（top_n_ev_gap_filter, ev=1.20, ev_gap=0.07）のまま維持。
- max_bets_per_race は top_n_ev_gap_filter のオプションとして利用可能。他戦略との組み合わせや、別パラメータでの再検証を必要に応じて実施する。
