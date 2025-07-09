# プロジェクト構造詳細

> **注記**: 本ドキュメントはdocs/配下に集約予定です。最新の参照は[README.md](README.md)・[docs/README.md](docs/README.md)から行ってください。

## 概要

競艇予測システムのプロジェクト構造と各コンポーネントの役割を詳細に説明します。

## ドキュメント索引・参照ガイド
- [README.md](README.md) - 全体概要・索引
- [docs/README.md](docs/README.md) - ドキュメント全体ガイド
- [docs/integration_design.md](docs/integration_design.md) - システム統合設計
- [docs/DEVELOPMENT_ROADMAP.md](docs/DEVELOPMENT_ROADMAP.md) - 開発ロードマップ

---

# 以下、従来の内容（構造詳細）は現状維持

## ディレクトリ構造

```
kyotei_Prediction/
├── docs/                          # ドキュメント
│   ├── DEVELOPMENT_ROADMAP.md     # 開発ロードマップ
│   ├── data_acquisition.md        # データ取得
│   ├── EQUIPMENT_ENHANCEMENT_PLAN.md
│   ├── EV_THRESHOLD_OPTIMIZATION.md
│   └── ...                        # その他のドキュメント
├── kyotei_predictor/              # メインアプリケーション
│   ├── app.py                     # Webアプリケーション
│   ├── config/                    # 設定ファイル
│   │   ├── settings.py            # 基本設定
│   │   ├── optuna_config.json     # Optuna設定
│   │   └── README.md              # 設定ファイル説明
│   ├── data/                      # データディレクトリ
│   │   ├── raw/                   # 生データ
│   │   ├── processed/             # 処理済みデータ
│   │   ├── results/               # 結果データ
│   │   ├── logs/                  # ログファイル
│   │   ├── backup/                # バックアップデータ
│   │   ├── temp/                  # 一時ファイル
│   │   ├── sample/                # サンプルデータ
│   │   └── README.md              # データディレクトリ説明
│   ├── pipelines/                 # データ処理パイプライン
│   │   ├── data_preprocessor.py   # データ前処理
│   │   ├── feature_enhancer.py    # 特徴量エンジニアリング
│   │   ├── db_integration.py      # データベース統合
│   │   ├── kyotei_env.py          # 競艇環境
│   │   └── README.md              # パイプライン説明
│   ├── tools/                     # ツール群
│   │   ├── batch/                 # バッチ処理
│   │   │   ├── __init__.py        # パッケージ初期化
│   │   │   ├── train_graduated_reward.py      # 段階的報酬学習
│   │   │   └── train_extended_graduated_reward.py  # 拡張学習
│   │   ├── evaluation/            # 評価ツール
│   │   │   ├── __init__.py        # パッケージ初期化
│   │   │   └── evaluate_graduated_reward_model.py  # 詳細評価
│   │   ├── optimization/          # 最適化ツール
│   │   │   ├── __init__.py        # パッケージ初期化
│   │   │   └── optimize_graduated_reward.py   # ハイパーパラメータ最適化
│   │   └── README.md              # ツール説明
│   ├── static/                    # 静的ファイル
│   │   ├── css/                   # CSSファイル
│   │   └── js/                    # JavaScriptファイル
│   ├── templates/                 # HTMLテンプレート
│   ├── utils/                     # ユーティリティ
│   │   └── helpers.py             # ヘルパー関数
│   ├── docs/                      # アプリケーション固有ドキュメント
│   │   ├── PHASE3_PROGRESS_REPORT.md
│   │   └── TRIFECTA_INVESTMENT_STRATEGY.md
│   ├── tests/                     # テストファイル
│   │   ├── ai/                    # AI関連テスト
│   │   ├── viz/                   # 可視化テスト
│   │   └── README.md              # テスト説明
│   └── README.md                  # アプリケーションREADME
├── optuna_models/                 # 学習済みモデル
│   ├── trial_*/                   # 各試行のモデル
│   └── graduated_reward_best/     # 最良モデル
├── optuna_logs/                   # 学習ログ
│   └── trial_*/                   # 各試行のログ
├── optuna_results/                # 最適化結果
│   └── *.json                     # 最適化結果JSON
├── optuna_studies/                # Optunaスタディ
│   └── *.db                       # スタディデータベース
├── optuna_tensorboard/            # TensorBoardログ
│   └── trial_*/                   # 各試行のTensorBoardログ
├── outputs/                       # 出力ファイル
│   └── *.json                     # 結果JSONファイル
├── ppo_tensorboard/               # PPO学習ログ
│   └── PPO_*/                     # PPO学習ログ
├── tests/                         # プロジェクト全体テスト
│   ├── ai/                        # AI関連テスト
│   └── viz/                       # 可視化テスト
├── tools/                         # プロジェクト全体ツール
│   └── optuna_optimizer.py        # Optuna最適化ツール
├── venv311/                       # 仮想環境
├── run_evaluation.py              # 評価スクリプト実行ラッパー
├── run_optimization.py            # 最適化スクリプト実行ラッパー
├── run_training.py                # 学習スクリプト実行ラッパー
├── API_SPECIFICATION.md           # API仕様書
├── PHASE3_COMPLETE_REPORT.md      # Phase3完了レポート
├── README.md                      # プロジェクト全体README
└── requirements.txt               # 依存関係
```

