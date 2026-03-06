#!/usr/bin/env python3
"""
3連単的中率改善策の設定管理クラス
"""

import json
import os
from typing import Dict, Any, Optional, Union
from pathlib import Path


class ImprovementConfigManager:
    """
    3連単的中率改善策の設定管理クラス
    
    特徴:
    - 設定ファイルの読み込み・保存
    - パラメータの動的変更
    - 設定の検証
    - デフォルト値の提供
    """
    
    def __init__(self, config_path: str = None):
        """
        初期化
        
        Args:
            config_path: 設定ファイルのパス（Noneの場合はデフォルトパス）
        """
        if config_path is None:
            config_path = os.path.join(
                os.path.dirname(__file__), 
                "improvement_config.json"
            )
        
        self.config_path = config_path
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """設定ファイルを読み込み"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"設定ファイルが見つかりません: {self.config_path}")
            return self._get_default_config()
        except json.JSONDecodeError as e:
            print(f"設定ファイルのJSON形式エラー: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """デフォルト設定を返す"""
        return {
            "reward_design": {
                "phase1": {
                    "win_multiplier": 1.5,
                    "partial_second_hit_reward": 10,
                    "partial_first_hit_penalty": -10,
                    "no_hit_penalty": -80
                }
            },
            "learning_parameters": {
                "phase2": {
                    "total_timesteps": 200000,
                    "n_eval_episodes": 5000
                }
            }
        }
    
    def get_active_reward_phase(self) -> str:
        """設定で指定された報酬フェーズ（phase1 / original）を返す。"""
        return self.config.get("active_reward_phase", "phase1")

    def get_reward_params(self, phase: Optional[str] = None) -> Dict[str, Any]:
        """
        報酬設計パラメータを取得。

        Args:
            phase: フェーズ名（"phase1" または "original"）。None のときは active_reward_phase を使用。

        Returns:
            報酬設計パラメータの辞書
        """
        if phase is None:
            phase = self.get_active_reward_phase()
        return self.config.get("reward_design", {}).get(phase, {})
    
    def get_learning_params(self, phase: str = "phase2", mode: str = "normal") -> Dict[str, Any]:
        """
        学習パラメータを取得
        
        Args:
            phase: フェーズ名（"phase2" または "original"）
            mode: モード（"normal", "test_mode", "minimal_mode"）
        
        Returns:
            学習パラメータの辞書
        """
        params = self.config.get("learning_parameters", {}).get(phase, {})
        
        if mode == "test_mode":
            return params.get("test_mode", params)
        elif mode == "minimal_mode":
            return params.get("minimal_mode", params)
        else:
            return params
    
    def get_hyperparameters(self, phase: str = "phase2") -> Dict[str, Any]:
        """
        ハイパーパラメータ範囲を取得
        
        Args:
            phase: フェーズ名（"phase2" または "original"）
        
        Returns:
            ハイパーパラメータ範囲の辞書
        """
        return self.config.get("hyperparameters", {}).get(phase, {})
    
    def get_ensemble_params(self) -> Dict[str, Any]:
        """アンサンブル学習パラメータを取得"""
        return self.config.get("ensemble", {}).get("phase3", {})
    
    def get_continuous_learning_params(self) -> Dict[str, Any]:
        """継続的学習パラメータを取得"""
        return self.config.get("continuous_learning", {}).get("phase4", {})
    
    def get_monitoring_params(self) -> Dict[str, Any]:
        """性能監視パラメータを取得"""
        return self.config.get("monitoring", {})
    
    def get_testing_params(self) -> Dict[str, Any]:
        """テストパラメータを取得"""
        return self.config.get("testing", {})
    
    def get_paths(self) -> Dict[str, str]:
        """ファイルパス設定を取得"""
        return self.config.get("paths", {})

    def get_evaluation_params(self) -> Dict[str, Any]:
        """
        評価用パラメータを取得（optimize_for, roi_evaluation_enabled）。

        Returns:
            optimize_for: "hit_rate" | "mean_reward" | "roi" | "hybrid"
            roi_evaluation_enabled: bool
        """
        return self.config.get("evaluation", {})

    def get_optimize_for(self) -> str:
        """最適化の目的指標を返す。未設定時は 'hybrid'（従来互換）。"""
        return self.config.get("evaluation", {}).get("optimize_for", "hybrid")

    # 検証ツールで使用。許可値: "first_only" | "selected_bets"
    EVALUATION_MODE_FIRST_ONLY = "first_only"
    EVALUATION_MODE_SELECTED_BETS = "selected_bets"
    EVALUATION_MODES = (EVALUATION_MODE_FIRST_ONLY, EVALUATION_MODE_SELECTED_BETS)

    def get_evaluation_mode(self) -> str:
        """
        検証時の評価モードを返す。未設定時は 'first_only'（従来互換）。

        Returns:
            "first_only": 1位予想に100円のみで検証。
            "selected_bets": 予測の selected_bets に基づく ROI 検証（B案用）。
        """
        mode = self.config.get("evaluation", {}).get("evaluation_mode", self.EVALUATION_MODE_FIRST_ONLY)
        if mode in self.EVALUATION_MODES:
            return mode
        return self.EVALUATION_MODE_FIRST_ONLY

    def get_roi_evaluation_enabled(self) -> bool:
        """ROI を評価に含めるか。未設定時は True。"""
        return self.config.get("evaluation", {}).get("roi_evaluation_enabled", True)

    def get_betting_params(self) -> Dict[str, Any]:
        """
        買い目選定用パラメータを取得。

        Returns:
            strategy, top_n, score_threshold, ev_threshold 等
        """
        return self.config.get("betting", {})

    def get_betting_strategy(self) -> str:
        """買い目選定戦略名。未設定時は 'single'。"""
        return self.config.get("betting", {}).get("strategy", "single")

    def get_betting_top_n(self) -> int:
        """上位N点買いの N。未設定時は 3。"""
        return int(self.config.get("betting", {}).get("top_n", 3))

    def get_betting_score_threshold(self) -> float:
        """スコア閾値。未設定時は 0.05。"""
        return float(self.config.get("betting", {}).get("score_threshold", 0.05))

    def get_betting_ev_threshold(self) -> float:
        """EV 閾値。未設定時は 0.0。"""
        return float(self.config.get("betting", {}).get("ev_threshold", 0.0))
    
    def update_config(self, updates: Dict[str, Any]) -> None:
        """
        設定を更新
        
        Args:
            updates: 更新する設定の辞書
        """
        self._update_nested_dict(self.config, updates)
        self._save_config()
    
    def _update_nested_dict(self, base_dict: Dict[str, Any], updates: Dict[str, Any]) -> None:
        """ネストした辞書を更新"""
        for key, value in updates.items():
            if key in base_dict and isinstance(base_dict[key], dict) and isinstance(value, dict):
                self._update_nested_dict(base_dict[key], value)
            else:
                base_dict[key] = value
    
    def _save_config(self) -> None:
        """設定をファイルに保存"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"設定ファイルの保存エラー: {e}")
    
    def validate_config(self) -> bool:
        """
        設定の妥当性を検証
        
        Returns:
            妥当性の結果
        """
        try:
            # 報酬設計の検証
            reward_params = self.get_reward_params("phase1")
            required_reward_keys = ["win_multiplier", "partial_second_hit_reward", 
                                  "partial_first_hit_penalty", "no_hit_penalty"]
            
            for key in required_reward_keys:
                if key not in reward_params:
                    print(f"報酬設計パラメータが不足: {key}")
                    return False
            
            # 学習パラメータの検証
            learning_params = self.get_learning_params("phase2")
            required_learning_keys = ["total_timesteps", "n_eval_episodes"]
            
            for key in required_learning_keys:
                if key not in learning_params:
                    print(f"学習パラメータが不足: {key}")
                    return False
            
            return True
            
        except Exception as e:
            print(f"設定検証エラー: {e}")
            return False
    
    def get_config_summary(self) -> Dict[str, Any]:
        """
        設定のサマリーを取得
        
        Returns:
            設定サマリーの辞書
        """
        return {
            "reward_design": {
                "phase1": self.get_reward_params("phase1"),
                "original": self.get_reward_params("original")
            },
            "learning_parameters": {
                "phase2": self.get_learning_params("phase2"),
                "original": self.get_learning_params("original")
            },
            "hyperparameters": {
                "phase2": self.get_hyperparameters("phase2"),
                "original": self.get_hyperparameters("original")
            },
            "ensemble": self.get_ensemble_params(),
            "continuous_learning": self.get_continuous_learning_params(),
            "monitoring": self.get_monitoring_params(),
            "testing": self.get_testing_params(),
            "paths": self.get_paths()
        }
    
    def print_config_summary(self) -> None:
        """設定サマリーを表示"""
        summary = self.get_config_summary()
        print("=== 3連単的中率改善策 設定サマリー ===")
        
        for section, params in summary.items():
            print(f"\n--- {section} ---")
            if isinstance(params, dict):
                for key, value in params.items():
                    if isinstance(value, dict):
                        print(f"  {key}:")
                        for sub_key, sub_value in value.items():
                            print(f"    {sub_key}: {sub_value}")
                    else:
                        print(f"  {key}: {value}")
            else:
                print(f"  {params}")


def create_config_manager(config_path: str = None) -> ImprovementConfigManager:
    """
    設定管理クラスのインスタンスを作成
    
    Args:
        config_path: 設定ファイルのパス
    
    Returns:
        ImprovementConfigManagerのインスタンス
    """
    return ImprovementConfigManager(config_path)


# 使用例
if __name__ == "__main__":
    # 設定管理クラスのインスタンスを作成
    config_manager = create_config_manager()
    
    # 設定サマリーを表示
    config_manager.print_config_summary()
    
    # 特定のパラメータを取得
    reward_params = config_manager.get_reward_params("phase1")
    print(f"\nPhase 1 報酬設計パラメータ: {reward_params}")
    
    # 設定の妥当性を検証
    is_valid = config_manager.validate_config()
    print(f"\n設定妥当性: {'✓' if is_valid else '✗'}") 