#!/usr/bin/env python3
"""
アンサンブル学習システム（Phase 3）
複数のモデルを組み合わせて予測精度を向上させる
"""

import os
import sys
import json
import numpy as np
from typing import List, Tuple, Dict, Any
from stable_baselines3 import PPO
import logging

# プロジェクトルートをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from kyotei_predictor.pipelines.kyotei_env import KyoteiEnvManager

class EnsembleTrifectaModel:
    """
    3連単予測のためのアンサンブル学習システム
    
    特徴:
    - 複数のPPOモデルを組み合わせ
    - 重み付き投票による統合予測
    - モデルの多様性を確保
    """
    
    def __init__(self):
        self.models = []
        self.weights = []
        self.model_info = []
        self.ensemble_id = None
    
    def add_model(self, model: PPO, weight: float = 1.0, model_info: Dict[str, Any] = None):
        """
        アンサンブルにモデルを追加
        
        Args:
            model: PPOモデル
            weight: 重み（デフォルト1.0）
            model_info: モデルの情報（ハイパーパラメータなど）
        """
        self.models.append(model)
        self.weights.append(weight)
        self.model_info.append(model_info or {})
        logging.info(f"Model added to ensemble. Total models: {len(self.models)}")
    
    def predict(self, state: np.ndarray) -> Tuple[int, float]:
        """
        アンサンブル予測を実行
        
        Args:
            state: 入力状態
            
        Returns:
            (action, confidence): 予測アクションと信頼度
        """
        if not self.models:
            raise ValueError("No models in ensemble")
        
        predictions = []
        for model, weight in zip(self.models, self.weights):
            # 各モデルの予測を取得
            action, _states = model.predict(state, deterministic=True)
            predictions.append((action, weight))
        
        # 重み付き投票による統合予測
        final_action, confidence = self.weighted_voting(predictions)
        return final_action, confidence
    
    def weighted_voting(self, predictions: List[Tuple[int, float]]) -> Tuple[int, float]:
        """
        重み付き投票による統合予測
        
        Args:
            predictions: [(action, weight), ...]
            
        Returns:
            (final_action, confidence): 最終予測と信頼度
        """
        # アクション別の重み合計を計算
        action_weights = {}
        total_weight = 0
        
        for action, weight in predictions:
            if action not in action_weights:
                action_weights[action] = 0
            action_weights[action] += weight
            total_weight += weight
        
        # 最も重みの高いアクションを選択
        best_action = max(action_weights.items(), key=lambda x: x[1])
        confidence = best_action[1] / total_weight if total_weight > 0 else 0
        
        return best_action[0], confidence
    
    def train_ensemble(self, data_dir: str, n_models: int = 3, **kwargs) -> None:
        """
        アンサンブルモデルの学習
        
        Args:
            data_dir: データディレクトリ
            n_models: 学習するモデル数
            **kwargs: その他の学習パラメータ
        """
        from kyotei_predictor.tools.optimization.optimize_graduated_reward import objective
        
        self.models = []
        self.weights = []
        self.model_info = []
        
        for i in range(n_models):
            logging.info(f"Training ensemble model {i+1}/{n_models}")
            
            # 各モデルを独立して学習
            # 実際の実装では、objective関数を呼び出してモデルを学習
            # ここでは簡略化のため、既存の最適化スクリプトを利用
            model = self._train_single_model(data_dir, model_id=i, **kwargs)
            self.add_model(model, weight=1.0, model_info={'model_id': i})
    
    def _train_single_model(self, data_dir: str, model_id: int, **kwargs) -> PPO:
        """
        単一モデルの学習（簡略化版）
        
        Args:
            data_dir: データディレクトリ
            model_id: モデルID
            **kwargs: 学習パラメータ
            
        Returns:
            学習済みPPOモデル
        """
        # 簡略化のため、基本的なPPOモデルを作成
        from stable_baselines3 import PPO
        from stable_baselines3.common.vec_env import DummyVecEnv
        
        def make_env():
            env = KyoteiEnvManager(data_dir=data_dir)
            return env
        
        env = DummyVecEnv([make_env])
        
        # デフォルトパラメータでモデルを作成
        model = PPO(
            "MlpPolicy",
            env,
            learning_rate=1e-4,
            batch_size=64,
            n_steps=2048,
            gamma=0.99,
            verbose=0
        )
        
        # 短時間で学習（実際の実装ではより長い時間）
        model.learn(total_timesteps=50000)
        
        return model
    
    def save_ensemble(self, output_path: str) -> None:
        """
        アンサンブルモデルを保存
        
        Args:
            output_path: 保存先パス
        """
        os.makedirs(output_path, exist_ok=True)
        
        # 各モデルを個別に保存
        for i, (model, weight, info) in enumerate(zip(self.models, self.weights, self.model_info)):
            model_path = os.path.join(output_path, f"model_{i}.zip")
            model.save(model_path)
            
            # 重みと情報を保存
            weight_info = {
                'weight': weight,
                'model_info': info,
                'model_path': model_path
            }
            
            weight_path = os.path.join(output_path, f"model_{i}_info.json")
            with open(weight_path, 'w', encoding='utf-8') as f:
                json.dump(weight_info, f, indent=2, ensure_ascii=False)
        
        # アンサンブル全体の情報を保存
        ensemble_info = {
            'n_models': len(self.models),
            'weights': self.weights,
            'model_info': self.model_info,
            'ensemble_id': self.ensemble_id
        }
        
        ensemble_path = os.path.join(output_path, "ensemble_info.json")
        with open(ensemble_path, 'w', encoding='utf-8') as f:
            json.dump(ensemble_info, f, indent=2, ensure_ascii=False)
        
        logging.info(f"Ensemble saved to {output_path}")
    
    def load_ensemble(self, input_path: str) -> None:
        """
        アンサンブルモデルを読み込み
        
        Args:
            input_path: 読み込み元パス
        """
        # アンサンブル情報を読み込み
        ensemble_path = os.path.join(input_path, "ensemble_info.json")
        with open(ensemble_path, 'r', encoding='utf-8') as f:
            ensemble_info = json.load(f)
        
        self.models = []
        self.weights = []
        self.model_info = []
        self.ensemble_id = ensemble_info.get('ensemble_id')
        
        # 各モデルを読み込み
        for i in range(ensemble_info['n_models']):
            model_path = os.path.join(input_path, f"model_{i}.zip")
            model = PPO.load(model_path)
            self.models.append(model)
            
            # 重みと情報を読み込み
            weight_path = os.path.join(input_path, f"model_{i}_info.json")
            with open(weight_path, 'r', encoding='utf-8') as f:
                weight_info = json.load(f)
            
            self.weights.append(weight_info['weight'])
            self.model_info.append(weight_info['model_info'])
        
        logging.info(f"Ensemble loaded from {input_path}. Models: {len(self.models)}")
    
    def evaluate_ensemble(self, eval_env, n_eval_episodes: int = 1000) -> Dict[str, Any]:
        """
        アンサンブルモデルの評価
        
        Args:
            eval_env: 評価環境
            n_eval_episodes: 評価エピソード数
            
        Returns:
            評価結果
        """
        from kyotei_predictor.tools.optimization.optimize_graduated_reward import evaluate_model
        
        # 各モデルの個別評価
        individual_results = []
        for i, model in enumerate(self.models):
            result = evaluate_model(model, eval_env, n_eval_episodes=n_eval_episodes)
            result['model_id'] = i
            individual_results.append(result)
        
        # アンサンブル評価
        ensemble_results = {
            'individual_results': individual_results,
            'ensemble_size': len(self.models),
            'weights': self.weights
        }
        
        # 平均的中率
        hit_rates = [r['hit_rate'] for r in individual_results]
        ensemble_results['mean_hit_rate'] = np.mean(hit_rates)
        ensemble_results['std_hit_rate'] = np.std(hit_rates)
        
        # 平均報酬
        mean_rewards = [r['mean_reward'] for r in individual_results]
        ensemble_results['mean_reward'] = np.mean(mean_rewards)
        ensemble_results['std_reward'] = np.std(mean_rewards)
        
        return ensemble_results

