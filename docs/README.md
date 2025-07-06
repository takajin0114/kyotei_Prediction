# 競艇予測システム ドキュメント

**最終更新日**: 2025-07-06  
**バージョン**: 1.0

---

## 📚 ドキュメント構成

### **🎯 プロジェクト概要**
- [README.md](../README.md) - プロジェクト全体概要・セットアップ・クイックスタート
- [NEXT_STEPS.md](../NEXT_STEPS.md) - 今後のタスク・進捗管理・優先度
- [CHANGELOG.md](../CHANGELOG.md) - 変更履歴・リリースノート
- [PERFORMANCE_IMPROVEMENTS.md](../PERFORMANCE_IMPROVEMENTS.md) - 性能改善記録

### **🏗️ 設計書・仕様書**
- [integration_design.md](integration_design.md) - システム統合設計・アーキテクチャ
- [prediction_algorithm_design.md](prediction_algorithm_design.md) - 予測アルゴリズム設計・実装方針
- [web_app_requirements.md](web_app_requirements.md) - Webアプリケーション要件・UI設計
- [site_analysis.md](site_analysis.md) - データ取得元サイト分析・スクレイピング仕様

### **🔧 機能別ドキュメント**
- [kyotei_predictor/README.md](../kyotei_predictor/README.md) - メインアプリケーション概要
- [kyotei_predictor/tools/README.md](../kyotei_predictor/tools/README.md) - ツール群概要
- [kyotei_predictor/tests/README.md](../kyotei_predictor/tests/README.md) - テスト概要

### **📊 詳細仕様**
- [kyotei_predictor/tools/batch/README.md](../kyotei_predictor/tools/batch/README.md) - バッチ処理詳細
- [kyotei_predictor/tools/fetch/README.md](../kyotei_predictor/tools/fetch/README.md) - データ取得詳細
- [kyotei_predictor/tools/analysis/README.md](../kyotei_predictor/tools/analysis/README.md) - 分析ツール詳細
- [kyotei_predictor/pipelines/README.md](../kyotei_predictor/pipelines/README.md) - パイプライン詳細

---

## 🎯 ドキュメントの使い方

### **新規参加者向け**
1. [README.md](../README.md) - プロジェクト概要・セットアップ
2. [integration_design.md](integration_design.md) - システム全体の理解
3. [prediction_algorithm_design.md](prediction_algorithm_design.md) - 予測ロジックの理解

### **開発者向け**
1. [NEXT_STEPS.md](../NEXT_STEPS.md) - 現在のタスク・優先度
2. 各機能別README - 実装詳細
3. [CHANGELOG.md](../CHANGELOG.md) - 最新の変更内容

### **運用者向け**
1. [kyotei_predictor/tools/batch/README.md](../kyotei_predictor/tools/batch/README.md) - バッチ処理運用
2. [PERFORMANCE_IMPROVEMENTS.md](../PERFORMANCE_IMPROVEMENTS.md) - 性能改善履歴
3. [kyotei_predictor/README.md](../kyotei_predictor/README.md) - アプリケーション運用

---

## 📝 ドキュメント更新ルール

### **更新頻度**
- **README.md**: 機能追加・変更時
- **NEXT_STEPS.md**: 週次更新
- **CHANGELOG.md**: リリース時
- **設計書**: 設計変更時

### **更新責任者**
- **プロジェクト全体**: プロジェクトリーダー
- **機能別**: 各機能担当者
- **テスト**: テスト担当者

### **レビュー**
- 重要な変更は必ずレビューを実施
- ドキュメントの整合性を確認
- リンク切れのチェック

---

## 🔗 関連リソース

### **外部リンク**
- [競艇オフィシャルサイト](https://www.boatrace.jp/)
- [競艇データサイト](https://boatrace.jp/owpc/pc/race/)

### **内部リソース**
- [データディレクトリ](../kyotei_predictor/data/)
- [設定ファイル](../kyotei_predictor/config/)
- [テストデータ](../kyotei_predictor/tests/)

---

## 📞 サポート

### **質問・要望**
- GitHub Issues で報告
- ドキュメント改善の提案も歓迎

### **貢献**
- ドキュメントの改善提案
- 翻訳・多言語化
- サンプルコードの追加

---

**最終更新**: 2025-07-06  
**次回更新予定**: 2025-07-13 