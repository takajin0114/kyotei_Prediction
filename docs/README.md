# 競艇予測システム - ドキュメント

## 📋 目次

### 📊 プロジェクト概要
- [CURRENT_STATUS_SUMMARY.md](CURRENT_STATUS_SUMMARY.md) - 現在の状況サマリー
- [config_usage_guide.md](config_usage_guide.md) - 設定ファイル使用ガイド
- [WORK_COMPLETION_SUMMARY_20250127.md](WORK_COMPLETION_SUMMARY_20250127.md) - 作業完了サマリー（2025-01-27）

### 🚀 最新の改善策（2025年1月実装完了）
- [trifecta_improvement_strategy.md](trifecta_improvement_strategy.md) - 3連単的中率改善戦略
- [improvement_implementation_summary.md](improvement_implementation_summary.md) - 改善策実装状況
- [test_results_summary.md](test_results_summary.md) - テスト結果サマリー

### 🔧 開発者向けドキュメント
- [test_results_summary.md](test_results_summary.md) - テスト結果サマリー

### 📁 運用ドキュメント
- [operations/](operations/) - 運用関連ドキュメント

### 📋 要件ドキュメント
- [requirements/](requirements/) - 要件関連ドキュメント

### 🌐 Web表示ドキュメント
- [web_display/](web_display/) - Web表示関連ドキュメント

---

## 🚀 実行方法

### 基本テスト実行
```bash
# 全テスト実行
.\run_tests.bat

# クイックテスト
.\run_quick_test.bat

# 個別テスト（tests/improvement_tests/ディレクトリ内）
cd tests\improvement_tests
.\run_all_tests.bat
```

### 本番想定パイプライン実行
```bash
# 基本パイプライン（オプション付き）
.\run_learning_pipeline.bat --test
.\run_learning_pipeline.bat --minimal --phase 1
.\run_learning_pipeline.bat --phase 2 --timesteps 100000

# 高度パイプライン（詳細オプション）
.\run_advanced_learning.bat --test
.\run_advanced_learning.bat --minimal --phase 1
.\run_advanced_learning.bat --production --phase 2 --timesteps 100000

# ヘルプ表示
.\run_learning_pipeline.bat --help
.\run_advanced_learning.bat --help
```

### オプション詳細

#### 実行モード
- `--test` - テストモード（短時間実行）
- `--minimal` - 最小限モード（超短時間実行）
- `--production` - 本番モード（長時間実行）

#### 実行制御
- `--phase PHASE` - 実行するPhase（1-4, all）
- `--data-dir DIR` - データディレクトリ
- `--timesteps N` - 学習ステップ数
- `--eval-episodes N` - 評価エピソード数
- `--n-trials N` - 試行回数

#### オプション機能
- `--cleanup` - 実行前のクリーンアップ（デフォルト有効）
- `--no-cleanup` - クリーンアップを無効化
- `--no-monitoring` - 監視機能を無効化
- `--no-backup` - バックアップ機能を無効化

---

## 🎯 プロジェクト概要

競艇予測システムは、強化学習を用いた競艇の3連単予測システムです。

### 主要機能
- **段階的報酬設計**: 的中率1.70%（理論値の約2倍）
- **最適化システム**: Optunaによる自動最適化
- **監視システム**: リアルタイム進捗監視
- **評価システム**: 客観的性能評価
- **統合ユーティリティ**: 標準化された設定管理・ログ機能・エラーハンドリング
- **🚀 最新**: 3連単的中率改善策（Phase 1-4）実装完了

### 技術スタック
- **強化学習**: Stable-Baselines3 (PPO)
- **最適化**: Optuna
- **データ処理**: pandas, numpy
- **可視化**: matplotlib
- **統合ユーティリティ**: カスタム設定管理・ログ機能・エラーハンドリング

### 現在の成果
- **的中率**: 1.70%（理論値0.83%の約2倍）
- **学習効率**: 16.2倍
- **報酬安定性**: 52.5%
- **総合スコア**: 40.5/100

### 🚀 最新の改善効果（2025年1月実装）
- **的中率目標**: 3.5% → 4.0%以上（+0.5%以上）
- **報酬の安定化**: 的中時の報酬強化、部分的中の報酬化
- **学習効率の向上**: より深い学習、アンサンブル効果

