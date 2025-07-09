
# データ取得運用・手順書

**役割**: データ取得・欠損管理・再取得・品質チェックの運用ルール・手順を記載
**参照先**: [../README.md](../README.md), [DEVELOPMENT_ROADMAP.md](DEVELOPMENT_ROADMAP.md), [kyotei_predictor/data/README.md](../kyotei_predictor/data/README.md)
**最終更新日**: 2025-07-09

---

## 概要
- 本ドキュメントは、データ取得・欠損管理・再取得・品質チェックの運用ルール・手順を体系的に記載します。

## 索引・関連ドキュメント
- [kyotei_predictor/data/README.md](../kyotei_predictor/data/README.md) - データ保存・命名規則
- [DEVELOPMENT_ROADMAP.md](DEVELOPMENT_ROADMAP.md) - 開発ロードマップ
- [NEXT_STEPS.md](NEXT_STEPS.md) - 進行中タスク

---

## データ取得・欠損管理・再取得・品質チェックの流れ
- データ取得は月単位・会場単位で分割実行、負荷分散・リトライ容易化
- 欠損データは `tools/batch/list_fetched_data_summary.py` で自動集計
- 欠損・異常データは `tools/batch/retry_missing_races.py` で自動再取得
- データ品質チェックは `tools/analysis/data_availability_checker.py` で定期実施
- 取得・再取得・品質チェックの運用状況は `logs/` に記録

## 今後のTODO
- 欠損データ自動集計・再取得バッチの定期運用
- 品質チェック・前処理パイプラインの自動化
- データ取得運用のドキュメント随時更新

## 更新履歴
- 2025-07-09: 現状運用・手順・索引・TODOを追記
