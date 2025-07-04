# config ディレクトリ

このディレクトリは、プロジェクト全体で利用する各種設定ファイル（パラメータ、APIキー、パス、定数など）を集約します。

## 主なファイル
- `optuna_config.json` : Optuna最適化用のパラメータ・サーチスペース・実験設定
- その他、今後追加予定の設定ファイル（APIキー、パス設定、定数定義など）

## 運用方針
- 機密情報（APIキー等）は .gitignore で除外推奨
- 設定値のバージョン管理・共有はこのディレクトリで一元化
- スクリプトからは `config/` 配下のファイルを参照

## 使い方例
```python
import json
with open('config/optuna_config.json') as f:
    config = json.load(f)
```

## 備考
- 設定ファイルの追加時はREADMEに用途を追記
- サンプル設定ファイル（*_sample.json等）もここに配置 