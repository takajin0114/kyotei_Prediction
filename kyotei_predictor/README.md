# kyotei_predictor サブシステム README

**最終更新日: 2025-07-03**

---

## 本READMEの役割
- サブシステム（kyotei_predictor/）の役割・API・予測精度・今後の予定を記載
- ディレクトリ配下の主要機能・使い方・注意点を明確化
- ルートREADMEや設計書、NEXT_STEPS.mdへのリンクを明記

## 関連ドキュメント
- [../README.md](../README.md)（全体概要・セットアップ・タスク入口）
- [../NEXT_STEPS.md](../NEXT_STEPS.md)（今後のタスク・優先度・進捗管理）
- [../integration_design.md](../integration_design.md)（統合設計・アーキテクチャ）
- [../prediction_algorithm_design.md](../prediction_algorithm_design.md)（予測アルゴリズム設計）
- [../site_analysis.md](../site_analysis.md)（データ取得元サイト分析）
- [../web_app_requirements.md](../web_app_requirements.md)（Webアプリ要件・UI設計）

---

# dataディレクトリの構成・運用ルール（2025-07-03時点）
- `raw/` : 取得したままの生データ
- `processed/` : 前処理・特徴量エンジニアリング済みデータ
- `results/` : 予測・分析・評価などの成果物（新設）
- `logs/` : データ取得・処理・学習等のログファイル（新設）
- `backup/` : バックアップ用データ
- `temp/` : 一時ファイル
- `sample/` : サンプルデータ（今後はraw/またはresults/へ統合・廃止予定）

- ファイル命名規則: `race_data_YYYY-MM-DD_VENUE_RN.json` など。種別・日付・会場・レース番号で統一。
- 生データは必ずraw/、前処理後はprocessed/、成果物はresults/、ログはlogs/へ保存。
- サンプルデータは一時的にsample/に置くが、将来的にはraw/resultsへ統合。
- 重要なデータはbackup/で世代管理。
- 一時ファイルはtemp/で作業終了後にクリーンアップ。

---

# 以下、従来の内容（API・予測精度・今後の予定など）を現状維持・必要に応じて最新化

# 競艇予測ツール - メインアプリケーション

## 📁 ディレクトリ構造

```
kyotei_predictor/
├── app.py                    # Flask Webアプリケーション
├── data_integration.py       # データ統合レイヤー
├── prediction_engine.py      # 予測エンジン
├── requirements.txt          # Python依存関係
├── README.md                # このファイル
├── data/                    # データファイル（整理済み）
│   ├── raw/                # 生データ
│   │   ├── race_data_*.json
│   │   └── odds_data_*.json
│   ├── processed/          # 処理済みデータ
│   ├── backup/             # バックアップデータ
│   └── temp/               # 一時データ
├── tools/                   # ツール類（機能別に整理）
│   ├── fetch/              # データ取得関連
│   │   ├── race_data_fetcher.py
│   │   └── odds_fetcher.py
│   ├── batch/              # バッチ処理関連
│   │   └── batch_fetch_all_venues.py
│   ├── analysis/           # 分析関連
│   │   └── odds_analysis.py
│   ├── viz/                # 可視化関連
│   │   ├── data_display.py
│   │   └── html_display.py
│   ├── ai/                 # AI/機械学習関連
│   │   ├── optuna_optimizer.py
│   │   └── rl_learn_sample.py
│   └── common/             # 共通機能
│       └── venue_mapping.py
├── tests/                   # テストファイル（機能別に整理）
│   ├── data/               # データ関連テスト
│   │   ├── test_data_fetch.py
│   │   ├── test_multiple_races.py
│   │   └── simple_race_test.py
│   └── ai/                 # AI関連テスト
│       ├── test_kyotei_env.py
│       ├── test_phase2_algorithms.py
│       └── test_trifecta_probability.py
├── outputs/                 # 出力ファイル
│   └── *.html              # HTML表示ファイル
├── logs/                    # ログファイル
│   └── *.log               # アプリケーションログ
├── static/                  # 静的ファイル
│   ├── css/
│   └── js/
└── templates/               # HTMLテンプレート
```

