import argparse
import os
import json
import logging
from datetime import datetime
import numpy as np
import optuna
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv
from stable_baselines3.common.callbacks import EvalCallback
from kyotei_predictor.pipelines.kyotei_env import KyoteiEnvManager

class KyoteiOptunaOptimizer:
    """
    競艇RLモデルのハイパーパラメータ最適化を行うクラス
    Optunaを使用してPPOの最適パラメータを探索
    """
    def __init__(self, data_dir="kyotei_predictor/data", study_name="kyotei_ppo_optimization"):
        self.data_dir = data_dir
        self.study_name = study_name
        self.study = None
        self.best_params = None
        self.best_value = None
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        if not self.logger.handlers:
            self.logger.addHandler(handler)
        self.param_ranges = {
            'learning_rate': {'type': 'float', 'range': (1e-5, 1e-2), 'log': True},
            'n_steps': {'type': 'int', 'range': (64, 2048)},
            'batch_size': {'type': 'int', 'range': (32, 256)},
            'n_epochs': {'type': 'int', 'range': (1, 20)},
            'gamma': {'type': 'float', 'range': (0.8, 0.999)},
            'gae_lambda': {'type': 'float', 'range': (0.8, 0.999)},
            'clip_range': {'type': 'float', 'range': (0.1, 0.4)},
            'clip_range_vf': {'type': 'float', 'range': (0.1, 0.4)},
            'ent_coef': {'type': 'float', 'range': (0.0, 0.1)},
            'vf_coef': {'type': 'float', 'range': (0.1, 1.0)},
            'max_grad_norm': {'type': 'float', 'range': (0.1, 2.0)}
        }
        self.optimization_config = {
            'n_trials': 50,
            'timeout': 3600,
            'direction': 'maximize',
            'metric': 'mean_reward',
            'eval_freq': 1000,
            'n_eval_episodes': 10,
            'total_timesteps': 10000
        }

    def create_study(self) -> optuna.Study:
        try:
            study_name = f"{self.study_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            storage_name = f"sqlite:///optuna_studies/{study_name}.db"
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

    def suggest_hyperparameters(self, trial: optuna.Trial):
        params = {}
        for param_name, config in self.param_ranges.items():
            if config['type'] == 'float':
                if config.get('log', False):
                    params[param_name] = trial.suggest_float(param_name, config['range'][0], config['range'][1], log=True)
                else:
                    params[param_name] = trial.suggest_float(param_name, config['range'][0], config['range'][1])
            elif config['type'] == 'int':
                params[param_name] = trial.suggest_int(param_name, config['range'][0], config['range'][1])
            elif config['type'] == 'categorical':
                params[param_name] = trial.suggest_categorical(param_name, config['range'])
        return params

    def objective(self, trial: optuna.Trial) -> float:
        try:
            params = self.suggest_hyperparameters(trial)
            self.logger.info(f"試行 {trial.number}: パラメータ = {params}")
            env = KyoteiEnvManager(data_dir=self.data_dir)
            if not env.pairs:
                self.logger.error(f"データペアが存在しません。data_dir: {self.data_dir}")
                return -1000.0
            env = DummyVecEnv([lambda: KyoteiEnvManager(data_dir=self.data_dir)])
            eval_env = KyoteiEnvManager(data_dir=self.data_dir)
            if not eval_env.pairs:
                self.logger.error(f"評価用データペアが存在しません。data_dir: {self.data_dir}")
                return -1000.0
            eval_env = DummyVecEnv([lambda: KyoteiEnvManager(data_dir=self.data_dir)])
            eval_callback = EvalCallback(
                eval_env,
                best_model_save_path=f"./optuna_models/trial_{trial.number}/",
                log_path=f"./optuna_logs/trial_{trial.number}/",
                eval_freq=self.optimization_config['eval_freq'],
                n_eval_episodes=self.optimization_config['n_eval_episodes'],
                deterministic=True,
                render=False
            )
            model = PPO(
                "MlpPolicy",
                env,
                verbose=1,
                tensorboard_log=f"./optuna_tensorboard/trial_{trial.number}/",
                **params
            )
            try:
                model.learn(
                    total_timesteps=self.optimization_config['total_timesteps'],
                    callback=eval_callback
                )
            except Exception as e:
                self.logger.error(f"学習中にエラー: {e}")
                return -1000.0
            try:
                mean_reward = self._evaluate_model(model, eval_env)
            except Exception as e:
                self.logger.error(f"評価中にエラー: {e}")
                mean_reward = -1000.0
            self.logger.info(f"試行 {trial.number}: 平均報酬 = {mean_reward:.2f}")
            try:
                model.save(f"./optuna_models/trial_{trial.number}/ppo_model.zip")
            except Exception as e:
                self.logger.warning(f"モデル保存エラー: {e}")
            return mean_reward
        except Exception as e:
            self.logger.error(f"試行 {trial.number} でエラー: {e}")
            return -1000.0

    def _evaluate_model(self, model, eval_env, n_eval_episodes: int = 10) -> float:
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

    def run_optimization(self):
        try:
            study = self.create_study()
            study.optimize(
                self.objective,
                n_trials=self.optimization_config['n_trials'],
                timeout=self.optimization_config['timeout']
            )
            self.best_params = study.best_params
            self.best_value = study.best_value
            self.logger.info(f"最適化完了!")
            self.logger.info(f"最適パラメータ: {self.best_params}")
            self.logger.info(f"最適値: {self.best_value}")
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
    parser = argparse.ArgumentParser()
    parser.add_argument('--data_dir', type=str, default="kyotei_predictor/data", help='データディレクトリ')
    args = parser.parse_args()
    optimizer = KyoteiOptunaOptimizer(data_dir=args.data_dir)
    results = optimizer.run_optimization()
    print("\n" + "="*50)
    print(f"最適化完了!\n最適パラメータ: {results['best_params']}\n最適値: {results['best_value']}")
    print("="*50)

if __name__ == "__main__":
    main()