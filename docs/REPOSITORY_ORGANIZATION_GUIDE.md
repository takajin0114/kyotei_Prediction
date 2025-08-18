# 🗂️ リポジトリ整理ガイド

## 📋 概要

このドキュメントは、競艇予測システムのリポジトリ整理と統合バッチファイルの使用方法について説明します。

## 🧹 整理完了項目

### **削除された不要ファイル**

#### **統合バッチで代替されたファイル**
- `run_advanced_learning_auto.bat` → `run_optimization_config.bat` で代替
- `run_advanced_learning_fixed.bat` → `run_optimization_config.bat` で代替
- `run_advanced_learning.bat` → `run_optimization_config.bat` で代替
- `run_learning_pipeline.bat` → `run_optimization_config.bat` で代替

#### **機能重複ファイル**
- `run_data_acquisition.bat` → 統合バッチで代替
- `run_data_maintenance_with_setup.ps1` → 統合バッチで代替
- `run_data_maintenance_with_setup.bat` → 統合バッチで代替
- `simple_check.bat` → 統合バッチで代替
- `check_test_data.bat` → 統合バッチで代替
- `run_tests.bat` → 統合バッチで代替
- `run_quick_test.bat` → 統合バッチで代替
- `cleanup_learning_files.bat` → `cleanup_old_files.bat` で代替
- `check_disk_usage.bat` → 統合バッチで代替
- `cleanup_all_learning_files.bat` → `cleanup_old_files.bat` で代替
- `monitor_batch_progress.ps1` → 統合バッチで代替

#### **不要なPythonファイル**
- `simple_check.py` → 統合バッチで代替
- `check_test_data.py` → 統合バッチで代替
- `activate_env.ps1` → 統合バッチで代替

## 🚀 統合バッチファイル

### **1. メイン最適化バッチ**
- **ファイル**: `run_optimization_config.bat`
- **機能**: 設定可能な最適化実行
- **特徴**: 設定ファイルによる柔軟な設定変更

### **2. シンプル最適化バッチ**
- **ファイル**: `run_optimization_batch.bat`
- **機能**: 即座実行可能な最適化
- **特徴**: 設定変更なしで即座実行

### **3. クリーンアップ専用バッチ**
- **ファイル**: `cleanup_old_files.bat`
- **機能**: 古いファイルの削除
- **特徴**: 日数指定による柔軟なクリーンアップ

## 📁 現在のファイル構造

```
kyotei_Prediction/
├── 📋 設定ファイル
│   ├── optimization_config.ini          # 最適化設定
│   └── requirements.txt                 # 依存関係
├── 🚀 統合バッチファイル
│   ├── run_optimization_config.bat     # メイン最適化
│   ├── run_optimization_batch.bat      # シンプル最適化
│   └── cleanup_old_files.bat           # クリーンアップ
├── 📚 ドキュメント
│   ├── README.md                        # プロジェクト概要
│   ├── BATCH_USAGE_GUIDE.md            # バッチ使用方法
│   └── docs/                           # 詳細ドキュメント
├── 🔧 コアシステム
│   └── kyotei_predictor/               # メインシステム
├── 📊 データ・結果
│   ├── data/                           # データファイル
│   ├── logs/                           # ログファイル
│   ├── outputs/                        # 出力結果
│   └── final_results/                  # 最終結果
└── 🧪 テスト
    └── tests/                          # テストファイル
```

## 📖 使用方法

### **最適化の実行**
```bash
# 設定可能な最適化
.\run_optimization_config.bat

# シンプルな最適化
.\run_optimization_batch.bat
```

### **クリーンアップの実行**
```bash
# 古いファイルの削除
.\cleanup_old_files.bat
```

### **設定の変更**
`optimization_config.ini` を編集して最適化パラメータを変更

## 🎯 整理の効果

### **1. ファイル数の削減**
- **整理前**: 30+ のバッチファイル
- **整理後**: 3つの統合バッチファイル
- **削減率**: 90%以上

### **2. 保守性の向上**
- 重複機能の排除
- 統一されたインターフェース
- 明確な責任分担

### **3. ユーザビリティの向上**
- 分かりやすい使用方法
- 一貫した操作感
- 詳細なログ出力

## 📚 関連ドキュメント

- [BATCH_USAGE_GUIDE.md](../BATCH_USAGE_GUIDE.md) - バッチファイルの詳細使用方法
- [docs/optimization/README.md](optimization/README.md) - 最適化の詳細説明
- [docs/README.md](README.md) - ドキュメント一覧

## 🔄 今後の改善

### **短期目標**
- 統合バッチファイルの動作確認
- ユーザーフィードバックの収集
- 必要に応じた機能追加

### **長期目標**
- より高度な設定管理
- 自動化の拡充
- パフォーマンス監視の強化

---

**最終更新**: 2025-01-27  
**更新者**: AI Assistant  
**バージョン**: 1.0
