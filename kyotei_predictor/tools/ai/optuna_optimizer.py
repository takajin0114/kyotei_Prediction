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
import glob
import traceback

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
            'n_trials': 3,  # 3試行で学習
            'timeout': 1800,  # 30分に延長
            'direction': 'maximize',
            'metric': 'mean_reward',
            'eval_freq': 200,  # 評価頻度を調整
            'n_eval_episodes': 5,  # 評価エピソード数を増加
            'total_timesteps': 5000  # 学習時間を大幅増加
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
            
            # データペアの詳細情報をprint
            env = KyoteiEnvManager(data_dir=self.data_dir)
            self.logger.info(f"データペア数: {len(env.pairs)}")
            if env.pairs:
                self.logger.info(f"サンプルペア: {env.pairs[0]}")
            
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
            # 学習開始前にデータの欠損値状況を詳細チェック
            self.logger.info("=== 学習前データチェック ===")
            try:
                obs = env.reset()
                if isinstance(obs, (list, tuple)):
                    obs = obs[0]  # DummyVecEnvの場合
                if hasattr(obs, 'shape'):
                    self.logger.info(f"初期観測データ形状: {obs.shape}")
                    if hasattr(obs, 'dtype'):
                        self.logger.info(f"データ型: {obs.dtype}")
                else:
                    self.logger.info(f"観測データ型: {type(obs)}")
                
                # step()関数を1回実行してデータチェック
                self.logger.info("=== step()関数テスト ===")
                action = np.array([0])  # DummyVecEnv用にnumpy配列で渡す
                step_result = env.step(action)
                
                # step()の戻り値を詳細にprint
                self.logger.info(f"step_result の型: {type(step_result)}")
                self.logger.info(f"step_result の値: {step_result}")
                
                # DummyVecEnvの場合、step_resultは(obs, reward, done, info)のタプル
                if isinstance(step_result, (list, tuple)):
                    self.logger.info(f"step_result の長さ: {len(step_result)}")
                    for i, item in enumerate(step_result):
                        self.logger.info(f"step_result[{i}] の型: {type(item)}, 値: {item}")
                    
                    # アンパックを試行
                    try:
                        if len(step_result) == 4:
                            obs, reward, done, info = step_result
                            self.logger.info(f"アンパック成功 - obs: {type(obs)}, reward: {type(reward)}, done: {type(done)}")
                            self.logger.info(f"obs: {obs}")
                            self.logger.info(f"reward: {reward}")
                            self.logger.info(f"done: {done}")
                            self.logger.info(f"info: {info}")
                        else:
                            self.logger.error(f"予期しないstep_resultの長さ: {len(step_result)}")
                    except Exception as unpack_error:
                        self.logger.error(f"アンパックエラー: {unpack_error}")
                        self.logger.error(f"step_result の詳細: {step_result}")
                else:
                    self.logger.error(f"予期しないstep_resultの型: {type(step_result)}")
                    self.logger.error(f"step_result の詳細: {step_result}")
                
                # None/NaNチェック
                if obs is None:
                    self.logger.error("観測データがNone")
                elif hasattr(obs, 'dtype') and obs.dtype.kind in 'biufc':
                    if np.isnan(obs).any():
                        self.logger.error("観測データにNaNが含まれています")
                    else:
                        self.logger.info("観測データは正常")
                
                if reward is None:
                    self.logger.error("報酬がNone")
                elif isinstance(reward, (int, float)) and np.isnan(reward):
                    self.logger.error("報酬がNaN")
                else:
                    self.logger.info(f"報酬は正常: {reward}")
                    
            except Exception as e:
                self.logger.error(f"データチェックエラー: {e}")
            try:
                model.learn(
                    total_timesteps=self.optimization_config['total_timesteps'],
                    callback=eval_callback
                )
            except Exception as e:
                self.logger.error(f"学習中にエラー: {e}")
                traceback.print_exc()
                trial.set_user_attr("error", str(e))
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

def check_data_pairs(data_dir, min_pairs=10):
    race_files = glob.glob(os.path.join(data_dir, 'race_data_*.json'))
    odds_files = glob.glob(os.path.join(data_dir, 'odds_data_*.json'))
    race_keys = set(os.path.basename(f).replace('race_data_', '').replace('.json', '') for f in race_files)
    odds_keys = set(os.path.basename(f).replace('odds_data_', '').replace('.json', '') for f in odds_files)
    pairs = race_keys & odds_keys
    if len(pairs) < min_pairs:
        print(f"[ERROR] {data_dir} に有効なデータペア（race_data/odds_data）が{min_pairs}組未満です。\nペア数: {len(pairs)}\nデータ取得・配置を確認してください。")
        exit(1)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--data_dir', type=str, default="kyotei_predictor/data/raw", help='データディレクトリ')
    args = parser.parse_args()
    check_data_pairs(args.data_dir, min_pairs=1)  # 最小限のテスト用
    optimizer = KyoteiOptunaOptimizer(data_dir=args.data_dir)
    results = optimizer.run_optimization()
    print("\n" + "="*50)
    print(f"最適化完了!\n最適パラメータ: {results['best_params']}\n最適値: {results['best_value']}")
    print("="*50)

if __name__ == "__main__":
    main()