# 最適化関連ドキュメント

競艇予測モデルのハイパーパラメータ最適化に関するドキュメントを管理するディレクトリです。

## 📚 ドキュメント一覧

### [OPTIMIZATION_GUIDE.md](OPTIMIZATION_GUIDE.md)
最適化実行の包括的なガイドです。
- 実行方法（汎用スクリプト、直接実行、Pythonコード）
- 設定オプション（テストモード、通常モード、パラメータ範囲）
- 実行例（2024年3月、1月、2月データ）
- 結果の確認方法
- トラブルシューティング
- ベストプラクティス

### [FAST_MODE_IMPLEMENTATION_SUMMARY.md](FAST_MODE_IMPLEMENTATION_SUMMARY.md)
高速モード実装の詳細サマリーです。
- 高速モードの実装内容と効果
- パラメータ設定の比較
- 実行時間の改善効果
- 使用方法と技術的詳細

## 🚀 クイックスタート

### 実行前の準備

**重要**: 以下のコマンドは、プロジェクトルート（`kyotei_Prediction`ディレクトリ）から実行してください。

```bash
# 現在のディレクトリを確認
pwd
# 出力例: C:\Users\takaj\Desktop\app\kyotei_Prediction\kyotei_Prediction

# 仮想環境をアクティベート
.\venv\Scripts\Activate.ps1
```

### 基本的な実行

```bash
# 2024年3月データでの最適化
python kyotei_predictor/tools/optimization/optimize_graduated_reward.py --year-month 2024-03

# テストモードでの実行
python kyotei_predictor/tools/optimization/optimize_graduated_reward.py --year-month 2024-03 --test-mode

# 試行回数を指定
python kyotei_predictor/tools/optimization/optimize_graduated_reward.py --year-month 2024-03 --n-trials 50

# 高速モードでの実行（開発・テスト用）
python kyotei_predictor/tools/optimization/optimize_graduated_reward.py --year-month 2024-03 --fast-mode --n-trials 5
```

### 他の期間データでの実行

```bash
# 2024年1月データ
python kyotei_predictor/tools/optimization/optimize_graduated_reward.py --year-month 2024-01

# 2024年2月データ
python kyotei_predictor/tools/optimization/optimize_graduated_reward.py --year-month 2024-02

# 2024年4月データ
python kyotei_predictor/tools/optimization/optimize_graduated_reward.py --year-month 2024-04
```

## 📊 最適化結果

### 保存場所

- **結果ファイル**: `optuna_results/`
- **最良モデル**: `optuna_models/graduated_reward_best/`
- **ログファイル**: `optuna_logs/`

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

### 完了済み最適化

| 期間 | 試行回数 | 最良スコア | 実行日 |
|------|----------|------------|--------|
| 2024年3月（テスト） | 3 | 6.107 | 2025-07-29 |
| 2024年3月（本格） | 20 | 実行中 | 2025-07-29 |

### 高速モードの効果

| モード | 1試行あたり | 5試行合計 | 改善率 |
|--------|-------------|-----------|--------|
| **通常モード** | 2-3時間 | 10-15時間 | - |
| **高速モード** | **5-10分** | **25-50分** | **約20-30倍高速** |

### 今後の予定

- [ ] 2024年1月データでの最適化
- [ ] 2024年2月データでの最適化
- [ ] 2024年4月データでの最適化
- [ ] 複数月データでの統合最適化

## 🔗 関連ドキュメント

- [最適化実行ガイド](OPTIMIZATION_GUIDE.md) - 詳細な実行方法
- [現在の状況サマリー](../CURRENT_STATUS_SUMMARY.md) - プロジェクト全体の状況
- [API仕様書](../API_SPECIFICATION.md) - API仕様
- [運用ガイド](../operations/README.md) - 運用に関するガイド

## 📝 更新履歴

- **2025-01-27**: 高速モード実装完了
- **2025-01-27**: 最適化ガイドの作成
- **2025-01-27**: 汎用最適化スクリプトの実装
- **2025-01-27**: ドキュメント構造の整理

---

**最終更新**: 2025-01-27  
**バージョン**: 1.0