---

## 🚀 最新の改善策（Phase 1-4）

### Phase 1: 報酬設計の最適化 ✓
- **的中報酬の強化**: 1.2 → 1.5倍
- **部分的中の報酬化**: 2着的中を0 → +10
- **ペナルティの緩和**: 1着的中を-20 → -10, 不的中を-100 → -80

### Phase 2: 学習時間の延長 ✓
- **total_timesteps**: 100000 → 200000（2倍に延長）
- **n_eval_episodes**: 2000 → 5000（2.5倍に延長）
- **ハイパーパラメータ範囲の調整**: より細かい調整が可能

### Phase 3: アンサンブル学習の導入 ✓
- **EnsembleTrifectaModelクラス**: 複数PPOモデルの組み合わせ
- **重み付き投票システム**: 予測精度の向上
- **モデル多様性の確保**: より安定した予測

### Phase 4: 継続的学習の実装 ✓
- **ContinuousLearningSystemクラス**: 既存モデルの継続学習
- **AutoUpdateSystemクラス**: 自動更新システム
- **学習履歴の記録**: 性能推移の追跡

---

## 🏗️ 新しいアーキテクチャ（v4.1）

### 統合ユーティリティ構造
```
kyotei_predictor/utils/
├── __init__.py          # 統合エントリーポイント
├── common.py            # 基本ユーティリティ
├── config.py            # 設定管理
├── logger.py            # ログ機能
├── venue_mapping.py     # 会場マッピング
└── exceptions.py        # エラーハンドリング
```

### 設定管理構造
```
kyotei_predictor/config/
├── config.json          # デフォルト設定
└── README.md           # 設定ドキュメント
```

### テスト構造
```
kyotei_predictor/tests/
├── test_utils.py        # 統合ユーティリティテスト
└── README.md           # テストドキュメント
```

### 改善策実装構造
```
tests/improvement_tests/
├── quick_test.py                    # 軽量テスト
├── simple_learning_verification.py  # 学習検証テスト
├── minimal_learning_test.py         # 最小限学習テスト
├── test_improvements.bat            # テスト用バッチ
└── run_all_tests.bat               # 包括的テスト
```

---

## 🔧 使用方法

### 1. **基本インポート**
```python
from kyotei_predictor.utils import (
    KyoteiUtils, Config, setup_logger, VenueMapper,
    KyoteiError, DataError, APIError
)
```

### 2. **設定管理**
```python
config = Config()
data_dir = config.get_data_dir()
timeout = config.get_api_timeout()
```

### 3. **ログ機能**
```python
logger = setup_logger(__name__)
logger.info("処理開始")
```

### 4. **改善策のテスト実行**
```bash
# 軽量テスト
cd tests/improvement_tests
python quick_test.py

# 学習検証テスト
python simple_learning_verification.py

# 包括的テスト
run_all_tests.bat
```

---

## 📈 性能指標

### 現在の性能
- **的中率**: 1.70%（理論値0.83%の約2倍）
- **学習効率**: 16.2倍
- **報酬安定性**: 52.5%
- **総合スコア**: 40.5/100

### 期待される改善効果
- **的中率**: 3.5% → 4.0%以上（+0.5%以上）
- **報酬の安定化**: 的中時の報酬強化、部分的中の報酬化
- **学習効率の向上**: より深い学習、アンサンブル効果

---

## 🔄 更新履歴

### 2025年1月 - 3連単的中率改善策実装
- Phase 1-4の全改善策を実装
- テストシステムの構築
- ドキュメントの整備

### 2024年12月 - アーキテクチャ改善
- 統合ユーティリティの導入
- 設定管理システムの改善
- エラーハンドリングの強化

---

## 📚 詳細ドキュメント

各ドキュメントの詳細については、上記の目次を参照してください。特に最新の改善策については、以下のドキュメントを参照してください：

- **改善戦略**: [trifecta_improvement_strategy.md](trifecta_improvement_strategy.md)
- **実装状況**: [improvement_implementation_summary.md](improvement_implementation_summary.md)
- **テスト結果**: [test_results_summary.md](test_results_summary.md) 