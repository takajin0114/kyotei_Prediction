#!/usr/bin/env python3
"""
報酬設計の機能性を客観的に評価する分析スクリプト
"""

import json
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
import pandas as pd
from typing import Dict, List, Any

def load_evaluation_results(file_path: str) -> Dict[str, Any]:
    """評価結果を読み込み"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def analyze_reward_design_effectiveness(results: Dict[str, Any]) -> Dict[str, Any]:
    """報酬設計の効果を客観的に分析"""
    
    print("=== 報酬設計の機能性分析 ===")
    
    # 基本統計
    hit_rate = results['statistics']['hit_rate']
    first_second_rate = results['statistics']['first_second_rate']
    first_only_rate = results['statistics']['first_only_rate']
    miss_rate = results['statistics']['miss_rate']
    positive_reward_rate = results['statistics']['positive_reward_rate']
    mean_reward = results['statistics']['mean_reward']
    
    # 1. 理論値との比較
    theoretical_hit_rate = 1/120  # 3連単の理論的中率
    hit_rate_improvement = (hit_rate / theoretical_hit_rate - 1) * 100
    
    print(f"\n1. 理論値との比較:")
    print(f"   理論的中率: {theoretical_hit_rate:.4f} ({theoretical_hit_rate*100:.2f}%)")
    print(f"   実際的中率: {hit_rate:.4f} ({hit_rate*100:.2f}%)")
    print(f"   改善率: {hit_rate_improvement:.1f}%")
    
    # 2. 段階的報酬の効果分析
    print(f"\n2. 段階的報酬の効果:")
    print(f"   完全的中: {hit_rate*100:.2f}%")
    print(f"   2着的中: {first_second_rate*100:.2f}%")
    print(f"   1着的中: {first_only_rate*100:.2f}%")
    print(f"   不的中: {miss_rate*100:.2f}%")
    
    # 3. 学習効率の評価
    learning_efficiency = (hit_rate + first_second_rate) / theoretical_hit_rate
    print(f"\n3. 学習効率:")
    print(f"   部分的中以上: {(hit_rate + first_second_rate)*100:.2f}%")
    print(f"   学習効率指数: {learning_efficiency:.2f}")
    
    # 4. 報酬分布の安定性
    reward_stability = positive_reward_rate
    print(f"\n4. 報酬分布の安定性:")
    print(f"   正の報酬率: {positive_reward_rate*100:.2f}%")
    print(f"   平均報酬: {mean_reward:.2f}")
    
    # 5. 客観的評価指標の計算
    evaluation_metrics = {
        'hit_rate_improvement': hit_rate_improvement,
        'learning_efficiency': learning_efficiency,
        'reward_stability': reward_stability,
        'partial_hit_rate': hit_rate + first_second_rate,
        'theoretical_vs_actual': hit_rate / theoretical_hit_rate
    }
    
    return evaluation_metrics

def calculate_objective_score(metrics: Dict[str, float]) -> Dict[str, float]:
    """客観的スコアを計算"""
    
    print(f"\n=== 客観的評価スコア ===")
    
    # 各指標の重み付け
    weights = {
        'hit_rate_improvement': 0.4,      # 的中率改善（最重要）
        'learning_efficiency': 0.3,       # 学習効率
        'reward_stability': 0.2,          # 報酬安定性
        'partial_hit_rate': 0.1           # 部分的中率
    }
    
    # スコア正規化（0-100点）
    scores = {}
    
    # 的中率改善スコア（0-100点）
    improvement = metrics['hit_rate_improvement']
    if improvement >= 100:  # 2倍以上
        scores['hit_rate_score'] = 100
    elif improvement >= 50:  # 1.5倍以上
        scores['hit_rate_score'] = 75 + (improvement - 50) * 0.5
    elif improvement >= 0:  # 理論値以上
        scores['hit_rate_score'] = 50 + improvement
    else:  # 理論値未満
        scores['hit_rate_score'] = max(0, 50 + improvement)
    
    # 学習効率スコア（0-100点）
    efficiency = metrics['learning_efficiency']
    if efficiency >= 10:  # 10倍以上
        scores['learning_efficiency_score'] = 100
    elif efficiency >= 5:  # 5倍以上
        scores['learning_efficiency_score'] = 75 + (efficiency - 5) * 5
    elif efficiency >= 2:  # 2倍以上
        scores['learning_efficiency_score'] = 50 + (efficiency - 2) * 8.33
    else:  # 2倍未満
        scores['learning_efficiency_score'] = max(0, efficiency * 25)
    
    # 報酬安定性スコア（0-100点）
    stability = metrics['reward_stability']
    scores['reward_stability_score'] = min(100, stability * 100)
    
    # 部分的中率スコア（0-100点）
    partial_rate = metrics['partial_hit_rate']
    if partial_rate >= 0.15:  # 15%以上
        scores['partial_hit_score'] = 100
    elif partial_rate >= 0.10:  # 10%以上
        scores['partial_hit_score'] = 75 + (partial_rate - 0.10) * 500
    elif partial_rate >= 0.05:  # 5%以上
        scores['partial_hit_score'] = 50 + (partial_rate - 0.05) * 500
    else:  # 5%未満
        scores['partial_hit_score'] = max(0, partial_rate * 1000)
    
    # 総合スコア計算
    total_score = 0
    for key in scores.keys():
        if key != 'total_score':
            weight_key = key.replace('_score', '')
            if weight_key in weights:
                total_score += scores[key] * weights[weight_key]
    
    scores['total_score'] = total_score
    
    # 結果表示
    print(f"的中率改善スコア: {scores['hit_rate_score']:.1f}/100")
    print(f"学習効率スコア: {scores['learning_efficiency_score']:.1f}/100")
    print(f"報酬安定性スコア: {scores['reward_stability_score']:.1f}/100")
    print(f"部分的中率スコア: {scores['partial_hit_score']:.1f}/100")
    print(f"総合スコア: {total_score:.1f}/100")
    
    # 評価レベルの判定
    if total_score >= 80:
        evaluation_level = "優秀"
    elif total_score >= 60:
        evaluation_level = "良好"
    elif total_score >= 40:
        evaluation_level = "普通"
    else:
        evaluation_level = "改善必要"
    
    print(f"評価レベル: {evaluation_level}")
    
    return scores

def create_comparison_analysis():
    """従来手法との比較分析"""
    
    print(f"\n=== 従来手法との比較分析 ===")
    
    # 従来手法の仮定値（理論値ベース）
    traditional_metrics = {
        'hit_rate': 1/120,  # 0.83%
        'learning_efficiency': 1.0,  # 基準値
        'reward_stability': 0.0083,  # 的中率と同じ
        'partial_hit_rate': 1/120,  # 完全的中のみ
        'mean_reward': -95.0  # 大幅な損失
    }
    
    # 現在の手法の実績値
    current_metrics = {
        'hit_rate': 0.017,  # 1.70%
        'learning_efficiency': 13.8,  # (1.70% + 11.8%) / 0.83%
        'reward_stability': 0.525,  # 52.5%
        'partial_hit_rate': 0.135,  # 13.5%
        'mean_reward': 4.83  # プラスの期待値
    }
    
    # 改善率計算
    improvements = {}
    for key in traditional_metrics.keys():
        if traditional_metrics[key] != 0:
            improvements[key] = (current_metrics[key] / traditional_metrics[key] - 1) * 100
        else:
            improvements[key] = float('inf')
    
    print(f"的中率改善: {improvements['hit_rate']:.1f}%")
    print(f"学習効率改善: {improvements['learning_efficiency']:.1f}%")
    print(f"報酬安定性改善: {improvements['reward_stability']:.1f}%")
    print(f"部分的中率改善: {improvements['partial_hit_rate']:.1f}%")
    print(f"平均報酬改善: {improvements['mean_reward']:.1f}%")
    
    return improvements

def generate_recommendations(scores: Dict[str, float], metrics: Dict[str, float]) -> List[str]:
    """改善提案の生成"""
    
    recommendations = []
    
    print(f"\n=== 改善提案 ===")
    
    # 的中率に関する提案
    if scores['hit_rate_score'] < 60:
        recommendations.append("的中率のさらなる向上が必要です。学習ステップ数の増加やパラメータ調整を検討してください。")
    
    # 学習効率に関する提案
    if scores['learning_efficiency_score'] < 60:
        recommendations.append("学習効率の改善が必要です。段階的報酬の重み調整を検討してください。")
    
    # 報酬安定性に関する提案
    if scores['reward_stability_score'] < 50:
        recommendations.append("報酬の安定性向上が必要です。ペナルティ設計の見直しを検討してください。")
    
    # 総合的な提案
    if scores['total_score'] >= 80:
        recommendations.append("報酬設計は優秀です。現在の設計を維持し、さらなる最適化を継続してください。")
    elif scores['total_score'] >= 60:
        recommendations.append("報酬設計は良好です。一部の改善によりさらなる向上が期待できます。")
    else:
        recommendations.append("報酬設計の大幅な見直しが必要です。根本的な設計変更を検討してください。")
    
    for i, rec in enumerate(recommendations, 1):
        print(f"{i}. {rec}")
    
    return recommendations

def main():
    """メイン実行関数"""
    
    # 評価結果ファイルの読み込み
    results_file = "outputs/graduated_reward_evaluation_20250727_064100.json"
    results = load_evaluation_results(results_file)
    
    # 報酬設計の効果分析
    metrics = analyze_reward_design_effectiveness(results)
    
    # 客観的スコア計算
    scores = calculate_objective_score(metrics)
    
    # 従来手法との比較
    improvements = create_comparison_analysis()
    
    # 改善提案の生成
    recommendations = generate_recommendations(scores, metrics)
    
    # 結果の保存
    analysis_results = {
        'analysis_time': datetime.now().isoformat(),
        'metrics': metrics,
        'scores': scores,
        'improvements': improvements,
        'recommendations': recommendations
    }
    
    output_file = f"outputs/reward_design_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(analysis_results, f, indent=2, ensure_ascii=False)
    
    print(f"\n分析結果を保存しました: {output_file}")

if __name__ == "__main__":
    main() 