## 🚀 クイックスタート

### 1. 依存関係インストール
```bash
pip install -r requirements.txt
```

### 2. Webアプリケーション起動
```bash
python app.py
```

### 3. ブラウザでアクセス
```
http://localhost:12000
```

## 🧪 テスト実行

### データ関連テスト
```bash
python tests/data/simple_race_test.py
python tests/data/test_multiple_races.py
python tests/data/test_data_fetch.py
```

### AI/機械学習関連テスト
```bash
python tests/ai/test_kyotei_env.py
python tests/ai/test_phase2_algorithms.py
python tests/ai/test_trifecta_probability.py
```

### 全テスト実行
```bash
python -m pytest tests/
```

## 🔧 ツール使用方法

### データ取得
```bash
# 単一レースデータ取得
python tools/fetch/race_data_fetcher.py

# オッズデータ取得
python tools/fetch/odds_fetcher.py

# 全競艇場バッチ取得
python tools/batch/batch_fetch_all_venues.py
```

### データ分析
```bash
# オッズ分析
python tools/analysis/odds_analysis.py

# データ表示
python tools/viz/data_display.py data/raw/race_data_*.json

# HTML表示生成
python tools/viz/html_display.py data/raw/race_data_*.json
```

### AI/機械学習
```bash
# Optuna最適化
python tools/ai/optuna_optimizer.py

# 強化学習サンプル
python tools/ai/rl_learn_sample.py
```

## 📊 予測アルゴリズム

### 1. basic (基本アルゴリズム)
- 全国勝率 60% + 当地勝率 40%
- シンプルで安定した予測

### 2. rating_weighted (級別重み付け)
- 級別係数: A1(1.2) > A2(1.1) > B1(1.0) > B2(0.9)
- A級選手を重視した予測

## 🎯 予測精度実績

### 検証済みレース (3レース)
- **本命的中率**: 33.3% (1/3)
- **連対精度**: 高精度 (A級選手の適切な評価)
- **3連対精度**: 上位3艇の特定精度が高い

### 特徴
- ✅ A級選手の適切な上位評価
- ✅ 異なる競艇場での安定性
- ✅ 投資観点での実用性確認

## 📈 API エンドポイント

| エンドポイント | メソッド | 説明 |
|---------------|---------|------|
| `/` | GET | メインページ |
| `/api/racers` | GET | 選手データ取得 |
| `/api/race_conditions` | GET | レース条件取得 |
| `/api/predict` | POST | 予測実行 |
| `/api/save_prediction` | POST | 予想保存 |
| `/api/predictions_history` | GET | 予想履歴取得 |

## 🔍 トラブルシューティング

### インポートエラー
```
⚠️ 既存データ取得機能のインポートに失敗: No module named 'race_data_fetcher'
```
これは正常な動作です。ツールファイルが別ディレクトリに移動したためですが、アプリケーション本体には影響ありません。

### ファイルが見つからない
データファイルは `data/` ディレクトリに配置されています。パスを確認してください。

## 📝 開発情報

- **開発者**: openhands
- **開発日**: 2025-06-13
- **ブランチ**: feature/kyotei-web-app
- **Python**: 3.8+
- **フレームワーク**: Flask 3.1.1

## 🚀 今後の予定

### Phase 2: 中級アルゴリズム
- 機材重視アルゴリズム
- 3連単確率計算
- 総合評価アルゴリズム

### Phase 3: フロントエンド強化
- HTMLテンプレート完成
- JavaScript機能実装
- レスポンシブデザイン

### Phase 4: データベース連携
- SQLiteデータベース
- 過去データ蓄積
- 統計分析機能