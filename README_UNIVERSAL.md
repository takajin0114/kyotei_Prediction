# Kyotei Prediction - 汎用版

## 🚀 概要

このプロジェクトは競艇予測のための機械学習システムです。Google Colab、Jupyter、ローカル環境など、複数の環境で実行できるように汎用化されています。

## 📋 対応環境

- **Google Colab** - クラウドベースのJupyter環境
- **Jupyter Notebook** - ローカルJupyter環境
- **ローカル環境** - Windows、Linux、macOS
- **その他のクラウド環境** - AWS、GCP、Azureなど

## 🛠️ セットアップ手順

### 1. 環境の選択

#### Google Colab
```python
# 新しいColabノートブックを作成
# 必要なパッケージをインストール
!pip install numpy pandas matplotlib seaborn scikit-learn optuna stable-baselines3 gymnasium torch flask flask-caching requests beautifulsoup4 lxml
```

#### Jupyter Notebook
```bash
# 仮想環境を作成
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# 必要なパッケージをインストール
pip install numpy pandas matplotlib seaborn scikit-learn optuna stable-baselines3 gymnasium torch flask flask-caching requests beautifulsoup4 lxml jupyter
```

#### ローカル環境
```bash
# 仮想環境を作成
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# 必要なパッケージをインストール
pip install numpy pandas matplotlib seaborn scikit-learn optuna stable-baselines3 gymnasium torch flask flask-caching requests beautifulsoup4 lxml
```

### 2. 汎用スクリプトをアップロード/配置

以下のファイルを環境に配置してください：
- `universal_integration.py` (新規追加)
- `analysis_202401_results_colab.py`

### 3. 汎用スクリプトを実行

```python
# 汎用スクリプトを実行
!python universal_integration.py
```

または

```bash
# ローカル環境の場合
python universal_integration.py
```

## 🎯 汎用スクリプトの機能

### 新機能: `universal_integration.py`

このスクリプトは以下の機能を提供します：

1. **自動環境検出**
   - Google Colab環境の検出
   - Jupyter環境の検出
   - ローカル環境の検出

2. **環境固有のセットアップ**
   - 必要なディレクトリ構造の作成
   - 環境に応じた設定ファイルの生成
   - 環境固有のモジュールのインポート

3. **汎用予測エンジン**
   - 5種類の予測アルゴリズム
   - 3連単確率計算
   - 環境に依存しない結果保存

4. **環境固有の機能**
   - Colab: ファイルアップロード/ダウンロード
   - Jupyter: 結果のHTML表示
   - ローカル: Webサーバー起動

### 利用可能なアルゴリズム

1. **basic** - 基本アルゴリズム
2. **rating_weighted** - レーティング重視
3. **equipment_focused** - 機材重視
4. **comprehensive** - 総合アルゴリズム
5. **relative_strength** - 相対強度

## 📁 ファイル構造

```
/
├── universal_integration.py              # 汎用統合スクリプト（新規）
├── universal_prediction_engine.py        # 汎用予測エンジン（自動生成）
├── universal_settings.json               # 汎用設定ファイル（自動生成）
├── colab_specific.py                    # Colab用スクリプト（自動生成）
├── jupyter_specific.py                  # Jupyter用スクリプト（自動生成）
├── local_specific.py                    # ローカル用スクリプト（自動生成）
├── universal_prediction_results.json     # 予測結果（自動生成）
├── analysis_202401_results_colab.py     # 分析スクリプト
├── graduated_reward_optimization_*.json  # 最適化結果ファイル
├── kyotei_predictor/                    # プロジェクトディレクトリ
│   ├── data/                           # データディレクトリ
│   ├── logs/                           # ログディレクトリ
│   └── outputs/                        # 出力ディレクトリ
├── optuna_results/                     # Optuna結果
├── optuna_studies/                     # Optuna研究
└── optuna_models/                      # 保存されたモデル
```

## 📈 出力ファイル

実行が完了すると、以下のファイルが生成されます：

- `universal_prediction_results.json` - 予測結果
- `universal_settings.json` - 環境設定
- `colab_specific.py` / `jupyter_specific.py` / `local_specific.py` - 環境固有スクリプト
- コンソール出力 - 詳細な分析結果

## 🔧 環境別の使用方法

### Google Colab

