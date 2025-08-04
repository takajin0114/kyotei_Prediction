#!/usr/bin/env python3
"""
既存の最適化システムと継続学習機能を統合するスクリプト
"""

import os
import sys
import json
import argparse
import logging
from datetime import datetime
from pathlib import Path

# プロジェクトルートをパスに追加
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
sys.path.insert(0, project_root)

from kyotei_predictor.tools.ai.enhanced_training_system import create_enhanced_training_system
from kyotei_predictor.tools.optimization.optimize_graduated_reward_202401 import optimize_graduated_reward_202401
from kyotei_predictor.tools.optimization.optimize_graduated_reward_continuous import optimize_graduated_reward_continuous

def setup_continuous_learning_system():
    """継続学習システムの初期化"""
    print("=== 継続学習システムの初期化 ===")
    
    enhanced_system = create_enhanced_training_system(
        model_dir="./optuna_models",
        history_file="./optuna_results/training_history.json",
        curriculum_file="./optuna_results/curriculum_config.json"
    )
    
    # 段階的学習の初期化
    enhanced_system.curriculum.create_default_curriculum()
    
    # 初期状況の表示
    initial_status = enhanced_system.get_training_status()
    print(f"初期学習状況: {initial_status}")
    
    return enhanced_system

def run_continuous_optimization(
    n_trials=10,
    study_name="integrated_continuous_opt",
    data_dir="kyotei_predictor/data/raw/2024-01",
    test_mode=True,
    resume_existing=False
):
    """継続学習機能を統合した最適化を実行"""
    
    print("=== 継続学習機能を統合した最適化開始 ===")
    print(f"開始時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 継続学習システムの初期化
    enhanced_system = setup_continuous_learning_system()
    
    # 既存の最適化システムを継続学習機能で拡張して実行
    study = optimize_graduated_reward_continuous(
        n_trials=n_trials,
        study_name=study_name,
        data_dir=data_dir,
        test_mode=test_mode,
        resume_existing=resume_existing
    )
    
    if study:
        print("継続学習機能を統合した最適化が正常に完了しました")
        
        # 最終結果の表示
        final_status = enhanced_system.get_training_status()
        print(f"\n=== 最終結果 ===")
        print(f"学習セッション数: {final_status['overall_progress']['total_training_sessions']}")
        print(f"カリキュラム完了率: {final_status['overall_progress']['curriculum_completion_rate']:.1f}%")
        print(f"最良のスコア: {study.best_value:.4f}")
        
        # 学習推奨事項の表示
        recommendations = enhanced_system.get_training_recommendations()
        print(f"\n=== 学習推奨事項 ===")
        for i, rec in enumerate(recommendations, 1):
            print(f"{i}. {rec}")
        
        return study
    else:
        print("最適化中にエラーが発生しました")
        return None

def run_legacy_optimization_with_continuous_features(
    n_trials=10,
    study_name="legacy_with_continuous",
    data_dir="kyotei_predictor/data/raw/2024-01",
    test_mode=True,
    resume_existing=False
):
    """既存の最適化システムを継続学習機能で拡張して実行"""
    
    print("=== 既存最適化システムを継続学習機能で拡張 ===")
    print(f"開始時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 継続学習システムの初期化
    enhanced_system = setup_continuous_learning_system()
    
    # 既存の最適化システムを実行（継続学習機能は後処理で適用）
    study = optimize_graduated_reward_202401(
        n_trials=n_trials,
        study_name=study_name,
        data_dir=data_dir,
        test_mode=test_mode,
        resume_existing=resume_existing
    )
    
    if study:
        print("既存最適化システムの実行が完了しました")
        
        # 継続学習機能で後処理
        print("継続学習機能による後処理を実行中...")
        
        # 学習履歴の記録
        for trial in study.trials:
            if trial.value is not None:
                performance_metrics = {
                    'mean_reward': float(trial.value),
                    'trial_number': trial.number,
                    'params': trial.params
                }
                
                # 学習履歴を記録
                model_path = f"./optuna_models/trial_{trial.number}/best_model.zip"
                enhanced_system.continuous_manager.record_training_history(model_path, performance_metrics)
        
        # 段階的学習の進捗を更新
        enhanced_system.curriculum.complete_current_stage({
            'mean_reward': float(study.best_value),
            'total_trials': len(study.trials)
        })
        
        # 最終結果の表示
        final_status = enhanced_system.get_training_status()
        print(f"\n=== 最終結果 ===")
        print(f"学習セッション数: {final_status['overall_progress']['total_training_sessions']}")
        print(f"カリキュラム完了率: {final_status['overall_progress']['curriculum_completion_rate']:.1f}%")
        print(f"最良のスコア: {study.best_value:.4f}")
        
        # 学習進捗の可視化
        enhanced_system.visualize_training_progress("./optuna_results/legacy_training_progress.png")
        
        # 学習データのエクスポート
        enhanced_system.export_training_data("./optuna_results/legacy_training_data_export.json")
        
        return study
    else:
        print("最適化中にエラーが発生しました")
        return None

def analyze_continuous_learning_progress():
    """継続学習の進捗を分析"""
    print("=== 継続学習進捗分析 ===")
    
    enhanced_system = create_enhanced_training_system(
        model_dir="./optuna_models",
        history_file="./optuna_results/training_history.json",
        curriculum_file="./optuna_results/curriculum_config.json"
    )
    
    # 学習状況の取得
    status = enhanced_system.get_training_status()
    
    print(f"継続学習状況:")
    print(f"  最新モデル: {status['continuous_learning']['latest_model']}")
    print(f"  学習履歴数: {status['continuous_learning']['history_count']}")
    print(f"  カリキュラム進捗: {status['curriculum_learning']['progress_percentage']:.1f}%")
    print(f"  完了段階数: {status['curriculum_learning']['completed_stages']}/{status['curriculum_learning']['total_stages']}")
    
    # 学習推奨事項の表示
    recommendations = enhanced_system.get_training_recommendations()
    print(f"\n学習推奨事項:")
    for i, rec in enumerate(recommendations, 1):
        print(f"  {i}. {rec}")
    
    # 学習進捗の可視化
    enhanced_system.visualize_training_progress("./optuna_results/analysis_progress.png")
    
    return status

def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description='継続学習機能を統合した最適化スクリプト')
    parser.add_argument('--mode', type=str, choices=['continuous', 'legacy', 'analyze'], 
                       default='continuous', help='実行モード')
    parser.add_argument('--n_trials', type=int, default=10, help='試行回数')
    parser.add_argument('--study_name', type=str, default='integrated_continuous_opt', help='スタディ名')
    parser.add_argument('--data_dir', type=str, default='kyotei_predictor/data/raw/2024-01', help='データディレクトリ')
    parser.add_argument('--test_mode', action='store_true', help='テストモード')
    parser.add_argument('--resume_existing', action='store_true', help='既存スタディを継続')
    
    args = parser.parse_args()
    
    # ログ設定
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # ディレクトリ作成
    os.makedirs("./optuna_models", exist_ok=True)
    os.makedirs("./optuna_logs", exist_ok=True)
    os.makedirs("./optuna_studies", exist_ok=True)
    os.makedirs("./optuna_results", exist_ok=True)
    
    if args.mode == 'continuous':
        # 継続学習機能を統合した最適化
        study = run_continuous_optimization(
            n_trials=args.n_trials,
            study_name=args.study_name,
            data_dir=args.data_dir,
            test_mode=args.test_mode,
            resume_existing=args.resume_existing
        )
        
    elif args.mode == 'legacy':
        # 既存の最適化システムを継続学習機能で拡張
        study = run_legacy_optimization_with_continuous_features(
            n_trials=args.n_trials,
            study_name=args.study_name,
            data_dir=args.data_dir,
            test_mode=args.test_mode,
            resume_existing=args.resume_existing
        )
        
    elif args.mode == 'analyze':
        # 継続学習の進捗を分析
        status = analyze_continuous_learning_progress()
        print("分析が完了しました")
        
    else:
        print(f"不明なモード: {args.mode}")
        return

if __name__ == "__main__":
    main() 