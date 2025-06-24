
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
            },
            'recent_form': {
                'formula': lambda x: np.log1p(x['recent_wins'] / (x['recent_races'] + 1)),
                'description': '最近の調子（直近10レース勝率）'
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
                df['recent_wins'] = df[['recent_wins', 'recent_races']].min(axis=1)
                self.logger.warning("異常値を自動修正しました")
            else:
                self._validate_input(df)
                
            # 基本特徴量の計算
            for feature, config in self.feature_config.items():
                try:
                    df[feature] = config['formula'](df)
                except KeyError as e:
                    self.logger.error(f"特徴量計算エラー: {e}")
                    
            # 交互作用特徴量
            df['win_motor_synergy'] = df['win_rate'] * df['motor_win_rate']
            
            return df
            
        except Exception as e:
            self.logger.exception("特徴量生成中にエラーが発生しました")
            raise

    def _validate_input(self, df):
        """異常値チェック"""
        # 勝率の範囲検証 (0-100%)
        # 勝率の範囲検証
        invalid_win_rates = df[(df['win_rate'] < 0) | (df['win_rate'] > 100)]['win_rate']
        if not invalid_win_rates.empty:
            raise ValueError(f"異常値: 勝率値 {invalid_win_rates.values} が0-100%の範囲外です")
            
        # モーター勝率の範囲検証
        invalid_motor_rates = df[(df['motor_win_rate'] < 0) | (df['motor_win_rate'] > 100)]['motor_win_rate']
        if not invalid_motor_rates.empty:
            raise ValueError(f"異常値: モーター勝率 {invalid_motor_rates.values} が0-100%の範囲外です")
            
        # 最近のレース数整合性
        invalid_races = df[df['recent_wins'] > df['recent_races']][['recent_wins', 'recent_races']]
        if not invalid_races.empty:
            raise ValueError(
                f"異常値: 勝利数がレース数を超えています\n"
                f"問題データ:\n{invalid_races.to_string()}"
            )

    def get_feature_descriptions(self):
        """特徴量の説明を取得"""
        return {k: v['description'] for k, v in self.feature_config.items()}
