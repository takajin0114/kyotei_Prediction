# 最適化関連ドキュメント

競艇予測モデルのハイパーパラメータ最適化に関するドキュメントを管理するディレクトリです。

## 📚 ドキュメント一覧

### [BATCH_EXECUTION_GUIDE.md](BATCH_EXECUTION_GUIDE.md) ⭐ **NEW**
最適化バッチ実行の包括的なガイドです。
- 実行方法（汎用スクリプト、直接実行、Pythonコード）
- 本番想定パラメータの詳細
- 実行状況監視方法
- トラブルシューティング
- 結果分析方法

### [CURRENT_STATUS.md](CURRENT_STATUS.md) ⭐ **NEW**
現在の最適化バッチ実行状況の詳細レポートです。
- 実行中の最適化状況
- 完了済み最適化履歴
- パフォーマンス指標
- 今後の予定

### [OPTIMIZATION_GUIDE.md](OPTIMIZATION_GUIDE.md)
最適化実行の詳細ガイドです。
- 実行方法（汎用スクリプト、直接実行、Pythonコード）
- 設定オプション（テストモード、通常モード、パラメータ範囲）
- 実行例（2024年3月、1月、2月データ）
- 結果の確認方法
- トラブルシューティング
- ベストプラクティス

### [EXECUTION_EXAMPLES.md](EXECUTION_EXAMPLES.md)
具体的な実行例とサンプルコードです。
- 各種実行パターンの例
- エラー対処法
- ベストプラクティス

## 🚀 クイックスタート

### 基本的な実行

```bash
# 2024年3月データでの最適化（本番想定）
python run_full_optimization.py

# テストモードでの実行
python test_optimization.py

# モジュール直接実行
python -m kyotei_predictor.tools.optimization.optimize_graduated_reward \
    --data-dir kyotei_predictor/data/raw/2024-03 \
    --n-trials 50
```

### 他の期間データでの実行

```bash
# 2024年1月データ
python -m kyotei_predictor.tools.optimization.optimize_graduated_reward \
    --data-dir kyotei_predictor/data/raw/2024-01 \
    --n-trials 50

# 2024年2月データ
python -m kyotei_predictor.tools.optimization.optimize_graduated_reward \
    --data-dir kyotei_predictor/data/raw/2024-02 \
    --n-trials 50

# 2024年4月データ
python -m kyotei_predictor.tools.optimization.optimize_graduated_reward \
    --data-dir kyotei_predictor/data/raw/2024-04 \
    --n-trials 50
```

## 📊 最適化結果

### 保存場所

- **結果ファイル**: `optuna_results/`
- **最良モデル**: `optuna_models/graduated_reward_best/`
- **ログファイル**: `optuna_logs/`
- **スタディファイル**: `optuna_studies/`

### 結果の確認

```python
import json

# 最新の結果を読み込み
with open('optuna_results/graduated_reward_optimization_YYYYMMDD_HHMMSS.json', 'r') as f:
    results = json.load(f)

print(f"最良スコア: {results['best_trial']['value']}")
print(f"最良パラメータ: {results['best_trial']['params']}")
```

## 🔧 設定ファイル

### Optuna設定

- **ファイル**: `kyotei_predictor/config/optuna_config.json`
- **内容**: ハイパーパラメータ範囲、最適化設定

### 環境設定

- **データディレクトリ**: `kyotei_predictor/data/raw/YYYY-MM/`
- **モデル保存**: `optuna_models/`
- **結果保存**: `optuna_results/`

## 📈 実行状況

### 現在実行中（2025-07-29）

| 項目 | 詳細 |
|------|------|
| **データ期間** | 2024年3月 |
| **データペア数** | 4,221 |
| **試行回数** | 50（本番想定） |
| **実行モード** | 本番モード |
| **スタディ名** | `graduated_reward_optimization_202403_full` |
| **開始時刻** | 2025-07-29 22:51:24 |
| **実行時間** | 進行中（予想8-12時間） |

### 完了済み最適化

| 期間 | 試行回数 | 最良スコア | 実行日 |
|------|----------|------------|--------|
| 2024年3月（テスト） | 3 | 6.107 | 2025-07-29 |
| 2024年3月（本格） | 30 | 8.3606 | 2025-07-29 |
| 2024年3月（本番想定） | 50 | 実行中 | 2025-07-29 |

### 今後の予定

- [ ] 2024年1月データでの最適化
- [ ] 2024年2月データでの最適化
- [ ] 2024年4月データでの最適化
- [ ] 複数月データでの統合最適化

## 🛠️ 監視・管理

### リアルタイム監視

```bash
# プロセス確認
Get-Process python | Select-Object Id, ProcessName, StartTime

# 進行状況確認
ls optuna_logs/ | Measure-Object

# 結果確認
ls optuna_results/
```

### 自動監視スクリプト

```python
import os
import time
from datetime import datetime

def monitor_optimization():
    while True:
        if os.system('Get-Process python >nul 2>&1') == 0:
            log_dirs = [d for d in os.listdir('optuna_logs') if d.startswith('trial_')]
            print(f"[{datetime.now()}] 進行中... 完了試行: {len(log_dirs)}")
        else:
            print(f"[{datetime.now()}] 完了")
            break
        time.sleep(60)
```

## 🔗 関連ドキュメント

- [バッチ実行ガイド](BATCH_EXECUTION_GUIDE.md) - 詳細な実行方法
- [現在の状況](CURRENT_STATUS.md) - 現在の実行状況
- [最適化実行ガイド](OPTIMIZATION_GUIDE.md) - 詳細な最適化手法
- [現在の状況サマリー](../CURRENT_STATUS_SUMMARY.md) - プロジェクト全体の状況
- [API仕様書](../API_SPECIFICATION.md) - API仕様
- [運用ガイド](../operations/README.md) - 運用に関するガイド

## 📝 更新履歴

- **2025-07-29**: バッチ実行ガイドの作成
- **2025-07-29**: 現在の状況ドキュメントの作成
- **2025-07-29**: READMEの更新
- **2025-01-27**: 最適化ガイドの作成
- **2025-01-27**: 汎用最適化スクリプトの実装
- **2025-01-27**: ドキュメント構造の整理

---

**最終更新**: 2025-07-29  
**バージョン**: 2.0