# Kyotei Prediction - Google Colab版

## 🚀 概要

このプロジェクトは競艇予測のための機械学習システムです。Google Colab環境で実行できるように最適化されています。

## 📋 前提条件

- Google Colabアカウント
- インターネット接続
- 分析対象のJSONファイル（オプション）

## 🛠️ セットアップ手順

### 1. 新しいColabノートブックを作成

Google Colabで新しいノートブックを作成してください。

### 2. 必要なパッケージをインストール

```python
# 必要なパッケージをインストール
!pip install numpy pandas matplotlib seaborn scikit-learn optuna stable-baselines3 gymnasium torch flask flask-caching requests beautifulsoup4 lxml pytest pytest-cov pytest-html
```

### 3. 統合スクリプトをアップロード

以下のファイルをColabにアップロードしてください：
- `colab_integration.py` (新規追加)
- `colab_setup.py`
- `analysis_202401_results_colab.py`

### 4. 統合スクリプトを実行

```python
# 統合スクリプトを実行（推奨）
!python colab_integration.py
```

または

```python
# 従来のセットアップスクリプトを実行
!python colab_setup.py
```

## 📊 分析の実行

### 基本的な分析

```python
# 分析スクリプトを実行
!python analysis_202401_results_colab.py
```

### カスタムデータでの分析

1. **JSONファイルをアップロード**

```python
from google.colab import files
uploaded = files.upload()
```

2. **分析を実行**

```python
!python analysis_202401_results_colab.py
```

## 🎯 統合スクリプトの機能

### 新機能: `colab_integration.py`

このスクリプトは以下の機能を提供します：

1. **自動セットアップ**
   - 必要なディレクトリ構造の作成
   - Colab用設定ファイルの生成
   - サンプルデータの作成

2. **予測エンジン**
   - 5種類の予測アルゴリズム
   - 3連単確率計算
   - リアルタイム予測

3. **デモ実行**
   - サンプルデータでの予測実行
   - 各アルゴリズムの比較
   - 3連単確率の表示

### 利用可能なアルゴリズム

1. **basic** - 基本アルゴリズム
2. **rating_weighted** - レーティング重視
3. **equipment_focused** - 機材重視
4. **comprehensive** - 総合アルゴリズム
5. **relative_strength** - 相対強度

## 📁 ファイル構造

```
/content/
├── colab_integration.py              # 統合スクリプト（新規）
├── colab_setup.py                    # セットアップスクリプト
├── analysis_202401_results_colab.py  # 分析スクリプト
├── colab_prediction_engine.py        # 予測エンジン（自動生成）
├── colab_settings.json               # 設定ファイル（自動生成）
├── graduated_reward_optimization_*.json  # 最適化結果ファイル
├── kyotei_predictor/                 # プロジェクトディレクトリ
│   ├── data/                        # データディレクトリ
│   ├── logs/                        # ログディレクトリ
│   └── outputs/                     # 出力ディレクトリ
├── optuna_results/                  # Optuna結果
├── optuna_studies/                  # Optuna研究
└── optuna_models/                   # 保存されたモデル
```

## 📈 出力ファイル

分析が完了すると、以下のファイルが生成されます：

- `analysis_202401_results_colab.png` - 可視化結果
- `colab_prediction_results.json` - 予測結果
- コンソール出力 - 詳細な分析結果

## 📥 結果のダウンロード

```python
from google.colab import files
files.download('analysis_202401_results_colab.png')
files.download('colab_prediction_results.json')
```

## 🔧 トラブルシューティング

### よくある問題

1. **ファイルが見つからない**
   - JSONファイルが正しくアップロードされているか確認
   - ファイル名が正しいか確認

2. **パッケージのインストールエラー**
   - インターネット接続を確認
   - ランタイムを再起動してから再実行

3. **メモリ不足**
   - ランタイムタイプを「GPU」または「TPU」に変更
   - 大きなファイルを分割して処理

### デバッグ用コマンド

```python
# 現在のディレクトリを確認
!pwd

# ファイル一覧を表示
!ls -la

# Pythonバージョンを確認
!python --version

# パッケージ一覧を確認
!pip list
```

## 📚 利用可能な機能

### 分析機能

- **パラメータ分布分析**: 最適化パラメータの統計分析
- **スコア分布分析**: 試行結果の統計分析
- **相関分析**: パラメータとスコアの相関関係
- **可視化**: 12種類のグラフによる詳細な可視化
- **サマリーレポート**: 分析結果の要約

### 予測機能（新規）

- **5種類の予測アルゴリズム**: 異なるアプローチでの予測
- **3連単確率計算**: 組み合わせ確率の算出
- **リアルタイム予測**: 即座に結果を表示
- **アルゴリズム比較**: 複数アルゴリズムの性能比較

### 可視化グラフ

1. スコア分布
2. スコアの時系列変化
3. 学習率分布
4. バッチサイズ分布
5. gamma分布
6. n_epochs分布
7. 学習率 vs スコア
8. gamma vs スコア
9. バッチサイズ vs スコア
10. n_epochs vs スコア
11. パラメータ相関ヒートマップ
12. バッチサイズ別スコア分布

## 🎯 カスタマイズ

### 独自の分析を追加

```python
# カスタム分析関数を追加
def custom_analysis(results):
    # 独自の分析ロジック
    pass

# メインスクリプトに追加
custom_analysis(results)
```

### パラメータの調整

```python
# 分析パラメータを調整
def analyze_score_distribution(results, threshold_high=8.0, threshold_medium=6.0):
    # カスタム閾値で分析
    pass
```

### 予測エンジンのカスタマイズ

```python
# 独自の予測アルゴリズムを追加
from colab_prediction_engine import ColabPredictionEngine

engine = ColabPredictionEngine()
# カスタムアルゴリズムを追加
engine.algorithms['custom'] = custom_algorithm
```

## 📞 サポート

問題が発生した場合は、以下を確認してください：

1. エラーメッセージの詳細
2. 使用しているファイルの形式
3. Colabのランタイム設定

## 🔄 更新履歴

- **v1.0.0**: 初回リリース
- **v1.1.0**: Colab対応版追加
- **v1.2.0**: エラーハンドリング強化
- **v1.3.0**: 統合スクリプト追加（新規）

## 📄 ライセンス

このプロジェクトはMITライセンスの下で公開されています。 