def create_ensemble_from_existing_models(model_paths: List[str], weights: List[float] = None) -> EnsembleTrifectaModel:
    """
    既存のモデルからアンサンブルを作成
    
    Args:
        model_paths: モデルファイルパスのリスト
        weights: 重みのリスト（Noneの場合は均等）
        
    Returns:
        アンサンブルモデル
    """
    ensemble = EnsembleTrifectaModel()
    
    if weights is None:
        weights = [1.0] * len(model_paths)
    
    for i, (model_path, weight) in enumerate(zip(model_paths, weights)):
        model = PPO.load(model_path)
        ensemble.add_model(model, weight=weight, model_info={'source_path': model_path})
    
    return ensemble

if __name__ == "__main__":
    # テスト実行
    logging.basicConfig(level=logging.INFO)
    
    # アンサンブルモデルの作成
    ensemble = EnsembleTrifectaModel()
    
    # データディレクトリの確認
    data_dir = "kyotei_predictor/data/raw"
    if os.path.exists(data_dir):
        print(f"Training ensemble with data from {data_dir}")
        ensemble.train_ensemble(data_dir, n_models=3)
        
        # 保存
        output_path = "kyotei_predictor/optuna_models/ensemble_test"
        ensemble.save_ensemble(output_path)
        
        print(f"Ensemble saved to {output_path}")
    else:
        print(f"Data directory not found: {data_dir}") 