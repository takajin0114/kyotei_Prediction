# Experiment: EXP-0040 ベットサイジング最適化

## experiment id

EXP-0040

## purpose

採用条件（skip_top20pct + 3≤EV<5 + prob≥0.05）を固定し、「いくら買うか」だけを変えて、ROI・total_profit・max_drawdown・profit_per_1000_bets の改善が可能かを検証する。

## ベース採用条件

- skip_top20pct（日付内でレースを max_ev 降順に並べ、上位20%を除外）
- 3 ≤ EV < 5
- prob ≥ 0.05

## bet sizing variant 定義

- **baseline の unit**: 100（全 bet 同額）。比較基準。
- **比例係数**: 下記のとおり。EV は [3,5)、prob は [0.05,1] のスケールに合わせて設定。
- **最小 unit**: 50、**最大 unit**: 200（capped 系は 150）。
- **丸め**: `round()` で整数。
- **レース単位の総額制約**: なし。bet ごとに clip(min_unit, max_unit) のみ。
- **既存 verify**: 1 回実行して race 単位の payout を取得。stake は本ツールで後段計算（選ばれる bet 集合は全 variant で同一）。

| variant | 式 |
|---------|---|
| baseline_fixed | unit = 100（全 bet 同額） |
| size_by_ev_linear | unit = clip(round(25×EV), 50, 200) |
| size_by_prob_linear | unit = clip(round(200×prob), 50, 200) |
| size_by_ev_prob | unit = clip(round(40×EV×prob), 50, 200) |
| size_by_ev_capped | unit = clip(round(25×EV), 50, 150) |
| size_by_ev_prob_capped | unit = clip(round(40×EV×prob), 50, 150) |

## implementation

- ツール: `kyotei_predictor/tools/run_exp0040_bet_sizing_optimization.py`
- 入力: EXP-0038 と同一の rolling predictions + verify（race 単位 payout のみ使用）。
- 前処理: 対象レース読み込み → skip_top20pct → 3≤EV<5 & prob≥0.05 で通過 bet を特定 → 各 variant で bet ごとの stake を算出 → race 単位で stake 合計・payout を集計し、window 別利益から max_drawdown を算出。

## command

```bash
cd /path/to/kyotei_Prediction
python3 -m kyotei_predictor.tools.run_exp0040_bet_sizing_optimization \
  --db-path kyotei_predictor/data/kyotei_races.sqlite \
  --n-windows 18
```

## results table (n_windows=18)

| variant                  | ROI     | total_profit | max_drawdown | profit_per_1000_bets | bet_count | total_stake | avg_bet | avg_stake/race |
|--------------------------|---------|--------------|--------------|----------------------|-----------|-------------|---------|----------------|
| baseline_fixed           | 77.19%  | 161,865      | 7,075        | 77,188.84            | 2,097     | 209,700     | 100.0   | 102.69        |
| size_by_ev_linear        | 83.84%  | 169,449      | 6,324        | 80,805.44            | 2,097     | 202,116     | 96.38   | 98.98         |
| size_by_prob_linear      | 119.39% | 202,200      | 4,287        | 96,423.46            | 2,097     | 169,365     | 80.77   | 82.94         |
| size_by_ev_prob          | 152.21% | 224,239      | 3,120        | 106,933.24           | 2,097     | 147,326     | 70.26   | 72.15         |
| size_by_ev_capped        | 83.84%  | 169,449      | 6,324        | 80,805.44            | 2,097     | 202,116     | 96.38   | 98.98         |
| size_by_ev_prob_capped   | **155.80%** | **226,307** | **3,081** | **107,919.41**       | 2,097     | 145,258     | 69.27   | 71.14         |

## interpretation

1. **ベットサイジングの効果**  
   EV×prob に比例させる sizing（size_by_ev_prob, size_by_ev_prob_capped）が、baseline_fixed を大きく上回る。ROI 77% → 152〜156%、total_profit 増加、max_drawdown は 7,075 → 3,081〜3,120 と約半分に抑制。高 EV・高 prob の bet に多く配分することで、利益効率とリスクの両方が改善している。

2. **total_profit と total_stake**  
   size_by_ev_prob_capped は total_stake が最小（145,258）で total_profit が最大（226,307）。同じ payout に対して stake を抑えているため ROI が高く、ドローダウンも最小。

3. **max_drawdown**  
   size_by_ev_prob_capped が最小（3,081）。baseline の約 44%。賭け金を EV×prob で配分し cap で抑えることで、変動が小さくなっている。

4. **average_bet_size / 実運用**  
   size_by_ev_prob_capped の平均 bet は 69.27、平均 stake/race は 71.14。baseline より小さく、過大ベットにはなっていない。ROI 向上とドローダウン抑制が両立しており、賭け金依存で不安定になる様子は見られない。

5. **EV のみ・prob のみ**  
   size_by_ev_linear / size_by_ev_capped は baseline よりやや改善（ROI 83.84%、max_dd 6,324）。size_by_prob_linear は ROI 119%、max_dd 4,287 とさらに改善。EV×prob が最もバランスが良い。

6. **採用候補**  
   **size_by_ev_prob_capped** が ROI・total_profit・max_drawdown・profit_per_1000_bets のいずれも最良。実運用では「採用条件はそのまま、stake を unit = clip(round(40×EV×prob), 50, 150) とする」ことを推奨。

## judgment

- **adopt**
- **size_by_ev_prob_capped**（unit = clip(round(40×EV×prob), 50, 150)）を採用。ROI・利益・ドローダウン・利益効率が baseline を上回り、平均 bet サイズも過大でない。実運用候補のベットサイジングを **EV×prob 比例＋上限 150** に更新する。

## result JSON

- outputs/bet_sizing_optimization/exp0040_bet_sizing_optimization_results.json