```python
# 1. パッケージをインストール
!pip install numpy pandas matplotlib seaborn scikit-learn optuna stable-baselines3 gymnasium torch flask flask-caching requests beautifulsoup4 lxml

# 2. 汎用スクリプトをアップロード

# 3. 汎用スクリプトを実行
!python universal_integration.py

# 4. ファイルをアップロード
from google.colab import files
uploaded = files.upload()

# 5. 結果をダウンロード
files.download('universal_prediction_results.json')
```

### Jupyter Notebook

```python
# 1. パッケージをインストール
!pip install numpy pandas matplotlib seaborn scikit-learn optuna stable-baselines3 gymnasium torch flask flask-caching requests beautifulsoup4 lxml

# 2. 汎用スクリプトを実行
!python universal_integration.py

# 3. 結果を表示
from jupyter_specific import display_results
import json
with open('universal_prediction_results.json', 'r') as f:
    results = json.load(f)
display_results(results)
```

### ローカル環境

```bash
# 1. 仮想環境を作成
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# 2. パッケージをインストール
pip install numpy pandas matplotlib seaborn scikit-learn optuna stable-baselines3 gymnasium torch flask flask-caching requests beautifulsoup4 lxml

# 3. 汎用スクリプトを実行
python universal_integration.py

# 4. 結果を確認
python local_specific.py
```

## 🔧 トラブルシューティング

### よくある問題

1. **環境検出エラー**
   - 手動で環境を指定: `UniversalIntegration("colab")`
   - 環境情報を確認: `EnvironmentDetector.get_environment_info()`

2. **パッケージのインストールエラー**
   - インターネット接続を確認
   - 仮想環境を再作成
   - パッケージを個別にインストール

3. **ファイルパスエラー**
   - 作業ディレクトリを確認
   - 相対パスを使用
   - 絶対パスを避ける

### デバッグ用コマンド

```python
# 環境情報を確認
from universal_integration import EnvironmentDetector
print(EnvironmentDetector.get_environment_info())

# 環境を手動指定
integration = UniversalIntegration("local")  # colab, jupyter, local

# 設定を確認
import json
with open('universal_settings.json', 'r') as f:
    settings = json.load(f)
print(settings)
```

## 📚 利用可能な機能

### 分析機能

- **パラメータ分布分析**: 最適化パラメータの統計分析
- **スコア分布分析**: 試行結果の統計分析
- **相関分析**: パラメータとスコアの相関関係
- **可視化**: 12種類のグラフによる詳細な可視化
- **サマリーレポート**: 分析結果の要約

### 予測機能

- **5種類の予測アルゴリズム**: 異なるアプローチでの予測
- **3連単確率計算**: 組み合わせ確率の算出
- **環境非依存**: どの環境でも同じ結果
- **結果保存**: 自動的にJSONファイルに保存

### 環境固有機能

- **Colab**: ファイルアップロード/ダウンロード
- **Jupyter**: HTML形式での結果表示
- **ローカル**: Webサーバー起動、ファイルブラウザ

## 🎯 カスタマイズ

### 独自の予測アルゴリズムを追加

```python
from universal_prediction_engine import UniversalPredictionEngine

engine = UniversalPredictionEngine()

def custom_algorithm(race_data):
    # 独自の予測ロジック
    pass

# アルゴリズムを追加
engine.algorithms['custom'] = custom_algorithm
```

### 環境固有の機能を追加

```python
# 環境固有のスクリプトを編集
# colab_specific.py, jupyter_specific.py, local_specific.py
```

### 設定のカスタマイズ

```python
# universal_settings.json を編集
# または設定を動的に変更
integration = UniversalIntegration()
settings = integration.create_universal_settings()
```

## 📞 サポート

問題が発生した場合は、以下を確認してください：

1. **環境情報**: `EnvironmentDetector.get_environment_info()`
2. **エラーメッセージ**: 詳細なエラー内容
3. **パッケージバージョン**: `pip list`
4. **Pythonバージョン**: `python --version`

## 🔄 更新履歴

- **v1.0.0**: 初回リリース
- **v1.1.0**: Colab対応版追加
- **v1.2.0**: エラーハンドリング強化
- **v1.3.0**: 統合スクリプト追加
- **v2.0.0**: 汎用化対応（新規）

## 📄 ライセンス

このプロジェクトはMITライセンスの下で公開されています。 