#!/usr/bin/env python3
"""
3連単投資価値分析システム

3連単予測確率とオッズを比較して投資価値を分析
期待値理論に基づく投資判断を提供
"""

import sys
import os
import json
import time
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
import numpy as np

# パス設定
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from kyotei_predictor.prediction_engine import PredictionEngine
from kyotei_predictor.data_integration import DataIntegration

class InvestmentValueAnalyzer:
    """3連単投資価値分析クラス"""
    
    def __init__(self):
        """初期化"""
        self.engine = PredictionEngine()
        self.data_integration = DataIntegration()
        
        # 投資戦略レベル
        self.investment_levels = {
            'conservative': 1.5,  # 保守的: 期待値1.5以上
            'balanced': 1.2,      # バランス: 期待値1.2以上
            'aggressive': 1.0     # 積極的: 期待値1.0以上
        }
    
    def calculate_expected_value(self, probability: float, odds: float) -> float:
        """
        期待値を計算
        
        Args:
            probability: 的中確率（0-1）
            odds: オッズ（倍率）
        
        Returns:
            期待値
        """
        return probability * odds
    
    def analyze_investment_value(self, trifecta_probabilities: List[Dict[str, Any]], 
                                odds_data: Dict[str, float], 
                                strategy_level: str = 'balanced') -> Dict[str, Any]:
        """
        投資価値を分析
        
        Args:
            trifecta_probabilities: 3連単確率リスト
            odds_data: オッズデータ {'1-2-3': 120.5, ...}
            strategy_level: 投資戦略レベル
        
        Returns:
            投資価値分析結果
        """
        threshold = self.investment_levels.get(strategy_level, 1.2)
        
        investment_opportunities = []
        total_probability = 0.0
        total_expected_value = 0.0
        
        for combo in trifecta_probabilities:
            combination = combo['combination']
            probability = combo['probability']
            expected_odds = combo['expected_odds']
            
            # 実際のオッズを取得（なければ期待オッズを使用）
            actual_odds = odds_data.get(combination, expected_odds)
            
            # オッズがNoneの場合は期待オッズを使用
            if actual_odds is None:
                actual_odds = expected_odds
            
            # 期待値計算
            expected_value = self.calculate_expected_value(probability, actual_odds)
            
            # 投資価値判定
            is_profitable = expected_value >= threshold
            
            if is_profitable:
                investment_opportunities.append({
                    'combination': combination,
                    'probability': probability,
                    'percentage': combo['percentage'],
                    'odds': actual_odds,
                    'expected_value': expected_value,
                    'investment_value': self._get_investment_value_level(expected_value),
                    'recommended_amount': self._calculate_recommended_amount(expected_value, probability)
                })
                
                total_probability += probability
                total_expected_value += expected_value
        
        # 投資推奨額の配分
        if investment_opportunities:
            self._distribute_investment_amounts(investment_opportunities)
        
        return {
            'strategy_level': strategy_level,
            'threshold': threshold,
            'total_opportunities': len(investment_opportunities),
            'total_probability': total_probability,
            'average_expected_value': total_expected_value / len(investment_opportunities) if investment_opportunities else 0,
            'investment_opportunities': sorted(investment_opportunities, 
                                             key=lambda x: x['expected_value'], reverse=True),
            'risk_analysis': self._analyze_risk(investment_opportunities),
            'portfolio_recommendation': self._generate_portfolio_recommendation(investment_opportunities)
        }
    
    def _get_investment_value_level(self, expected_value: float) -> str:
        """投資価値レベルを判定"""
        if expected_value >= 2.0:
            return 'very_high'
        elif expected_value >= 1.5:
            return 'high'
        elif expected_value >= 1.2:
            return 'medium'
        else:
            return 'low'
    
    def _calculate_recommended_amount(self, expected_value: float, probability: float) -> int:
        """推奨投資額を計算"""
        # 期待値と的中確率に基づいて投資額を決定
        base_amount = 1000  # 基本投資額
        
        # 期待値が高いほど投資額を増加
        ev_multiplier = min(expected_value / 1.2, 3.0)
        
        # 的中確率が高いほど投資額を増加
        prob_multiplier = min(probability * 100, 2.0)
        
        recommended = int(base_amount * ev_multiplier * prob_multiplier)
        return max(100, min(recommended, 10000))  # 100円〜10,000円の範囲
    
    def _distribute_investment_amounts(self, opportunities: List[Dict[str, Any]]):
        """投資額の配分を調整"""
        total_recommended = sum(opp['recommended_amount'] for opp in opportunities)
        
        # 総投資額を20,000円に制限
        max_total = 20000
        
        if total_recommended > max_total:
            # 期待値の高い順に配分を調整
            for opp in opportunities:
                opp['recommended_amount'] = int(opp['recommended_amount'] * max_total / total_recommended)
    
    def _analyze_risk(self, opportunities: List[Dict[str, Any]]) -> Dict[str, Any]:
        """リスク分析"""
        if not opportunities:
            return {'risk_level': 'none', 'diversification': 0, 'max_loss': 0}
        
        # リスクレベル判定
        avg_ev = np.mean([opp['expected_value'] for opp in opportunities])
        if avg_ev >= 1.5:
            risk_level = 'low'
        elif avg_ev >= 1.2:
            risk_level = 'medium'
        else:
            risk_level = 'high'
        
        # 分散度（組み合わせ数）
        diversification = len(opportunities)
        
        # 最大損失（全額投資した場合）
        max_loss = sum(opp['recommended_amount'] for opp in opportunities)
        
        return {
            'risk_level': risk_level,
            'diversification': diversification,
            'max_loss': max_loss,
            'average_expected_value': avg_ev
        }
    
    def _generate_portfolio_recommendation(self, opportunities: List[Dict[str, Any]]) -> Dict[str, Any]:
        """ポートフォリオ推奨を生成"""
        if not opportunities:
            return {'recommendation': 'no_investment', 'reason': '投資価値のある組み合わせがありません'}
        
        # 上位5位の組み合わせを推奨
        top_5 = opportunities[:5]
        total_investment = sum(opp['recommended_amount'] for opp in top_5)
        total_probability = sum(opp['probability'] for opp in top_5)
        avg_expected_value = np.mean([opp['expected_value'] for opp in top_5])
        
        return {
            'recommendation': 'invest',
            'target_combinations': [opp['combination'] for opp in top_5],
            'total_investment': total_investment,
            'total_probability': total_probability,
            'average_expected_value': avg_expected_value,
            'expected_return': total_investment * avg_expected_value,
            'risk_assessment': '分散投資によりリスクを軽減'
        }
    
    def analyze_race(self, race_data: Dict[str, Any], 
                    odds_data: Dict[str, float],
                    algorithm: str = 'equipment_focused',
                    strategy_level: str = 'balanced') -> Dict[str, Any]:
        """
        単一レースの投資価値分析
        
        Args:
            race_data: レースデータ
            odds_data: オッズデータ
            algorithm: 使用するアルゴリズム
            strategy_level: 投資戦略レベル
        
        Returns:
            投資価値分析結果
        """
        print(f"🎯 レース投資価値分析開始: {algorithm}アルゴリズム")
        
        # 3連単予測実行
        trifecta_result = self.engine.get_top_trifecta_recommendations(
            race_data, 
            algorithm=algorithm, 
            top_n=120  # 全組み合わせ
        )
        
        # 投資価値分析
        investment_analysis = self.analyze_investment_value(
            trifecta_result['top_combinations'],
            odds_data,
            strategy_level
        )
        
        # 結果にレース情報を追加
        result = {
            'race_info': trifecta_result['race_info'],
            'algorithm': algorithm,
            'strategy_level': strategy_level,
            'analysis_timestamp': datetime.now().isoformat(),
            'investment_analysis': investment_analysis
        }
        
        return result
    
    def generate_investment_report(self, analysis_result: Dict[str, Any]) -> str:
        """投資レポートを生成"""
        analysis = analysis_result['investment_analysis']
        race_info = analysis_result['race_info']
        
        report = f"""# 3連単投資価値分析レポート
**分析日時**: {analysis_result['analysis_timestamp']}
**レース情報**: {race_info.get('stadium', 'N/A')} 第{race_info.get('race_number', 'N/A')}レース
**使用アルゴリズム**: {analysis_result['algorithm']}
**投資戦略レベル**: {analysis_result['strategy_level']}

## 📊 投資機会サマリー
- **投資対象組み合わせ数**: {analysis['total_opportunities']}件
- **総的中確率**: {analysis['total_probability']:.4f} ({analysis['total_probability']*100:.2f}%)
- **平均期待値**: {analysis['average_expected_value']:.3f}

## 🎯 投資推奨組み合わせ（上位10位）
"""
        
        for i, opp in enumerate(analysis['investment_opportunities'][:10], 1):
            report += f"""
{i}位: {opp['combination']}
- 的中確率: {opp['percentage']:.2f}%
- オッズ: {opp['odds']:.1f}倍
- 期待値: {opp['expected_value']:.3f}
- 投資価値: {opp['investment_value']}
- 推奨投資額: {opp['recommended_amount']:,}円
"""
        
        # リスク分析
        risk = analysis['risk_analysis']
        report += f"""
## ⚠️ リスク分析
- **リスクレベル**: {risk.get('risk_level', 'unknown')}
- **分散度**: {risk.get('diversification', 0)}組み合わせ
- **最大損失**: {risk.get('max_loss', 0):,}円
- **平均期待値**: {risk.get('average_expected_value', 0):.3f}

## 💰 ポートフォリオ推奨
"""
        
        portfolio = analysis['portfolio_recommendation']
        if portfolio['recommendation'] == 'invest':
            report += f"""
- **推奨アクション**: 投資実行
- **対象組み合わせ**: {', '.join(portfolio['target_combinations'])}
- **総投資額**: {portfolio['total_investment']:,}円
- **総的中確率**: {portfolio['total_probability']:.4f} ({portfolio['total_probability']*100:.2f}%)
- **期待リターン**: {portfolio['expected_return']:.0f}円
- **リスク評価**: {portfolio['risk_assessment']}
"""
        else:
            report += f"""
- **推奨アクション**: 投資見送り
- **理由**: {portfolio['reason']}
"""
        
        return report
    
    def save_analysis_result(self, analysis_result: Dict[str, Any], 
                           output_dir: Optional[str] = None) -> Tuple[str, str]:
        """分析結果を保存"""
        if output_dir is None:
            output_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'outputs')
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        race_info = analysis_result['race_info']
        filename_base = f"investment_analysis_{race_info.get('stadium', 'UNKNOWN')}_{race_info.get('race_number', '0')}_{timestamp}"
        
        # JSON結果保存
        json_file = os.path.join(output_dir, f"{filename_base}.json")
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(analysis_result, f, ensure_ascii=False, indent=2)
        
        # レポート保存
        report = self.generate_investment_report(analysis_result)
        report_file = os.path.join(output_dir, f"{filename_base}_report.md")
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        return json_file, report_file

