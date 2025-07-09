import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer

class DataPreprocessor:
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

    def fit_transform(self, raw_data):
        """生データから特徴量を生成"""
        features = self._create_base_features(raw_data)
        return self.preprocessor.fit_transform(features)

    def _create_base_features(self, race_data):
        """競艇データから基本特徴量を抽出（存在する情報のみ）"""
        features = []
        for entry in race_data['race_entries']:
            features.append({
                'win_rate': entry.get('performance', {}).get('rate_in_all_stadium', 0),
                'local_win_rate': entry.get('performance', {}).get('rate_in_event_going_stadium', 0),
                'motor_win_rate': entry.get('motor', {}).get('quinella_rate', 0),
                'boat_class': entry.get('racer', {}).get('current_rating', 'B1'),
                'weather_condition': race_data.get('weather_condition', {}).get('weather', 'FINE'),
                # 今後拡張例: 'boat_quinella_rate': entry.get('boat', {}).get('quinella_rate', 0),
                #           'start_time': ...
            })
        return pd.DataFrame(features)

if __name__ == '__main__':
    # テスト実行用
    import json
    with open('../data/complete_race_data_20240615_KIRYU_R1.json') as f:
        data = json.load(f)
    preprocessor = DataPreprocessor()
    processed = preprocessor.fit_transform(data)
    print(f"生成された特徴量の形状: {processed.shape}")
