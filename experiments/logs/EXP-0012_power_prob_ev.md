# Experiment: EXP-0012 EV スコア再設計（top_n_ev_power_prob）

## experiment id

EXP-0012

## purpose

EV スコアの再設計により ROI 改善を図る。従来の expected_roi = pred_prob * odds に代え、**EV_adj = (pred_prob ** alpha) * odds** でスコア化し、ev_threshold 以上から top_n を選抜する戦略「top_n_ev_power_prob」を評価する。alpha=1.0 のとき従来の top_n_ev と一致。

## configuration

- model: xgboost, calibration: sigmoid, features: extended_features
- n_windows: 12, seed: 42
- tool: `kyotei_predictor.tools.run_power_prob_experiment`
- output: outputs/power_prob_experiments/exp0012_power_prob_results.json

### ベースライン

- top_n_ev: top_n=3, ev_threshold=1.18（現行ベスト -14.54%）

### top_n_ev_power_prob sweep

- alpha: 0.7, 0.8, 0.9, 1.0, 1.1
- top_n: 2, 3
- ev_threshold: 1.15, 1.17, 1.18, 1.19, 1.20

## command

```bash
PYTHONPATH=. python3 -m kyotei_predictor.tools.run_power_prob_experiment \
  --db-path kyotei_predictor/data/kyotei_races.sqlite \
  --n-windows 12 \
  --seed 42
```

## results

結果の詳細は **outputs/power_prob_experiments/exp0012_power_prob_results.json** を参照。各条件で strategy, alpha, top_n, ev_threshold, overall_roi_selected, total_selected_bets, hit_rate_rank1_pct, baseline_diff_roi を記録。

### Results table（実行後に JSON から転記）

| strategy_name | alpha | top_n | ev_threshold | overall_roi_selected | total_selected_bets | hit_rate_rank1_pct |
|---------------|-------|-------|--------------|---------------------|---------------------|---------------------|
| （exp0012_power_prob_results.json の results を参照） |

## baseline comparison

- ベースライン top_n_ev top_n=3 ev=1.18: **-14.54%**（n_w=12）
- top_n_ev_power_prob 全条件でベースラインを**下回った**。最良は powerprob_a1x1_top3_ev120 の **-26.28%**（diff=－11.74%pt）。EV_adj 再設計では現行ベースラインを超える組み合わせはなし。

## conclusion

- **実行完了**: 2026-03-09 17:29 JST 頃。結果 JSON: outputs/power_prob_experiments/exp0012_power_prob_results.json。
- **結論**: top_n_ev_power_prob は全グリッドでベースライン（-14.54%）を上回らず**採用見送り**。alpha=1.1, top_n=3, ev=1.20 が power_prob 内では最良（-26.28%）だが、ベースラインより約 11.7%pt 悪化。

## learning

- alpha < 1 で確率を圧縮すると低確率候補の EV_adj が相対的に下がり、高確率に寄った選抜になる。alpha > 1 ではその逆。
- alpha=1.0 は従来の expected_roi と同一のため、既存 top_n_ev と整合する。
- 本実験では (prob^alpha)*odds の単純な再設計では ROI 改善に至らなかった。別の EV 設計や選抜ロジックの検討が必要。

## next action

- ベースライン（top_n_ev 3/1.18）を維持。別の EV 設計（閾値の細分化、他スコア）や別軸の実験へ。
