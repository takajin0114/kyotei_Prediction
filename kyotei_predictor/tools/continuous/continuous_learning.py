#!/usr/bin/env python3
"""
継続的学習システム（Phase 4）
既存の最良モデルを基に、新しいデータで継続学習を行う
"""

import os
import sys
import json
import numpy as np
from datetime import datetime
from typing import Dict, Any, List, Optional
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv
from stable_baselines3.common.monitor import Monitor
import logging

# プロジェクトルートをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from kyotei_predictor.pipelines.kyotei_env import KyoteiEnvManager

class ContinuousLearningSystem:
    """
    継続的学習システム
    
    特徴:
    - 既存の最良モデルを読み込み
    - 新しいデータで継続学習
    - 学習履歴の記録
    - モデルの自動更新
    """
    
    def __init__(self, base_model_path: str):
        self.base_model_path = base_model_path
        self.current_model = None
        self.learning_history = []
        self.performance_history = []
        
    def load_best_model(self) -> PPO:
        """
        最良モデルを読み込み
        
        Returns:
            読み込まれたPPOモデル
        """
        if not os.path.exists(self.base_model_path):
            raise FileNotFoundError(f"Model not found: {self.base_model_path}")
        
        self.current_model = PPO.load(self.base_model_path)
        logging.info(f"Best model loaded from {self.base_model_path}")
        return self.current_model
    
    def continue_learning(self, new_data_dir: str, additional_steps: int = 50000, 
                        eval_episodes: int = 1000) -> PPO:
        """
        継続学習の実行
        
        Args:
            new_data_dir: 新しいデータディレクトリ
            additional_steps: 追加学習ステップ数
            eval_episodes: 評価エピソード数
            
        Returns:
            更新されたPPOモデル
        """
        if self.current_model is None:
            self.load_best_model()
        
        # 新しいデータで環境を作成
        def make_env():
            env = KyoteiEnvManager(data_dir=new_data_dir)
            env = Monitor(env)
            return env
        
        train_env = DummyVecEnv([make_env])
        eval_env = DummyVecEnv([make_env])
        
        # 継続学習の実行
        logging.info(f"Starting continuous learning with {additional_steps} steps")
        self.current_model.set_env(train_env)
        self.current_model.learn(total_timesteps=additional_steps)
        
        # 学習履歴を記録
        learning_record = {
            'timestamp': datetime.now().isoformat(),
            'additional_steps': additional_steps,
            'data_dir': new_data_dir,
            'base_model_path': self.base_model_path
        }
        self.learning_history.append(learning_record)
        
        # 性能評価
        performance = self.evaluate_current_model(eval_env, n_eval_episodes=eval_episodes)
        self.performance_history.append(performance)
        
        logging.info(f"Continuous learning completed. Performance: {performance}")
        return self.current_model
    
    def evaluate_current_model(self, eval_env, n_eval_episodes: int = 1000) -> Dict[str, Any]:
        """
        現在のモデルの評価
        
        Args:
            eval_env: 評価環境
            n_eval_episodes: 評価エピソード数
            
        Returns:
            評価結果
        """
        from kyotei_predictor.tools.optimization.optimize_graduated_reward import evaluate_model
        
        if self.current_model is None:
            raise ValueError("No model loaded")
        
        results = evaluate_model(self.current_model, eval_env, n_eval_episodes=n_eval_episodes)
        results['timestamp'] = datetime.now().isoformat()
        results['model_path'] = self.base_model_path
        
        return results
    
    def save_updated_model(self, output_path: Optional[str] = None) -> str:
        """
        更新されたモデルを保存
        
        Args:
            output_path: 保存先パス（Noneの場合は自動生成）
            
        Returns:
            保存されたパス
        """
        if self.current_model is None:
            raise ValueError("No model to save")
        
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"{self.base_model_path}_updated_{timestamp}"
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        self.current_model.save(output_path)
        
        # 学習履歴と性能履歴を保存
        history_path = f"{output_path}_history.json"
        history_data = {
            'learning_history': self.learning_history,
            'performance_history': self.performance_history,
            'base_model_path': self.base_model_path,
            'updated_timestamp': datetime.now().isoformat()
        }
        
        with open(history_path, 'w', encoding='utf-8') as f:
            json.dump(history_data, f, indent=2, ensure_ascii=False)
        
        logging.info(f"Updated model saved to {output_path}")
        return output_path
    
    def get_learning_summary(self) -> Dict[str, Any]:
        """
        学習履歴のサマリーを取得
        
        Returns:
            学習サマリー
        """
        if not self.learning_history:
            return {'message': 'No learning history available'}
        
        total_steps = sum(record['additional_steps'] for record in self.learning_history)
        learning_sessions = len(self.learning_history)
        
        # 性能の推移
        hit_rates = [p.get('hit_rate', 0) for p in self.performance_history]
        mean_rewards = [p.get('mean_reward', 0) for p in self.performance_history]
        
        summary = {
            'total_learning_sessions': learning_sessions,
            'total_additional_steps': total_steps,
            'performance_trend': {
                'hit_rates': hit_rates,
                'mean_rewards': mean_rewards,
                'latest_hit_rate': hit_rates[-1] if hit_rates else 0,
                'latest_mean_reward': mean_rewards[-1] if mean_rewards else 0
            },
            'learning_history': self.learning_history
        }
        
        return summary

