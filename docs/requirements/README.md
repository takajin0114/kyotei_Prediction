# 要件定義

プロジェクトの要件定義に関するドキュメントを管理するディレクトリです。

## 📌 要件レベルでの全体像

**まずは [REQUIREMENTS_OVERVIEW.md](../REQUIREMENTS_OVERVIEW.md)** を参照してください。  
目的・業務要件・機能要件（領域別）・非機能要件の整理と、各ドキュメントとの対応表があります。

## 📚 本ディレクトリのドキュメント一覧

### [ux_improvement.md](ux_improvement.md)
Phase 4のUX改善・拡張要件定義書です。
- 検索・フィルター機能
- ソート機能
- エクスポート機能
- グラフ・チャート表示
- 履歴比較・複数日付比較
- ユーザー設定保存・通知  
**状態**: 要件定義完了、未実装

### [system_status_page.md](system_status_page.md)
システムステータスページの要件・UI設計書です。
- 目的・対象ユーザー
- 画面イメージ（ワイヤーフレーム）
- 表示項目一覧
- データ構造・取得元
- 技術要件・運用・拡張要件  
**状態**: 要件定義完了、実装は一部（テンプレート system_status.html 等）

## 📊 要件管理状況

- ✅ **Web表示基本機能**: 要件定義・実装完了（[web_display/requirements.md](../web_display/requirements.md)）
- ✅ **UX改善要件**: Phase 4 要件定義完了（本ディレクトリ ux_improvement.md）
- ✅ **システムステータスページ**: 要件・UI設計完了、実装一部
- 📋 **今後の要件**: 新機能追加時は本ディレクトリに md を追加し、[REQUIREMENTS_OVERVIEW.md](../REQUIREMENTS_OVERVIEW.md) の表を更新

## 🔗 関連ドキュメント

- [REQUIREMENTS_OVERVIEW.md](../REQUIREMENTS_OVERVIEW.md) - 要件レベル全体整理
- [web_display/](../web_display/) - Web表示機能の要件・計画・完了状況
- [operations/](../operations/) - 運用ガイド
- [CURRENT_STATUS_SUMMARY.md](../CURRENT_STATUS_SUMMARY.md) - プロジェクト全体の進捗