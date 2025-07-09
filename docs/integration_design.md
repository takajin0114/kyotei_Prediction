# システム統合設計書

**役割**: 競艇予測システム全体の統合設計・アーキテクチャ・運用フローを記載
**参照先**: [../README.md](../README.md), [DEVELOPMENT_ROADMAP.md](DEVELOPMENT_ROADMAP.md)
**最終更新日**: 2025-07-09

---

## 概要
- 本ドキュメントは、データ取得・前処理・学習・評価・API・Webアプリまでの全体設計・運用フローを体系的に記載します。
- 現状の運用ルール・進行中タスク・今後の拡張方針も明記します。

## 索引・関連ドキュメント
- [DEVELOPMENT_ROADMAP.md](DEVELOPMENT_ROADMAP.md) - 開発ロードマップ
- [data_acquisition.md](data_acquisition.md) - データ取得運用
- [prediction_algorithm_design.md](prediction_algorithm_design.md) - 予測アルゴリズム設計
- [web_app_requirements.md](web_app_requirements.md) - Webアプリ要件
- [../kyotei_predictor/data/README.md](../kyotei_predictor/data/README.md) - データ運用ルール

---

## 現状の運用・開発フロー
- データ取得は月単位・会場単位で分割実行、欠損自動集計・再取得バッチ運用
- データ品質チェック・前処理パイプラインは自動化・定期実行
- 学習・評価・最適化・API化まで一連の流れをドキュメント化
- 欠損・異常データ管理、再取得、品質チェックの運用ルールを明記

## 主要設計・運用方針
- データ保存・命名規則・成果物管理の標準化
- バッチ処理・API・Webアプリの連携設計
- モデル学習・評価・再学習サイクルの自動化

## 成果・課題・今後のTODO
- 成果: データ取得・学習・評価・API化までの一貫運用が実現
- 課題: 欠損データの完全自動化、品質チェックのさらなる強化
- TODO: API/Webアプリの拡張、ビジネス展開準備、ドキュメント運用の徹底

## 更新履歴
- 2025-07-09: 現状運用・開発フロー・索引・運用ルールを追記