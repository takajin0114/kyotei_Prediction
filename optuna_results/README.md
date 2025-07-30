# 最適化結果ディレクトリ

このディレクトリには、強化学習モデルのハイパーパラメータ最適化の結果が保存されます。

## ファイル形式

- **graduated_reward_optimization_YYYYMMDD_HHMMSS.json**: 最適化実行結果
  - 最良パラメータ
  - 全試行の結果
  - 実行時刻・設定情報

## 最新結果

- `graduated_reward_optimization_20250725_145817.json`: 2025年7月25日実行
  - 最良スコア: -0.01
  - 試行回数: 10回
  - データ: 2024年4月分

## 使用方法

```python
import json

# 結果ファイルの読み込み
with open('graduated_reward_optimization_20250725_145817.json', 'r') as f:
    results = json.load(f)

# 最良パラメータの取得
best_params = results['best_trial']['params']
best_score = results['best_trial']['value']
```

## 注意事項

- このディレクトリは `.gitignore` で除外されています
- 大容量ファイルのため、リポジトリには含まれません
- 結果のバックアップは別途管理してください 