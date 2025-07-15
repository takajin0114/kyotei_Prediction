"""
データ前処理・特徴量生成バッチ

- 役割: 生データ（race_data_*.json）から特徴量データ（feature_data.csv等）を一括生成
- 使い方:
    python kyotei_predictor/pipelines/data_preprocessor.py --input-dir kyotei_predictor/data/raw --output kyotei_predictor/data/processed/feature_data.csv
    # テスト用: --max-files 100 などで件数制限可
- 出力: 指定CSVファイル（特徴量テーブル）
- 詳細: pipelines/README.md, docs/integration_design.md 参照
"""
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer

class DataPreprocessor:
    """競艇データの前処理・特徴量生成を行うクラス"""
    def __init__(self):
        # 数値特徴量の処理
        numeric_features = ['win_rate', 'local_win_rate', 'motor_win_rate']
        numeric_transformer = Pipeline(steps=[
            ('imputer', SimpleImputer(strategy='median')),
            ('scaler', StandardScaler())
        ])

        # カテゴリカル特徴量の処理
        categorical_features = ['boat_class', 'weather_condition']
        categorical_transformer = Pipeline(steps=[
            ('imputer', SimpleImputer(strategy='constant', fill_value='missing')),
            ('onehot', OneHotEncoder(handle_unknown='ignore'))
        ])

        # カラムごとの変換を定義
        self.preprocessor = ColumnTransformer(
            transformers=[
                ('num', numeric_transformer, numeric_features),
                ('cat', categorical_transformer, categorical_features)
            ])

    def fit_transform(self, raw_data: dict) -> pd.DataFrame:
        """
        生データから特徴量を生成（1レース分）
        Args:
            raw_data (dict): レースデータの辞書
        Returns:
            pd.DataFrame: 特徴量データフレーム
        """
        features = self._create_base_features(raw_data)
        return self.preprocessor.fit_transform(features)

    def _create_base_features(self, race_data: dict) -> pd.DataFrame:
        """
        競艇データから基本特徴量を抽出（存在する情報のみ）
        Args:
            race_data (dict): レースデータの辞書
        Returns:
            pd.DataFrame: 特徴量データフレーム
        """
        features = []
        for entry in race_data['race_entries']:
            features.append({
                'win_rate': entry.get('performance', {}).get('rate_in_all_stadium', 0),
                'local_win_rate': entry.get('performance', {}).get('rate_in_event_going_stadium', 0),
                'motor_win_rate': entry.get('motor', {}).get('quinella_rate', 0),
                'boat_class': entry.get('racer', {}).get('current_rating', 'B1'),
                'weather_condition': race_data.get('weather_condition', {}).get('weather', 'FINE'),
            })
        return pd.DataFrame(features)

if __name__ == '__main__':
    import argparse
    import glob
    import json
    import os
    parser = argparse.ArgumentParser(description='競艇データ一括前処理スクリプト')
    parser.add_argument('--input-dir', type=str, default='../data/raw', help='入力ディレクトリ（race_data_*.jsonが格納されている場所）')
    parser.add_argument('--output', type=str, default='../data/processed/feature_data.csv', help='出力CSVファイル名')
    parser.add_argument('--max-files', type=int, default=None, help='最大処理ファイル数（テスト用）')
    args = parser.parse_args()

    files = sorted(glob.glob(os.path.join(args.input_dir, 'race_data_*.json')))
    if args.max_files:
        files = files[:args.max_files]
    print(f"処理対象ファイル数: {len(files)}")
    dfs = []
    prep = DataPreprocessor()
    for f in files:
        with open(f, encoding='utf-8') as fp:
            d = json.load(fp)
            df = prep._create_base_features(d)
            dfs.append(df)
    if dfs:
        df_all = pd.concat(dfs, ignore_index=True)
        os.makedirs(os.path.dirname(args.output), exist_ok=True)
        df_all.to_csv(args.output, index=False, encoding='utf-8-sig')
        print(f"出力: {args.output} (shape={df_all.shape})")
    else:
        print("処理対象データがありませんでした")

    # 既存のテスト実行部分（1ファイルのみ）も残す
    # import json
    # with open('../data/complete_race_data_20240615_KIRYU_R1.json') as f:
    #     data = json.load(f)
    # preprocessor = DataPreprocessor()
    # processed = preprocessor.fit_transform(data)
    # print(f"生成された特徴量の形状: {processed.shape}")
