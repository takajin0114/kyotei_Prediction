# Experiment: EXP-0027 EV percentile ROI analysis

## experiment id

EXP-0027

## purpose

EXP-0026 の結果を踏まえ、EV percentile 別 ROI 分析を行い、「どの EV 帯が利益源で、どの EV 帯が損失源か」を特定する。selected bets を持つレースをレース内最大 EV 順に並べ、top 1% / 5% / 10% / 20% / 50% / full の帯ごとに ROI・total_profit・max_drawdown・profit_per_1000_bets・bet_count を集計する。

## background

- モデルが「高 EV」と判断したレースで実際の成績がどうか検証する。
- EV 帯ごとの成績を把握し、cutoff（高 EV のみ／低 EV 除外など）の候補を検討する。

## command

```bash
PYTHONPATH=. python3 -m kyotei_predictor.tools.analyze_ev_percentile_roi \
  --db-path kyotei_predictor/data/kyotei_races.sqlite \
  --n-windows 12 \
  --output-dir outputs/confidence_weighted_sizing_experiments
```

## results table

| strategy_id | band     | ROI     | total_profit | max_drawdown | profit_per_1000_bets | bet_count |
|-------------|----------|---------|--------------|--------------|----------------------|-----------|
| exp0015     | top_1pct | -100.0% | -13,200      | 13,200       | -100,000             | 132       |
| exp0015     | top_5pct | -54.61% | -38,770      | 41,860       | -54,605.63           | 710       |
| exp0015     | top_10pct| -55.74% | -80,650      | 83,440       | -55,736.01           | 1,447     |
| exp0015     | top_20pct| -45.87% | -133,300     | 134,090      | -45,870.61           | 2,906     |
| exp0015     | top_50pct| -20.65% | -151,730     | 152,450      | -20,654.78           | 7,346     |
| exp0015     | full     | -14.68% | -215,840     | 265,880      | -14,678.0            | 14,705    |
| exp0013     | top_1pct | -100.0% | -13,500      | 13,500       | -100,000             | 135       |
| exp0013     | top_5pct | -55.54% | -40,270      | 43,360       | -55,544.83           | 725       |
| exp0013     | top_10pct| -56.49% | -83,150      | 85,940       | -56,487.77           | 1,472     |
| exp0013     | top_20pct| -46.34% | -136,970     | 137,560      | -46,336.27           | 2,956     |
| exp0013     | top_50pct| -20.62% | -154,080     | 154,800      | -20,620.99           | 7,472     |
| exp0013     | full     | -13.81% | -207,010     | 267,160      | -13,806.19           | 14,994    |
| exp0007     | top_1pct | -100.0% | -13,900      | 13,900       | -100,000             | 139       |
| exp0007     | top_5pct | -51.64% | -38,370      | 41,460       | -51,641.99           | 743       |
| exp0007     | top_10pct| -57.72% | -87,450      | 90,240       | -57,722.77           | 1,515     |
| exp0007     | top_20pct| -42.63% | -129,600     | 130,190      | -42,631.58           | 3,040     |
| exp0007     | top_50pct| -21.67% | -166,450     | 167,070      | -21,670.36           | 7,681     |
| exp0007     | full     | -14.54% | -224,090     | 279,480      | -14,544.69           | 15,407    |

## interpretation

- **損失源**: 高 EV 帯（top 1%〜20%）が明確な損失源。top 1% は ROI -100%（全敗に近い）、top 5〜20% は ROI -42%〜-56%。モデルが「最も期待値が高い」と判断したレースほど実績が悪い（過信・キャリブレーション不足の可能性）。
- **相対的にマシな帯**: full（全レース）が 3 戦略とも各帯の中で最も ROI が良い（-13.81%〜-14.68%）。top 50% は -20% 台。つまり「高 EV だけ」に絞るとかえって悪化し、全体を含めた方が相対的に損失が小さくなる。
- **利益源**: 全帯で total_profit は負。利益源となる EV 帯は存在せず、いずれも損失。高 EV 帯の損失が特に大きい。

## best cutoff candidate

- **現状**: 全帯で赤字のため「この帯だけ採用」する利益源 cutoff はない。
- **有望な次の検証**: 「高 EV 帯を除外する」cutoff（例: top 10% または top 20% を skip し、残り 90% または 80% のみ bet）で overall ROI が full より改善するか検証する実験が候補。本分析のみでは adopt する cutoff はなし。**hold**（次の実験で top-X% 除外を試す）。

## conclusion

- EV percentile 分析により、**高 EV 帯（top 1〜20%）が損失の主因**であることを特定した。
- 全帯で利益源はなく、full が相対的に最良 ROI。高 EV に絞るほど ROI が悪化する構造。
- 採用判断: **hold**。cutoff による採用は見送り。次の実験で「高 EV 帯除外」による ROI 改善の可否を検証する。

## next action

- 次の実験候補: top 10% または top 20% を skip する戦略（EV percentile 下位 90% または 80% のみ bet）を実装し、n_w=12 で full と比較する。
- キャリブレーション改善や高 EV 帯の特徴分析は別軸で検討可能。
