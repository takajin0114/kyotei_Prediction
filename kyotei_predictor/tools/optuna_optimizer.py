import optuna
import numpy as np
import os
import json
from typing import Dict, Any, List
import logging
from datetime import datetime

# RL関連のインポート
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv
from stable_baselines3.common.callbacks import EvalCallback
import gymnasium as gym

# プロジェクト固有のインポート
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pipelines.kyotei_env import KyoteiEnvManager

class KyoteiOptunaOptimizer:
    """
    競艇RLモデルのハイパーパラメータ最適化を行うクラス
    Optunaを使用してPPOの最適パラメータを探索
    """
    
    def __init__(self, data_dir="../data", study_name="kyotei_ppo_optimization"):
        self.data_dir = data_dir
        self.study_name = study_name
        self.study = None
        self.best_params = None
        self.best_value = None
        
        # ログ設定
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        
        # 最適化対象ハイパーパラメータの定義
        self.param_ranges = {
            # PPOの主要パラメータ
            'learning_rate': {
                'type': 'float',
                'range': (1e-5, 1e-2),
                'log': True,
                'description': '学習率（対数スケール）'
            },
            'n_steps': {
                'type': 'int',
                'range': (64, 2048),
                'description': '1エポックあたりのステップ数'
            },
            'batch_size': {
                'type': 'int',
                'range': (32, 256),
                'description': 'バッチサイズ'
            },
            'n_epochs': {
                'type': 'int',
                'range': (1, 20),
                'description': '1エポックあたりの更新回数'
            },
            'gamma': {
                'type': 'float',
                'range': (0.8, 0.999),
                'description': '割引率'
            },
            'gae_lambda': {
                'type': 'float',
                'range': (0.8, 0.999),
                'description': 'GAEのλパラメータ'
            },
            'clip_range': {
                'type': 'float',
                'range': (0.1, 0.4),
                'description': 'PPOのクリップ範囲'
            },
            'clip_range_vf': {
                'type': 'float',
                'range': (0.1, 0.4),
                'description': '価値関数のクリップ範囲'
            },
            'ent_coef': {
                'type': 'float',
                'range': (0.0, 0.1),
                'description': 'エントロピー係数'
            },
            'vf_coef': {
                'type': 'float',
                'range': (0.1, 1.0),
                'description': '価値関数の係数'
            },
            'max_grad_norm': {
                'type': 'float',
                'range': (0.1, 2.0),
                'description': '勾配クリッピングの閾値'
            }
        }
        
        # 最適化設定
        self.optimization_config = {
            'n_trials': 50,  # 試行回数
            'timeout': 3600,  # タイムアウト（秒）
            'direction': 'maximize',  # 最大化（報酬を最大化）
            'metric': 'mean_reward',  # 最適化対象メトリクス
            'eval_freq': 1000,  # 評価頻度
            'n_eval_episodes': 10,  # 評価エピソード数
            'total_timesteps': 10000  # 1試行あたりの学習ステップ数
        }
    
    def create_study(self) -> optuna.Study:
        """Optuna研究を作成"""
        try:
            # 研究の作成（SQLiteで永続化）
            study_name = f"{self.study_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            storage_name = f"sqlite:///optuna_studies/{study_name}.db"
            
            # ディレクトリ作成
            os.makedirs("optuna_studies", exist_ok=True)
            
            self.study = optuna.create_study(
                study_name=study_name,
                storage=storage_name,
                direction=self.optimization_config['direction'],
                load_if_exists=True
            )
            
            self.logger.info(f"Optuna研究を作成しました: {study_name}")
            self.logger.info(f"最適化対象: {self.optimization_config['metric']}")
            self.logger.info(f"試行回数: {self.optimization_config['n_trials']}")
            
            return self.study
            
        except Exception as e:
            self.logger.error(f"研究作成エラー: {e}")
            raise
    
    def suggest_hyperparameters(self, trial: optuna.Trial) -> Dict[str, Any]:
        """試行からハイパーパラメータを提案"""
        params = {}
        
        for param_name, config in self.param_ranges.items():
            if config['type'] == 'float':
                if config.get('log', False):
                    params[param_name] = trial.suggest_float(
                        param_name, 
                        config['range'][0], 
                        config['range'][1], 
                        log=True
                    )
                else:
                    params[param_name] = trial.suggest_float(
                        param_name, 
                        config['range'][0], 
                        config['range'][1]
                    )
            elif config['type'] == 'int':
                params[param_name] = trial.suggest_int(
                    param_name, 
                    config['range'][0], 
                    config['range'][1]
                )
            elif config['type'] == 'categorical':
                params[param_name] = trial.suggest_categorical(
                    param_name, 
                    config['range']
                )
        
        return params
    
    def objective(self, trial: optuna.Trial) -> float:
        """
        最適化の目的関数
        与えられたハイパーパラメータでPPOを学習し、評価報酬を返す
        """
        try:
            # ハイパーパラメータの提案
            params = self.suggest_hyperparameters(trial)
            self.logger.info(f"試行 {trial.number}: パラメータ = {params}")

            # 環境の作成
            env = KyoteiEnvManager(data_dir=self.data_dir)
            if not env.pairs:
                self.logger.error(f"データペアが存在しません。data_dir: {self.data_dir}")
                return -1000.0
            env = DummyVecEnv([lambda: KyoteiEnvManager(data_dir=self.data_dir)])

            # 評価用環境の作成
            eval_env = KyoteiEnvManager(data_dir=self.data_dir)
            if not eval_env.pairs:
                self.logger.error(f"評価用データペアが存在しません。data_dir: {self.data_dir}")
                return -1000.0
            eval_env = DummyVecEnv([lambda: KyoteiEnvManager(data_dir=self.data_dir)])

            # 評価コールバックの設定
            eval_callback = EvalCallback(
                eval_env,
                best_model_save_path=f"./optuna_models/trial_{trial.number}/",
                log_path=f"./optuna_logs/trial_{trial.number}/",
                eval_freq=self.optimization_config['eval_freq'],
                n_eval_episodes=self.optimization_config['n_eval_episodes'],
                deterministic=True,
                render=False
            )

            # PPOモデルの作成
            model = PPO(
                "MlpPolicy",
                env,
                verbose=1,  # ログ出力を有効化
                tensorboard_log=f"./optuna_tensorboard/trial_{trial.number}/",
                **params
            )

            # 学習実行
            try:
                model.learn(
                    total_timesteps=self.optimization_config['total_timesteps'],
                    callback=eval_callback
                )
            except Exception as e:
                self.logger.error(f"学習中にエラー: {e}")
                return -1000.0

            # 評価実行
            try:
                mean_reward = self._evaluate_model(model, eval_env)
            except Exception as e:
                self.logger.error(f"評価中にエラー: {e}")
                mean_reward = -1000.0

            self.logger.info(f"試行 {trial.number}: 平均報酬 = {mean_reward:.2f}")

            # trialごとの中間結果保存
            try:
                model.save(f"./optuna_models/trial_{trial.number}/ppo_model.zip")
            except Exception as e:
                self.logger.warning(f"モデル保存エラー: {e}")

            return mean_reward

        except Exception as e:
            self.logger.error(f"試行 {trial.number} でエラー: {e}")
            return -1000.0  # エラー時は低い報酬を返す
    
    def _evaluate_model(self, model, eval_env, n_eval_episodes: int = 10) -> float:
        """モデルの評価"""
        rewards = []
        
        for _ in range(n_eval_episodes):
            obs = eval_env.reset()
            done = False
            episode_reward = 0
            
            while not done:
                action, _ = model.predict(obs, deterministic=True)
                obs, reward, done, _ = eval_env.step(action)
                episode_reward += reward
            
            rewards.append(episode_reward)
        
        return float(np.mean(rewards))
    
    def run_optimization(self) -> Dict[str, Any]:
        """最適化を実行"""
        try:
            # 研究の作成
            study = self.create_study()
            
            # 最適化実行
            study.optimize(
                self.objective,
                n_trials=self.optimization_config['n_trials'],
                timeout=self.optimization_config['timeout']
            )
            
            # 結果の保存
            self.best_params = study.best_params
            self.best_value = study.best_value
            
            self.logger.info(f"最適化完了!")
            self.logger.info(f"最適パラメータ: {self.best_params}")
            self.logger.info(f"最適値: {self.best_value}")
            
            # 結果をJSONで保存
            self._save_results()
            
            return {
                'best_params': self.best_params,
                'best_value': self.best_value,
                'study': study
            }
            
        except Exception as e:
            self.logger.error(f"最適化実行エラー: {e}")
            raise
    
    def _save_results(self):
        """最適化結果を保存"""
        results = {
            'timestamp': datetime.now().isoformat(),
            'best_params': self.best_params,
            'best_value': self.best_value,
            'optimization_config': self.optimization_config,
            'param_ranges': self.param_ranges
        }
        
        os.makedirs("optuna_results", exist_ok=True)
        with open(f"optuna_results/optimization_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", 'w') as f:
            json.dump(results, f, indent=2)
        
        self.logger.info("最適化結果を保存しました")

def main():
    """メイン実行関数"""
    optimizer = KyoteiOptunaOptimizer()
    results = optimizer.run_optimization()
    
    print("\n" + "="*50)
    print("最適化完了!")
    print(f"最適パラメータ: {results['best_params']}")
    print(f"最適値: {results['best_value']}")
    print("="*50)

if __name__ == "__main__":
    main() 