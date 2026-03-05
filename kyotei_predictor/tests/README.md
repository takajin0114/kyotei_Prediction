# tests ディレクトリ README

> **注記**: 詳細なテスト設計・運用ルールは[../../docs/README.md](../../docs/README.md)・[../pipelines/README.md](../pipelines/README.md)・各サブディレクトリREADMEを参照

## 概要
- AI学習・推論・評価、データ取得・前処理、可視化などのテストコードを集約
- サブディレクトリごとに用途別に整理
- 詳細なテスト設計・運用ルールはdocs/配下に集約

## 主なサブディレクトリ
- `ai/` : AI学習・推論・評価テスト
- `data/` : データ取得・前処理・品質テスト
- `viz/` : 可視化・グラフ生成テスト

## テスト実行例
- pytestで一括実行
```bash
pytest tests/
```
- サブディレクトリ単位で実行
```bash
pytest tests/ai/
pytest tests/data/
pytest tests/viz/
```

## 参照先
- [../pipelines/README.md](../pipelines/README.md) - パイプライン運用・分析
- [../../docs/README.md](../../docs/README.md) - ドキュメント全体ガイド
- [../../docs/README.md](../../docs/README.md) - ドキュメント索引・タスク一覧

---

# 以下、従来の内容（詳細なテスト例・サンプル等）は現状維持 