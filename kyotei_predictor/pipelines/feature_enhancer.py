import pandas as pd
import numpy as np
import logging

class FeatureEnhancer:
    """競艇データの特徴量エンジニアリングを行うクラス
    
    機能:
    - 基本特徴量の生成（速度指標、安定性指標など）
    - 異常値検出と自動修正
    - ログ記録
    
    使用例:
    >>> enhancer = FeatureEnhancer()
    >>> df = pd.DataFrame(...)
    >>> enhanced_df = enhancer.enhance(df, auto_correct=True)
    """
    def __init__(self):
        # ロガー設定
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.WARNING)
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(handler)
        
        self.feature_config = {
            'speed_index': {
                'formula': lambda x: x['win_rate']*0.6 + x['motor_win_rate']*0.4,
                'description': '速度指標（勝率とモーター勝率の加重平均）'
            },
            'stability': {
                'formula': lambda x: x['win_rate'] / (x['local_win_rate'] + 0.01),
                'description': '安定性指標（全国勝率/当地勝率）'
            }
        }

    def enhance(self, df, auto_correct=False):
        """基本特徴量を拡張
        Args:
            df: 入力データフレーム
            auto_correct: Trueの場合、異常値を自動修正
        """
        try:
            if auto_correct:
                # 自動修正処理
                df['win_rate'] = df['win_rate'].clip(0, 100)
                df['motor_win_rate'] = df['motor_win_rate'].clip(0, 100)
                self.logger.warning("異常値を自動修正しました")
            else:
                self._validate_input(df)
                
            # 既存の特徴量も含めて全て欠損値を0で埋める
            for col in df.columns:
                if df[col].dtype.kind in 'biufc':  # 数値型
                    df[col] = df[col].fillna(0)
                else:
                    df[col] = df[col].fillna('')

            # 基本特徴量の計算
            for feature, config in self.feature_config.items():
                try:
                    df[feature] = config['formula'](df)
                except KeyError as e:
                    self.logger.error(f"特徴量計算エラー: {e}")
                    
            # 交互作用特徴量
            df['win_motor_synergy'] = (df['win_rate'].fillna(0).astype(float)) * (df['motor_win_rate'].fillna(0).astype(float))
            # 級別×モーター性能（A1=3, A2=2, B1=1, B2=0でエンコード）
            class_map = {'A1': 3, 'A2': 2, 'B1': 1, 'B2': 0}
            df['boat_class_code'] = df['boat_class'].map(class_map).fillna(0).astype(int)
            df['class_motor_interaction'] = df['boat_class_code'] * df['motor_win_rate'].fillna(0).astype(float)
            # 勝率×天候（天候をone-hotエンコードして掛け算）
            for weather in ['晴', '曇', '雨', '雪', '霧', '不明']:
                col = f'win_rate_weather_{weather}'
                df[col] = df['win_rate'].fillna(0).astype(float) * (df['weather_condition'].fillna('') == weather).astype(int)
            # モーター性能×ボート性能
            if 'boat_win_rate' in df.columns:
                df['motor_boat_synergy'] = df['motor_win_rate'].fillna(0).astype(float) * df['boat_win_rate'].fillna(0).astype(float)
            # 荒天リスクフラグ（風速>5m/s or 波高>10cm）
            if 'wind_speed' in df.columns:
                wind = df['wind_speed'].fillna(0).astype(float)
            else:
                wind = pd.Series(0, index=df.index)
            if 'wave_height' in df.columns:
                wave = df['wave_height'].fillna(0).astype(float)
            else:
                wave = pd.Series(0, index=df.index)
            df['rough_weather_flag'] = ((wind > 5) | (wave > 10)).astype(int)
            
            # 欠損値チェック: 1つでもNaN/Noneが残っていれば全カラムの欠損数をprintし、エラーで停止
            nulls = df.isnull().sum()
            if nulls.sum() > 0:
                print('【欠損値検出】各カラムの欠損数:')
                print(nulls[nulls > 0])
                raise ValueError('特徴量生成後に欠損値が残っています。該当カラムを確認してください。')
            
            return df
            
        except Exception as e:
            self.logger.exception("特徴量生成中にエラーが発生しました")
            raise

    def _validate_input(self, df):
        """異常値チェック"""
        # 勝率の範囲検証 (0-100%)
        invalid_win_rates = df[(df['win_rate'] < 0) | (df['win_rate'] > 100)]['win_rate']
        if not invalid_win_rates.empty:
            raise ValueError(f"異常値: 勝率値 {invalid_win_rates.values} が0-100%の範囲外です")
        # モーター勝率の範囲検証
        invalid_motor_rates = df[(df['motor_win_rate'] < 0) | (df['motor_win_rate'] > 100)]['motor_win_rate']
        if not invalid_motor_rates.empty:
            raise ValueError(f"異常値: モーター勝率 {invalid_motor_rates.values} が0-100%の範囲外です")

    def get_feature_descriptions(self):
        """特徴量の説明を取得"""
        return {k: v['description'] for k, v in self.feature_config.items()}
