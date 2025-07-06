#!/usr/bin/env python3
"""
3連単特化モデル

着順依存性と艇間相関を考慮した3連単予測システム
"""

import sys
import os
import json
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime
import itertools

# パス設定
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from kyotei_predictor.prediction_engine import PredictionEngine
from kyotei_predictor.data_integration import DataIntegration

class TrifectaDependentModel:
    """3連単特化モデルクラス"""
    
    def __init__(self):
        """初期化"""
        self.engine = PredictionEngine()
        self.data_integration = DataIntegration()
        
        # 着順依存性の重み係数
        self.position_weights = {
            '1st': 1.0,    # 1着の重み
            '2nd': 0.8,    # 2着の重み（1着が決まった後の条件付き確率）
            '3rd': 0.6     # 3着の重み（1着、2着が決まった後の条件付き確率）
        }
        
        # 艇間相関マトリックス（初期値）
        self.correlation_matrix = None
        
    def calculate_dependent_probabilities(self, race_data: Dict[str, Any], 
                                        algorithm: str = 'equipment_focused') -> Dict[str, Any]:
        """
        着順依存性を考慮した3連単確率を計算
        
        Args:
            race_data: レースデータ
            algorithm: 使用するアルゴリズム
        
        Returns:
            着順依存性を考慮した3連単確率
        """
        print(f"🎯 着順依存性を考慮した3連単確率計算開始: {algorithm}アルゴリズム")
        
        # 基本予測を取得
        basic_predictions = self.engine.predict(race_data, algorithm=algorithm)
        
        # 艇数
        num_boats = len(basic_predictions['predictions'])
        
        # 着順依存性を考慮した確率計算
        dependent_probabilities = {}
        
        # 全組み合わせを生成
        all_combinations = list(itertools.permutations(range(1, num_boats + 1), 3))
        
        for combo in all_combinations:
            combination_str = f"{combo[0]}-{combo[1]}-{combo[2]}"
            
            # 1着確率
            p1 = self._get_boat_probability(basic_predictions, combo[0], 1)
            
            # 2着確率（1着が決まった後の条件付き確率）
            p2_given_1 = self._get_conditional_probability(basic_predictions, combo[1], [combo[0]], 2)
            
            # 3着確率（1着、2着が決まった後の条件付き確率）
            p3_given_12 = self._get_conditional_probability(basic_predictions, combo[2], [combo[0], combo[1]], 3)
            
            # 着順依存性を考慮した確率
            dependent_prob = p1 * p2_given_1 * p3_given_12
            
            # 艇間相関を考慮した調整
            correlation_adjustment = self._calculate_correlation_adjustment(combo)
            adjusted_prob = dependent_prob * correlation_adjustment
            
            dependent_probabilities[combination_str] = {
                'combination': combination_str,
                'probability': adjusted_prob,
                'percentage': adjusted_prob * 100,
                'p1': p1,
                'p2_given_1': p2_given_1,
                'p3_given_12': p3_given_12,
                'correlation_adjustment': correlation_adjustment,
                'expected_odds': self._calculate_expected_odds(adjusted_prob)
            }
        
        # 確率の正規化
        total_prob = sum(prob['probability'] for prob in dependent_probabilities.values())
        if total_prob > 0:
            for combo in dependent_probabilities.values():
                combo['probability'] /= total_prob
                combo['percentage'] = combo['probability'] * 100
        
        # 結果をソート
        sorted_combinations = sorted(
            dependent_probabilities.values(),
            key=lambda x: x['probability'],
            reverse=True
        )
        
        return {
            'race_info': basic_predictions['race_info'],
            'algorithm': algorithm,
            'model_type': 'dependent_trifecta',
            'total_combinations': len(sorted_combinations),
            'top_combinations': sorted_combinations,
            'summary': self._generate_summary(sorted_combinations),
            'calculation_timestamp': datetime.now().isoformat()
        }
    
    def _get_boat_probability(self, predictions: Dict[str, Any], boat_number: int, position: int) -> float:
        """艇の特定順位の確率を取得"""
        for pred in predictions['predictions']:
            if pred['boat_number'] == boat_number:
                if position == 1:
                    return pred['probability']
                elif position == 2:
                    return pred.get('second_probability', pred['probability'] * 0.8)
                elif position == 3:
                    return pred.get('third_probability', pred['probability'] * 0.6)
        return 0.0
    
    def _get_conditional_probability(self, predictions: Dict[str, Any], 
                                   target_boat: int, 
                                   excluded_boats: List[int], 
                                   position: int) -> float:
        """条件付き確率を計算"""
        # 除外された艇を除いた確率分布を計算
        available_boats = [pred for pred in predictions['predictions'] 
                          if pred['boat_number'] not in excluded_boats]
        
        if not available_boats:
            return 0.0
        
        # 対象艇の確率を取得
        target_prob = 0.0
        total_prob = 0.0
        
        for boat in available_boats:
            if position == 2:
                prob = boat.get('second_probability', boat['probability'] * 0.8)
            elif position == 3:
                prob = boat.get('third_probability', boat['probability'] * 0.6)
            else:
                prob = boat['probability']
            
            total_prob += prob
            if boat['boat_number'] == target_boat:
                target_prob = prob
        
        # 条件付き確率を計算
        if total_prob > 0:
            return target_prob / total_prob
        return 0.0
    
    def _calculate_correlation_adjustment(self, combination: Tuple[int, int, int]) -> float:
        """艇間相関による調整係数を計算"""
        # 初期値（後で学習データから計算）
        adjustment = 1.0
        
        # 特定の組み合わせパターンに対する調整
        boat1, boat2, boat3 = combination
        
        # 隣接艇の相関（1-2, 2-3）
        if abs(boat1 - boat2) == 1:
            adjustment *= 1.1  # 隣接艇は相関が高い
        
        if abs(boat2 - boat3) == 1:
            adjustment *= 1.1
        
        # 内側・外側コースの相関
        if boat1 <= 3 and boat2 <= 3 and boat3 <= 3:
            adjustment *= 1.05  # 内側コース集中
        elif boat1 >= 4 and boat2 >= 4 and boat3 >= 4:
            adjustment *= 1.05  # 外側コース集中
        
        return adjustment
    
    def _calculate_expected_odds(self, probability: float) -> float:
        """期待オッズを計算"""
        if probability <= 0:
            return 1000.0  # 最大オッズ
        
        # 理論オッズ（確率の逆数）
        theoretical_odds = 1.0 / probability
        
        # 実際のオッズは理論オッズより低い（胴元の取り分）
        actual_odds = theoretical_odds * 0.8
        
        return max(100.0, min(actual_odds, 1000.0))
    
    def _generate_summary(self, combinations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """結果サマリーを生成"""
        if not combinations:
            return {}
        
        most_likely = combinations[0]
        probabilities = [combo['probability'] for combo in combinations]
        
        return {
            'most_likely': most_likely,
            'average_probability': np.mean(probabilities),
            'std_probability': np.std(probabilities),
            'max_probability': max(probabilities),
            'min_probability': min(probabilities),
            'average_odds': np.mean([combo['expected_odds'] for combo in combinations]),
            'probability_distribution': {
                'high': len([p for p in probabilities if p > 0.01]),
                'medium': len([p for p in probabilities if 0.005 <= p <= 0.01]),
                'low': len([p for p in probabilities if p < 0.005])
            }
        }
    
    def learn_from_historical_data(self, data_dir: Optional[str] = None) -> Dict[str, Any]:
        """過去データから艇間相関を学習"""
        print("📚 過去データから艇間相関を学習中...")
        
        if data_dir is None:
            data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
        
        # 過去データを読み込み
        race_files = [f for f in os.listdir(data_dir) if f.startswith('race_data_') and f.endswith('.json')]
        
        correlation_data = {
            'adjacent_boats': {},  # 隣接艇の相関
            'course_patterns': {},  # コースパターンの相関
            'position_patterns': {}  # 着順パターンの相関
        }
        
        processed_races = 0
        
        for race_file in race_files[:100]:  # 最初の100レースで学習
            try:
                with open(os.path.join(data_dir, race_file), 'r', encoding='utf-8') as f:
                    race_data = json.load(f)
                
                # 実際の結果を抽出
                actual_result = self._extract_actual_result(race_data)
                if not actual_result:
                    continue
                
                # 相関データを収集
                self._collect_correlation_data(actual_result, correlation_data)
                processed_races += 1
                
            except Exception as e:
                print(f"⚠️ データ読み込みエラー: {race_file} - {e}")
                continue
        
        print(f"✅ 相関学習完了: {processed_races}レースを処理")
        
        # 相関マトリックスを更新
        self._update_correlation_matrix(correlation_data)
        
        return {
            'processed_races': processed_races,
            'correlation_data': correlation_data,
            'learning_timestamp': datetime.now().isoformat()
        }
    
    def _extract_actual_result(self, race_data: Dict[str, Any]) -> Optional[str]:
        """実際の結果を抽出"""
        try:
            if 'actual_result' in race_data:
                return race_data['actual_result']
            
            race_records = race_data.get('race_records', [])
            if not race_records:
                return None
            
            valid_records = [r for r in race_records if r.get('arrival') is not None]
            if not valid_records:
                return None
            
            sorted_records = sorted(valid_records, key=lambda x: x.get('arrival', 999))
            top_3 = []
            
            for record in sorted_records:
                if record.get('arrival') is not None and record.get('arrival') <= 3:
                    top_3.append(str(record['pit_number']))
            
            if len(top_3) >= 3:
                return f"{top_3[0]}-{top_3[1]}-{top_3[2]}"
            
            return None
            
        except Exception as e:
            print(f"⚠️ 結果抽出エラー: {e}")
            return None
    
    def _collect_correlation_data(self, actual_result: str, correlation_data: Dict[str, Any]):
        """相関データを収集"""
        try:
            boats = [int(x) for x in actual_result.split('-')]
            
            # 隣接艇の相関
            for i in range(len(boats) - 1):
                pair = f"{boats[i]}-{boats[i+1]}"
                correlation_data['adjacent_boats'][pair] = correlation_data['adjacent_boats'].get(pair, 0) + 1
            
            # コースパターンの相関
            pattern = 'inner' if all(b <= 3 for b in boats) else 'outer' if all(b >= 4 for b in boats) else 'mixed'
            correlation_data['course_patterns'][pattern] = correlation_data['course_patterns'].get(pattern, 0) + 1
            
            # 着順パターンの相関
            pattern = f"{boats[0]}-{boats[1]}-{boats[2]}"
            correlation_data['position_patterns'][pattern] = correlation_data['position_patterns'].get(pattern, 0) + 1
            
        except Exception as e:
            print(f"⚠️ 相関データ収集エラー: {e}")
    
    def _update_correlation_matrix(self, correlation_data: Dict[str, Any]):
        """相関マトリックスを更新"""
        # 隣接艇の相関係数を計算
        total_adjacent = sum(correlation_data['adjacent_boats'].values())
        if total_adjacent > 0:
            for pair, count in correlation_data['adjacent_boats'].items():
                correlation_data['adjacent_boats'][pair] = count / total_adjacent
        
        # コースパターンの相関係数を計算
        total_patterns = sum(correlation_data['course_patterns'].values())
        if total_patterns > 0:
            for pattern, count in correlation_data['course_patterns'].items():
                correlation_data['course_patterns'][pattern] = count / total_patterns
        
        print(f"📊 相関マトリックス更新完了:")
        print(f"  - 隣接艇相関: {len(correlation_data['adjacent_boats'])}パターン")
        print(f"  - コースパターン: {correlation_data['course_patterns']}")
    
    def save_model(self, output_dir: Optional[str] = None) -> str:
        """モデルを保存"""
        if output_dir is None:
            output_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'outputs')
        
        os.makedirs(output_dir, exist_ok=True)
        
        model_data = {
            'model_type': 'trifecta_dependent',
            'position_weights': self.position_weights,
            'correlation_matrix': self.correlation_matrix,
            'created_timestamp': datetime.now().isoformat()
        }
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        model_file = os.path.join(output_dir, f'trifecta_dependent_model_{timestamp}.json')
        
        with open(model_file, 'w', encoding='utf-8') as f:
            json.dump(model_data, f, ensure_ascii=False, indent=2)
        
        print(f"💾 モデル保存完了: {model_file}")
        return model_file

