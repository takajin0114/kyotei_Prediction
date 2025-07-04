# pipelines ディレクトリ README

**最終更新日: 2025-07-03**

---

## 本READMEの役割
- データ前処理・特徴量生成・AI学習環境などパイプラインの役割・使い方を記載
- 典型的な処理フロー・設計書へのリンクを明記
- ルートREADMEやNEXT_STEPS.mdへのリンクも記載

## 関連ドキュメント
- [../../README.md](../../README.md)（全体概要・セットアップ・タスク入口）
- [../../NEXT_STEPS.md](../../NEXT_STEPS.md)（今後のタスク・優先度・進捗管理）
- [../../integration_design.md](../../integration_design.md)（統合設計・アーキテクチャ）
- [../../prediction_algorithm_design.md](../../prediction_algorithm_design.md)（予測アルゴリズム設計）

---

# 以下、従来の内容（パイプラインの説明・使い方など）を現状維持・必要に応じて最新化

# pipelines ディレクトリ

データ前処理・特徴量生成・AI学習環境など、データ処理パイプラインを構成するスクリプト群を管理します。

## 📁 主なスクリプト
- `data_preprocessor.py` : データ前処理・クリーニング
- `feature_enhancer.py` : 特徴量エンジニアリング
- `kyotei_env.py` : 強化学習用環境クラス

## 🚀 運用方針
- データ取得後、raw/→processed/への変換処理を担当
- AI学習・推論用のデータセット生成
- 新規パイプラインは本ディレクトリに追加
- 共通処理は tools/common/ へ集約

## 📝 典型的な処理フロー
1. `data_preprocessor.py` で生データをクリーニング
2. `feature_enhancer.py` で特徴量追加
3. `kyotei_env.py` でAI学習環境を構築

## 🔧 備考
- 中間生成物は data/processed/ へ保存
- パイプラインの自動化は今後 scripts/ や workflow/ で管理予定
- テストコードは tests/ 配下に設置 