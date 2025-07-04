# ai ディレクトリ README

**最終更新日: 2025-07-04**

---

## 本READMEの役割
- AI・強化学習・Optuna最適化ツールの役割・使い方・運用ルールを記載
- 主要スクリプトの説明・設計書へのリンクを明記
- ルートREADMEやtools/README、NEXT_STEPS.mdへのリンクも記載

## 関連ドキュメント
- [../../../README.md](../../../README.md)（全体概要・セットアップ・タスク入口）
- [../README.md](../README.md)（tools全体の運用ルール）
- [../../../NEXT_STEPS.md](../../../NEXT_STEPS.md)（今後のタスク・優先度・進捗管理）
- [../../../integration_design.md](../../../integration_design.md)（統合設計・アーキテクチャ）
- [../../../prediction_algorithm_design.md](../../../prediction_algorithm_design.md)（予測アルゴリズム設計）

---

## 役割・用途
- 強化学習（PPO等）・Optunaによるハイパーパラメータ最適化
- AI学習・評価・可視化
- モデル・ログ・結果はoptuna_models/、optuna_logs/、optuna_results/等に保存

---

## 主要スクリプト
- `optuna_optimizer.py` : Optuna最適化
- `rl_learn_sample.py` : RL学習サンプル

---

## 運用ルール
- 学習・最適化の成果物は所定のディレクトリに保存
- パラメータ・設定はconfig/で一元管理
- 不要な一時ファイルは随時削除

---

# 以下、従来の内容（使い方・注意点など）を現状維持・必要に応じて最新化

# AI & Machine Learning Tools

競艇予測AI・機械学習ツール群です。強化学習・Optuna最適化を担当します。

## 📁 ファイル構成

- `rl_learn_sample.py` - 強化学習サンプル実装
- `rl_visualization.py` - 強化学習結果可視化
- `optuna_optimizer.py` - Optunaハイパーパラメータ最適化
- `test_optuna_setup.py` - Optuna設定テスト

## 🚀 使用方法

### 強化学習
```bash
python rl_learn_sample.py
```

### 最適化
```bash
python optuna_optimizer.py
```

### 可視化
```bash
python rl_visualization.py
```

## 🤖 AI機能

### 強化学習（Reinforcement Learning）
- **Q-Learning** ベースの予測モデル
- **Actor-Critic** アーキテクチャ
- **Policy Gradient** 手法
- **Multi-Agent** システム

### ハイパーパラメータ最適化
- **Optuna** による自動最適化
- **Bayesian Optimization**
- **Grid Search** 代替
- **Cross Validation**

### 予測モデル
- 3連単・3連複的中予測
- 期待値最大化
- リスク管理
- ポートフォリオ最適化

## 🔧 技術仕様

### 強化学習フレームワーク
- **Stable-Baselines3** / **RLlib**
- **PyTorch** / **TensorFlow**
- **Gymnasium** 環境
- **Custom Environment** 実装

### 最適化フレームワーク
- **Optuna** ハイパーパラメータ最適化
- **Hyperopt** 代替
- **MLflow** 実験管理
- **Weights & Biases** 統合

### モデル評価
- **Cross Validation**
- **Backtesting**
- **Walk-Forward Analysis**
- **Monte Carlo Simulation**

## 📊 学習データ

### 特徴量
- 選手成績・スタート展示
- 艇性能・コンディション
- 天候・風向・波高
- オッズ・人気度

### ラベル
- 3連単的中パターン
- 3連複的中パターン
- 期待値
- リスク指標

## 🎯 最適化目標

### 主要指標
- **的中率** 最大化
- **期待値** 最大化
- **シャープレシオ** 最大化
- **最大ドローダウン** 最小化

### 制約条件
- 資金管理
- リスク制限
- 取引頻度制限
- 分散投資

## 📈 可視化機能

### 学習過程
- 損失関数推移
- 報酬推移
- 探索率変化
- パフォーマンス指標

### 最適化結果
- パラメータ重要度
- 最適化履歴
- パフォーマンス比較
- 収束性分析 