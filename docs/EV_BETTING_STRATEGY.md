# EV ベッティング戦略モジュール

EV 戦略を本格的な betting system として拡張した内容の整理。
baseline B + calibration=sigmoid を基準とする。

---

## 1. モジュール構成

| ファイル | 役割 |
|----------|------|
| `kyotei_predictor/betting/expected_value.py` | EV（期待リターン）計算。`expected_roi(probability, odds)`、`ev_above_threshold(...)` |
| `kyotei_predictor/betting/bet_sizing.py` | ベットサイズ。fixed / kelly_full / kelly_half。`kelly_fraction(p, odds)`、`compute_stake(...)` |
| `kyotei_predictor/betting/bankroll_simulation.py` | 資金シミュレーション。`simulate_bankroll(bets, ...)` → bankroll_curve, max_drawdown, sharpe_ratio, profit_factor。`build_bet_list_from_verify(predictions, details)` で検証結果から賭けリストを組み立て。 |

---

## 2. EV threshold sweep

### 目的

閾値 1.02, 1.05, 1.08, 1.10, 1.12, 1.15, 1.20 で B top_n=5 を比較し、最適な EV 閾値を探索する。

### 記録指標

- ROI（%）
- hit_rate（%）
- bet_count
- profit
- mean_odds_placed（購入した点の平均オッズ）

### 実行方法

```bash
PYTHONPATH=. python3 kyotei_predictor/tools/ev_threshold_sweep.py
```

### 結果保存

- **logs/ev_threshold_sweep.json**

### EV threshold スイープ結果（要実行して追記）

| ev_threshold | roi_pct | hit_rate_pct | bet_count | profit | mean_odds_placed |
|--------------|---------|--------------|-----------|--------|------------------|
| 1.02 | （実行後に追記） | | | | |
| 1.05 | | | | | |
| 1.08 | | | | | |
| 1.10 | | | | | |
| 1.12 | | | | | |
| 1.15 | | | | | |
| 1.20 | | | | | |

- **最適閾値（暫定）**: スイープ実行後、ROI と bet_count のバランスで決定する。

---

## 3. Kelly betting 比較

### 方式

- **fixed**: 1 点あたり 100 円固定。
- **kelly_full**: 賭け率 f = (b×p - q) / b（b = odds - 1, p = 予測確率, q = 1-p）。stake = bankroll × f。
- **kelly_half**: stake = bankroll × 0.5 × f。

### 比較方法

rolling validation（4 window）で fixed と kelly_half の両方をシミュレーションし、同一の選定結果（selected_bets）に対して資金曲線・max_drawdown・Sharpe・profit_factor を比較する。

### 結果

- **logs/rolling_ev_strategy_compare.json** の `aggregate_by_strategy` に fixed / kelly_half の mean_max_drawdown, mean_sharpe_ratio を記録。

### Kelly 比較結果（要実行して追記）

| 戦略 | fixed mean_drawdown | fixed mean_sharpe | kelly_half mean_drawdown | kelly_half mean_sharpe |
|------|---------------------|-------------------|--------------------------|------------------------|
| B top_n=5 EV>1.10 | | | | |
| B top_n=5 EV>1.15 | | | | |

---

## 4. Bankroll simulation

### 入力

- **predictions**: 予測リスト（selected_bets, all_combinations に ratio / probability あり）
- **verify details**: `run_verify(..., evaluation_mode="selected_bets")` の詳細（actual 等）

または

- **bets**: `[{"stake", "odds", "hit", "probability"?}, ...]` のリスト。`build_bet_list_from_verify(predictions, details)` で生成可能。

### 出力

- **bankroll_curve**: 各賭け後の資金のリスト
- **max_drawdown**: 最大ドローダウン（円）
- **sharpe_ratio**: 1 賭けあたりリターンの Sharpe（簡易）
- **profit_factor**: 総利益 / 総損失
- **bet_count**, **total_stake**, **total_payout**, **final_bankroll**, **roi_pct**

### 利用例

```python
from kyotei_predictor.betting.bankroll_simulation import (
    build_bet_list_from_verify,
    simulate_bankroll,
)

bets = build_bet_list_from_verify(predictions, verify_details, fixed_stake=100.0)
result_fixed = simulate_bankroll(bets, initial_bankroll=100_000, bet_sizing="fixed")
result_kelly = simulate_bankroll(bets, initial_bankroll=100_000, bet_sizing="kelly_half")
```

---

## 5. Rolling validation 拡張（EV 戦略比較）

### 条件

- train 15日 / test 7日 / 4 window（従来と同じ）
- calibration = sigmoid
- 戦略: B top_n=3, B top_n=5 EV>1.10, B top_n=5 EV>1.15

### 比較軸

- EV threshold（1.10, 1.15）
- bet sizing（fixed, kelly_half）

### 出力指標

- ROI（%）
- max_drawdown
- Sharpe ratio
- profit factor

### 実行方法

```bash
PYTHONPATH=. python3 kyotei_predictor/tools/rolling_ev_strategy_compare.py
```

### 結果保存

- **logs/rolling_ev_strategy_compare.json**

---

## 6. 最終推奨戦略（要スイープ・rolling 実行後に更新）

- **calibration**: sigmoid（基準）
- **EV threshold**: スイープ結果に基づき 1.10 または 1.15 を推奨（現時点は 1.10 / 1.15 の両方で rolling 改善を確認済み）。
- **bet sizing**: fixed をデフォルト推奨。リスク抑制を重視する場合は kelly_half を比較の上で検討。
- **選定**: B top_n=5、expected_roi >= 閾値 の組み合わせのみ購入。

実行後、本セクションに「EV threshold 最適値」「fixed vs Kelly の推奨」を追記する。
