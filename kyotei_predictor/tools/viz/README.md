# viz ディレクトリ README

**最終更新日: 2025-07-04**

---

## 本READMEの役割
- 可視化・表示ツール（データ・学習結果のグラフ化、HTML表示等）の役割・使い方・運用ルールを記載
- 主要スクリプトの説明・設計書へのリンクを明記
- ルートREADMEやtools/README、NEXT_STEPS.mdへのリンクも記載

## 関連ドキュメント
- [../../../README.md](../../../README.md)（全体概要・セットアップ・タスク入口）
- [../README.md](../README.md)（tools全体の運用ルール）
- [../../../NEXT_STEPS.md](../../../NEXT_STEPS.md)（今後のタスク・優先度・進捗管理）
- [../../../docs/PROJECT_LAYOUT.md](../../../docs/PROJECT_LAYOUT.md)（プロジェクト構成）
- [../../../prediction_algorithm_design.md](../../../prediction_algorithm_design.md)（予測アルゴリズム設計）

---

## 役割・用途
- データ・学習結果のグラフ化・HTML表示
- 分析・AI学習の可視化
- outputs/やresults/に出力

---

## 主要スクリプト
- `data_display.py` : データ表示
- `html_display.py` : HTML表示
- `rl_visualization.py` : RL学習結果可視化

---

## 運用ルール
- 入出力ファイルのパス・命名規則を統一
- 可視化結果はoutputs/やresults/に保存
- 不要な一時ファイルは随時削除

---

# 以下、従来の内容（使い方・注意点など）を現状維持・必要に応じて最新化

# Visualization Tools

競艇データ可視化ツール群です。HTML表示・グラフ生成を担当します。

## 📁 ファイル構成

- `html_display.py` - HTML形式でのデータ表示
- `data_display.py` - データ表示・フォーマット

## 🚀 使用方法

### HTML表示
```bash
python html_display.py
```

### データ表示
```bash
python data_display.py
```

## 📊 可視化機能

### HTML表示
- レース結果のHTMLテーブル生成
- オッズ情報の表示
- 予測結果の可視化
- レスポンシブデザイン対応

### データ表示
- コンソール出力でのデータ表示
- フォーマット済みテーブル表示
- 統計情報の表示
- エラー・警告メッセージ

## 🎨 表示形式

### HTML出力
- **Bootstrap** ベースのモダンUI
- レスポンシブテーブル
- カラーコーディング（順位・オッズ等）
- インタラクティブ要素

### コンソール出力
- 表形式での整理表示
- カラー出力対応
- 進捗表示
- エラー表示

## 📈 表示項目

### レース情報
- 開催日・会場・レース番号
- 出走艇・選手情報
- スタート展示タイム
- 決まり手・決まり手タイム

### オッズ情報
- 3連単・3連複オッズ
- 期待値・投資判定
- オッズ推移
- 的中率統計

### 予測結果
- AI予測確率
- 強化学習結果
- 最適化パラメータ
- パフォーマンス指標

## 🔧 技術仕様

### HTML生成
- **jinja2** テンプレートエンジン
- **Bootstrap 5** CSSフレームワーク
- **Chart.js** グラフ描画
- **Font Awesome** アイコン

### データフォーマット
- **pandas** データフレーム処理
- **tabulate** テーブル表示
- **rich** コンソール出力
- **colorama** カラー出力 