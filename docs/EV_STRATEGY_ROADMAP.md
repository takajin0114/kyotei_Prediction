# EV 戦略ロードマップ

買い目選定の EV（期待値）戦略について、現在の実装と将来の本格実装の整理。

---

## 現在の EV

- **betting_selector の ev 戦略**: `strategy=ev` で利用可能。
- **スコアベースの簡易実装の可能性**: オッズが取得できない、または EV 計算に必要な要素が揃っていない場合、**スコア（probability）と閾値**で代用している可能性がある。
- **expected_value フィールド**: 予測 JSON の `all_combinations[].expected_value` は、B案では最小実装として **0 固定**になっている場合がある。A案でもオッズ未使用時は 0 の可能性あり。

確認方法: `betting_selector.select_bets(..., strategy="ev")` の内部で、オッズを参照しているか・EV を prob × payout で計算しているかをコードで確認する。

---

## 将来の EV（本格実装）

**EV = probability × payout - bet**

- **probability**: その 3連単が的中する確率（モデル出力の calibration が理想）
- **payout**: オッズ（倍率）× 購入単価。オッズはレース前のものを使う想定。
- **bet**: 1点あたりの購入額（例: 100円）

EV > 0 の組み合わせだけ購入、または EV が閾値以上のものを選ぶ。

---

## 必要な要素

| 要素 | 説明 |
|------|------|
| **オッズ取得** | 検証用の race_data と同じ日・会場・レースの `odds_data_*.json` を用意する。本番ではレース前オッズを取得する導線が必要。 |
| **probability calibration** | モデルが出す確率が、実際の的中率と一致していると ROI が安定する。現状はスコアをそのまま確率として扱っているため、calibration（Platt scaling や isotonic regression 等）の検討余地あり。 |
| **bet size** | 1点 100円固定か、Kelly 基準などで変動させるか。まずは固定でよい。 |

---

## 実装の進め方

1. **現状確認**: `utils/betting_selector.py` の ev 戦略で、オッズをどこまで使っているか・expected_value が 0 のときのフォールバックを確認する。
2. **オッズ接続**: 予測時に `odds_data_*.json` を読み、`all_combinations` の各 combination に対応するオッズを付け、`expected_value = probability * (odds * unit_bet) - unit_bet` を計算する。
3. **B案での EV 出力**: baseline_predict の `scores_to_all_combinations` の後、オッズがあれば expected_value を上書きする。
4. **calibration**: 必要に応じて、学習済みモデルの出力を calibration 用データで補正する。
