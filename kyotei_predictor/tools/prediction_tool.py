#!/usr/bin/env python3
"""
予測ツール
"""

import os
import sys
import json
import logging
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any

# プロジェクトルートを動的に取得
def get_project_root() -> Path:
    """プロジェクトルートを動的に検出"""
    current_file = Path(__file__)
    project_root = current_file.parent.parent.parent
    
    # Google Colab環境の検出
    if str(project_root).startswith('/content/'):
        return Path('/content/kyotei_Prediction')
    
    return project_root

PROJECT_ROOT = get_project_root()

# プロジェクトルートをパスに追加
sys.path.append(str(PROJECT_ROOT))

from kyotei_predictor.pipelines.kyotei_env import KyoteiEnvManager

class PredictionTool:
    """予測ツールクラス"""
    
    def __init__(self, log_level=logging.INFO):
        """初期化"""
        self.project_root = PROJECT_ROOT
        self.log_dir = self.project_root / "kyotei_predictor" / "logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # ログ設定
        log_file = self.log_dir / "prediction_tool.log"
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        self.logger.info("PredictionTool初期化完了")
    
    def predict_races(self, predict_date: str, venues: List[str] = None) -> Optional[Dict]:
        """
        レース予測を実行
        
        Args:
            predict_date: 予測対象日
            venues: 対象会場リスト
            
        Returns:
            予測結果の辞書
        """
        try:
            self.logger.info(f"予測開始: {predict_date}, 会場: {venues}")
            
            # 環境作成
            env = self.create_prediction_env()
            
            # 予測実行
            predictions = self.run_predictions(env, predict_date, venues)
            
            if predictions:
                result = {
                    'predict_date': predict_date,
                    'venues': venues or [],
                    'predictions': predictions,
                    'timestamp': datetime.now().isoformat()
                }
                
                self.logger.info(f"予測完了: {len(predictions)}件")
                return result
            else:
                self.logger.warning("予測結果が空でした")
                return None
                
        except Exception as e:
            self.logger.error(f"予測実行エラー: {e}")
            return None
    
    def create_prediction_env(self):
        """予測用環境を作成"""
        try:
            # データディレクトリ
            data_dir = self.project_root / "kyotei_predictor" / "data" / "raw"
            
            # 環境作成
            env = KyoteiEnvManager(data_dir=str(data_dir), bet_amount=100)
            
            return env
            
        except Exception as e:
            self.logger.error(f"環境作成エラー: {e}")
            return None
    
    def run_predictions(self, env, predict_date: str, venues: List[str] = None) -> List[Dict]:
        """
        予測を実行
        
        Args:
            env: 予測環境
            predict_date: 予測対象日
            venues: 対象会場リスト
            
        Returns:
            予測結果のリスト
        """
        predictions = []
        
        try:
            # 環境をリセット
            obs = env.reset()
            
            # 予測実行（簡易版）
            for _ in range(10):  # 10レース分の予測
                # ランダムな行動を選択（実際のモデルでは学習済みモデルを使用）
                import numpy as np
                action = np.random.randint(0, 120)
                
                # 環境をステップ
                obs, reward, done, info = env.step(action)
                
                # 予測結果を記録
                prediction = {
                    'race_id': f"race_{len(predictions)+1}",
                    'action': action,
                    'reward': reward,
                    'info': info
                }
                predictions.append(prediction)
                
                if done:
                    obs = env.reset()
            
            return predictions
            
        except Exception as e:
            self.logger.error(f"予測実行エラー: {e}")
            return []
    
    def save_prediction_result(self, result: Dict) -> Optional[Path]:
        """
        予測結果を保存
        
        Args:
            result: 予測結果
            
        Returns:
            保存されたファイルのパス
        """
        try:
            # 出力ディレクトリ
            output_dir = self.project_root / "outputs" / "predictions"
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # ファイル名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"prediction_{result['predict_date']}_{timestamp}.json"
            output_path = output_dir / filename
            
            # 保存
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"予測結果を保存: {output_path}")
            return output_path
            
        except Exception as e:
            self.logger.error(f"予測結果保存エラー: {e}")
            return None
    
    def load_model(self, model_path: str):
        """
        学習済みモデルを読み込み
        
        Args:
            model_path: モデルファイルのパス
        """
        try:
            from stable_baselines3 import PPO
            
            model = PPO.load(model_path)
            self.logger.info(f"モデルを読み込み: {model_path}")
            return model
            
        except Exception as e:
            self.logger.error(f"モデル読み込みエラー: {e}")
            return None
    
    def get_prediction_history(self, days: int = 7) -> List[Dict]:
        """
        予測履歴を取得
        
        Args:
            days: 取得日数
            
        Returns:
            予測履歴のリスト
        """
        try:
            history = []
            output_dir = self.project_root / "outputs" / "predictions"
            
            if output_dir.exists():
                # 指定日数分のファイルを取得
                cutoff_date = datetime.now() - timedelta(days=days)
                
                for file_path in output_dir.glob("prediction_*.json"):
                    if file_path.stat().st_mtime > cutoff_date.timestamp():
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                data = json.load(f)
                                history.append(data)
                        except Exception as e:
                            self.logger.warning(f"履歴ファイル読み込みエラー {file_path}: {e}")
            
            return history
            
        except Exception as e:
            self.logger.error(f"予測履歴取得エラー: {e}")
            return []

def main():
    """メイン関数"""
    tool = PredictionTool()
    
    # 今日の日付で予測実行
    today = date.today().strftime('%Y-%m-%d')
    
    result = tool.predict_races(today)
    
    if result:
        output_path = tool.save_prediction_result(result)
        print(f"予測完了: {len(result['predictions'])}件")
        print(f"結果保存: {output_path}")
    else:
        print("予測に失敗しました")

if __name__ == "__main__":
    main() 