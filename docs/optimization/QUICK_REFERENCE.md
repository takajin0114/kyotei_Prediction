# 最適化バッチ実行 クイックリファレンス

## 🚀 即座に実行可能なコマンド

### 本番想定の最適化（50試行）
```bash
python run_full_optimization.py
```

### テスト最適化（3試行）
```bash
python test_optimization.py
```

### モジュール直接実行
```bash
python -m kyotei_predictor.tools.optimization.optimize_graduated_reward \
    --data-dir kyotei_predictor/data/raw/2024-03 \
    --n-trials 50
```

## 📊 監視コマンド

### プロセス確認
```bash
Get-Process python | Select-Object Id, ProcessName, StartTime
```

### 進行状況確認
```bash
ls optuna_logs/ | Measure-Object
```

### 結果確認
```bash
ls optuna_results/
```

## ⚙️ パラメータ一覧

### 本番想定パラメータ
| パラメータ | 値 | 説明 |
|------------|----|------|
| `n_trials` | 50 | 最適化試行回数 |
| `total_timesteps` | 100,000 | 学習ステップ数 |
| `n_eval_episodes` | 2,000 | 評価エピソード数 |
| `test_mode` | False | 本番モード |
| `data_dir` | kyotei_predictor/data/raw/2024-03 | データディレクトリ |

### テストモードパラメータ
| パラメータ | 値 | 説明 |
|------------|----|------|
| `n_trials` | 3 | 少ない試行回数 |
| `total_timesteps` | 10,000 | 短時間学習 |
| `n_eval_episodes` | 100 | 少ない評価回数 |
| `test_mode` | True | テストモード |

## 📁 ファイル構造

### 結果ファイル
```
optuna_results/
├── graduated_reward_optimization_YYYYMMDD_HHMMSS.json
└── README.md
```

### モデルファイル
```
optuna_models/
├── graduated_reward_best/best_model.zip
├── graduated_reward_checkpoints/
└── trial_X/best_model.zip
```

### ログファイル
```
optuna_logs/
├── graduated_reward/evaluations.npz
└── trial_X/evaluations.npz
```

## 🔍 結果分析

### 結果ファイル読み込み
```python
import json

with open('optuna_results/graduated_reward_optimization_YYYYMMDD_HHMMSS.json', 'r') as f:
    results = json.load(f)

print(f"最良スコア: {results['best_trial']['value']}")
print(f"最良パラメータ: {results['best_trial']['params']}")
```

### 評価結果読み込み
```python
import numpy as np

eval_data = np.load('optuna_logs/trial_X/evaluations.npz')
rewards = eval_data['rewards']
hit_rates = eval_data['hit_rates']

print(f"平均報酬: {np.mean(rewards):.4f}")
print(f"的中率: {np.mean(hit_rates)*100:.2f}%")
```

## 🛠️ トラブルシューティング

### プロセス中断
```bash
Stop-Process -Name python -Force
```

### メモリ不足
```python
# バッチサイズを小さくする
batch_size = 32  # 256から32に変更
```

### データエラー
```python
# データペア数の確認
from kyotei_predictor.pipelines.kyotei_env import KyoteiEnvManager
env = KyoteiEnvManager(data_dir="kyotei_predictor/data/raw/2024-03")
print(f"データペア数: {len(env.pairs)}")
```

## 📈 実行時間目安

| 試行回数 | 実行時間 | メモリ使用量 |
|----------|----------|--------------|
| 3（テスト） | 30分 | 2GB |
| 20（標準） | 3-4時間 | 4GB |
| 50（本番） | 8-12時間 | 4GB |

## 🎯 最適化目標

### スコア計算
```python
score = hit_rate * 100 + mean_reward / 1000
```

### 目標値
- **的中率**: 10-15%
- **平均報酬**: 正の値
- **スコア**: 8.0以上

## 📝 注意事項

1. **メモリ**: 大量のメモリを使用（4GB以上推奨）
2. **時間**: 50試行で8-12時間程度
3. **ディスク**: 約25GBの容量が必要
4. **ネットワーク**: データアクセス時の負荷

## 🔗 関連ドキュメント

- [バッチ実行ガイド](BATCH_EXECUTION_GUIDE.md) - 詳細な実行方法
- [現在の状況](CURRENT_STATUS.md) - 現在の実行状況
- [最適化ガイド](OPTIMIZATION_GUIDE.md) - 詳細な最適化手法

---

**最終更新**: 2025-07-29  
**バージョン**: 1.0