## 主要コンポーネント詳細

### 1. ドキュメント (docs/)

#### DEVELOPMENT_ROADMAP.md
- 段階的報酬設計の成功を受けた今後の開発計画
- Phase 1-4の詳細なロードマップ
- 各フェーズの期待される成果と実行内容

#### その他のドキュメント
- データ取得、設備強化計画、閾値最適化など
- プロジェクトの各側面に関する詳細な技術文書

### 2. メインアプリケーション (kyotei_predictor/)

#### 設定ファイル (config/)
- **settings.py**: アプリケーションの基本設定
- **optuna_config.json**: Optuna最適化の設定
- 環境変数、データパス、学習パラメータなどの設定

#### データディレクトリ (data/)
- **raw/**: 取得したままの生データ
- **processed/**: 前処理・特徴量エンジニアリング済みデータ
- **results/**: 予測・分析・評価などの成果物
- **logs/**: データ取得・処理・学習等のログファイル
- **backup/**: バックアップ用データ
- **temp/**: 一時ファイル
- **sample/**: サンプルデータ

#### データ処理パイプライン (pipelines/)
- **data_preprocessor.py**: データの前処理
- **feature_enhancer.py**: 特徴量エンジニアリング
- **db_integration.py**: データベース統合
- **kyotei_env.py**: 競艇用強化学習環境

#### ツール群 (tools/)

##### バッチ処理 (batch/)
- **train_graduated_reward.py**: 段階的報酬設計での学習
- **train_extended_graduated_reward.py**: 拡張学習（100万ステップ）

##### 評価ツール (evaluation/)
- **evaluate_graduated_reward_model.py**: 学習済みモデルの詳細評価
- 的中率、報酬分布、学習効果の分析

##### 最適化ツール (optimization/)
- **optimize_graduated_reward.py**: ハイパーパラメータ最適化
- Optunaを使用した自動最適化

### 3. 学習関連ディレクトリ

#### optuna_models/
- 各試行の学習済みモデル
- 最良モデルの保存場所

#### optuna_logs/
- 学習過程のログファイル
- 評価結果の記録

#### optuna_results/
- 最適化結果のJSONファイル
- 試行結果の統計情報

#### optuna_studies/
- Optunaスタディのデータベース
- 最適化履歴の保存

#### optuna_tensorboard/
- TensorBoard用のログファイル
- 学習過程の可視化データ

### 4. 実行ラッパー

#### run_evaluation.py
- 評価スクリプトの実行ラッパー
- プロジェクトルートからの簡単実行

#### run_optimization.py
- 最適化スクリプトの実行ラッパー
- ハイパーパラメータ最適化の実行

#### run_training.py
- 学習スクリプトの実行ラッパー
- 基本学習と拡張学習の選択可能

## 実行方法

### 1. 基本的な学習
```bash
# 段階的報酬設計での学習
python run_training.py --mode basic

# 拡張学習（100万ステップ）
python run_training.py --mode extended
```

### 2. モデル評価
```bash
# 学習済みモデルの詳細評価
python run_evaluation.py
```

### 3. ハイパーパラメータ最適化
```bash
# Optunaを使用した自動最適化
python run_optimization.py
```

### 4. Webアプリケーション
```bash
# 予測システムの起動
python kyotei_predictor/app.py
```

## データフロー

### 1. データ取得
```
外部サイト → data/raw/ → データ品質チェック
```

### 2. データ処理
```
data/raw/ → pipelines/ → data/processed/
```

### 3. 学習
```
data/processed/ → kyotei_env.py → PPO学習 → optuna_models/
```

### 4. 評価
```
optuna_models/ → 評価ツール → outputs/
```

### 5. 最適化
```
学習 → 評価 → パラメータ調整 → 再学習 → optuna_results/
```

## 設定管理

### 環境変数
- データディレクトリパス
- 学習パラメータ
- ログレベル

### 設定ファイル
- **settings.py**: アプリケーション設定
- **optuna_config.json**: 最適化設定

## ログ管理

### ログレベル
- DEBUG: 詳細なデバッグ情報
- INFO: 一般的な情報
- WARNING: 警告
- ERROR: エラー

### ログファイル
- アプリケーションログ: `data/logs/`
- 学習ログ: `optuna_logs/`
- TensorBoardログ: `optuna_tensorboard/`

## バックアップ戦略

### データバックアップ
- 重要なデータは `data/backup/` に保存
- 世代管理による履歴保持

### モデルバックアップ
- 学習済みモデルは `optuna_models/` に保存
- 最良モデルは専用ディレクトリにコピー

## テスト戦略

### 単体テスト
- 各モジュールの機能テスト
- データ処理パイプラインのテスト

### 統合テスト
- エンドツーエンドのテスト
- 学習から評価までの一連の流れ

### 性能テスト
- 学習時間の測定
- メモリ使用量の監視

## 今後の拡張予定

### Phase 2: アンサンブル学習
- 複数モデルの組み合わせ
- 投票システムの実装

### Phase 3: リアルタイム予測
- Web APIの実装
- リアルタイムデータ取得

### Phase 4: 高度な特徴量
- 時系列分析
- 外部データ統合

---

この構造により、競艇予測システムの開発、学習、評価、最適化が体系的に行えるようになっています。 