def main():
    """メイン処理（テスト用）"""
    import argparse
    
    parser = argparse.ArgumentParser(description='3連単投資価値分析')
    parser.add_argument('--race_file', type=str, help='レースデータファイル')
    parser.add_argument('--odds_file', type=str, help='オッズデータファイル')
    parser.add_argument('--algorithm', type=str, default='equipment_focused', help='使用アルゴリズム')
    parser.add_argument('--strategy', type=str, default='balanced', help='投資戦略レベル')
    args = parser.parse_args()
    
    analyzer = InvestmentValueAnalyzer()
    
    # テスト用のサンプルデータ
    if not args.race_file:
        print("❌ レースデータファイルを指定してください")
        return
    
    # レースデータ読み込み
    with open(args.race_file, 'r', encoding='utf-8') as f:
        race_data = json.load(f)
    
    # オッズデータ読み込み（またはサンプルデータ）
    if args.odds_file:
        with open(args.odds_file, 'r', encoding='utf-8') as f:
            odds_data = json.load(f)
    else:
        # サンプルオッズデータ
        odds_data = {
            '1-2-3': 120.5, '1-2-4': 150.2, '1-2-5': 180.0, '1-2-6': 200.0,
            '1-3-2': 130.0, '1-3-4': 160.0, '1-3-5': 190.0, '1-3-6': 210.0,
            '2-1-3': 140.0, '2-1-4': 170.0, '2-1-5': 200.0, '2-1-6': 220.0,
            '2-3-1': 150.0, '2-3-4': 180.0, '2-3-5': 210.0, '2-3-6': 230.0,
            '3-1-2': 160.0, '3-1-4': 190.0, '3-1-5': 220.0, '3-1-6': 240.0,
            '3-2-1': 170.0, '3-2-4': 200.0, '3-2-5': 230.0, '3-2-6': 250.0,
        }
    
    # 投資価値分析実行
    result = analyzer.analyze_race(
        race_data, 
        odds_data, 
        algorithm=args.algorithm,
        strategy_level=args.strategy
    )
    
    # 結果保存
    json_file, report_file = analyzer.save_analysis_result(result)
    
    print(f"✅ 投資価値分析完了:")
    print(f"  - JSON: {json_file}")
    print(f"  - レポート: {report_file}")
    
    # 結果表示
    analysis = result['investment_analysis']
    print(f"\n📊 投資機会: {analysis['total_opportunities']}件")
    print(f"📈 平均期待値: {analysis['average_expected_value']:.3f}")
    
    if analysis['investment_opportunities']:
        print(f"\n🎯 上位3位の投資機会:")
        for i, opp in enumerate(analysis['investment_opportunities'][:3], 1):
            print(f"{i}位: {opp['combination']} (期待値: {opp['expected_value']:.3f}, 投資額: {opp['recommended_amount']:,}円)")

if __name__ == "__main__":
    main() 