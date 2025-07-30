# 競艇予測システム - ドキュメント

**最終更新日**: 2025-07-30  
**バージョン**: 5.0（リファクタリング完了・統合システム完成）

## 📋 目次

### 📊 プロジェクト概要
- [CURRENT_STATUS_SUMMARY.md](CURRENT_STATUS_SUMMARY.md) - 現在の状況サマリー（最新）
- [DOCUMENTATION_STANDARDS.md](DOCUMENTATION_STANDARDS.md) - ドキュメント標準

### 🔄 リファクタリング・整理作業
- [refactoring/](refactoring/) - リファクタリング関連ドキュメント
  - [README.md](refactoring/README.md) - リファクタリング作業概要
  - [COMPREHENSIVE_REFACTORING_SUMMARY.md](refactoring/COMPREHENSIVE_REFACTORING_SUMMARY.md) - 包括的サマリー

### 🚀 今後の方針
- [future_strategy.md](future_strategy.md) - 今後の方針と戦略

### 🔧 開発者向けドキュメント
- [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md) - 開発者ガイド
- [API_SPECIFICATION.md](API_SPECIFICATION.md) - API仕様書

### 📁 運用ドキュメント
- [OPERATIONS_MANUAL.md](OPERATIONS_MANUAL.md) - 運用マニュアル
- [operations/](operations/) - 運用関連ドキュメント

### 📋 要件ドキュメント
- [requirements/](requirements/) - 要件関連ドキュメント

### 🌐 Web表示ドキュメント
- [web_display/](web_display/) - Web表示関連ドキュメント

### 🔧 最適化ドキュメント
- [optimization/](optimization/) - 最適化関連ドキュメント

---

## 🎯 プロジェクト概要

競艇予測システムは、強化学習を用いた競艇の3連単予測システムです。

### 主要機能
- **段階的報酬設計**: 的中率1.70%（理論値の約2倍）
- **統合最適化システム**: Optunaによる自動最適化（4つの最適化タイプ対応）
- **監視システム**: リアルタイム進捗監視
- **評価システム**: 客観的性能評価
- **統合ユーティリティ**: 標準化された設定管理・ログ機能・エラーハンドリング

### 技術スタック
- **強化学習**: Stable-Baselines3 (PPO)
- **最適化**: Optuna（統合システム）
- **データ処理**: pandas, numpy
- **可視化**: matplotlib
- **統合ユーティリティ**: カスタム設定管理・ログ機能・エラーハンドリング

### 現在の成果
- **的中率**: 1.70%（理論値0.83%の約2倍）
- **学習効率**: 16.2倍
- **報酬安定性**: 52.5%
- **総合スコア**: 40.5/100
- **ディスク容量節約**: 約8MB
- **保守性向上**: 重複コード完全削除

---

## 🏗️ 新しいアーキテクチャ（v5.0）

### 統合最適化システム
```
kyotei_predictor/tools/optimization/
├── unified_optimizer.py          # 統合最適化スクリプト
└── optimization_config.json      # 設定ファイル
```

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

---

## 🔧 使用方法

### 1. **統合最適化システム**
```bash
# 段階的報酬最適化
python -m kyotei_predictor.tools.optimization.unified_optimizer --type graduated_reward

# シンプル最適化
python -m kyotei_predictor.tools.optimization.unified_optimizer --type simple --n-trials 50

# テスト最適化
python -m kyotei_predictor.tools.optimization.unified_optimizer --type test --n-trials 10
```

### 2. **基本インポート**
```python
from kyotei_predictor.utils import (
    KyoteiUtils, Config, setup_logger, VenueMapper,
    KyoteiError, DataError, APIError
)
```

### 3. **設定管理**
```python
config = Config()
data_dir = config.get_data_dir()
timeout = config.get_api_timeout()
```

### 4. **ログ機能**
```python
logger = setup_logger(__name__)
logger.info("処理開始")
logger.error("エラー発生", exc_info=True)
```

---

## 📊 リファクタリング成果

### **ディスク容量の大幅節約**
- アーカイブ移動: 約8MB
- 重複ファイル削除: 約100KB
- **合計: 約8MBの容量節約**

### **保守性の大幅向上**
- 重複コードの完全削除
- 統一されたインターフェース
- 設定ファイルによる制御
- 明確なディレクトリ構造

### **開発効率の大幅向上**
- 明確なディレクトリ構造
- 統一されたツール
- 分かりやすいファイル配置
- 統合最適化システム

---

## 🚀 次のステップ

### **即座に実行可能**
1. **Phase 4: 最終クリーンアップ** - 古いtrialディレクトリの整理
2. **統合最適化システムのテスト** - 動作確認

### **中期的な作業**
3. **Phase 5: ドキュメント最終更新** - 運用ガイドの完成
4. **Phase 6: テスト・検証作業** - システムの安定性確保

### **長期的な作業**
5. **Phase 7: 運用準備作業** - 完全な運用体制の構築

---

**Phase 1-3は正常に完了しました。プロジェクトの保守性・拡張性・パフォーマンス・運用性が大幅に向上し、統合最適化システムによる効率的な開発・運用が可能になりました。** 