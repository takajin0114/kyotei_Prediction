"""
trifecta_probability.py

3連単（Trifecta）確率計算クラス

- 各艇のスコア・勝率リストから全120通りの3連単組み合わせ確率を計算
- 独立性仮定・重み調整・今後の拡張性を考慮
- PredictionEngineやテストから呼び出し可能なAPI設計

作成日: 2025-07-04
"""

import itertools
from typing import List, Dict, Any, Optional

class TrifectaProbabilityCalculator:
    """
    3連単確率計算クラス
    特徴量・重みを柔軟に指定可能
    """
    DEFAULT_WEIGHTS = {
        'all_stadium_rate': 0.35,
        'event_going_rate': 0.25,
        'rating': 0.1,
        'boat_quinella_rate': 0.15,
        'motor_quinella_rate': 0.15,
        'course_bias': 0.0,  # コース特性（拡張）
        'odds_bias': 0.0,    # オッズ補正（拡張）
    }
    RATING_COEFFICIENTS = {
        'A1': 1.2,
        'A2': 1.1,
        'B1': 1.0,
        'B2': 0.9
    }

    def __init__(self, second_weight: float = 0.8, third_weight: float = 0.6, weights: Optional[dict] = None):
        """
        Args:
            second_weight: 2着艇の確率重み（デフォルト0.8）
            third_weight: 3着艇の確率重み（デフォルト0.6）
            weights: 特徴量ごとの重みdict（未指定時はDEFAULT_WEIGHTS）
        """
        self.second_weight = second_weight
        self.third_weight = third_weight
        self.weights = weights or self.DEFAULT_WEIGHTS.copy()

    def calculate(self, predictions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        3連単の全組み合わせ確率を計算
        Args:
            predictions: 各艇の予測データリスト
        Returns:
            3連単確率リスト（確率順）
        """
        # 1. 各艇のスコア計算
        scores = []
        for pred in predictions:
            score = 0.0
            # 選手成績
            score += pred.get('rate_in_all_stadium', 0) * self.weights.get('all_stadium_rate', 0)
            score += pred.get('rate_in_event_going_stadium', 0) * self.weights.get('event_going_rate', 0)
            # 級別補正
            rating = pred.get('current_rating', 'B2')
            rating_coeff = self.RATING_COEFFICIENTS.get(rating, 1.0)
            score += rating_coeff * self.weights.get('rating', 0)
            # 機材成績
            score += pred.get('boat_quinella_rate', 0) * self.weights.get('boat_quinella_rate', 0)
            score += pred.get('motor_quinella_rate', 0) * self.weights.get('motor_quinella_rate', 0)
            # 拡張: course_bias, odds_bias など
            score += pred.get('course_bias', 0) * self.weights.get('course_bias', 0)
            score += pred.get('odds_bias', 0) * self.weights.get('odds_bias', 0)
            scores.append(score)
        # 2. スコア正規化（0-1→100%）
        min_score = min(scores)
        max_score = max(scores)
        norm_scores = [((s - min_score) / (max_score - min_score) if max_score > min_score else 1.0) for s in scores]
        total = sum(norm_scores)
        win_probabilities = [(s / total * 100) if total > 0 else 100.0 / len(norm_scores) for s in norm_scores]
        # 3. pit_numberリスト
        pit_numbers = [pred.get('pit_number') for pred in predictions]
        # 4. 3連単確率計算
        trifecta_combinations = []
        for combination in itertools.permutations(pit_numbers, 3):
            first, second, third = combination
            first_idx = pit_numbers.index(first)
            second_idx = pit_numbers.index(second)
            third_idx = pit_numbers.index(third)
            first_prob = win_probabilities[first_idx] / 100
            second_prob = win_probabilities[second_idx] / 100 * self.second_weight
            third_prob = win_probabilities[third_idx] / 100 * self.third_weight
            combination_prob = first_prob * second_prob * third_prob
            trifecta_combinations.append({
                'combination': f"{first}-{second}-{third}",
                'pit_numbers': [first, second, third],
                'probability': combination_prob,
                'percentage': round(combination_prob * 100, 2),
                'expected_odds': round(1 / combination_prob, 1) if combination_prob > 0 else 999.9
            })
        trifecta_combinations.sort(key=lambda x: x['probability'], reverse=True)
        return trifecta_combinations

    @staticmethod
    def calc_expected_value(probability: float, odds: float) -> float:
        """
        期待値（Expected Value）を計算
        Args:
            probability: 的中確率（0-1）
            odds: オッズ（倍率）
        Returns:
            期待値（1.0以上なら投資価値あり）
        """
        return probability * odds

    @staticmethod
    def analyze_investment_value(trifecta_combinations: list, odds_map: dict, threshold: float = 1.0) -> list:
        """
        3連単組み合わせごとに期待値・投資価値を判定
        Args:
            trifecta_combinations: [{'combination': '1-2-3', 'probability': 0.008, ...}, ...]
            odds_map: {'1-2-3': 120.5, ...}  # 実際のオッズ
            threshold: 期待値の閾値（デフォルト1.0）
        Returns:
            [{'combination': str, 'probability': float, 'odds': float, 'expected_value': float, 'is_profitable': bool}, ...]
        """
        results = []
        for combo in trifecta_combinations:
            comb = combo['combination']
            prob = combo['probability']
            odds = odds_map.get(comb, combo.get('expected_odds', 0))
            ev = TrifectaProbabilityCalculator.calc_expected_value(prob, odds)
            results.append({
                'combination': comb,
                'probability': prob,
                'odds': odds,
                'expected_value': ev,
                'is_profitable': ev >= threshold
            })
        return results

# --- サンプル利用例 ---
if __name__ == "__main__":
    # 仮の予測データ（特徴量付き＋コース・オッズ補正）
    predictions = [
        {'pit_number': 1, 'rate_in_all_stadium': 6.5, 'rate_in_event_going_stadium': 7.0, 'current_rating': 'A1', 'boat_quinella_rate': 44.0, 'motor_quinella_rate': 38.0, 'course_bias': 0.5, 'odds_bias': 0.1},
        {'pit_number': 2, 'rate_in_all_stadium': 5.8, 'rate_in_event_going_stadium': 6.2, 'current_rating': 'A2', 'boat_quinella_rate': 41.0, 'motor_quinella_rate': 35.0, 'course_bias': 0.3, 'odds_bias': 0.2},
        {'pit_number': 3, 'rate_in_all_stadium': 5.2, 'rate_in_event_going_stadium': 5.5, 'current_rating': 'B1', 'boat_quinella_rate': 38.0, 'motor_quinella_rate': 32.0, 'course_bias': 0.2, 'odds_bias': 0.3},
        {'pit_number': 4, 'rate_in_all_stadium': 4.9, 'rate_in_event_going_stadium': 5.0, 'current_rating': 'B1', 'boat_quinella_rate': 36.0, 'motor_quinella_rate': 30.0, 'course_bias': 0.1, 'odds_bias': 0.4},
        {'pit_number': 5, 'rate_in_all_stadium': 4.5, 'rate_in_event_going_stadium': 4.8, 'current_rating': 'B2', 'boat_quinella_rate': 33.0, 'motor_quinella_rate': 28.0, 'course_bias': 0.0, 'odds_bias': 0.5},
        {'pit_number': 6, 'rate_in_all_stadium': 4.2, 'rate_in_event_going_stadium': 4.5, 'current_rating': 'B2', 'boat_quinella_rate': 30.0, 'motor_quinella_rate': 25.0, 'course_bias': -0.1, 'odds_bias': 0.6},
    ]
    calculator = TrifectaProbabilityCalculator(weights={
        'all_stadium_rate': 0.2,
        'event_going_rate': 0.2,
        'rating': 0.1,
        'boat_quinella_rate': 0.2,
        'motor_quinella_rate': 0.2,
        'course_bias': 0.15,  # コース特性重み
        'odds_bias': 0.15,    # オッズ補正重み
    })
    results = calculator.calculate(predictions)
    print("コース・オッズ補正込みの上位5件:")
    for combo in results[:5]:
        print(combo)
    # 重みをカスタマイズした例
    custom_weights = {
        'all_stadium_rate': 0.2,
        'event_going_rate': 0.2,
        'rating': 0.1,
        'boat_quinella_rate': 0.25,
        'motor_quinella_rate': 0.25,
    }
    calculator2 = TrifectaProbabilityCalculator(weights=custom_weights)
    results2 = calculator2.calculate(predictions)
    print("\nカスタム重みでの上位5件:")
    for combo in results2[:5]:
        print(combo)
    # --- 投資価値分析サンプル ---
    print("\n--- 投資価値分析サンプル ---")
    # 仮のオッズデータ
    odds_map = {
        '1-2-3': 120.5,
        '2-1-3': 98.0,
        '1-3-2': 150.0,
        '2-3-1': 110.0,
        '3-1-2': 200.0,
        # ...
    }
    invest_results = TrifectaProbabilityCalculator.analyze_investment_value(results, odds_map)
    for r in invest_results[:5]:
        print(r) 