class AutoUpdateSystem:
    """
    自動更新システム
    
    特徴:
    - 定期的なモデル更新
    - 性能監視
    - 自動バックアップ
    """
    
    def __init__(self, continuous_learning_system: ContinuousLearningSystem):
        self.cls = continuous_learning_system
        self.update_schedule = []
        self.backup_paths = []
    
    def schedule_update(self, data_dir: str, steps: int = 50000, 
                      interval_hours: int = 24) -> None:
        """
        更新スケジュールを設定
        
        Args:
            data_dir: データディレクトリ
            steps: 学習ステップ数
            interval_hours: 更新間隔（時間）
        """
        schedule = {
            'data_dir': data_dir,
            'steps': steps,
            'interval_hours': interval_hours,
            'last_update': None
        }
        self.update_schedule.append(schedule)
        logging.info(f"Update scheduled for {data_dir} every {interval_hours} hours")
    
    def check_and_update(self) -> bool:
        """
        更新が必要かチェックして実行
        
        Returns:
            更新が実行されたかどうか
        """
        current_time = datetime.now()
        
        for schedule in self.update_schedule:
            if schedule['last_update'] is None:
                # 初回更新
                self._perform_update(schedule)
                return True
            
            # 間隔チェック
            last_update = datetime.fromisoformat(schedule['last_update'])
            hours_since_update = (current_time - last_update).total_seconds() / 3600
            
            if hours_since_update >= schedule['interval_hours']:
                self._perform_update(schedule)
                return True
        
        return False
    
    def _perform_update(self, schedule: Dict[str, Any]) -> None:
        """
        更新を実行
        
        Args:
            schedule: 更新スケジュール
        """
        try:
            # 継続学習を実行
            self.cls.continue_learning(
                new_data_dir=schedule['data_dir'],
                additional_steps=schedule['steps']
            )
            
            # 更新されたモデルを保存
            updated_path = self.cls.save_updated_model()
            
            # バックアップを作成
            self._create_backup(updated_path)
            
            # スケジュールを更新
            schedule['last_update'] = datetime.now().isoformat()
            
            logging.info(f"Auto-update completed. Model saved to {updated_path}")
            
        except Exception as e:
            logging.error(f"Auto-update failed: {e}")
    
    def _create_backup(self, model_path: str) -> None:
        """
        モデルのバックアップを作成
        
        Args:
            model_path: モデルパス
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"{model_path}_backup_{timestamp}"
        
        # ファイルをコピー
        import shutil
        shutil.copy2(model_path, backup_path)
        
        # 履歴ファイルもコピー
        history_path = f"{model_path}_history.json"
        if os.path.exists(history_path):
            backup_history_path = f"{backup_path}_history.json"
            shutil.copy2(history_path, backup_history_path)
        
        self.backup_paths.append(backup_path)
        logging.info(f"Backup created: {backup_path}")
    
    def get_update_status(self) -> Dict[str, Any]:
        """
        更新状況を取得
        
        Returns:
            更新状況
        """
        status = {
            'scheduled_updates': len(self.update_schedule),
            'backup_count': len(self.backup_paths),
            'last_backup': self.backup_paths[-1] if self.backup_paths else None,
            'schedules': self.update_schedule
        }
        
        return status

def create_continuous_learning_from_best_model(best_model_path: str) -> ContinuousLearningSystem:
    """
    最良モデルから継続的学習システムを作成
    
    Args:
        best_model_path: 最良モデルのパス
        
    Returns:
        継続的学習システム
    """
    cls = ContinuousLearningSystem(best_model_path)
    cls.load_best_model()
    return cls

if __name__ == "__main__":
    # テスト実行
    logging.basicConfig(level=logging.INFO)
    
    # 最良モデルのパスを指定
    best_model_path = "kyotei_predictor/optuna_models/graduated_reward_best/best_model.zip"
    
    if os.path.exists(best_model_path):
        print(f"Creating continuous learning system from {best_model_path}")
        
        # 継続的学習システムを作成
        cls = create_continuous_learning_from_best_model(best_model_path)
        
        # 新しいデータディレクトリ
        new_data_dir = "kyotei_predictor/data/raw"
        
        if os.path.exists(new_data_dir):
            print(f"Starting continuous learning with data from {new_data_dir}")
            
            # 継続学習を実行
            cls.continue_learning(new_data_dir, additional_steps=10000)
            
            # 更新されたモデルを保存
            updated_path = cls.save_updated_model()
            print(f"Updated model saved to {updated_path}")
            
            # 学習サマリーを表示
            summary = cls.get_learning_summary()
            print(f"Learning summary: {summary}")
        else:
            print(f"Data directory not found: {new_data_dir}")
    else:
        print(f"Best model not found: {best_model_path}") 