def main():
    """メイン処理（テスト用）"""
    import argparse
    
    parser = argparse.ArgumentParser(description='3連単特化モデル')
    parser.add_argument('--race_file', type=str, required=True, help='レースデータファイル')
    parser.add_argument('--learn', action='store_true', help='過去データから学習')
    parser.add_argument('--algorithm', type=str, default='equipment_focused', help='使用アルゴリズム')
    args = parser.parse_args()
    
    model = TrifectaDependentModel()
    
    # 過去データから学習
    if args.learn:
        learning_result = model.learn_from_historical_data()
        print(f"📚 学習結果: {learning_result['processed_races']}レースを処理")
    
    # レースデータ読み込み
    with open(args.race_file, 'r', encoding='utf-8') as f:
        race_data = json.load(f)
    
    # 着順依存性を考慮した3連単予測
    result = model.calculate_dependent_probabilities(race_data, algorithm=args.algorithm)
    
    # 結果表示
    print(f"\n🎯 着順依存性を考慮した3連単予測結果:")
    print(f"  - 最有力組み合わせ: {result['summary']['most_likely']['combination']}")
    print(f"  - 最有力確率: {result['summary']['most_likely']['percentage']:.4f}%")
    print(f"  - 平均確率: {result['summary']['average_probability']:.6f}")
    print(f"  - 確率標準偏差: {result['summary']['std_probability']:.6f}")
    
    print(f"\n📊 上位10位の組み合わせ:")
    for i, combo in enumerate(result['top_combinations'][:10], 1):
        print(f"{i:2d}位: {combo['combination']} - {combo['percentage']:.4f}% (期待オッズ: {combo['expected_odds']:.1f}倍)")
    
    # モデル保存
    model.save_model()
    
    print(f"\n✅ 3連単特化モデル処理完了")

if __name__ == "__main__":
    main() 